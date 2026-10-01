# EXECUTION PLAN — IVAN Creative Rewrite

This document contains the full creative rewrite plan and automation strategy for transforming IVAN from its current frog/banana/Attnam setting into a cohesive dark fantasy world.

---

## 1. New World Geography: The Continent of Aethelgard

### 1.1 Overview
Aethelgard is a vast, ancient continent shaped by the Divine War — a cataclysmic conflict between the Elder Gods that left deep scars on the land. The world rests upon the back of **Valpurus**, the Great Frog who emerged from the Sea of Eternity (the Void) at the Awakening and carried the flat cylinder-world into existence.

### 1.2 Regions & Locations

| Old Name | New Name | Description | Game Mapping |
|---|---|---|---|
| **Perttuera** (Isle/World) | **Aethelgard** | The continent — a flat cylinder of land, ~4242 miles wide and 256 miles high, resting on Valpurus's back above the Sea of Eternity. Home to multiple kingdoms, ancient ruins, and sacred sites. | World map / entire game world |
| **Pertturia** (Forest) | **The Sylvan Weald** | An ancient, enchanted forest surrounding the Holy City. Trees are said to be saplings from the Divine Tree Puu. The canopy is so thick that sunlight barely reaches the forest floor. Home to hidden shops and mysterious ruins. | evergreenforest terrain type; Black Market location |
| **Attnam** (Holy City) | **Valpuris** | The Holy City of Valpuri, capital of the Aethelgard Empire. Built around the Cathedral of Valpurus — a massive cathedral with no windows, its interior lit by enchanted crystals. Snow-covered fell surrounded by frozen lakes. Home to the Four Cardinals and the Bureau of Investigation. | ATTNAM dungeon; Cathedral of Valpurus (61x67); City levels 0-4 |
| **New Attnam / Tweraif** (Village) | **Oakhaven** | A farming village in a hidden forest valley walled in by mountains (changed from a coastal jungle island on 2026-09-30, for a classic-fantasy feel), ruled by Viceroy Richel Decos. Once a thriving settlement, now oppressed under Decos's monopoly on the miracle crop. The mansion was formerly a temple of Silva. | NEW_ATTNAM dungeon; leafy forest valley ringed by `mountain` world terrain |
| **Underwater Tunnel** | **The Sunken Passage** | An ancient road beneath the mountains around Oakhaven's valley, its only way out, leading toward Valpuris. Built during the Pax Aethelgardica era. Contains boss rooms with Genetrix Vesana (carnivorous plant), Terra's Crystal Shrine, and Lobh-se's Spider Lair. | UNDER_WATER_TUNNEL dungeon; 5 levels |
| **Tomb of Xinroch** | **The Crypt of Khaz-Zadm** | An 11-level necromancy dungeon in the northern glacier mountains. Guarded by fanatical Dark Knights who followed Lord Xinroch into undeath. Contains artifacts from the Divine War and gas chambers with kamikaze dwarves. | XINROCH_TOMB dungeon; Glacier/Tundra terrain |
| **Aslona Castle** | **Castle Aethelred** | A seaside castle in the leafy forest region, seat of the Aslona kingdom. Currently under siege during a civil war between crown forces and rebels. Contains sapphire altars, wine cellars, and a cistern with angelic guardians. | ASLONA_CASTLE dungeon; Leafy Forest terrain |
| **Rebel Camp** | **The Blackwood Encampment** | A hidden rebel camp in the steppe grasslands. Led by Harvan Black-cloak. Contains kamikaze dwarves loyal to Legifer, a quartermaster shop, and the rebel leader's private quarters. | REBEL_CAMP dungeon; Steppe terrain (hidden) |
| **Goblin Fort** | **The Ruins of Quetzaltia** | Overgrown ruins of an ancient goblin empire built around a salt cave system. Home to goblin princes, warlocks with fire wands, and the captured crown prince Artorius in prison cells. | GOBLIN_FORT dungeon; Evergreen Forest terrain (hidden) |
| **Pyramid** | **The Bunker of Otoul'iv** | A crumbling pyramid/bunker from the ancient Otoul'iv Ik-Omit empire. Contains concrete corridors, mind worm rooms, and a nuclear device in a lead-walled chamber. Aslona-related quest location. | PYRAMID dungeon; Desert/Jungle terrain (hidden) |
| **Black Market** | **The Shadow Bazaar** | A hidden underground market in the Sylvan Weald. Operated by a one-eyed orc merchant. Sells black blood, rare artifacts including a ring of speed. Heavily guarded by elite fighters and golems. | BLACK_MARKET dungeon; Leafy Forest terrain (hidden) |
| **Fungal Cave** | **The Mycelial Depths** | A damp cave system with strange fungal growths near the coal mines. Contains the massive magical mushroom Fusanga, weeping obsidian shards, and poison rooms. Source of the "Tear of Silva" artifact. | FUNGAL_CAVE dungeon; Jungle terrain (hidden) |
| **Elpuri's Cave** | **The Gloomy Caves** | A dark cave system containing Elpuri's lair — a fortress of darkness where the monstrous guardian dwells. Also contains Oree's Lair (blood lake, ruby walls), Enner Beast levels, and the Ivan/communist level with Vladimir. | ELPURI_CAVE / GloomyCaves dungeon; Tundra terrain (hidden) |
| **Dark Forest** | **The Wailing Woods** | A mysterious outdoor forest area with inactive beartraps and scattered food. Part of a dungeon pair with Irinox. | DARK_FOREST dungeon; Grass terrain |
| **Irinox** | **The Silent Hollows** | Nearly identical to Dark Forest — an outdoor area with traps, food, and boulders. Dungeon pair component. | IRINOX dungeon; Grass terrain |
| **Mondedr / Empty Area** | **The Barrens** | An empty tundra/grassland region on the continent's edge. No special features beyond beartraps and scattered resources. | MONDEDR / EMPTY_AREA dungeons |

### 1.3 World Map Layout
- **Valpuris** placed on a continent with evergreen forest + snow tiles (PetrusLikes)
- **Oakhaven** in a small forest valley ringed by impassable mountains, carved out of Valpuris's continent (worldmap::CarveValley)
- **Sunken Passage** runs under the mountains from the valley to the continent outside
- **Crypt of Khaz-Zadm** hidden in northern glacier/tundra
- **Castle Aethelred** hidden in leafy forest (Aslona region)
- **Blackwood Encampment** hidden in steppe grasslands
- **Ruins of Quetzaltia** hidden in evergreen forest
- **The Bunker of Otoul'iv** hidden in desert/jungle
- **Shadow Bazaar** hidden in leafy forest
- **Mycelial Depths** hidden in jungle
- **Gloomy Caves** hidden in tundra

---

## 2. New Pantheon: The Sixteen Divine Trees

The pantheon is reimagined through the mythology of the Great Tree Puu and its sixteen saplings (Divine Trees). Each god corresponds to a domain, with alignment reflecting their current state after the Chaos corrupted some of them during the Divine War.

### 2.1 Pantheon Table

| ID | Old Name | New Name | Domain | Alignment | Epithet | Color | Description Summary |
|---|---|---|---|---|---|---|---|
| VALPURUS | Valpurus | **Valpuris** | King of Gods, Creation | Lawful Good | The Great Frog, Creator Father, Carrier of Worlds | rgb(46,224,56) | Supreme deity who emerged from the Sea of Eternity (Void), created the Elder Gods by laying eggs, carries the flat world on his back. The Void is his true form; physical manifestation is but one of countless forms. |
| LEGIFER | Legifer | **Legifer** | Law and Order | Lawful Good | The Iron Scepter, Keeper of Oaths | rgb(200,200,255) | God of law, justice, and martial order. Founded the Shining Knights to fight the Dark Knights after the fall of Fortress Prym. His maces (Turox) were blessed with divine fire. |
| ATAVUS | Atavus | **Atavus** | Charity and Munificence | Lawful Good | The Bread Father, Giver of Plenty | rgb(255,200,100) | God of charity, generosity, and communal feasting. Associated with the sacred flatbread tradition — the Stollen of Atavus is blessed during the Day of Giving at Valpuris Cathedral. |
| DULCIS | Dulcis | **Dulcis** | Love and Art | Neutral Good | The Harmonic Voice, Weaver of Beauty | rgb(255,100,200) | Goddess of love, music, art, and beauty. Her voice was once the most beautiful in creation — until it was lost during the Divine War. Musical instruments bear her blessing. |
| SEGES | Seges | **Seges** | Health and Nutrition | Neutral Good | The Green Healer, Root of Life | rgb(100,255,100) | God of health, nutrition, and natural healing. Associated with the miracle crop (Oakhaven's economy). His followers believe in the restorative power of sacred foods and herbs. |
| SOPHOS | Sophos | **Sophos** | Knowledge, Magic, Handicrafts | Lawful Good | The All-Knowing, Architect of Wonders | rgb(100,200,255) | God of knowledge, magic, scholarly pursuits, and skilled craftsmanship. His champion Karl the Sophite monk wielded Vermis — a diamond-bladed spear that teleports enemies on command. |
| SILVA | Silva | **Silva** | Nature | True Neutral | The Great Mother, Keeper of the Cycle | rgb(50,180,50) | Goddess of nature, life and death, the wild places. Descended from Pyha (the sycamore Divine Tree). Her Champion Eternal is Mestari, who sacrificed himself to destroy Paha's corruption. Sacred tree: the Holy Mango World-tree. |
| LORICATUS | Loricatus | **Loricatus** | Fire, Machines, Weaponry | True Neutral | The Forge Master, Smith of War | rgb(255,150,50) | God of fire, metallurgy, weapons crafting, and mechanical ingenuity. Patron of smiths, engineers, and weapon-makers. Associated with dwarven forge-culture. |
| MELLIS | Mellis | **Mellis** | Money, Trade, Politics | Chaotic Neutral | The Golden Tongue, Merchant Prince | rgb(255,255,0) | God of commerce, trade, wealth accumulation, and political maneuvering. Patron of merchants, bankers, and those who seek profit through cunning. His black market connections are extensive. |
| CLEPTIA | Cleptia | **Cleptia** | Assassins and Thieves | Chaotic Evil | The Shadow Hand, Whisper in the Dark | rgb(100,50,150) | Goddess of thievery, assassination, and shadow operations. Her whips steal from enemies when she aids her champions. Associated with underground networks and covert operations. |
| NEFAS | Nefas | **Nefas** | Forbidden Pleasures | Chaotic Evil | The Tempter, Lord of Vice | rgb(200,50,100) | God of forbidden pleasures, temptation, and indulgence. Associated with exotic foods, intoxicating beverages, and the darker side of desire. His followers seek pleasure at any cost. |
| SCABIES | Scabies | **Scabies** | Mutations, Disease, Famine | Chaotic Evil | The Blight Mother, Corruptor of Flesh | rgb(150,200,50) | Goddess of mutations, disease, and biological corruption. Her daughter Lobh-se is an invulnerable being accumulated millennia of diseases and poisons. Associated with carnivorous plants and fungal growths. |
| INFUSCOR | Infuscor | **Infuscor** | Wrong Knowledge and Vile Magic | Chaotic Evil | The Dark Architect, Lord of Forbidden Arts | rgb(150,50,150) | God of forbidden knowledge, necromancy, and dark magic. Founded the Unholy Order of Dark Knights through Xinroch. His temples glow with blood-red light and are adorned with dead trees and glowing fountains. |
| CRUENTUS | Cruentus | **Cruentus** | War and Blood | Chaotic Evil | The Red Butcher, Lord of Slaughter | rgb(255,0,0) | God of war, bloodshed, and martial violence. Recommends followers to serve Mortifer. His blood is associated with combat prowess and battlefield fury. |
| MORTIFER | Mortifer | **Mortifer** | Destroyer of Worlds | Chaotic Evil | The Annihilator, End of All Things | rgb(50,50,50) | God of destruction, apocalypse, and the end of all things. His champion gift is delivered in scrambled text — a sign that his very speech corrupts meaning. Associated with undead armies and world-ending power. |

### 2.2 Additional Deities
| ID | Name | Domain | Alignment | Notes |
|---|---|---|---|---|
| ATHEIST | **The Unbound** | None | Neutral | The philosophical position of rejecting divine authority. Associated with the communist ideology found in the Gloomy Caves. |

### 2.3 God Color Mapping (for UI rendering)
- Valpuris: rgb(46,224,56) — sacred green
- Legifer: rgb(200,200,255) — silver-blue
- Atavus: rgb(255,200,100) — golden wheat
- Dulcis: rgb(255,100,200) — rose pink
- Seges: rgb(100,255,100) — fresh green
- Sophos: rgb(100,200,255) — sky blue
- Silva: rgb(50,180,50) — deep forest green
- Loricatus: rgb(255,150,50) — forge orange
- Mellis: rgb(255,255,0) — gold
- Cleptia: rgb(100,50,150) — shadow purple
- Nefas: rgb(200,50,100) — dark crimson
- Scabies: rgb(150,200,50) — sickly yellow-green
- Infuscor: rgb(150,50,150) — necrotic purple
- Cruentus: rgb(255,0,0) — blood red
- Mortifer: rgb(50,50,50) — void black

---

## 3. New Character Roster

### 3.1 Key NPCs (Replacing Original Characters)

| Old Name | Role | New Name | Title/Role | Story Arc | Notes |
|---|---|---|---|---|---|
| **Richel Decos** | Viceroy of Oakhaven, tyrant | **Viceroy Richel Decos** → **Lord Regent Valerius Decimus** | Tyrannical Viceroy of Oakhaven | Freedom Quest | Oppressive ruler who monopolizes the miracle crop. His mansion was formerly a temple of Silva. Keeps levitating messenger birds and an army of farm workers. |
| **Petrus** | High Priest of Valpuris in Cathedral | **High Priest Petrus Cordatus** → **Archpriest Valerius Cordatus** | Archpriest of the Great Frog, wielder of the Justifier | Freedom Quest | Spiritual leader of Valpuris Cathedral. Wields the Justifier (holy sword). Has seven wives and a legendary beard. His "left nut" relic is a quest item. |
| **Elpuri** | Evil dark frog boss | **The Guardian Elpuri** → **The Blight-Beast Malgorath** | Monstrous guardian of the Gloomy Caves | Freedom Quest (boss) | A massive, corrupted creature born from Scabies's blight. Once served Valpuris as a sacred protector but was twisted by millennia of corruption. Hates all who serve the Great Frog. |
| **Xinroch** | Immortal lich-king | **Lord Xinroch** → **Arch-Lich Khaz-Zadm** | Ancient undead lord, third Grand Master Dark Knight | Xinroch Tomb | Founded necromancy after the Divine War. His ghost haunts the deepest level of his crypt. Wielded the Lost Ruby Flaming Sword. |
| **Golgor Dhan** | Present Grand Master Dark Knight | **Grand Master Golgor Dhan** → **Grand Master Gorath Vex** | Current leader of the Unholy Order | Xinroch Tomb | Commands the Dark Knights in Khaz-Zadm's absence. Wields dark armor and commands necromancers. |
| **Artorius** | Crown Prince of Aslona (missing) | **Prince Artorius** → **Prince Aethelred II** | Missing heir to Castle Aethelred | Civil War | Kidnapped by goblins at Castle Noth. Currently held in the Ruins of Quetzaltia's prison cells as a child prisoner. |
| **Huang Ming Pong** | Sumo wrestler champion | **Huang Ming Pong** → **Master Kendo Oshiro** | Champion martial artist, guardian of sacred combat techniques | Side quest (Sumo) | Guardian of Oakhaven's sacred fighting traditions. Fights in the arena for entertainment and honor. |
| **Karl** | Sophite monk, wielder of Vermis | **Karl** → **Brother Aldric the Scholar** | Sophite monk who united kobold tribes | Lore story | Wielded Vermis (diamond spear). Died stepping on a land mine while uniting the kobold tribes. His weapon now rests in Valpuris's legendary weapons chest. |
| **Saal'Thul** | Assassin of Cleptia | **Saal'Thul** → **Shade Vespera** | Shadow assassin serving Cleptia | Lore story | Master thief who stole from Mellis's vaults. Operates through the Shadow Bazaar network. |

### 3.2 Supporting NPCs (Replacing Original Characters)

| Old Name | New Name | Role |
|---|---|---|
| **Genetrix Vesana** | Genetrix Vesana → **The Carnivorous Matriarch Vespera** | Mother carnivorous plant, created by Valpuris alchemists. Boss in Sunken Passage. |
| **Vladimir** (bunny pet) | Vladimir → **Shadowpaw** | Ivan's bunny companion. Follows the player through adventures. |
| **Lobh-se** | Lobh-se → **Lobh-se the Undying** | Misbegotten daughter of Scabies, dwells in Sunken Passage. Invulnerable due to accumulated diseases/poisons over millennia. Spider lair boss. |
| **Nihil** | Nihil → **Nihil the Fallen** | Fallen Archangel of Mortifer. Philosophical dialogue about nothingness and absurdity. |
| **Terra** | Terra → **Terra Greenweaver** | Elder Priestess of Silva, guards Crystal Cave shrine against Lobh-se. References Oakhaven invasion. |
| **Harvan Black-cloak** | Harvan Black-cloak → **Harvan Shadowcloak** | Rebel leader who murdered King Othyr. Wields Muramasa (dark katana). AttachedGod: LEGIFER. |
| **Lord Regent Efra Peredivall** | Lord Regent Efra Peredivall → **Lord Regent Efra Pendragon** | Rules Castle Aethelred after king's death. Wields Masamune (holy katana). AttachedGod: SEGES. |
| **Myrddin Wyllt** | Myrddin Wyllt → **Merlin the Arcane** | Royal wizard of Aslona, born with magic powers. AttachedGod: SOPHOS. Quest-giver for Pyramid weapon. |
| **Lord Mittrars (Tristram)** | Lord Mittrars → **Marshal Tristram** | Royal army commander of Aslona. Field marshal serving the crown forces. |

### 3.3 Faction NPCs

| Old Config | New Name/Role | Notes |
|---|---|---|
| guard.MASTER | Sir Haedlac Galladon VII → **Cardinal Galahad the Seventh** | Attnamese Cardinal of Peace, head of Bureau of Investigation. References Archpriest's beard legend. House of Galladon has served since Sir Galladon I. |
| guard.EMISSARY | Sir Lancelyn → **Sir Lancelot of Aslona** | Diplomatic envoy to goblin lands and orcish freeholds. AttachedGod: CRUENTUS. |
| shopkeeper.NEW_ATTNAM | Zolku → **Merchant Zulko** | Cheapest miracle crop shop owner. References Decimus's alchemists, levitating messenger birds. |
| shopkeeper.ATTNAM | Hulbo → **Hulvo the Merchant** | References mutant mushrooms, enner beasts (forest guardians), Malgorath's doings. |
| shopkeeper.ELPURI_CAVE | Merka → **Guildmaster Merka** | Guild member with extensive lore about Malgorath hatching in Valpuris Cathedral as Archpriest's pet favorite, becoming the Devourer. |
| shopkeeper.XINROCH_TOMB | Pate → **Pedlar Pate** | References Archpriest as "scum", rotten priests of Valpuris. |
| shopkeeper.BLACK_MARKET | One-eyed Sam → **One-Eyed Samir** | Orc flesh/black blood merchant. Sells unique artifact ring of speed. |
| shopkeeper.REBEL_CAMP | Gustaff → **Quartermaster Guff** | Rebel quartermaster. References Harvan Shadowcloak, rats in camp. |
| priest.VALPURUS | Verax → **Cardinal Verax** | Cardinal of Truth. Extensive lore about Valpuris as Great Frog carrying world on back, Cathedral with no windows, Justifier, Shirt of Golden Eagle. |
| priest.SILVA | Florea → **Priestess Florea** | References elven nation Lunethia, giant holy tree (Holy Mango World-tree), Decimus making firewood from altar, Valpuris occupation. |
| priest.INFUSCOR | Praecantrix → **Praecantrix Morwenna** | Priestess of Infuscor with extensive Khaz-Zadm/Dark Knights lore. Purple tattoos with holy book text. |
| priest.LEGIFER | Lady Decora → **Lady Decora the Shining** | Shining Knight of Legifer. References Order founded to fight Dark Knights, defeat at Fortress Prym, Turox maces blessed by Legifer. |

---

## 4. Story Arc Mapping

### 4.1 Arc A: The Freedom Quest (Primary Opening)
**Old:** Player summoned to Decos mansion → letter to Petrus in Attnam → underwater tunnel → Cathedral → slay Elpuri the dark frog → bring head → granted freedom → become new viceroy of Tweraif

**New:** Player is a serf on Lord Regent Valerius Decimus's estate in Oakhaven. One morning, you are summoned to the mansion (formerly a temple of Silva) where Decimus gives you a sealed scroll — a message from Archpriest Valerius Cordatus in the Holy City of Valpuris. You must deliver it through the dangerous Sunken Passage.

In Valpuris Cathedral, Archpriest Petrus reveals that the Blight-Beast Malgorath has emerged from the Gloomy Caves and threatens all who serve the Great Frog. He tasks you with slaying Malgorath and bringing back its corrupted heart as proof. You journey through the Sunken Passage (facing Genetrix Vesana, Terra's Crystal Shrine, and Lobh-se's Spider Lair), reach the Dark Fortress where Malgorath dwells, and defeat it.

Upon returning with Malgorath's heart, Archpriest Petrus grants you freedom from your serfdom. Later, when Oakhaven is freed from Decimus's tyranny (all his colonists defeated), you are named the new protector of Oakhaven — a position of honor and responsibility.

**Parallel Structure:**
- Oppressive ruler → tyrannical viceroy ✓
- Letter delivery quest → sealed scroll from Archpriest ✓
- Journey through dangerous passage → Sunken Passage with boss rooms ✓
- Boss monster (Elpuri) → corrupted guardian (Malgorath) ✓
- Freedom reward → serfdom lifted, named protector ✓

### 4.2 Arc B: The Crypt of Khaz-Zadm Quest
**Old:** Delve into Tomb of Xinroch (11 levels, necromancy-heavy), guarded by Dark Knights and kamikaze dwarves in gas chambers. Contains artifacts from Divine War: Neerc Se-ulb, Mjolak, Vermis, Turox.

**New:** The Crypt of Khaz-Zadm is an 11-level necromancy dungeon in the northern glacier mountains. It was built by Arch-Lich Khaz-Zadm after he became the third Grand Master Dark Knight following the Divine War. The crypt is guarded by fanatical Dark Knights who serve Infuscor and follow Khaz-Zadm's ghost even in undeath.

Deeper levels contain gas chambers with kamikaze dwarves — dwarf engineers who were conscripted into suicide squads by the Dark Knights. These dwarves detonate themselves to protect the crypt's treasures.

The crypt contains four legendary artifacts from the Divine War:
1. **Neerc Se-ulb** → **Nethervane** — Dark mace of Mortifer/Cruentus, life-draining energies
2. **Mjolak** → **Thunderfist** — Hammer of Mortifer, unholy energy bursts
3. **Vermis** → **Soulthorn** — Diamond-bladed spear of Sophos/Brother Aldric, teleports enemies
4. **Turox** → **Dawnbreaker** — Holy maces of Legifer/Shining Knights, magical explosions

**Victory Condition:** Deliver the Shadow Veil to the Necromancer (Anmah) in exchange for Khaz-Zadm's Lost Ruby Flaming Sword. At the Infuscor altar in level 0, three-stage vision system leads to becoming Master Dark Knight of the Unholy Order of Infuscor.

### 4.3 Arc C: The Aslona Civil War
**Old:** Kingdom of Aslona with civil war between rebels and crown forces. Crown Prince Artorius missing (allegedly goblin raid). Player can side with either rebels or crown. Involves Goblin Fort, Pyramid, Rebel Camp.

**New:** The Kingdom of Aethelred is torn by civil war. King Othyr was murdered under mysterious circumstances, and his son Prince Aethelred II has been kidnapped — allegedly by goblins at Castle Noth (now the Ruins of Quetzaltia).

Two factions vie for control:
- **Crown Forces** led by Lord Regent Efra Pendragon (Marshal Tristram's uncle), wielding the Masamune (holy katana)
- **Rebel Forces** led by Harvan Shadowcloak, wielding the Muramasa (dark katana)

The player can infiltrate either side. The Pyramid quest involves obtaining a thaumic bomb from Merlin the Arcane to destroy the Bunker of Otoul'iv. Multiple victory paths exist: nuclear option, weeping obsidian shard, katana duel, or prince rescue.

**Victory Conditions:**
- Crown path: Coronation regalia + Masamune at Castle Aethelred throne → "usurped the throne" (but as rightful heir's regent)
- Rebel path: Muramasa + Masamune + Blue Blood at Castle Aethelred throne → "Long live the king!"

### 4.4 Arc D: Side Quests & Locations
| Old | New | Description |
|---|---|---|
| Sumo Wrestling (Huang Ming Pong) | **Martial Arts Tournament** (Master Kendo Oshiro) | Sacred combat arena in Oakhaven. Champion fights for honor and Decimus's advertising contract. |
| Black Market (One-eyed Sam) | **Shadow Bazaar** (One-Eyed Samir) | Hidden underground market in the Sylvan Weald. Sells black blood, rare artifacts. |
| Fungal Cave (mushroom growths) | **Mycelial Depths** (fungal corruption) | Strange fungal growths near coal mines. Source of weeping obsidian shards ("Tear of Silva"). |
| Dark Forest / Irinox | **Wailing Woods / Silent Hollows** | Mysterious outdoor dungeon pair with beartraps and scattered resources. |
| Mondedr (empty tundra) | **The Barrens** | Empty wasteland on continent's edge. No special features. |

---

## 5. Creature Replacement Table

### 5.1 Unique Creatures Requiring Complete Replacement

| Old Creature | New Creature | Stats Tier | Ecological Niche | Notes |
|---|---|---|---|---|
| **Ommel** (8-humped herbivore) | **Brambleback** — massive armored herbivores with thorn-covered hides and multiple humps storing sacred sap | Large Herbivore | Replaces Ommels as a source of valuable materials (hair, bone, teeth, blood). The sap is used in potions. Eight humps preserved for visual distinction. |
| **Enner Beast** (horrible forest beast) | **Wraithstalker** — massive predatory creatures that dwell in the Sylvan Weald's deepest groves. Their screams shatter armor and items. | Large Predator | Replaces Enner Beasts as a dangerous forest predator. Village of Enner → Village of Wraeth (mountain valley far east). |
| **Enner Child** | **Wraithling** — young wraithstalkers, smaller but still dangerous. Their wailing screams are heard across dungeon levels. | Medium Predator | Replaces ennerchild. |
| **Dark Frog / Light Frog / Giant Dark Frog** | **Blighttoad** (DARK_FROG), **Marsh Toad** (LIGHT_FROG), **Colossal Blighttoad** (GIANT_DARK_FROG) | Small→Large Amphibian | Replaces frog configs. Serve Malgorath the Blight-Beast. Blood is toxic and corrupted by Scabies's blight. Cathedral of Valpuris was once home to sacred toads that served Archpriest Petrus as pets. |
| **Hedgehog** (corrupted sacred animal) | **Thornback Porcupine** — large, aggressive porcupines whose spines are corrupted by Nefas's influence. Once sacred animals of Dulcis, now twisted creatures of vice and corruption. | Medium Beast | Replaces hedgehogs. Corrupted sacred animals of Dulcis (love/art deity). |
| **Banana Grower / Encourager** | **Crop Tender / Enforcer** — workers on Decimus's estate who tend the miracle crop. AI goes insane if they leave Oakhaven. HostileReplies: "The Crop is Power!" References Decimus's agricultural empire. | Medium Laborer | Replaces bananagrower/encourager. Miracle crop replaces banana as economic driver. |
| **Ostrich** (messenger bird) | **Skygull** — large flying birds used as messengers by Decimus's estate. Deliver miracle crops between Oakhaven and Valpuris. | Medium Flying Beast | Replaces ostriches. Levitating messenger birds → Skygulls with enchanted wings. |
| **Billswill** (pure mass of Bill's Will) | **The Archive** — a floating ethereal entity, remnants of an ancient magical operating system. References the "Recycle Bin," "640K RAM" joke adapted to fantasy: "the Great Vault holds only 640 kilostones of memory." AttachedGod: MELLIS. | Unique Entity | Replaces Billswill. Tech humor preserved but re-skinned as arcane machinery. |
| **Mommo** (goblin-related) | **Gloomspawn** — goblin-related creatures in fungal caves. Three variants: CONICAL, FLAT, BLOAT with different inventory drops. | Medium Monster | Replaces mommo variants. |

### 5.2 Creatures Kept (With Renaming Where Appropriate)
| Creature | Notes |
|---|---|
| Humans | Keep as baseline race |
| Dwarves (kamikaze dwarves, veteran kamikaze) | Keep dwarf archetype but rename culture to "Dwarves of Khaz-zadm" |
| Elves | Referenced in materials — expand presence as elven nation Lunethia |
| Orcs | Present in code — keep orc archetype. One-eyed Samir is an orc merchant. Cossack Ivan (communist) kept with new name/lore. |
| Goblins | Present in Goblin Fort dungeon — keep goblin archetype. Empire of Quetzaltia lore preserved. |
| Kobolds | Referenced in lore — keep kobold archetype. Brother Aldric united kobold tribes. |
| Trolls | Referenced in materials and lore — keep troll archetype |
| Skeletons, Zombies, Ghosts | Undead types kept as standard necromancy enemies |
| Spiders (LARGE/GIANT/ARANEA) | Kept — Lobh-se's Spider Lair uses these. Phase spiders added to Goblin Fort. |
| Wolves, Werewolves | Kept — wolf howling in Gloomy Caves, werewolfhuman/werewolfwolf variants |
| Vampires | Kept — origin from Cruentus+Infuscor blood (lore preserved) |
| Angels/Archangels | Kept — spawned by various gods. Fallen Archangel Nihil is a unique NPC. |
| Golems | Kept — artificial constructs from Divine War era, masterless golems in ruined Khaz-zadm mines |
| Carnivorous Plants | Kept — Genetrix Vesana is crossbreed of carnivorous plant + pineapple tree by Valpuris alchemists |
| Floating Eyes, Blink Dogs | D&D-like monsters — can keep or adapt |
| Various animals (bears, buffalo, lions, etc.) | Generic wildlife kept as-is |

---

## 6. Artifact Naming & Lore

### 6.1 Unique Weapons and Artifacts

| Old Name | New Name | Type | God | Effect | Lore Summary |
|---|---|---|---|---|---|
| **Justifier** | **The Justifier** (kept name — means "one who justifies") | Holy Sword | VALPURUS | Outline: green shimmer. Raises wielder to nobility. | Holy sword of Valpuris forged from Valpurium metal. Named for the Archpriest who wields it. PostFix: "named Valpuris' Justifier" |
| **Neerc Se-ulb** | **Nethervane** | Dark Mace | MORTIFER/CRUENTUS | 1/5 chance: life-drain (DRAIN damage). Red outline shimmer. | Dark mace of Mortifer and Cruentus. Its life-draining energies consume enemies' vitality. PostFix: "named Nethervane" |
| **Mjolak** | **Thunderfist** | Dark Hammer | MORTIFER | 1/3 chance: energy burst (ENERGY damage). Red outline shimmer. | Hammer of Mortifer that channels unholy lightning. PostFix: "named Thunderfist" |
| **Vermis** | **Soulthorn** | Diamond Spear | SOPHOS | 1/5 chance: teleport target randomly. Lore about Brother Aldric uniting kobold tribes, dying on a land mine. | Spear of Sophos wielded by Brother Aldric the Scholar. Sends enemies on sudden journeys through arcane portals. PostFix: "of Brother Aldric" |
| **Turox** | **Dawnbreaker** | Holy Mace | LEGIFER/Shining Knights | 1/5 chance: magical explosion (BURNED damage). Lore about siege of Fortress Prym, Shining Knights' divine blessing. | Holy maces of Legifer forged by the Shining Knights. PostFix: "named Dawnbreaker" |
| **Muramasa** | **Muramasa** (kept — Japanese dark katana name) | Dark Katana | Rebel faction | Against lawful/neutral: disease/debuff OR slow/poison/confused. Message: "%s defiles %s." | Dark katana of the rebel forces. Its blade corrupts all it touches. One of two regalia katanas (Muramasa + E-numa sa-am → Muramasa + **Kusanagi**). |
| **Masamune** | **Masamune** (kept — Japanese holy katana name) | Holy Katana | Crown faction | Against chaotic: removes negative effects, inflicts PANIC+TELEPORT_LOCK. Message: "%s rebukes %s." | Holy katana of the crown forces. Its blade purifies and repels evil. The other regalia katana (Muramasa + Kusanagi). |
| **Whip of Thievery** | **Cleptia's Lash** | Whip | CLEPTIA | Steals enemy's main wielded item when Cleptia helps. Message: "help of Cleptia." | Whip of Cleptia that steals from enemies with divine assistance. |
| **Chameleon Whip** | **Scabies' Tongue** | Whip | SCABIES | Polymorphs target randomly when Scabies helps. Player does evil deed. | Whip of Scabies that transforms enemies into random forms. |
| **Wonder Smell Staff** | **Staff of Strange Scent** | Staff | — | 1/5 chance: red smoke on enemies OR blue smoke under hitter. | Staff with dual smoke effects — red for offense, blue for defense. |
| **Slow Axe** | **Frostcleaver** | Axe | — | Applies SLOW status (400+ ticks). Message: "chills %s." | Axe that chills enemies to the bone. |
| **Terror Scythe** | **Panicblade** | Scythe | — | Inflicts PANIC based on target's mana (200+ ticks). Message: "terrifies %s." | Scythe that terrifies enemies with spectral dread. |
| **Banshee Sickle** | **Wailsong Sickle** | Sickle | — | Shrieks and calls attention, SOUND damage. Message: "shrieks at %s." | Sickle that shrieks like a banshee. |
| **Rust Scythe** | **Corrodeblade** | Scythe | — | Rusts armor/body parts on humanoid targets. | Scythe that corrodes metal and flesh alike. |
| **Sharp Axe** | **Severing Axe** | Axe | — | Severs body parts from humanoids. Message: "Your %s is severed off!" | Axe that cleaves limbs with brutal efficiency. |
| **Weeping Blade** | **Tearblade** | Blade | — | 2/3 chance: spills sulphuric acid (25+ damage). | Blade that weeps corrosive tears. |
| **Acid Shield** | **Corrosion Guard** | Shield | — | Douses attackers in sulphuric acid. Multiple messages about being "completely doused" or "splashed." | Shield that protects by dousing enemies in acid. |
| **Eptyron** | **Softener's Edge** | Weapon/Armor | — | Softens armor/body parts of humanoids (offense and defense). | Weapon and armor softener — disarms opponents mechanically. |

### 6.2 Quest Items & Relics

| Old Name | New Name | Description |
|---|---|---|
| **Holy Banana** | **Sacred Mango** | Golden sacred fruit imbued by Seges. NutritionValue=20000, Effect=EFFECT_SACRED_MANGO. Origin story: Oily Orpiv → **Sage Orpheus**, Mellis → **Seges**, banana discovery → mango discovery in the jungles of Oakhaven, subjugation of village → Decimus's monopoly on the sacred crop. |
| **Banana Peel** | **Mango Pit** | Slip hazard, food source. Replaces banana peel mechanics. |
| **Left Nut of Petrus** | **The Archpriest's Relic** | Quest relic of Archpriest Petrus. DescriptiveInfo: "A sacred relic of the fallen Archpriest." |
| **Copy of Left Nut of Petrus** | **The Imitation Relic** | Joke item about Petrus losing his nut, Attnamese throne → Valpuris throne. Cheap config version. |
| **Head of Elpuri** | **Heart of Malgorath** | Boss trophy. PostFix: "of Malgorath". Elegiac death message describing the Blight-Beast's final moments. |
| **Skull of Xinroch** | **Crown of Khaz-Zadm** | Quest item. PostFix: "of Khaz-Zadm the Arch-Lich". Extensive tomb lore in DescriptiveInfo about the crypt, Dark Knights, and Divine War artifacts. |
| **Encrypted Scroll** | **Sealed Dispatch** | Freedom Quest key item. DescriptiveInfo references Archpriest Petrus, Lord Regent Decimus, Oakhaven, Cathedral of Valpuris. "This scroll seems to be somehow disfunctional" → "This dispatch seems to be sealed with arcane wards." |
| **Avatar of Valpurus** | **Icon of Valpuris** | Quest item made of Valpurium metal. PostFix: "of Valpuris". |
| **Shirt of Golden Eagle** | **Tunic of the Golden Hawk** | Reward for completing Petrus's quest chain. Holy armor blessed by Valpuris. |

### 6.3 The Miracle Crop Replacement (Banana → Sacred Mango)

The banana is replaced with the **Sacred Mango** — a golden fruit that grows in the sheltered orchards of Oakhaven's valley. It serves as:
- **Economic driver:** Decimus's monopoly on mangoes funds his oppressive rule
- **Food source:** Mango flesh provides nutrition; mango pits are slippery hazards
- **Religious significance:** Imbued by Seges with sacred properties (Sacred Mango variant)
- **Cultural identity:** Oakhaven's economy and culture revolve around the crop
- **Quest item:** The Holy Banana → Sacred Mango is central to the Freedom Quest ending

The mango seedling mechanic for the Freedom Quest victory remains: planting a sacred tree/seedling at the drop area liberates Oakhaven from Decimus's tyranny.

---

## 7. Technical Planning

### 7.1 Image Generation Pipeline

**Model:** `wikeeyang/Flux2-Klein-9B-True-V2` via HuggingFace Diffusers library

**Asset Catalog (to be generated by script):**
Each PNG file needs: filename, dimensions, pixel format, purpose, replacement prompt

| File | Purpose | Replacement Prompt Theme |
|---|---|---|
| `Char.png` | Character sprite sheet | Dark fantasy adventurer sprites in medieval armor/clothing |
| `Humanoid.png` | Humanoid NPC sprites | Fantasy NPCs: priests, knights, merchants, rebels in period-appropriate clothing |
| `Item.png` | Item icons | Fantasy RPG item icons (swords, maces, spears, whips, staves) |
| `Item-outlined.png` | Outlined item icons | Same items with white outline for UI visibility |
| `Cursor.png` | Game cursor | Keep generic or adapt to fantasy arrow/crosshair |
| `Font.png`, `Font2.png`, `Font3.png` | Font bitmaps | Medieval/fantasy style bitmap fonts |
| `WTerra.png` | World terrain tiles | Fantasy landscape: snow, glacier, desert, tundra, jungle, evergreen forest, steppe |
| `OLTerra.png` | Overworld terrain tiles | Same biomes at overworld scale with landmarks (cathedrals, castles, ruins) |
| `GLTerra.png` | Ground terrain tiles | Floor types: stone, gravel, bone, ice, coal, steel, obsidian, etc. |
| `Effect.png` | Spell/effect particles | Fantasy spell effects: fire, lightning, dark energy, holy light, acid |
| `FOW.png` | Fog of war overlay | Keep generic fog pattern |
| `Menu.png`, `Menu1-5.png` | Menu screens | Dark fantasy UI with medieval borders and iconography |
| `Symbol.png` | Game symbol/logo | New IVAN logo: dark fantasy crest/emblem |
| `IVlad.png` | Vladimir character sprite | Bunny companion sprite → Shadowpaw the bunny |
| `Enner.png` | Enner Beast sprite | Wraithstalker — large predatory forest creature with glowing eyes |
| `Smiley.png` | ??? | Keep or replace with fantasy expression sprites |

**Script Architecture:**
```python
# image_generator.py
import diffusers
from PIL import Image
import json

class AssetGenerator:
    def __init__(self, model_path="wikeeyang/Flux2-Klein-9B-True-V2"):
        self.pipe = load_diffusion_pipeline(model_path)
        self.asset_catalog = load_asset_catalog()  # JSON with dimensions/purposes
    
    def generate_sprite(self, prompt, width, height, output_path):
        """Generate a sprite sheet at exact required dimensions"""
        image = self.pipe(prompt, width=width, height=height).images[0]
        image.save(output_path)
    
    def batch_generate(self, asset_list, api_key=None):
        """Batch generate all assets with rate limiting and retry logic"""
        for i, asset in enumerate(asset_list):
            try:
                self.generate_sprite(
                    prompt=asset['prompt'],
                    width=asset['width'],
                    height=asset['height'],
                    output_path=asset['output']
                )
            except Exception as e:
                retry_with_backoff(i, asset, max_retries=3)

# Usage: python image_generator.py --catalog assets.json --output-dir Graphics/
```

### 7.2 Text Generation Pipeline Architecture

**Model:** Claude (claude-sonnet-4-6)

**Pipeline Stages:**
1. **Name Translation Pass:** Apply old→new name mapping to all .dat files
2. **Descriptive Text Rewrite:** LLM generates new lore/flavor text for each item, material, character
3. **Dialogue Adaptation:** Rewrite C++ hardcoded strings with new setting names
4. **Lore Document Rewrite:** Generate new versions of all lore TXT/RTF files
5. **Validation Pass:** Verify numerical values unchanged, check for missed references

**Batch Strategy:**
- .dat files: batch 100 items per API call (context window ~8K tokens)
- C++ strings: batch by file (human.cpp ~200 strings, game.cpp ~60 strings, etc.)
- Lore documents: one document per API call (~3-5K tokens each)

**Prompt Template Example:**
```
You are rewriting creative content for a dark fantasy roguelike game.
Old setting: frog-worshipping empire with banana plantations
New setting: Valpuris Cathedral, Great Frog deity, Oakhaven estate with sacred mango crop

Rewrite this item description maintaining the same tone and length:
OLD: "{old_text}"
CONTEXT: {item_context}
RETURN ONLY THE NEW TEXT.
```

### 7.3 Name/Term Translation Table Template (CSV)

| Category | Old Term | New Term | Arc Association | Notes |
|---|---|---|---|---|
| God | Valpurus/Valpuri | Valpuris | All | Supreme deity, Great Frog epithet |
| God | Mortifer | Mortifer (kept) | All | Destroyer of Worlds |
| Location | Attnam | Valpuris | Freedom Quest | Holy City of Valpuris |
| Location | New Attnam/Tweraif | Oakhaven | Freedom Quest | Coastal farming village |
| Location | Pertturia | Sylvan Weald | All | Ancient enchanted forest |
| Creature | Elpuri (dark frog) | Malgorath (Blight-Beast) | Freedom Quest | Boss monster |
| Creature | Ommel | Brambleback | All | 8-humped armored herbivore |
| Artifact | Justifier | The Justifier | Freedom Quest | Holy sword of Valpuris |
| Item | banana | mango / Sacred Mango | Freedom Quest | Miracle crop replacement |
| Item | holybanana | sacredmango | Freedom Quest | Imbued religious fruit |
| NPC | Petrus | Archpriest Valerius Cordatus | Freedom Quest | High priest, wielder of Justifier |
| NPC | Richel Decos | Lord Regent Valerius Decimus | Freedom Quest | Tyrannical viceroy |

### 7.4 Batch Processing Strategy

**Order of Operations:**
1. **Phase 1 — .dat Files (Text-Only, No Dependencies):**
   - `define.dat` → rename enums, effect IDs, material IDs
   - `material.dat` → rewrite all names and descriptions
   - `item.dat` → rewrite item names, descriptions, PostFixes
   - `char.dat` → rewrite character names, descriptions, dialogue references
   
2. **Phase 2 — C++ Source Files (Depends on Phase 1 Names):**
   - `human.cpp` → quest dialogues (~200+ strings)
   - `game.cpp` → opening text, story messages (~60+ strings)
   - `gods.cpp` → prayer effects (~8 hardcoded strings)
   - `gear.cpp` → artifact hit effect messages (~15 strings)
   - `rooms.cpp` → room-specific dialogue (5 strings)
   - `char.cpp` → death messages, victory text (~10 strings)
   - `miscitem.cpp` → banana references (5 strings)
   - `team.cpp` → alarm/angel dialogue (2 strings)

3. **Phase 3 — Lore Documents:**
   - All TXT files in Doc/Lore/Fiction/ and Doc/Lore/HolyStack/
   - RTF files need format conversion first

4. **Phase 4 — Graphics Generation:**
   - Sprite sheets, terrain tiles, UI art
   - Depends on new creature/NPC designs being finalized

5. **Phase 5 — Validation & Testing:**
   - Diff-based comparison of numerical values in .dat files
   - String search for any missed old references
   - Compile test to verify C++ changes are syntactically correct

**Estimated API Calls:**
- .dat file rewrites: ~20 calls (100 items/call)
- C++ string rewrites: ~8 calls (by file)
- Lore document rewrites: ~15 calls (one per document)
- Total text generation: ~43 API calls

### 7.5 Game Balance Validation Approach

**Diff-Based Comparison Script:**
```python
# balance_validator.py
import csv, json

def extract_numerical_values(dat_file):
    """Extract all numerical values from a .dat file, ignoring string fields"""
    # Parse .dat DSL and extract: PriceModifier, NutritionValue, 
    # StrengthValue, Color RGB, Enchantment levels, HP/Day requirements, etc.
    pass

def compare_dat_files(old_file, new_file):
    """Verify numerical values are unchanged between old and new .dat files"""
    old_values = extract_numerical_values(old_file)
    new_values = extract_numerical_values(new_file)
    
    mismatches = []
    for key in old_values:
        if old_values[key] != new_values.get(key):
            mismatches.append(f"{key}: {old_values[key]} → {new_values[key]}")
    
    return mismatches

# Run on all .dat files after rewrite
for dat_file in ['item.dat', 'material.dat', 'char.dat']:
    mismatches = compare_dat_files(f'backup/{dat_file}', f'rewrite/{dat_file}')
    if mismatches:
        print(f"WARNING: {len(mismatches)} numerical value changes in {dat_file}")
```

### 7.6 Additional C++ Files with Story References

| File | Story References | Action Needed |
|---|---|---|
| `cmdcraft.cpp` | banana/Ommel class references (lines 69, 2458, 4243) | Rename class references when item classes change |
| `cmdcraftfilters.cpp` | dynamic_cast to banana/bananapeels/holybanana (lines 31, 33, 72) | Update type casts for renamed classes |
| `stack.cpp` | comment about bananas, OMMEL_BONE enum reference (line 980) | Update comments and enum references |

### 7.7 Header File Updates — Cross-File Rename Strategy

**Functions to Rename:**
| Old Name | New Name | Files Affected |
|---|---|---|
| `HasHeadOfElpuri()` | `HasHeartOfMalgorath()` | char.h, human.cpp, game.cpp |
| `HasPetrussNut()` | `HasArchpriestsRelic()` | char.h, human.cpp, game.cpp |
| `HasGoldenEagleShirt()` | `HasGoldenHawkTunic()` | char.h, human.cpp, game.cpp |
| `GetPetrus()` | `GetArchpriest()` | game.h, team.cpp, human.cpp |
| `IsDecosAdShirt()` | `IsDecimusAdShirt()` | item.h, game.cpp |

**Classes to Rename:**
| Old Class | New Class | Description |
|---|---|---|
| `banana` | `mango` | Zappable weapon with charges/jam mechanics |
| `holybanana` | `sacredmango` | Sacred weapon item with flame special flag |
| `bananapeels` | `mangopits` | Slippery terrain material on ground |

**Enums to Update:**
- `OMMEL_*` → `BRAMBLEBACK_*` (material IDs)
- `EFFECT_OMMEL_*` → `EFFECT_BRAMBLEBACK_*` (effect IDs)
- `CEM_FROG_FLESH` → `CEM_BLIGHTTOAD_FLESH`
- `HM_FROG_FLESH` → `HM_BLIGHTTOAD_FLESH`
- `ELPURI_FLESH` → `MALGORATH_FLESH`
- `ENNER_BEAST_FLESH` → `WRAITHSTALKER_FLESH`

### 7.8 Formatting Fixes for HIGH_LEVEL_PLAN.md

1. **Section 5.1.1 olterra.dat scan:** Add numbered header "#### 5.1.1.20 `Script/olterra.dat`" to match other scans
2. **rooms.cpp inventory count:** Change "6 total" to "5 total" (only 5 hardcoded strings listed)

---

## 8. Execution Checklist

### Phase 1: Creative Design (This Document)
- [x] Define new fantasy world geography (Aethelgard continent, 17 locations)
- [x] Design new pantheon (16 gods + ATHEIST, with names, domains, alignments, colors)
- [x] Create new character roster (key NPCs, supporting NPCs, faction NPCs)
- [x] Map old story arcs → new story arcs (Freedom Quest, Xinroch Tomb, Aslona Civil War, Side Quests)
- [x] Design replacement creatures for Ommels, Enner Beasts, and other unique IVAN creatures
- [x] Create new artifact names and lore (15+ weapons/artifacts with effects and descriptions)
- [x] Plan the banana → Sacred Mango replacement (economic driver, quest item, food source)
- [x] Review EncounterWithKamikazeDwarf.txt (kamikaze dwarf encounter — creation myth of Puu tree)
- [x] Review Creation.rtf ("The Eight Eggs of Valpuri" — creation myth with Elder Gods and Nenimhi)

### Phase 2: Data File Rewrites
- [x] Rewrite `Script/define.dat` — rename enums, effect IDs, material IDs, team IDs, dungeon IDs
- [ ] Rewrite `Script/material.dat` — all names, descriptions, cross-references
- [ ] Rewrite `Script/item.dat` — item names, descriptions, PostFixes, god attachments
- [ ] Rewrite `Script/char.dat` — character names, descriptions, dialogue references

### Phase 3: C++ Source Rewrites
- [ ] Rewrite `Main/Source/human.cpp` (~200+ story strings)
- [ ] Rewrite `Main/Source/game.cpp` (~60+ story strings)
- [ ] Rewrite `Main/Source/gods.cpp` (~8 hardcoded strings)
- [ ] Rewrite `Main/Source/gear.cpp` (~15 artifact strings)
- [ ] Rewrite `Main/Source/rooms.cpp` (5 room strings)
- [ ] Rewrite `Main/Source/char.cpp` (~10 story strings + function renames)
- [ ] Rewrite `Main/Source/miscitem.cpp` (5 banana strings + class renames)
- [ ] Rewrite `Main/Source/team.cpp` (2 strings)
- [ ] Update `cmdcraft.cpp`, `cmdcraftfilters.cpp`, `stack.cpp` (class references)

### Phase 4: Header File Updates
- [ ] Rename functions in char.h, game.h, gear.h, item.h
- [ ] Rename classes for banana/mango system
- [ ] Update enum comments in ivandef.h

### Phase 5: Lore Document Rewrites
- [ ] Rewrite all TXT files in Doc/Lore/Fiction/ (14 files)
- [ ] Convert and rewrite RTF files in Doc/Lore/HolyStack/ (3 files)
- [ ] Rewrite Titues.txt, ValpuriFAQ.txt, README.txt

### Phase 6: Documentation Updates
- [ ] Update MANUAL file (~5 story references)
- [ ] Update NEWS changelog (~36+ story references)

### Phase 7: Graphics Generation
- [ ] Generate new sprite sheets (Char.png, Humanoid.png, etc.)
- [ ] Generate terrain tiles (WTerra.png, OLTerra.png, GLTerra.png)
- [ ] Generate UI art (Menu.png, Menu1-5.png, Symbol.png)
- [ ] Generate item icons (Item.png, Item-outlined.png)

### Phase 8: Validation & Testing
- [ ] Run balance_validator.py on all .dat files
- [ ] String search for any missed old references across entire codebase
- [ ] Compile test to verify C++ changes are syntactically correct
- [ ] Test game with new assets to verify visual consistency
