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

#ifndef __BITMAP_H__
#define __BITMAP_H__

#include "v2.h"
#include "SDL.h"

class bitmap;
class rawbitmap;
class outputfile;
class inputfile;
class festring;

typedef void (*bitmapeditor)(bitmap*, truth);

struct blitdata
{
  bitmap* Bitmap;
  v2 Src;
  v2 Dest;
  v2 Border;
  union
  {
    col24 Luminance;
    int Flags, Stretch;
  };
  col16 MaskColor;
  ulong CustomData;
};
#define DEFAULT_BLITDATA {NULL,{0,0},{0,0},{0,0}, {0}, TRANSPARENT_COLOR,0} //easy initializer TODO should be TRANSPARENT_COLOR? TODO update everywere with this default and just apply there differences to shrink the code?

/*
 * A 16-bit image addressed in layout pixels (the classic 800x600 grid, 16-unit tiles).
 *
 * Each bitmap stores Density x Density physical pixels per layout pixel, fixed when it is
 * created (graphics::GetDensity() by default), so the same drawing code renders 16, 32 or
 * 64 pixel tiles. All coordinates, sizes and blitdata in the public interface are layout
 * pixels; GetImage(), GetPhysicalSize() and the Size member are physical. Blits require
 * both bitmaps to share a density.
 */
class bitmap
{
 public:
  friend class cachedfont;
  bitmap(cfestring&);
  bitmap(cbitmap*, int = 0, truth = true);
  bitmap(v2);
  bitmap(v2, col16);
  bitmap(v2 LayoutSize, int Density, col16 Color);
  ~bitmap();
  void Save(outputfile&) const;
  void Load(inputfile&);
  void Save(cfestring&) const;
  void PutPixel(int X, int Y, col16 Color)
  {
    if(Density == 1)
      Image[Y][X] = Color;
    else
      PutBlock(X, Y, Color);
  }
  void PutPixel(v2 Pos, col16 Color) { PutPixel(Pos.X, Pos.Y, Color); }
  void PowerPutPixel(int, int, col16, alpha, priority);
  col16 GetPixel(int X, int Y) const { return Image[Y * Density][X * Density]; }
  col16 GetPixel(v2 Pos) const { return GetPixel(Pos.X, Pos.Y); }

  void Fill(int, int, int, int, col16);
  void Fill(v2, int, int, col16);
  void Fill(int, int, v2, col16);
  void Fill(v2, v2, col16);

  void ClearToColor(col16);
  void NormalBlit(cblitdata&) const;
  void NormalBlit(bitmap*, int = 0) const;
  void FastBlit(bitmap*) const;
  void FastBlit(bitmap*, v2) const;

  void LuminanceBlit(cblitdata&) const;
  void NormalMaskedBlit(cblitdata&) const;
  void LuminanceMaskedBlit(cblitdata&) const;
  void SimpleAlphaBlit(bitmap*, alpha, col16 = TRANSPARENT_COLOR) const;
  void AlphaMaskedBlit(cblitdata&) const;
  void AlphaLuminanceBlit(cblitdata&) const;

  void DrawLine(int, int, int, int, col16, truth = false);
  void DrawLine(v2, int, int, col16, truth = false);
  void DrawLine(int, int, v2, col16, truth = false);
  void DrawLine(v2, v2, col16, truth = false);

  void DrawVerticalLine(int, int, int, col16, truth = false);
  void DrawHorizontalLine(int, int, int, col16, truth = false);

  void StretchBlit(cblitdata&) const;
  void StretchBlitXbrz(cblitdata&,bool) const;
  SDL_Surface* CopyToSurface(v2 v2TopLeft, v2 v2Size, col16 MaskColor = TRANSPARENT_COLOR, SDL_Surface* srf = NULL) const;

  static void ResetBlitdataRotation(blitdata& B);
  static void ConfigureBlitdataRotation(blitdata& B,int i);

  void DrawRectangle(int, int, int, int, col16, truth = false);
  void DrawRectangle(v2, int, int, col16, truth = false);
  void DrawRectangle(int, int, v2, col16, truth = false);
  void DrawRectangle(v2, v2, col16, truth = false);

  void BlitAndCopyAlpha(bitmap*, int = 0) const;
  void MaskedPriorityBlit(cblitdata&) const;
  void AlphaPriorityBlit(cblitdata&) const;
  void FastBlitAndCopyAlpha(bitmap*) const;
  v2 GetSize() const { return v2(Size.X / Density, Size.Y / Density); }
  v2 GetPhysicalSize() const { return Size; }
  int GetDensity() const { return Density; }
  void DrawPolygon(int, int, int, int, col16, truth = true, truth = false, double = 0);
  void CreateAlphaMap(alpha);
  truth Fade(long&, packalpha&, int);
  void SetAlpha(int X, int Y, alpha Alpha);
  void SetAlpha(v2 Pos, alpha Alpha) { SetAlpha(Pos.X, Pos.Y, Alpha); }
  alpha GetAlpha(int X, int Y) const { return AlphaMap[Y * Density][X * Density]; }
  alpha GetAlpha(v2 Pos) const { return GetAlpha(Pos.X, Pos.Y); }
  void Outline(col16, alpha, priority);
  void FadeToScreen(bitmapeditor = 0);
  void CreateFlames(rawbitmap*, v2, ulong, int);
  truth IsValidPos(v2 What) const { return IsValidPos(What.X, What.Y); }
  truth IsValidPos(int X, int Y) const
  { return X >= 0 && Y >= 0 && X < Size.X / Density && Y < Size.Y / Density; }
  void CreateSparkle(v2, int);
  void CreateFlies(ulong, int, int);
  void CreateLightning(ulong, col16);
  truth CreateLightning(v2, v2, int, col16);
  packcol16** GetImage() const { return Image; }
  packalpha** GetAlphaMap() const { return AlphaMap; }
  static truth PixelVectorHandler(long, long);
  void FillAlpha(alpha);
  void InitPriorityMap(priority);
  void FillPriority(priority);
  void SafeSetPriority(int, int, priority);
  void SafeSetPriority(v2 Pos, priority What) { SafeSetPriority(Pos.X, Pos.Y, What); }
  void SafeUpdateRandMap(v2, truth);
  void UpdateRandMap(long, truth);
  void InitRandMap();
  v2 RandomizePixel() const;
  void AlphaPutPixel(int, int, col16, col24, alpha);
  void AlphaPutPixel(v2 Pos, col16 Color, col24 Luminance, alpha Alpha) { AlphaPutPixel(Pos.X, Pos.Y, Color, Luminance, Alpha); }
  void CalculateRandMap();
  alpha CalculateAlphaAverage() const;
  void ActivateFastFlag() { FastFlag = 1; }
  void DeactivateFastFlag() { FastFlag = 0; }
  void Wobble(int, int, truth);
  void MoveLineVertically(int, int);
  void MoveLineHorizontally(int, int);
  void InterLace();

  truth HasColor(col16 findColor);
  void ReplaceColor(col16 findColor,col16 replaceWith);
  void CopyLineFrom(int iYDest, bitmap* bmpFrom, int iYFrom, int iSize, bool bFailSafe=false);
 protected:
  void PutBlock(int X, int Y, col16 Color);
  void ToPhysical(blitdata&) const;
  void DrawThickPixel(int X, int Y, col16 Color);
  void SetPhysicalOutlinePixel(int, int, alpha, priority);
  v2 Size;
  int Density;
  ulong XSizeTimesYSize : 31;
  ulong FastFlag : 1;
  packcol16** Image;
  packalpha** AlphaMap;
  packpriority** PriorityMap;
  truth* RandMap;
  SDL_Surface* img;
  SDL_Surface* imgStretched;
};

inline void bitmap::SafeUpdateRandMap(v2 Pos, truth What)
{
  if(RandMap)
    for(int y = Pos.Y * Density; y < (Pos.Y + 1) * Density; ++y)
      for(int x = Pos.X * Density; x < (Pos.X + 1) * Density; ++x)
        UpdateRandMap(y * Size.X + x, What);
}

inline void bitmap::SafeSetPriority(int x, int y, priority What)
{
  if(PriorityMap)
    for(int py = y * Density; py < (y + 1) * Density; ++py)
      for(int px = x * Density; px < (x + 1) * Density; ++px)
        PriorityMap[py][px] = What;
}

inline void bitmap::FastBlit(bitmap* Bitmap) const
{
  memcpy(Bitmap->Image[0], Image[0], XSizeTimesYSize * sizeof(packcol16));
}

inline void bitmap::FastBlit(bitmap* Bitmap, v2 Pos) const
{
  packcol16** SrcImage = Image;
  packcol16** DestImage = Bitmap->Image;
  cint Bytes = Size.X * sizeof(packcol16);
  cint Height = Size.Y;
  Pos *= Density;

  for(int y = 0; y < Height; ++y)
    memcpy(&DestImage[Pos.Y + y][Pos.X], SrcImage[y], Bytes);
}

inline void bitmap::NormalBlit(bitmap* Bitmap, int Flags) const
{
  v2 LayoutSize = GetSize();
  blitdata B = { Bitmap,
                 { 0, 0 },
                 { 0, 0 },
                 { LayoutSize.X, LayoutSize.Y },
                 { static_cast<col24>(Flags) }, // stupid union initialization rules...
                 0,
                 0 };
  NormalBlit(B);
}

outputfile& operator<<(outputfile&, cbitmap*);
inputfile& operator>>(inputfile&, bitmap*&);

class cachedfont : public bitmap
{
 public:
  cachedfont(v2);
  cachedfont(v2, col16);
  ~cachedfont() { delete [] MaskMap; }
  void PrintCharacter(cblitdata) const;
  void CreateMaskMap();
 private:
  packcol16** MaskMap;
};

#endif
