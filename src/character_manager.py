from typing import Dict, List, Optional, Set
from .data_manager import DataManager

class CharacterManager:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.current_character: Optional[Dict] = None
        self.world_manager = None  # Will be set by main.py

    def set_world_manager(self, world_manager) -> None:
        """Set the world manager reference."""
        self.world_manager = world_manager

    def determine_world_from_room(self, room_id: str) -> str:
        """Determine which world a room belongs to."""
        if room_id.startswith("spirit_"):
            return "spirit_realm"
        return "default"

    def create_character(self, name: str) -> bool:
        """Create a new character."""
        if self.data_manager.get_character(name):
            print(f"Character '{name}' already exists.")
            return False

        character = {
            "name": name,
            "current_room": "forest_clearing_001",  # Starting room
            "inventory": [],
            "equipment": {
                "weapon": None,
                "armor": None,
                "ring": None,
                "amulet": None
            },
            "base_stats": {
                "level": 1,
                "max_hp": 100,
                "current_hp": 100,
                "attack": 10,
                "defense": 5,
                "xp": 0,
                "xp_to_next_level": 100,
                "weight_limit": 20.0
            },
            "stats": {
                "level": 1,
                "max_hp": 100,
                "current_hp": 100,
                "attack": 10,
                "defense": 5,
                "xp": 0,
                "xp_to_next_level": 100,
                "weight_limit": 20.0
            },
            "combat_state": {
                "in_combat": False,
                "target": None,
                "turns_in_combat": 0,
                "mob_state": None
            },
            "known_topics": {},
            "money": 100,
            "defeated_mobs": {},
            "world_state": {
                "removed_items": {}
            }
        }

        self.current_character = character
        self.data_manager.add_character(character)
        print(f"\nCharacter '{name}' created successfully!")
        return True

    def load_character(self, name: str) -> bool:
        """Load an existing character."""
        character = self.data_manager.get_character(name)
        if not character:
            print(f"Character '{name}' not found.")
            return False

        # Ensure character has required fields
        if "known_topics" not in character:
            character["known_topics"] = {}
        if "money" not in character:
            character["money"] = 100
        if "defeated_mobs" not in character:
            character["defeated_mobs"] = {}
        if "world_state" not in character:
            character["world_state"] = {"removed_items": {}}
            
        # Add weight limit if missing (20kg base + 2kg per level above 1)
        if "weight_limit" not in character["base_stats"]:
            character["base_stats"]["weight_limit"] = 20.0
        if "weight_limit" not in character["stats"]:
            level = character["stats"]["level"]
            character["stats"]["weight_limit"] = 20.0 + ((level - 1) * 2.0)
            self.data_manager.update_character(character)

        self.current_character = character

        # Sync world manager with character's location
        if self.world_manager:
            current_world = self.determine_world_from_room(character["current_room"])
            self.world_manager.change_world(current_world)

        print(f"Welcome back, {name}!")
        return True

    def save_character(self) -> None:
        """Save the current character's state."""
        if self.current_character:
            self.data_manager.update_character(self.current_character)

    def get_current_room(self) -> str:
        """Get the current room ID of the character."""
        if not self.current_character:
            raise RuntimeError("No character is currently loaded")
        return self.current_character["current_room"]

    def set_current_room(self, room_id: str) -> None:
        """Update the character's current room."""
        if not self.current_character:
            raise RuntimeError("No character is currently loaded")
        
        # Clear defeated mobs when changing rooms
        if room_id != self.current_character["current_room"]:
            self.current_character["defeated_mobs"] = {}
            
        self.current_character["current_room"] = room_id
        self.save_character()

    def add_to_inventory(self, item_id: str) -> bool:
        """Add an item to the character's inventory if weight limit allows."""
        if not self.current_character:
            raise RuntimeError("No character is currently loaded")
            
        # Check weight limit
        item = self.data_manager.get_item(item_id)
        if not item:
            return False
            
        item_weight = item.get("properties", {}).get("weight", 0)
        if not self.can_carry_weight(item_weight):
            return False
            
        self.current_character["inventory"].append(item_id)
        self.save_character()
        return True

    def remove_from_inventory(self, item_id: str) -> bool:
        """Remove an item from the character's inventory."""
        if not self.current_character:
            raise RuntimeError("No character is currently loaded")
            
        if item_id in self.current_character["inventory"]:
            self.current_character["inventory"].remove(item_id)
            self.save_character()
            return True
        return False

    def get_inventory(self) -> List[str]:
        """Get the character's inventory item IDs."""
        if not self.current_character:
            raise RuntimeError("No character is currently loaded")
        return self.current_character["inventory"]

    def has_item(self, item_id: str) -> bool:
        """Check if the character has a specific item."""
        if not self.current_character:
            raise RuntimeError("No character is currently loaded")
        return item_id in self.current_character["inventory"]

    def get_known_topics(self, npc_id: str) -> List[str]:
        """Get list of known dialogue topics for an NPC."""
        if not self.current_character:
            raise RuntimeError("No character is currently loaded")
        return self.current_character.get("known_topics", {}).get(npc_id, [])

    def add_known_topic(self, npc_id: str, topic_id: str) -> None:
        """Add a topic to the list of known topics for an NPC."""
        if not self.current_character:
            raise RuntimeError("No character is currently loaded")
        
        if "known_topics" not in self.current_character:
            self.current_character["known_topics"] = {}
        
        if npc_id not in self.current_character["known_topics"]:
            self.current_character["known_topics"][npc_id] = []
        
        if topic_id not in self.current_character["known_topics"][npc_id]:
            self.current_character["known_topics"][npc_id].append(topic_id)
            self.save_character()

    def get_money(self) -> int:
        """Get the character's current money."""
        if not self.current_character:
            raise RuntimeError("No character is currently loaded")
        return self.current_character.get("money", 0)

    def add_money(self, amount: int) -> None:
        """Add money to the character's purse."""
        if not self.current_character:
            raise RuntimeError("No character is currently loaded")
        self.current_character["money"] = self.current_character.get("money", 0) + amount
        self.save_character()

    def remove_money(self, amount: int) -> bool:
        """
        Remove money from the character's purse.
        Returns False if they don't have enough.
        """
        if not self.current_character:
            raise RuntimeError("No character is currently loaded")
        
        current_money = self.current_character.get("money", 0)
        if current_money < amount:
            return False
            
        self.current_character["money"] = current_money - amount
        self.save_character()
        return True

    def get_character(self, name: str) -> Optional[Dict]:
        """Get character data by name."""
        if self.current_character and self.current_character["name"].lower() == name.lower():
            return self.current_character
        return self.data_manager.get_character(name) 

    def add_defeated_mob(self, mob_id: str) -> None:
        """Add a mob to the defeated list for current room."""
        if not self.current_character:
            raise RuntimeError("No character is currently loaded")
        
        current_room = self.current_character["current_room"]
        if current_room not in self.current_character["defeated_mobs"]:
            self.current_character["defeated_mobs"][current_room] = []
            
        self.current_character["defeated_mobs"][current_room].append(mob_id)
        self.save_character()

    def is_mob_defeated(self, mob_id: str) -> bool:
        """Check if a mob has been defeated in current room."""
        if not self.current_character:
            raise RuntimeError("No character is currently loaded")
            
        current_room = self.current_character["current_room"]
        return mob_id in self.current_character["defeated_mobs"].get(current_room, []) 

    def get_fancy_stats(self) -> str:
        """Generate a fancy ASCII-art stats display."""
        if not self.current_character:
            raise RuntimeError("No character is currently loaded")
        
        char = self.current_character
        stats = char["stats"]
        
        # Calculate derived stats
        hp_percent = (stats["current_hp"] / stats["max_hp"]) * 100
        xp_percent = (stats["xp"] / stats["xp_to_next_level"]) * 100
        
        # Calculate total weight carried
        total_weight = 0.0
        inventory_weights = {}  # Store weights for display in inventory
        
        # Add weights from inventory
        for item_id in char["inventory"]:
            item = self.data_manager.get_item(item_id)
            if item and "weight" in item.get("properties", {}):
                weight = item["properties"]["weight"]
                total_weight += weight
                inventory_weights[item["short_desc"]] = weight
        
        # Add weights from equipped items
        for slot, equipped_id in char["equipment"].items():
            if equipped_id:
                item = self.data_manager.get_item(equipped_id)
                if item and "weight" in item.get("properties", {}):
                    total_weight += item["properties"]["weight"]
        
        # Generate health and XP bars
        hp_bar = self._generate_progress_bar(hp_percent, 20)
        xp_bar = self._generate_progress_bar(xp_percent, 20)
        
        # Get equipment info with proper handling of None values
        equipment = char["equipment"]
        equipped_items = {}
        for slot in ["weapon", "armor", "ring", "amulet"]:
            item_id = equipment.get(slot)
            if item_id:
                item = self.data_manager.get_item(item_id)
                if item:
                    weight_str = f" ({item['properties'].get('weight', 0):.1f}kg)"
                    equipped_items[slot.title()] = (item["short_desc"] + weight_str)[:20]
                else:
                    equipped_items[slot.title()] = "None"
            else:
                equipped_items[slot.title()] = "None"
        
        # Format the stats display with proper spacing
        stats_display = f"""
╔══════════════════════════════════════════════════════════╗
║                     {char['name']:<37}║
╠══════════════════════════════════════════════════════════╣
║  Level: {stats['level']:<5}                Gold: {char.get('money', 0):<14}║
║  Weight Carried: {total_weight:.1f}kg                                  ║
║                                                          ║
║  HP: {stats['current_hp']}/{stats['max_hp']:<48}║
║  [{hp_bar}] {hp_percent:>3.0f}%                        ║
║                                                          ║
║  XP: {stats['xp']}/{stats['xp_to_next_level']:<48}║
║  [{xp_bar}] {xp_percent:>3.0f}%                        ║
╠══════════════════════════════════════════════════════════╣
║  COMBAT STATS                   EQUIPMENT                ║
║  ───────────────               ──────────               ║
║  Attack:  {stats['attack']:<6}             Weapon:  {equipped_items['Weapon']:<14}║
║  Defense: {stats['defense']:<6}             Armor:   {equipped_items['Armor']:<14}║
║                                Ring:    {equipped_items['Ring']:<14}║
║                                Amulet:  {equipped_items['Amulet']:<14}║"""

        # Add inventory section with weights
        sections = [stats_display]
        
        # Group items and count quantities with weights
        item_counts = {}
        item_details = {}  # Store full item details for display
        
        for item_id in char["inventory"]:
            item = self.data_manager.get_item(item_id)
            if not item:
                continue
            
            # Use short_desc as the display key
            display_name = item["short_desc"]
            item_counts[display_name] = item_counts.get(display_name, 0) + 1
            item_details[display_name] = item

        # Categorize items
        categories = {
            "WEAPONS": [],
            "ARMOR": [],
            "CONSUMABLES": [],
            "QUEST ITEMS": [],
            "VALUABLES": [],
            "MISCELLANEOUS": []
        }

        for display_name, item in item_details.items():
            # Skip if item is equipped
            is_equipped = False
            for equipped_id in char["equipment"].values():
                if equipped_id and self.data_manager.get_item(equipped_id)["short_desc"] == display_name:
                    is_equipped = True
                    break
            if is_equipped:
                continue

            count = item_counts[display_name]
            weight = item["properties"].get("weight", 0)
            count_str = f" (x{count})" if count > 1 else ""
            weight_str = f" [{weight:.1f}kg]"
            item_line = f"  {display_name}{count_str}{weight_str}"

            props = item.get("properties", {})
            item_type = props.get("type", "misc")

            if item_type == "weapon":
                categories["WEAPONS"].append(item_line)
            elif item_type == "armor":
                categories["ARMOR"].append(item_line)
            elif item_type == "consumable":
                categories["CONSUMABLES"].append(item_line)
            elif item_type == "quest":
                categories["QUEST ITEMS"].append(item_line)
            elif item_type == "valuable":
                categories["VALUABLES"].append(item_line)
            else:
                categories["MISCELLANEOUS"].append(item_line)

        # Add inventory header
        sections.append("╠══════════════════════════════════════════════════════════╣")
        sections.append("║                     INVENTORY                            ║")
        sections.append("╠══════════════════════════════════════════════════════════╣")

        # Add categories to display
        for category, items in categories.items():
            if items:
                sections.append(f"║  {category:<52}║")
                sections.append("║  ──────────────                                        ║")
                for item in sorted(items):
                    sections.append(f"║  {item:<52}║")
                sections.append("║                                                          ║")

        # Add footer
        sections.append("╚══════════════════════════════════════════════════════════╝")

        return "\n".join(sections)

    def _generate_progress_bar(self, percentage: float, length: int = 20) -> str:
        """Generate a progress bar with custom characters."""
        fill_length = int((percentage / 100) * length)
        return "█" * fill_length + "░" * (length - fill_length)

    def calculate_total_weight(self) -> float:
        """Calculate total weight of all carried items (inventory + equipped)."""
        if not self.current_character:
            raise RuntimeError("No character is currently loaded")

        total_weight = 0.0
        
        # Add weights from inventory
        for item_id in self.current_character["inventory"]:
            item = self.data_manager.get_item(item_id)
            if item and "weight" in item.get("properties", {}):
                total_weight += item["properties"]["weight"]
        
        # Add weights from equipped items
        for equipped_id in self.current_character["equipment"].values():
            if equipped_id:
                item = self.data_manager.get_item(equipped_id)
                if item and "weight" in item.get("properties", {}):
                    total_weight += item["properties"]["weight"]
                    
        return total_weight

    def can_carry_weight(self, additional_weight: float) -> bool:
        """Check if character can carry additional weight."""
        if not self.current_character:
            raise RuntimeError("No character is currently loaded")
            
        current_weight = self.calculate_total_weight()
        weight_limit = self.current_character["stats"]["weight_limit"]
        
        return (current_weight + additional_weight) <= weight_limit

    def level_up(self, character: Dict) -> None:
        """Handle character level up with weight limit increase."""
        character["stats"]["level"] += 1
        character["stats"]["max_hp"] += 10
        character["stats"]["current_hp"] = character["stats"]["max_hp"]
        character["stats"]["attack"] += 2
        character["stats"]["defense"] += 1
        character["stats"]["weight_limit"] += 2.0  # Increase weight limit by 2kg per level
        character["stats"]["xp"] -= character["stats"]["xp_to_next_level"]
        character["stats"]["xp_to_next_level"] = int(character["stats"]["xp_to_next_level"] * 1.5)

    def get_current_room_items(self) -> List[str]:
        """Get list of items in the current room."""
        if not self.current_character or not self.world_manager:
            return []
        return self.world_manager.get_room_items(self.get_current_room(), self.current_character)

    def pick_up_item(self, item_id: str) -> bool:
        """Pick up an item from the current room."""
        if not self.current_character or not self.world_manager:
            return False
            
        current_room = self.get_current_room()
        if self.world_manager.remove_item_from_room(current_room, item_id, self.current_character):
            return self.add_to_inventory(item_id)
        return False

    def drop_item(self, item_id: str) -> bool:
        """Drop an item in the current room."""
        if not self.current_character or not self.world_manager:
            return False
            
        if self.remove_from_inventory(item_id):
            current_room = self.get_current_room()
            return self.world_manager.add_item_to_room(current_room, item_id)
        return False