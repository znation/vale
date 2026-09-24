/*
 *
 *  Violent Adventure to Lethal Ends (VALE)
 *  Copyright (C) Timo Kiviluoto
 *  Released under the GNU General
 *  Public License
 *
 *  See LICENSING which should be included
 *  along with this file for more details
 *
 */

#include <cstdarg>
#include <map>
#include <memory>
#include <vector>

#include "png.h"

#include "allocate.h"
#include "rawbit.h"
#include "bitmap.h"
#include "graphics.h"
#include "save.h"
#include "femath.h"
#include "error.h"

void rawbitmap::MaskedBlit(bitmap* Bitmap, packcol16* Color) const { MaskedBlit(Bitmap, ZERO_V2, ZERO_V2, GetSize(), Color); }

rawbitmap::rawbitmap(cfestring& RequestedName) : Density(graphics::GetDensity())
{
  int FileDensity;
  festring FileName = graphics::ResolveDensityAsset(RequestedName, FileDensity);
  std::shared_ptr<FILE> File(fopen(FileName.CStr(), "rb"), fclose);

  if(!File)
    ABORT("Bitmap %s not found!", FileName.CStr());

  png_structp PNGStruct = png_create_read_struct(PNG_LIBPNG_VER_STRING, 0, 0, 0);

  if(!PNGStruct)
    ABORT("Couldn't read PNG file %s!", FileName.CStr());

  png_infop PNGInfo = png_create_info_struct(PNGStruct);

  if(!PNGInfo)
    abort();

  if(setjmp(png_jmpbuf(PNGStruct)) != 0)
    abort();

  png_init_io(PNGStruct, File.get());
  png_read_info(PNGStruct, PNGInfo);

  Size.X = png_get_image_width(PNGStruct, PNGInfo);
  Size.Y = png_get_image_height(PNGStruct, PNGInfo);

  if(png_get_bit_depth(PNGStruct, PNGInfo) != 8)
    ABORT("%s has wrong bit depth %d, should be 8!", FileName.CStr(),
          int(png_get_bit_depth(PNGStruct, PNGInfo)));

  png_colorp PNGPalette;
  int PaletteSize;

  if(!png_get_PLTE(PNGStruct, PNGInfo, &PNGPalette, &PaletteSize))
    ABORT("%s is not in indexed color mode!", FileName.CStr());

  if(PaletteSize != 256)
    ABORT("%s has wrong palette size %d, should be 256!", FileName.CStr(), PaletteSize);

  Palette = new uchar[768];

  for(int i = 0; i < PaletteSize; ++i)
  {
    Palette[i * 3 + 0] = PNGPalette[255 - i].red;
    Palette[i * 3 + 1] = PNGPalette[255 - i].green;
    Palette[i * 3 + 2] = PNGPalette[255 - i].blue;
  }

  Alloc2D(PaletteBuffer, Size.Y, Size.X);
  png_read_image(PNGStruct, PaletteBuffer);
  paletteindex* Buffer = PaletteBuffer[0];
  paletteindex* End = &PaletteBuffer[Size.Y - 1][Size.X];

  for(; Buffer != End; ++Buffer)
    *Buffer = 255 - *Buffer;

  png_destroy_read_struct(&PNGStruct, &PNGInfo, nullptr);

  if(FileDensity != Density)
    Rescale(FileDensity);
}

/* Convert PaletteBuffer from FromDensity to Density. Upscaling repeats each pixel. Downscaling
   (e.g. 64-pixel master art shown at 32 pixels) resamples each block by class: a mostly
   transparent block stays transparent; otherwise the block takes its most common class, material
   pixels average their brightness within their channel and fixed colours average in RGB and snap
   to the nearest palette entry. Indices are rescaled, never flattened to colours, so material
   pixels keep their channel and brightness. */
void rawbitmap::Rescale(int FromDensity)
{
  if(Size.X % FromDensity || Size.Y % FromDensity)
    ABORT("Graphics file of %dx%d pixels is not a whole number of %dx pixels!", Size.X, Size.Y, FromDensity);

  v2 Layout(Size.X / FromDensity, Size.Y / FromDensity);
  v2 NewSize = Layout * Density;
  paletteindex** NewBuffer;
  Alloc2D(NewBuffer, NewSize.Y, NewSize.X);

  if(Density > FromDensity)
  {
    cint Factor = Density / FromDensity;

    for(int y = 0; y < NewSize.Y; ++y)
      for(int x = 0; x < NewSize.X; ++x)
        NewBuffer[y][x] = PaletteBuffer[y / Factor][x / Factor];
  }
  else
  {
    cint Factor = FromDensity / Density;
    cint Samples = Factor * Factor;
    auto IsTransparentIndex = [this](int Index)
    {
      cuchar* RGB = &Palette[Index * 3];
      return ((RGB[0] & 0xF8) << 8 | (RGB[1] & 0xFC) << 3 | RGB[2] >> 3) == TRANSPARENT_COLOR;
    };
    std::vector<int> FixedIndices;

    for(int c = 0; c < 192; ++c)
      if(!IsTransparentIndex(c))
        FixedIndices.push_back(c);

    std::map<long, int> NearestCache;
    auto NearestFixed = [&](int R, int G, int B)
    {
      long Key = long(R) << 16 | G << 8 | B;
      std::map<long, int>::iterator Cached = NearestCache.find(Key);

      if(Cached != NearestCache.end())
        return Cached->second;

      int Best = FixedIndices.front();
      long BestDistance = 0x7FFFFFFF;

      for(int Index : FixedIndices)
      {
        cuchar* RGB = &Palette[Index * 3];
        long Distance = (RGB[0] - R) * (RGB[0] - R) + (RGB[1] - G) * (RGB[1] - G) + (RGB[2] - B) * (RGB[2] - B);

        if(Distance < BestDistance)
        {
          Best = Index;
          BestDistance = Distance;
        }
      }

      return NearestCache[Key] = Best;
    };

    for(int y = 0; y < NewSize.Y; ++y)
      for(int x = 0; x < NewSize.X; ++x)
      {
        /* Classes 0-3 are material channels, 4 is fixed colours, 5 is transparent. */
        int Count[6] = { 0, 0, 0, 0, 0, 0 }, Brightness[4] = { 0, 0, 0, 0 };
        int Red = 0, Green = 0, Blue = 0, Transparent = TRANSPARENT_PALETTE_INDEX;

        for(int c = 0; c < Samples; ++c)
        {
          int Index = PaletteBuffer[y * Factor + c / Factor][x * Factor + c % Factor];

          if(IsMaterialColor(Index))
          {
            ++Count[GetMaterialColorIndex(Index)];
            Brightness[GetMaterialColorIndex(Index)] += Index & 15;
          }
          else if(IsTransparentIndex(Index))
          {
            ++Count[5];
            Transparent = Index;
          }
          else
          {
            ++Count[4];
            Red += Palette[Index * 3];
            Green += Palette[Index * 3 + 1];
            Blue += Palette[Index * 3 + 2];
          }
        }

        if(Count[5] * 2 > Samples)
        {
          NewBuffer[y][x] = Transparent;
          continue;
        }

        int Class = 0;

        for(int c = 1; c < 5; ++c)
          if(Count[c] > Count[Class])
            Class = c;

        if(Class < 4)
          NewBuffer[y][x] = 192 + (Class << 4) + (Brightness[Class] + Count[Class] / 2) / Count[Class];
        else
          NewBuffer[y][x] = NearestFixed(Red / Count[4], Green / Count[4], Blue / Count[4]);
      }
  }

  delete [] PaletteBuffer;
  PaletteBuffer = NewBuffer;
  Size = NewSize;
}

rawbitmap::rawbitmap(v2 LayoutSize) : Density(graphics::GetDensity())
{
  Size = LayoutSize * Density;
  Palette = new uchar[768];
  Alloc2D(PaletteBuffer, Size.Y, Size.X);
}

rawbitmap::~rawbitmap()
{
  delete [] Palette;
  delete [] PaletteBuffer;

  for(fontcache::value_type& p : FontCache)
  {
    delete p.second.first;
    delete p.second.second;
  }
}

void rawbitmap::Save(cfestring& FileName)
{
  std::shared_ptr<FILE> File(fopen(FileName.CStr(), "wb"), fclose);
  png_structp PNGStruct = png_create_write_struct(PNG_LIBPNG_VER_STRING, 0, 0, 0);
  png_infop PNGInfo = png_create_info_struct(PNGStruct);
  png_init_io(PNGStruct, File.get());

  png_color PNGPalette[256];

  for(int i = 0; i < 256; ++i)
  {
    PNGPalette[255 - i].red = Palette[i * 3 + 0];
    PNGPalette[255 - i].green = Palette[i * 3 + 1];
    PNGPalette[255 - i].blue = Palette[i * 3 + 2];
  }

  png_set_IHDR(PNGStruct, PNGInfo, Size.X, Size.Y, 8, PNG_COLOR_TYPE_PALETTE,
               PNG_INTERLACE_NONE, PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT);
  png_set_PLTE(PNGStruct, PNGInfo, PNGPalette, 256);
  png_write_info(PNGStruct, PNGInfo);

  paletteindex* Buffer = PaletteBuffer[0];
  paletteindex* End = &PaletteBuffer[Size.Y - 1][Size.X];

  for(; Buffer != End; ++Buffer)
    *Buffer = 255 - *Buffer;

  png_write_image(PNGStruct, PaletteBuffer);
  png_write_end(PNGStruct, PNGInfo);
  png_destroy_write_struct(&PNGStruct, &PNGInfo);

  Buffer = PaletteBuffer[0];

  for(; Buffer != End; ++Buffer)
    *Buffer = 255 - *Buffer;
}

void rawbitmap::MaskedBlit(bitmap* Bitmap, v2 Src, v2 Dest, v2 Border, packcol16* Color) const
{
  if(Bitmap->GetDensity() != Density)
    ABORT("Masked blit between a %dx sheet and a %dx bitmap!", Density, Bitmap->GetDensity());

  Src *= Density;
  Dest *= Density;
  Border *= Density;

  if(!femath::Clip(Src.X, Src.Y, Dest.X, Dest.Y, Border.X, Border.Y,
                   Size.X, Size.Y, Bitmap->GetPhysicalSize().X, Bitmap->GetPhysicalSize().Y))
    return;

  paletteindex* Buffer = &PaletteBuffer[Src.Y][Src.X];
  packcol16* DestBuffer = &Bitmap->GetImage()[Dest.Y][Dest.X];
  int BitmapXSize = Bitmap->GetPhysicalSize().X;
  uchar* Palette = this->Palette; // eliminate the efficiency cost of dereferencing

  for(int y = 0; y < Border.Y; ++y)
  {
    for(int x = 0; x < Border.X; ++x)
    {
      int PaletteElement = Buffer[x];

      if(PaletteElement >= 192)
      {
        int ThisColor = Color[(PaletteElement - 192) >> 4];
        int Index = PaletteElement & 15;
        int Red = (ThisColor >> 8 & 0xF8) * Index;
        int Green = (ThisColor >> 3 & 0xFC) * Index;
        int Blue = (ThisColor << 3 & 0xF8) * Index;

        if(Red > 0x7FF)
          Red = 0x7FF;

        if(Green > 0x7FF)
          Green = 0x7FF;

        if(Blue > 0x7FF)
          Blue = 0x7FF;

        DestBuffer[x] = (Red << 5 & 0xF800) | (Green & 0x7E0) | (Blue >> 6 & 0x1F);
      }
      else
      {
        int PaletteIndex = PaletteElement + (PaletteElement << 1);
        int ThisColor = ((Palette[PaletteIndex] & 0xFFF8) << 8)
                        | ((Palette[PaletteIndex + 1] & 0xFFFC) << 3)
                        |  (Palette[PaletteIndex + 2] >> 3);

        if(ThisColor != TRANSPARENT_COLOR)
          DestBuffer[x] = ThisColor;
      }
    }

    DestBuffer += BitmapXSize;
    Buffer += Size.X;
  }
}

cachedfont* rawbitmap::Colorize(cpackcol16* Color, alpha BaseAlpha, cpackalpha* Alpha) const
{
  cachedfont* Bitmap = new cachedfont(GetSize());
  paletteindex* Buffer = PaletteBuffer[0];
  packcol16* DestBuffer = Bitmap->GetImage()[0];
  uchar* Palette = this->Palette; // eliminate the efficiency cost of dereferencing
  packalpha* AlphaMap;
  truth UseAlpha;

  if(BaseAlpha != 255 || (Alpha && (Alpha[0] != 255 || Alpha[1] != 255 || Alpha[2] != 255 || Alpha[3] != 255)))
  {
    Bitmap->CreateAlphaMap(BaseAlpha);
    AlphaMap = Bitmap->GetAlphaMap()[0];
    UseAlpha = true;
  }
  else
  {
    AlphaMap = 0;
    UseAlpha = false;
  }

  int BitmapXSize = Bitmap->GetPhysicalSize().X;

  for(int y = 0; y < Size.Y; ++y)
  {
    for(int x = 0; x < Size.X; ++x)
    {
      int PaletteElement = Buffer[x];

      if(PaletteElement >= 192)
      {
        int ColorIndex = (PaletteElement - 192) >> 4;
        int ThisColor = Color[ColorIndex];

        if(ThisColor != TRANSPARENT_COLOR)
        {
          int Index = PaletteElement & 15;
          int Red = (ThisColor >> 8 & 0xF8) * Index;
          int Green = (ThisColor >> 3 & 0xFC) * Index;
          int Blue = (ThisColor << 3 & 0xF8) * Index;

          if(Red > 0x7FF)
            Red = 0x7FF;

          if(Green > 0x7FF)
            Green = 0x7FF;

          if(Blue > 0x7FF)
            Blue = 0x7FF;

          DestBuffer[x] = (Red << 5 & 0xF800)
                          | (Green & 0x7E0)
                          | (Blue >> 6 & 0x1F);

          if(UseAlpha)
            AlphaMap[x] = Alpha[ColorIndex];
        }
        else
          DestBuffer[x] = TRANSPARENT_COLOR;
      }
      else
      {
        int PaletteIndex = PaletteElement + (PaletteElement << 1);
        DestBuffer[x] = ((Palette[PaletteIndex] & 0xFFF8) << 8)
                        | ((Palette[PaletteIndex + 1] & 0xFFFC) << 3)
                        |  (Palette[PaletteIndex + 2] >> 3);
      }
    }

    DestBuffer += BitmapXSize;
    AlphaMap += BitmapXSize;
    Buffer += Size.X;
  }

  return Bitmap;
}

bitmap* rawbitmap::Colorize(v2 Pos, v2 Border, v2 Move, cpackcol16* Color, alpha BaseAlpha, cpackalpha* Alpha,
                            cuchar* RustData, cuchar* BurnData, truth AllowReguralColors) const
{
  bitmap* Bitmap = new bitmap(Border);
  v2 TargetPos(0, 0);

  if(Bitmap->GetDensity() != Density)
    ABORT("Colorizing a %dx sheet into a %dx bitmap!", Density, Bitmap->GetDensity());

  Pos *= Density;
  Border *= Density;
  Move *= Density;

  if(Move.X || Move.Y)
  {
    Bitmap->ClearToColor(TRANSPARENT_COLOR);

    if(Move.X < 0)
    {
      Pos.X -= Move.X;
      Border.X += Move.X;
    }
    else if(Move.X > 0)
    {
      TargetPos.X = Move.X;
      Border.X -= Move.X;
    }

    if(Move.Y < 0)
    {
      Pos.Y -= Move.Y;
      Border.Y += Move.Y;
    }
    else if(Move.Y > 0)
    {
      TargetPos.Y = Move.Y;
      Border.Y -= Move.Y;
    }
  }

  paletteindex* Buffer = &PaletteBuffer[Pos.Y][Pos.X];
  packcol16* DestBuffer = &Bitmap->GetImage()[TargetPos.Y][TargetPos.X];
  int BitmapXSize = Bitmap->GetPhysicalSize().X;
  uchar* Palette = this->Palette; // eliminate the efficiency cost of dereferencing
  packalpha* AlphaMap;
  truth UseAlpha;

  if(BaseAlpha != 255 || (Alpha && (Alpha[0] != 255 || Alpha[1] != 255 || Alpha[2] != 255 || Alpha[3] != 255)))
  {
    Bitmap->CreateAlphaMap(BaseAlpha);
    AlphaMap = &Bitmap->GetAlphaMap()[TargetPos.Y][TargetPos.X];
    UseAlpha = true;
  }
  else
  {
    AlphaMap = 0;
    UseAlpha = false;
  }

  truth Rusted = RustData && (RustData[0] || RustData[1] || RustData[2] || RustData[3]);
  ulong RustSeed[4];

  if(Rusted)
  {
    RustSeed[0] = (RustData[0] & 0xFC) >> 2;
    RustSeed[1] = (RustData[1] & 0xFC) >> 2;
    RustSeed[2] = (RustData[2] & 0xFC) >> 2;
    RustSeed[3] = (RustData[3] & 0xFC) >> 2;
  }

  truth Burnt = BurnData && (BurnData[0] || BurnData[1] || BurnData[2] || BurnData[3]);
  ulong BurnSeed[4];

  if(Burnt)
  {
    BurnSeed[0] = (BurnData[0] & 0xFC) >> 2;
    BurnSeed[1] = (BurnData[1] & 0xFC) >> 2;
    BurnSeed[2] = (BurnData[2] & 0xFC) >> 2;
    BurnSeed[3] = (BurnData[3] & 0xFC) >> 2;
  }

  for(int y = 0; y < Border.Y; ++y)
  {
    for(int x = 0; x < Border.X; ++x)
    {
      int PaletteElement = Buffer[x];

      if(PaletteElement >= 192)
      {
        int ColorIndex = (PaletteElement - 192) >> 4;
        int ThisColor = Color[ColorIndex];

        if(ThisColor != TRANSPARENT_COLOR)
        {
          int Index = PaletteElement & 15;
          int Red = (ThisColor >> 8 & 0xF8) * Index;
          int Green = (ThisColor >> 3 & 0xFC) * Index;
          int Blue = (ThisColor << 3 & 0xF8) * Index;
          int Max = (Red > Green ? Red : Green);
          Max = (Max > Blue ? Max : Blue);

          if(Rusted && RustData[ColorIndex]
             && (RustData[ColorIndex] & 3UL)
             > (RustSeed[ColorIndex] = RustSeed[ColorIndex] * 1103515245 + 12345) >> 30)
          {
            Green = ((Green << 1) + Green) >> 2;
            Blue >>= 1;
          }

          if(Burnt && BurnData[ColorIndex]
             && (BurnData[ColorIndex] & 3UL)
             > (BurnSeed[ColorIndex] = BurnSeed[ColorIndex] * 1103515245 + 12345) >> 30)
          {
            Max >>= 2;
            Red = Max + (Red >> 3);
            Green = Max + (Green >> 3);
            Blue = Max + (Blue >> 3);
          }

          if(Red > 0x7FF)
            Red = 0x7FF;

          if(Green > 0x7FF)
            Green = 0x7FF;

          if(Blue > 0x7FF)
            Blue = 0x7FF;

          DestBuffer[x] = (Red << 5 & 0xF800)
                          | (Green & 0x7E0)
                          | (Blue >> 6 & 0x1F);

          if(UseAlpha)
            AlphaMap[x] = Alpha[ColorIndex];
        }
        else
          DestBuffer[x] = TRANSPARENT_COLOR;
      }
      else if(AllowReguralColors)
      {
        int PaletteIndex = PaletteElement + (PaletteElement << 1);
        DestBuffer[x] = ((Palette[PaletteIndex] & 0xFFF8) << 8)
                        | ((Palette[PaletteIndex + 1] & 0xFFFC) << 3)
                        |  (Palette[PaletteIndex + 2] >> 3);
      }
      else
        DestBuffer[x] = TRANSPARENT_COLOR;
    }

    DestBuffer += BitmapXSize;
    AlphaMap += BitmapXSize;
    Buffer += Size.X;
  }

  return Bitmap;
}

void rawbitmap::Printf(bitmap* Bitmap, v2 Pos, packcol16 Color, cchar* Format, ...) const
{
  char Buffer[256];

  va_list AP;
  va_start(AP, Format);
  vsnprintf(Buffer, sizeof(Buffer), Format, AP);
  va_end(AP);

  fontcache::const_iterator Iterator = FontCache.find(Color);

  if(Iterator == FontCache.end())
  {
    packcol16 ShadeCol = MakeShadeColor(Color);

    for(int c = 0; Buffer[c]; ++c)
    {
      v2 F(((Buffer[c] - 0x20) & 0xF) << 4, (Buffer[c] - 0x20) & 0xF0);
          //printf("X=%4d -- Y=%d\n", F.X, F.Y);
      MaskedBlit(Bitmap, F, v2(Pos.X + (c << 3) + 1, Pos.Y + 1), v2(8, 8), &ShadeCol);
      MaskedBlit(Bitmap, F, v2(Pos.X + (c << 3), Pos.Y), v2(8, 8), &Color);
    }
  }
  else
  {
    const cachedfont* Font = Iterator->second.first;
    blitdata B = { Bitmap,
                   { 0, 0 },
                   { Pos.X, Pos.Y },
                   { 9, 9 },
                   { 0 },
                   TRANSPARENT_COLOR,
                   0 };

    for(int c = 0; Buffer[c]; ++c, B.Dest.X += 8)
    {
      B.Src.X = ((Buffer[c] - 0x20) & 0xF) << 4;
      B.Src.Y = (Buffer[c] - 0x20) & 0xF0;
          //printf("'%c' -> X=%5d -- Y=%5d\n", Buffer[c], B.Src.X, B.Src.Y);
      Font->PrintCharacter(B);
    }
  }
}

void rawbitmap::PrintfUnshaded(bitmap* Bitmap, v2 Pos, packcol16 Color, cchar* Format, ...) const
{
  char Buffer[256];

  va_list AP;
  va_start(AP, Format);
  vsnprintf(Buffer, sizeof(Buffer), Format, AP);
  va_end(AP);

  fontcache::const_iterator Iterator = FontCache.find(Color);

  if(Iterator == FontCache.end())
  {
    for(int c = 0; Buffer[c]; ++c)
    {
      v2 F(((Buffer[c] - 0x20) & 0xF) << 4, (Buffer[c] - 0x20) & 0xF0);
      MaskedBlit(Bitmap, F, v2(Pos.X + (c << 3), Pos.Y), v2(8, 8), &Color);
    }
  }
  else
  {
    const cachedfont* Font = Iterator->second.second;
    blitdata B = { Bitmap,
                   { 0, 0 },
                   { Pos.X, Pos.Y },
                   { 9, 9 },
                   { 0 },
                   TRANSPARENT_COLOR,
                   0 };

    for(int c = 0; Buffer[c]; ++c, B.Dest.X += 8)
    {
      B.Src.X = ((Buffer[c] - 0x20) & 0xF) << 4;
      B.Src.Y = (Buffer[c] - 0x20) & 0xF0;
      Font->PrintCharacter(B);
    }
  }
}

void rawbitmap::AlterGradient(v2 Pos, v2 Border, int MColor, int Amount, truth Clip)
{
  Pos *= Density;
  Border *= Density;
  int ColorMin = 192 + (MColor << 4);
  int ColorMax = 207 + (MColor << 4);

  if(Clip)
  {
    for(int x = Pos.X; x < Pos.X + Border.X; ++x)
      for(int y = Pos.Y; y < Pos.Y + Border.Y; ++y)
      {
        int Pixel = PaletteBuffer[y][x];

        if(Pixel >= ColorMin && Pixel <= ColorMax)
        {
          int NewPixel = Pixel + Amount;

          if(NewPixel < ColorMin)
            NewPixel = ColorMin;

          if(NewPixel > ColorMax)
            NewPixel = ColorMax;

          PaletteBuffer[y][x] = NewPixel;
        }
      }
  }
  else
  {
    int x;

    for(x = Pos.X; x < Pos.X + Border.X; ++x)
      for(int y = Pos.Y; y < Pos.Y + Border.Y; ++y)
      {
        int Pixel = PaletteBuffer[y][x];

        if(Pixel >= ColorMin && Pixel <= ColorMax)
        {
          int NewPixel = Pixel + Amount;

          if(NewPixel < ColorMin)
            return;

          if(NewPixel > ColorMax)
            return;
        }
      }

    for(x = Pos.X; x < Pos.X + Border.X; ++x)
      for(int y = Pos.Y; y < Pos.Y + Border.Y; ++y)
      {
        int Pixel = PaletteBuffer[y][x];

        if(Pixel >= ColorMin && Pixel <= ColorMax)
          PaletteBuffer[y][x] = Pixel + Amount;
      }
  }
}

void rawbitmap::SwapColors(v2 Pos, v2 Border, int Color1, int Color2)
{
  Pos *= Density;
  Border *= Density;

  if(Color1 > 3 || Color2 > 3)
    ABORT("Illegal col swap!");

  for(int x = Pos.X; x < Pos.X + Border.X; ++x)
    for(int y = Pos.Y; y < Pos.Y + Border.Y; ++y)
    {
      paletteindex& Pixel = PaletteBuffer[y][x];

      if(Pixel >= 192 + (Color1 << 4) && Pixel <= 207 + (Color1 << 4))
        Pixel += (Color2 - Color1) << 4;
      else if(Pixel >= 192 + (Color2 << 4) && Pixel <= 207 + (Color2 << 4))
        Pixel += (Color1 - Color2) << 4;
    }
}

/* TempBuffer must be an array of Border.X * Border.Y * GetDensity()^2 paletteindices */

void rawbitmap::Roll(v2 Pos, v2 Border, v2 Move, paletteindex* TempBuffer)
{
  Pos *= Density;
  Border *= Density;
  Move *= Density;

  int x, y;

  for(x = Pos.X; x < Pos.X + Border.X; ++x)
    for(y = Pos.Y; y < Pos.Y + Border.Y; ++y)
    {
      int XPos = x + Move.X, YPos = y + Move.Y;

      if(XPos < Pos.X)
        XPos += Border.X;

      if(YPos < Pos.Y)
        YPos += Border.Y;

      if(XPos >= Pos.X + Border.X)
        XPos -= Border.X;

      if(YPos >= Pos.Y + Border.Y)
        YPos -= Border.Y;

      TempBuffer[(YPos - Pos.Y) * Border.X + XPos - Pos.X] = PaletteBuffer[y][x];
    }

  for(x = Pos.X; x < Pos.X + Border.X; ++x)
    for(y = Pos.Y; y < Pos.Y + Border.Y; ++y)
      PaletteBuffer[y][x] = TempBuffer[(y - Pos.Y) * Border.X + x - Pos.X];
}

void rawbitmap::CreateFontCache(packcol16 Color)
{
  if(FontCache.find(Color) != FontCache.end())
    return;

  packcol16 ShadeColor = MakeShadeColor(Color);
  v2 LayoutSize = GetSize();
  cachedfont* Font = new cachedfont(LayoutSize, TRANSPARENT_COLOR);
  MaskedBlit(Font, ZERO_V2, v2(1, 1), v2(LayoutSize.X - 1, LayoutSize.Y - 1), &ShadeColor);
  cachedfont* UnshadedFont = Colorize(&Color);

  blitdata B = { Font,
                 { 0, 0 },
                 { 0, 0 },
                 { LayoutSize.X, LayoutSize.Y },
                 { 0 },
                 TRANSPARENT_COLOR,
                 0 };

  UnshadedFont->NormalMaskedBlit(B);
  Font->CreateMaskMap();
  UnshadedFont->CreateMaskMap();
  FontCache[Color] = std::make_pair(Font, UnshadedFont);
}

/* returns ERROR_V2 if fails find Pos else returns pos */

v2 rawbitmap::RandomizeSparklePos(cv2* ValidityArray, v2* PossibleBuffer, v2 Pos, v2 Border,
                                  int ValidityArraySize, int SparkleFlags) const
{
  if(!SparkleFlags)
    return ERROR_V2;

  /* Don't use { } to initialize, or GCC optimizations will produce code that crashes! */

  v2* BadPossible[4];
  BadPossible[0] = PossibleBuffer;
  BadPossible[1] = BadPossible[0] + ((Border.X + Border.Y) << 1) -  4;
  BadPossible[2] = BadPossible[1] + ((Border.X + Border.Y) << 1) - 12;
  BadPossible[3] = BadPossible[2] + ((Border.X + Border.Y) << 1) - 20;
  v2* PreferredPossible = BadPossible[3] + ((Border.X + Border.Y) << 1) - 28;
  int Preferred = 0;
  int Bad[4] = { 0, 0, 0, 0 };
  int XMax = Pos.X + Border.X;
  int YMax = Pos.Y + Border.Y;

  for(int c = 0; c < ValidityArraySize; ++c)
  {
    v2 V = ValidityArray[c] + Pos;
    int Entry = PaletteBuffer[V.Y * Density][V.X * Density];

    if(IsMaterialColor(Entry) && 1 << GetMaterialColorIndex(Entry) & SparkleFlags)
    {
      int MinDist = 0x7FFF;

      if(V.X < Pos.X + 4)
        MinDist = Min(V.X - Pos.X, MinDist);

      if(V.X >= XMax - 4)
        MinDist = Min(XMax - V.X - 1, MinDist);

      if(V.Y < Pos.Y + 4)
        MinDist = Min(V.Y - Pos.Y, MinDist);

      if(V.Y >= YMax - 4)
        MinDist = Min(YMax - V.Y - 1, MinDist);

      if(MinDist >= 4)
        PreferredPossible[Preferred++] = V;
      else
        BadPossible[MinDist][Bad[MinDist]++] = V;
    }
  }

  v2 Return;

  if(Preferred)
    Return = PreferredPossible[RAND() % Preferred] - Pos;
  else if(Bad[3])
    Return = BadPossible[3][RAND() % Bad[3]] - Pos;
  else if(Bad[2])
    Return = BadPossible[2][RAND() % Bad[2]] - Pos;
  else if(Bad[1])
    Return = BadPossible[1][RAND() % Bad[1]] - Pos;
  else if(Bad[0])
    Return = BadPossible[0][RAND() % Bad[0]] - Pos;
  else
    Return = ERROR_V2;

  return Return;
}

truth rawbitmap::IsTransparent(v2 Pos) const
{
  return PaletteBuffer[Pos.Y * Density][Pos.X * Density] == TRANSPARENT_PALETTE_INDEX;
}

truth rawbitmap::IsMaterialColor1(v2 Pos) const
{
  int P = PaletteBuffer[Pos.Y * Density][Pos.X * Density];
  return P >= 192 && P < 208;
}

void rawbitmap::PutPixel(v2 Pos, paletteindex Color)
{
  for(int y = Pos.Y * Density; y < (Pos.Y + 1) * Density; ++y)
    for(int x = Pos.X * Density; x < (Pos.X + 1) * Density; ++x)
      PaletteBuffer[y][x] = Color;
}

void rawbitmap::CopyPaletteFrom(rawbitmap* Bitmap)
{
  memcpy(Palette, Bitmap->Palette, 768);
}

void rawbitmap::Clear()
{
  memset(PaletteBuffer[0], TRANSPARENT_PALETTE_INDEX, Size.X * Size.Y * sizeof(paletteindex));
}

void rawbitmap::NormalBlit(rawbitmap* Bitmap, v2 Src, v2 Dest, v2 Border, int Flags) const
{
  if(Bitmap->Density != Density)
    ABORT("Blit between %dx and %dx paletted bitmaps!", Density, Bitmap->Density);

  Src *= Density;
  Dest *= Density;
  Border *= Density;
  paletteindex** SrcBuffer = PaletteBuffer;
  paletteindex** DestBuffer = Bitmap->PaletteBuffer;

  switch(Flags & 7)
  {
   case NONE:
    {
      if(Size.X == Bitmap->Size.X && Size.Y == Bitmap->Size.Y)
        memcpy(DestBuffer[0], SrcBuffer[0], Size.X * Size.Y * sizeof(paletteindex));
      else
      {
        cint Bytes = Border.X * sizeof(paletteindex);

        for(int y = 0; y < Border.Y; ++y)
          memcpy(&DestBuffer[Dest.Y + y][Dest.X], &SrcBuffer[Src.Y + y][Src.X], Bytes);
      }

      break;
    }

   case MIRROR:
    {
      Dest.X += Border.X - 1;

      for(int y = 0; y < Border.Y; ++y)
      {
        cpaletteindex* SrcPtr = &SrcBuffer[Src.Y + y][Src.X];
        cpaletteindex* EndPtr = SrcPtr + Border.X;
        paletteindex* DestPtr = &DestBuffer[Dest.Y + y][Dest.X];

        for(; SrcPtr != EndPtr; ++SrcPtr, --DestPtr)
          *DestPtr = *SrcPtr;
      }

      break;
    }

   case FLIP:
    {
      Dest.Y += Border.Y - 1;
      cint Bytes = Border.X * sizeof(paletteindex);

      for(int y = 0; y < Border.Y; ++y)
        memcpy(&DestBuffer[Dest.Y - y][Dest.X], &SrcBuffer[Src.Y + y][Src.X], Bytes);

      break;
    }

   case (MIRROR | FLIP):
    {
      Dest.X += Border.X - 1;
      Dest.Y += Border.Y - 1;

      for(int y = 0; y < Border.Y; ++y)
      {
        cpaletteindex* SrcPtr = &SrcBuffer[Src.Y + y][Src.X];
        cpaletteindex* EndPtr = SrcPtr + Border.X;
        paletteindex* DestPtr = &DestBuffer[Dest.Y - y][Dest.X];

        for(; SrcPtr != EndPtr; ++SrcPtr, --DestPtr)
          *DestPtr = *SrcPtr;
      }

      break;
    }

   case ROTATE:
    {
      Dest.X += Border.X - 1;
      int TrueDestXMove = Bitmap->Size.X;
      paletteindex* DestBase = &DestBuffer[Dest.Y][Dest.X];

      for(int y = 0; y < Border.Y; ++y)
      {
        cpaletteindex* SrcPtr = &SrcBuffer[Src.Y + y][Src.X];
        cpaletteindex* EndPtr = SrcPtr + Border.X;
        paletteindex* DestPtr = DestBase - y;

        for(; SrcPtr != EndPtr; ++SrcPtr, DestPtr += TrueDestXMove)
          *DestPtr = *SrcPtr;
      }

      break;
    }

   case (MIRROR | ROTATE):
    {
      int TrueDestXMove = Bitmap->Size.X;
      paletteindex* DestBase = &DestBuffer[Dest.Y][Dest.X];

      for(int y = 0; y < Border.Y; ++y)
      {
        cpaletteindex* SrcPtr = &SrcBuffer[Src.Y + y][Src.X];
        cpaletteindex* EndPtr = SrcPtr + Border.X;
        paletteindex* DestPtr = DestBase + y;

        for(; SrcPtr != EndPtr; ++SrcPtr, DestPtr += TrueDestXMove)
          *DestPtr = *SrcPtr;
      }

      break;
    }

   case (FLIP | ROTATE):
    {
      Dest.X += Border.X - 1;
      Dest.Y += Border.Y - 1;
      int TrueDestXMove = Bitmap->Size.X;
      paletteindex* DestBase = &DestBuffer[Dest.Y][Dest.X];

      for(int y = 0; y < Border.Y; ++y)
      {
        cpaletteindex* SrcPtr = &SrcBuffer[Src.Y + y][Src.X];
        cpaletteindex* EndPtr = SrcPtr + Border.X;
        paletteindex* DestPtr = DestBase - y;

        for(; SrcPtr != EndPtr; ++SrcPtr, DestPtr -= TrueDestXMove)
          *DestPtr = *SrcPtr;
      }

      break;
    }

   case (MIRROR | FLIP | ROTATE):
    {
      Dest.Y += Border.Y - 1;
      int TrueDestXMove = Bitmap->Size.X;
      paletteindex* DestBase = &DestBuffer[Dest.Y][Dest.X];

      for(int y = 0; y < Border.Y; ++y)
      {
        cpaletteindex* SrcPtr = &SrcBuffer[Src.Y + y][Src.X];
        cpaletteindex* EndPtr = SrcPtr + Border.X;
        paletteindex* DestPtr = DestBase + y;

        for(; SrcPtr != EndPtr; ++SrcPtr, DestPtr -= TrueDestXMove)
          *DestPtr = *SrcPtr;
      }

      break;
    }
  }
}
