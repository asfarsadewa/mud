# MUDewa - a solo player MUD with some AI (Gemini)

A JSON-based MUD (Multi-User Dungeon) game written in Python. This single-player MUD (SUD) allows you to explore a text-based world, interact with items, and auto-save your progress. This game has also sprinkles of AI here and there that I am still developing.
This is a love letter to SDFMud, a world I lived in more than two decades ago.

## Architecture Overview

The engine is built around several key managers that handle different aspects of the game state:

### Core Managers

1. **DataManager** (`src/data_manager.py`)
   - Central data access layer
   - Handles raw JSON file operations (load/save)
   - Maintains in-memory cache of game data
   - Provides basic CRUD operations for game entities
   - **Important**: Does not modify data directly; delegates to specialized managers

2. **CharacterManager** (`src/character_manager.py`)
   - Manages character state and persistence
   - Handles inventory operations and weight limits
   - Tracks character stats and progression
   - Maintains character's known dialogue topics
   - Manages character-specific world state
   - Uses DataManager for persistence but owns character logic

3. **WorldManager** (`src/world_manager.py`)
   - Manages world state and room transitions
   - Handles room contents (items, NPCs)
   - Manages multiple world files
   - Validates world connectivity
   - Handles item respawning per character
   - Uses DataManager for persistence but owns world logic

4. **CombatManager** (`src/combat_manager.py`)
   - Handles combat state and mechanics
   - Manages mob spawning and combat turns
   - Handles loot distribution
   - Uses both WorldManager (for loot placement) and DataManager (for state)

### Manager Relationships

```
DataManager
    ↑
    | (data access)
    |
    +----------------+----------------+
    |                |                |
CharacterManager  WorldManager    CombatManager
    |                |                |
    +----------------+----------------+
    |
CommandHandler (coordinates between managers)
```

### AI Integration with Gemini 2.0

The game integrates Google's Gemini 2.0 AI model for enhanced gameplay features. The integration is handled through the `GeminiHelper` class in `src/ai_helper.py`.

#### Setup Requirements

1. Get a Google API key from [Google AI Studio](https://ai.google.dev/)
2. Create a `.env` file in the root directory with your API key:
```bash
GOOGLE_API_KEY=your_api_key_here
```

#### AI Helper Features

The `GeminiHelper` class provides:
- Async-compatible interface with synchronous Gemini API calls
- Context-aware response generation
- Basic error handling and fallback responses
- Simple session cleanup

Example Usage:
```python
from src.ai_helper import GeminiHelper

# Initialize the helper
ai_helper = GeminiHelper()

# Generate a response (async signature but synchronous operation)
response = await ai_helper.generate_response(
    "Describe this location",
    context={"location": "dark forest", "time": "midnight"}
)

# Clean up
await ai_helper.close_session()
```

### Key Design Patterns

1. **Manager Pattern**
   - Each manager is responsible for a specific domain
   - Managers don't directly modify each other's data
   - All persistence goes through DataManager

2. **Dependency Injection**
   - Managers receive their dependencies in constructors
   - Allows for easier testing and modification
   - Example: CombatManager receives both DataManager and WorldManager

3. **Single Responsibility**
   - Each manager has a clear, focused purpose
   - DataManager: Raw data operations
   - CharacterManager: Character state
   - WorldManager: World state
   - CombatManager: Combat mechanics

4. **Character-Specific World State**
   - Each character maintains their own view of the world
   - Tracks removed items and respawn timers independently
   - Prevents item state conflicts between characters
   - Ensures new characters start with fresh world state
   ```json
   Character World State Structure
   {
     "world_state": {
       "removed_items": {
         "item_id": {
           "room": "room_id",
           "time": timestamp,
           "world": "world_name"
         }
       }
     }
   }
   ```

5. **Item Management System**
   - Weight-based inventory system
   - Character weight limits (base + level bonus)
   - Item respawn mechanics
   - Per-character item tracking
   ```json
   Item Properties Structure
   {
     "properties": {
       "type": "weapon|armor|consumable|etc",
       "weight": float,
       "respawnable": boolean,
       "respawn_time": integer (seconds)
     }
   }
   ```

6. **NPC Interaction Pattern**
   - Dialogue-based interaction system
   - Progressive topic discovery
   - Specialized NPC types (e.g., merchants)
   - Flexible topic matching with partial name support
   
   **Core Components:**
   ```
   NPC Data Structure
   ├── Basic Info (ID, name, descriptions)
   ├── Dialogue System
   │   ├── Greeting
   │   └── Topics
   │       ├── Simple Topics (string responses)
   │       └── Complex Topics (dictionary format)
   │           ├── Prompt (what player can ask)
   │           ├── Response (NPC's answer)
   │           ├── Requirements (prerequisites)
   │           └── Leads To (unlocked topics)
   └── Special Data (e.g., merchant_data)
   ```

   **Topic System:**
   - Supports both simple string responses and complex topic structures
   - Topics can be locked/unlocked based on prerequisites
   - Topics can lead to new conversation branches
   - Special topics can trigger functionality (e.g., trading)
   - Character maintains known topics per NPC
   - Flexible partial name matching for NPCs and topics
   
   **Merchant System (Example Special NPC):**
   ```
   Merchant Data
   ├── Regular Inventory
   │   ├── Items
   │   └── Prices
   ├── Premium Inventory (unlockable)
   │   ├── Special Items
   │   └── Premium Prices
   └── Trade Settings
       ├── Buy Multiplier
       └── Unlock Status
   ```

   **Interaction Flow:**
   ```
   Player Command -> NPC Check -> Topic Validation -> Response/Action
        │              │              │                    │
        │              │              │                    │
    talk/list/    Find NPC in     Check if     Generate response or
    buy/sell        current      topic is       trigger special
                     room       available         functionality
   ```

   **State Management:**
   - NPCs maintain their own state (inventory, etc.)
   - Characters track known topics per NPC
   - Merchant transactions affect both NPC and character state
   - All state changes are atomic and consistent

   **Quest System:**
   - Item-based quest system integrated with dialogue
   - Effects system for quest completion
   - Multiple reward types
   
   **Quest Topic Structure:**
   ```json
   {
     "prompt": "Player's question",
     "response": "Default response",
     "item_requirement": "required_item_id",
     "success_response": "Response when item is present",
     "effects": {
       "unlock_merchant": true,      // Unlock premium inventory
       "remove_item": true,          // Consume quest item
       "add_item": "reward_item_id", // Give reward item
       "add_money": 100,             // Give coins
       "unlock_topics": ["topic_id"] // Unlock new dialogues
     }
   }
   ```

   **Quest Flow Example:**
   ```
   Merchant's Lost Key Quest
   ├── Initial Topic ("wares")
   │   └── Leads to key topic
   ├── Quest Topic ("key")
   │   ├── Requires: key_001
   │   └── Effects:
   │       └── unlock_merchant: true
   └── Result
       └── Access to premium inventory
   ```

   **Quest Design Patterns:**
   - Progressive discovery through dialogue
   - Multiple quest completion effects
   - Flexible reward system
   - State persistence per character
   - Non-linear quest progression

7. **Portal Design Pattern**
   - World transition system using portals
   - Requirements-based access control
   - Bidirectional portal connections
   
   **Core Components:**
   ```
   Portal Data Structure
   ├── Type: "world_transition"
   ├── Target Information
   │   ├── Target World
   │   └── Target Room
   ├── Requirements
   │   ├── Level Requirement
   │   └── Item Requirements
   └── Description (portal appearance)
   ```

   **Portal System:**
   - Portals are defined in room exits
   - Each portal can have multiple requirements
   - Requirements are checked before transition
   - Bidirectional portals for return trips
   
   **Example Portal Definition:**
   ```json
   "exits": {
     "portal": {
       "type": "world_transition",
       "target_world": "spirit_realm",
       "target_room": "spirit_entrance_001",
       "description": "A shimmering portal of pure light hovers in the air.",
       "requirements": {
         "item": "spirit_key_001",
         "level": 5
       }
     }
   }
   ```

   **Transition Flow:**
   ```
   Player Command -> Requirements Check -> World Load -> Room Transition
        │                    │                │               │
        │                    │                │               │
    go portal      Check level/items    Load target     Move player to
                                         world        destination room
   ```

   **State Management:**
   - World transitions maintain character state
   - Requirements are validated before each transition
   - Portal states can be dynamic (e.g., only active at certain times)
   - Failed requirements provide clear feedback to player

### Common Pitfalls to Avoid

1. **Data Access**
   - Always use manager methods instead of direct file access
   - Example: Use `character_manager.save_character()` instead of direct JSON manipulation

2. **State Management**
   - Combat state should be cleared consistently across all combat endings
   - Always validate state transitions
   - Mob state should be stored in character's combat_state
   - Defeated mobs are tracked to prevent immediate respawning
   - Level up messages should be consistent
   - Item respawn state is character-specific
   - Weight limits must be checked before item pickup

3. **Cross-Manager Operations**
   - When an operation affects multiple domains:
     - CombatManager calculates loot
     - WorldManager places it in room
     - CharacterManager handles pickup and weight checks
   - World transitions should use character state
   - Item operations must update both world and character state
   - Respawn mechanics coordinate between WorldManager and CharacterManager

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd mudewa
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix/MacOS:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up AI integration (optional):
   - Get an API key from [Google AI Studio](https://ai.google.dev/)
   - Create a `.env` file in the root directory
   - Add your API key: `GOOGLE_API_KEY=your_api_key_here`

## Running the Game

To start the game, run:
```bash
python -m src.main
```

## Commands

- `look` or `l`: Look around the current room
- `map`: Show world map with your location and room connections
- `go <direction>` or `n/s/e/w/u/d`: Move in a direction
- `inventory` or `i`: Check your inventory
- `take <item>`: Pick up an item
- `take all`: Pick up all items in the room
- `examine <target>`: Examine an item, mob, or NPC (shows detailed description and stats if available)
- `drop <item>`: Drop an item
- `equip <item>` or `eq <item>`: Equip a weapon, armor, ring, or amulet
- `unequip <item>` or `uneq <item>`: Remove equipped item
- `use <item>`: Use a consumable item (like potions)
- `stats` or `st`: Show character stats
- `attack <mob>` or `k/a <mob>`: Attack a mob
- `flee` or `f`: Flee from combat
- `godkill` or `gk/god`: Instantly defeat target (cheat command)
- `talk <npc>`: Start a conversation with an NPC
- `ask <npc> about <topic>`: Ask an NPC about a specific topic
- `list`: View merchant's wares when talking to one
- `buy <item>`: Buy an item from a merchant
- `sell <item>`: Sell an item to a merchant
- `sacrifice <item>` or `sac <item>`: Sacrifice an item for 1 XP
- `quit`: Exit the game
- `help`: Show available commands

## Data Structure

The game uses JSON files for data storage:
- `data/characters.json`: Character data and progress
- `data/items.json`: Item definitions
- `data/mobs.json`: Monster definitions
- `data/npcs.json`: NPC definitions and dialogue trees
- `data/worlds/*.json`: World and room definitions

### NPC Data Format Example
```json
{
  "id": "merchant_001",
  "name": "Old Merchant",
  "dialogue": {
    "greeting": "Welcome, traveler!",
    "topics": {
      "wares": {
        "prompt": "What do you have for sale?",
        "response": "Let me show you my wares...",
        "leads_to": ["trade", "special_items"]
      }
    }
  },
  "merchant_data": {
    "inventory": {},
    "buy_multiplier": 0.5,
    "unlocked": false
  }
}
```

### Item Data Format Example
```json
{
  "id": "sword_001",
  "short_desc": "Steel Sword",
  "long_desc": "A well-crafted steel sword with a sharp edge.",
  "properties": {
    "type": "weapon",
    "damage": 7,
    "value": 100
  }
}
```

## License

MIT License - See LICENSE file for details 