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

#ifndef __WTERRAS_H__
#define __WTERRAS_H__

#include "wterra.h"

GWTERRAIN(ocean, gwterrain)
{
 public:
  ocean() { SetAnimationFrames(32); }
  virtual v2 GetBitmapPos(int) const;
  virtual cchar* SurviveMessage() const;
  virtual cchar* MonsterSurviveMessage() const;
  virtual cchar* DeathMessage() const;
  virtual cchar* MonsterDeathVerb() const;
  virtual cchar* ScoreEntry() const;
  virtual truth IsFatalToStay() const { return true; }
  virtual int GetWalkability() const;
};

GWTERRAIN(glacier, gwterrain)
{
};

GWTERRAIN(desert, gwterrain)
{
};

GWTERRAIN(snow, gwterrain)
{
};

GWTERRAIN(jungle, gwterrain)
{
};

GWTERRAIN(leafyforest, gwterrain)
{
};

GWTERRAIN(evergreenforest, gwterrain)
{
};

GWTERRAIN(steppe, gwterrain)
{
};

/* Impassable except in flight; only the valley around Oakhaven is ringed with it (see worldmap::CarveValley). */
GWTERRAIN(mountain, gwterrain)
{
 public:
  virtual int GetWalkability() const;
};

OWTERRAIN(attnam, owterrain)
{
};

OWTERRAIN(malgorathcave, owterrain)
{
};

OWTERRAIN(newattnam, owterrain)
{
};

OWTERRAIN(underwatertunnel, owterrain)
{
};

OWTERRAIN(underwatertunnelexit, owterrain)
{
};

OWTERRAIN(aslonacastle, owterrain)
{
};

OWTERRAIN(rebelcamp, owterrain)
{
};

OWTERRAIN(goblinfort, owterrain)
{
};

OWTERRAIN(fungalcave, owterrain)
{
};

OWTERRAIN(pyramid, owterrain)
{
};

OWTERRAIN(blackmarket, owterrain)
{
};

OWTERRAIN(xinrochtomb, owterrain)
{
};

OWTERRAIN(locationA, owterrain)
{
};

OWTERRAIN(locationB, owterrain)
{
};

OWTERRAIN(locationC, owterrain)
{
};

OWTERRAIN(locationD, owterrain)
{
};

OWTERRAIN(locationE, owterrain)
{
};

OWTERRAIN(locationF, owterrain)
{
};

OWTERRAIN(locationG, owterrain)
{
};

OWTERRAIN(locationH, owterrain)
{
};

#endif
