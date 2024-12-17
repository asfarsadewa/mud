# MUD Game Tools

This directory contains various tools for managing and editing game content.

## Available Tools

### Item Editor (item_editor.py)
A tool for managing game items. Features:
- List all items with their weights and respawn settings
- Create new items with:
  - Basic info (ID, name, descriptions)
  - Item type (weapon, armor, consumable, etc.)
  - Weight property (affects character carrying capacity)
  - Respawn settings (if item should reappear after being taken)
  - Type-specific properties (damage, defense, effects)
- Edit existing items
- Delete items

### NPC Editor (npc_editor.py)
A tool for managing NPCs and their dialogue. Features:
- List all NPCs
- Create new NPCs with dialogue trees
- Edit existing NPCs and their dialogue
- Delete NPCs

### World Editor (world_editor.py)
A tool for managing game worlds and rooms. Features:
- List all worlds
- Create new worlds
- Edit existing worlds and their rooms
- Delete worlds
- Manage room connections and items

### Mob Editor (mob_editor.py)
A tool for managing game monsters and enemies. Features:
- List all mobs with their stats
- Create new mobs with:
  - Basic info (ID, name, descriptions)
  - Combat stats (HP, attack, defense)
  - Loot tables with drop probabilities
  - Spawn area definitions
- Edit existing mobs
- Delete mobs

## Usage

Each tool can be run directly from the command line:

```bash
python item_editor.py
python npc_editor.py
python world_editor.py
python mob_editor.py
```

## Data Structure

All tools operate on JSON files in the `data` directory:
- `items.json` - Item definitions with weight and respawn properties
- `npcs.json` - NPC definitions and dialogue
- `worlds/` - World and room definitions
- `mobs.json` - Monster/enemy definitions

## Best Practices

1. Always use descriptive IDs (e.g., `wolf_001`, `spider_002`)
2. Provide detailed descriptions for better gameplay experience
3. Balance mob stats appropriately for their level
4. Set reasonable drop rates for loot
5. Place mobs in appropriate spawn areas
6. Set appropriate weights for items based on their type and size
7. Configure respawn timers that make sense for game balance
8. Save your changes before exiting

## Example Item Creation

Here's an example of creating a new item:

```
=== Create New Item ===
Enter item ID: health_potion_002
Enter short desc: a large healing potion
Enter long desc: A crystal vial containing a bright red liquid that sparkles with healing energy.
Choose item type (1-8): 3 (consumable)
Enter item weight (in units): 0.5
Is this item respawnable? (y/n): y
Enter respawn time in seconds (default 1800): 900
Enter effect: heal
Enter effect value: 50
```

## Example Mob Creation

Here's an example of creating a new mob:

```
=== Create New Mob ===
Enter mob ID: spider_003
Enter mob name: Giant Cave Spider
Enter short desc: a massive, hairy spider
Enter long desc: This enormous arachnid is the size of a horse. Its eight eyes gleam with malevolent intelligence.
Enter level: 3
Enter max HP: 45
Enter attack: 12
Enter defense: 4
Enter XP value: 40

Loot Table:
Enter item ID: spider_silk_001
Enter probability: 0.8
Enter item ID: poison_sac_001
Enter probability: 0.5
Enter item ID: done

Spawn Areas:
Enter room ID: cave_chamber_001
Enter room ID: cave_tunnel_001
Enter room ID: done
```

## Item Properties Reference

When creating or editing items, consider these properties:

1. **Weight System**
   - All items must have a weight value (in units)
   - Weight affects character carrying capacity
   - Typical weight ranges:
     - Light items (scrolls, potions): 0.1-0.5 units
     - Medium items (weapons, tools): 1.0-3.0 units
     - Heavy items (armor, large weapons): 3.0-8.0 units

2. **Respawn Settings**
   - Respawnable: Whether item reappears after being taken
   - Respawn time: Seconds until item reappears
   - Recommended respawn times:
     - Common items: 300-900 seconds (5-15 minutes)
     - Uncommon items: 1800-3600 seconds (30-60 minutes)
     - Rare items: No respawn