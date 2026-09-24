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

#ifndef __COLORBIT_H__
#define __COLORBIT_H__

#include <map>
#include <vector>

#include "v2.h"

class outputfile;
class inputfile;
class bitmap;
class cachedfont;
class festring;

typedef std::map<col16, std::pair<cachedfont*, cachedfont*>> fontcache;

/*
 * An 8-bit paletted image (sprite sheets, fonts, ...) addressed in layout pixels.
 *
 * Like bitmap, it stores GetDensity() x GetDensity() physical pixels per layout pixel:
 * a sheet loads from Graphics/<D>x/ when that set exists and is otherwise rescaled on load
 * (see graphics::ResolveDensityAsset). Every coordinate in the public interface is in
 * layout pixels; Size is the physical size.
 */
class rawbitmap
{
 public:
  friend class bitmap;
  rawbitmap(cfestring&);
  rawbitmap(v2);
  ~rawbitmap();
  void Save(cfestring&);
  void MaskedBlit(bitmap*, v2, v2,
                  v2, packcol16*) const;
  void MaskedBlit(bitmap*, packcol16*) const;

  void LIKE_PRINTF(5, 6) Printf(bitmap*, v2, packcol16,
                                cchar*, ...) const;
  void LIKE_PRINTF(5, 6) PrintfUnshaded(bitmap*, v2, packcol16,
                                        cchar*, ...) const;
  cachedfont* Colorize(cpackcol16*, alpha = 255,
                       cpackalpha* = 0) const;
  bitmap* Colorize(v2, v2, v2,
                   cpackcol16*, alpha = 255,
                   cpackalpha* = 0,
                   cuchar* = 0, cuchar* = 0, truth = true) const;
  v2 GetSize() const { return v2(Size.X / Density, Size.Y / Density); }
  v2 GetPhysicalSize() const { return Size; }
  int GetDensity() const { return Density; }

  void AlterGradient(v2, v2, int, int, truth);
  void SwapColors(v2, v2, int, int);
  void Roll(v2, v2, v2, paletteindex*);

  void CreateFontCache(packcol16);
  static truth IsMaterialColor(int Color) { return Color >= 192; }
  static int GetMaterialColorIndex(int Color) { return (Color - 192) >> 4; }
  int GetMaterialColorIndex(int X, int Y) const
  { return (PaletteBuffer[Y * Density][X * Density] - 192) >> 4; }
  truth IsTransparent(v2) const;
  truth IsMaterialColor1(v2) const;
  v2 RandomizeSparklePos(cv2*, v2*, v2, v2, int, int) const;
  void CopyPaletteFrom(rawbitmap*);
  void PutPixel(v2 Pos, paletteindex Color);
  paletteindex GetPixel(v2 Pos) const
  { return PaletteBuffer[Pos.Y * Density][Pos.X * Density]; }
  void Clear();
  void NormalBlit(rawbitmap*, v2, v2, v2, int = 0) const;
 protected:
  void Rescale(int FromDensity);
  v2 Size;
  int Density;
  uchar* Palette;
  paletteindex** PaletteBuffer;
  fontcache FontCache;
};

#endif
