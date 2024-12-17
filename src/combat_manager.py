from typing import Dict, Optional, List
from .data_manager import DataManager
from .world_manager import WorldManager
import random

class CombatManager:
    def __init__(self, data_manager: DataManager, world_manager: WorldManager):
        self.data_manager = data_manager
        self.world_manager = world_manager
        self.character_manager = None  # Will be set by main.py
        
    def set_character_manager(self, character_manager) -> None:
        """Set the character manager reference."""
        self.character_manager = character_manager
        
    def load_mob(self, mob_id):
        """Load a mob from the mobs.json file."""
        mobs_data = self.data_manager.load_json("mobs.json")
        for mob in mobs_data["mobs"]:
            if mob["id"] == mob_id:
                # Create a deep copy of the mob to prevent shared state
                mob_copy = {
                    "id": mob["id"],
                    "name": mob["name"],
                    "short_desc": mob["short_desc"],
                    "long_desc": mob["long_desc"],
                    "level": mob["level"],
                    "stats": {
                        "max_hp": mob["stats"]["max_hp"],
                        "current_hp": mob["stats"]["max_hp"],  # Reset HP to max
                        "attack": mob["stats"]["attack"],
                        "defense": mob["stats"]["defense"],
                        "xp_value": mob["stats"]["xp_value"]
                    },
                    "loot_table": dict(mob["loot_table"]),
                    "spawn_areas": list(mob["spawn_areas"])
                }
                return mob_copy
        return None
        
    def calculate_damage(self, attacker_stats, defender_stats):
        """Calculate damage based on attack and defense stats."""
        base_damage = attacker_stats["attack"] - defender_stats["defense"]
        if base_damage < 1:
            base_damage = 1
        # Add some randomness
        damage = random.randint(base_damage - 2, base_damage + 2)
        return max(1, damage)  # Minimum 1 damage
        
    def process_combat_turn(self, character_name, mob_id):
        """Process one turn of combat between character and mob."""
        character = self.data_manager.get_character(character_name)
        if not character:
            return "Character not found."
            
        # Get mob state from combat state
        mob = character["combat_state"].get("mob_state")
        if not mob or mob["id"] != mob_id:
            mob = self.load_mob(mob_id)
            if not mob:
                return "Mob not found."
            character["combat_state"]["mob_state"] = mob
            
        # Character attacks mob
        damage_to_mob = self.calculate_damage(character["stats"], mob["stats"])
        mob["stats"]["current_hp"] -= damage_to_mob
        
        combat_log = [f"You hit {mob['name']} for {damage_to_mob} damage!"]
        
        # Show health bars
        char_health_percent = (character["stats"]["current_hp"] / character["stats"]["max_hp"]) * 100
        mob_health_percent = (mob["stats"]["current_hp"] / mob["stats"]["max_hp"]) * 100
        
        combat_log.append(f"\nYour health: [{self.generate_health_bar(char_health_percent)}] {character['stats']['current_hp']}/{character['stats']['max_hp']}")
        combat_log.append(f"{mob['name']}'s health: [{self.generate_health_bar(mob_health_percent)}] {mob['stats']['current_hp']}/{mob['stats']['max_hp']}\n")
        
        # Check if mob is defeated
        if mob["stats"]["current_hp"] <= 0:
            combat_log.append(f"You have defeated {mob['name']}!")
            # Award XP
            character["stats"]["xp"] += mob["stats"]["xp_value"]
            combat_log.append(f"You gained {mob['stats']['xp_value']} experience!")
            
            # Check for level up
            if character["stats"]["xp"] >= character["stats"]["xp_to_next_level"]:
                old_level = character["stats"]["level"]
                self.level_up(character)
                combat_log.append(f"\nLevel up! You are now level {character['stats']['level']}!")
                combat_log.append("Your stats have increased:")
                combat_log.append("  +10 Max HP")
                combat_log.append("  +2 Attack")
                combat_log.append("  +1 Defense")
                combat_log.append("You are fully healed!")
            
            # Roll for loot
            loot = self.roll_loot(mob["loot_table"])
            if loot:
                character["inventory"].extend(loot)
                combat_log.append(f"You found: {', '.join(loot)}")
            
            # Mark mob as defeated in current room
            self.character_manager.add_defeated_mob(mob_id)
            
            character["combat_state"]["in_combat"] = False
            character["combat_state"]["target"] = None
            character["combat_state"]["turns_in_combat"] = 0
            character["combat_state"]["mob_state"] = None  # Clear mob state
        else:
            # Mob attacks character
            damage_to_char = self.calculate_damage(mob["stats"], character["stats"])
            character["stats"]["current_hp"] -= damage_to_char
            combat_log.append(f"{mob['name']} hits you for {damage_to_char} damage!")
            
            # Check if character is defeated
            if character["stats"]["current_hp"] <= 0:
                # Death penalties
                character["stats"]["current_hp"] = character["stats"]["max_hp"] // 2  # Respawn with half HP
                character["current_room"] = "forest_clearing_001"  # Respawn at starting area
                character["combat_state"]["in_combat"] = False
                character["combat_state"]["target"] = None
                character["combat_state"]["turns_in_combat"] = 0
                character["combat_state"]["mob_state"] = None  # Clear mob state
                
                # XP penalty - lose 10% of XP to next level
                xp_penalty = character["stats"]["xp_to_next_level"] // 10
                character["stats"]["xp"] = max(0, character["stats"]["xp"] - xp_penalty)
                
                # Money penalty - lose 10% of money
                money_penalty = character["money"] // 10
                character["money"] = max(0, character["money"] - money_penalty)
                
                combat_log.append("\nYou have been defeated!")
                combat_log.append(f"You lose {xp_penalty} XP and {money_penalty} coins.")
                combat_log.append("You wake up at the forest clearing with half health...")
            else:
                character["combat_state"]["turns_in_combat"] += 1
        
        # Save character state (which includes mob state)
        self.data_manager.update_character(character)
        return "\n".join(combat_log)
    
    def generate_health_bar(self, percentage, length=20):
        """Generate a text-based health bar."""
        fill_length = int((percentage / 100) * length)
        return "=" * fill_length + " " * (length - fill_length)
    
    def level_up(self, character):
        """Handle character level up."""
        character["stats"]["level"] += 1
        character["stats"]["max_hp"] += 10
        character["stats"]["current_hp"] = character["stats"]["max_hp"]
        character["stats"]["attack"] += 2
        character["stats"]["defense"] += 1
        character["stats"]["xp"] -= character["stats"]["xp_to_next_level"]
        character["stats"]["xp_to_next_level"] = int(character["stats"]["xp_to_next_level"] * 1.5)
    
    def roll_loot(self, loot_table):
        """Roll for loot drops based on loot table probabilities."""
        loot = []
        for item, probability in loot_table.items():
            if random.random() < probability:
                loot.append(item)
        return loot
    
    def flee(self, character_name: str) -> str:
        """Handle fleeing from combat."""
        character = self.data_manager.get_character(character_name)
        if not character:
            return "Character not found."
            
        # End combat
        character["combat_state"]["in_combat"] = False
        character["combat_state"]["target"] = None
        character["combat_state"]["turns_in_combat"] = 0
        character["combat_state"]["mob_state"] = None  # Clear mob state
        self.data_manager.update_character(character)
        
        return "You flee from combat!"

    def _handle_mob_defeat(self, character: Dict, mob: Dict) -> List[str]:
        """Handle mob defeat, including XP gain and loot drops."""
        response = []
        
        # Award XP
        xp_gain = mob["stats"]["xp_value"]
        character["stats"]["xp"] += xp_gain
        response.append(f"You gain {xp_gain} XP!")
        
        # Check for level up
        while character["stats"]["xp"] >= character["stats"]["xp_to_next_level"]:
            self._handle_level_up(character)
            response.append(f"Level up! You are now level {character['stats']['level']}!")
        
        # Handle loot drops
        loot = self._generate_loot(mob)
        if loot:
            # Add items to the room using world_manager
            current_room = character["current_room"]
            for item_id in loot:
                self.world_manager.add_item_to_room(current_room, item_id)
            response.append(f"\nLoot dropped: {', '.join(loot)}")
        
        # Mark mob as defeated in this room
        if hasattr(self.data_manager, 'character_manager'):
            self.data_manager.character_manager.add_defeated_mob(mob["id"])
        
        return response

    def instant_kill(self, character_name: str, mob_id: str) -> str:
        """Instantly defeat the current mob (cheat/debug command)."""
        character = self.data_manager.get_character(character_name)
        if not character:
            return "Character not found."
            
        if not character["combat_state"]["in_combat"]:
            return "You are not in combat."
            
        if character["combat_state"]["target"] != mob_id:
            return "That's not your current target."
            
        # Get mob data
        mobs_data = self.data_manager.load_json("mobs.json")
        mob = None
        for m in mobs_data["mobs"]:
            if m["id"] == mob_id:
                mob = m
                break
                
        if not mob:
            return "Invalid mob ID."
            
        response = ["You instantly defeat the enemy!"]
        
        # Handle loot and XP
        response.extend(self._handle_mob_defeat(character, mob))
        
        # End combat
        character["combat_state"]["in_combat"] = False
        character["combat_state"]["target"] = None
        character["combat_state"]["turns_in_combat"] = 0
        character["combat_state"]["mob_state"] = None
        
        # Save character data
        self.data_manager.update_character(character)
        
        return "\n".join(response)
    
    def start_combat(self, character_name, mob_id):
        """Initialize combat with a mob."""
        character = self.data_manager.get_character(character_name)
        if not character:
            return "Character not found."
            
        if character["combat_state"]["in_combat"]:
            return "You are already in combat!"
            
        mob = self.load_mob(mob_id)
        if not mob:
            return "Mob not found."
        
        character["combat_state"]["in_combat"] = True
        character["combat_state"]["target"] = mob_id
        character["combat_state"]["turns_in_combat"] = 0
        character["combat_state"]["mob_state"] = mob  # Store mob state
        
        self.data_manager.update_character(character)
        return f"You engage in combat with {mob['name']}!"