from typing import Dict, List, Optional, Set, Tuple, Any
from .data_manager import DataManager
import os
import json
import time
from datetime import datetime

class WorldManager:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.worlds_dir = os.path.join("data", "worlds")
        self.loaded_worlds = {}  # Cache for loaded world files
        self.current_world = "default"  # Track current active world
        self.original_items = {}  # Track original item locations
        self.last_load_time = {}
        self.ai_helper = None  # Will be set after initialization
        self.load_world(self.current_world)

    def load_world(self, world_name: str) -> Dict:
        """Load a world file."""
        if world_name in self.loaded_worlds:
            return self.loaded_worlds[world_name]

        try:
            world_path = os.path.join(self.worlds_dir, f"{world_name}.json")
            with open(world_path, 'r') as f:
                world_data = json.load(f)
                self.loaded_worlds[world_name] = world_data
                
                # Track original item locations
                for room in world_data.get("rooms", []):
                    if "items" in room:
                        for item_id in room["items"]:
                            self.original_items[item_id] = {
                                "world": world_name,
                                "room": room["id"]
                            }
                
                return world_data
        except FileNotFoundError:
            print(f"Warning: World '{world_name}' not found. Creating empty world.")
            empty_world = {"rooms": []}
            self.loaded_worlds[world_name] = empty_world
            return empty_world
        except json.JSONDecodeError:
            print(f"Error: {world_name}.json is not valid JSON.")
            return {"rooms": []}

    def _validate_world(self) -> None:
        """Validate world data for broken links and invalid references."""
        room_ids = {room["id"] for room in self.current_world.get("rooms", [])}
        
        for room in self.current_world.get("rooms", []):
            for direction, target_room_id in room.get("exits", {}).items():
                if target_room_id not in room_ids:
                    print(f"Warning: Room {room['id']} has invalid exit {direction} to non-existent room {target_room_id}")

    def set_ai_helper(self, ai_helper):
        """Set the AI helper for enhanced descriptions."""
        self.ai_helper = ai_helper

    def get_time_of_day(self) -> str:
        """Get the current time of day period."""
        hour = datetime.now().hour
        if 5 <= hour < 8:
            return "dawn"
        elif 8 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 20:
            return "evening"
        elif 20 <= hour < 22:
            return "dusk"
        else:
            return "night"

    async def get_enhanced_description(self, base_description: str, room: Dict) -> str:
        """Get an AI-enhanced room description based on time of day."""
        if not self.ai_helper:
            return base_description
            
        try:
            time_of_day = self.get_time_of_day()
            context = {
                "time_of_day": time_of_day,
                "room_type": room.get("type", "generic"),
                "world_name": self.current_world
            }
            
            prompt = (
                "You are a descriptive writer tasked with enhancing a room description. "
                "Rules:\n"
                "1. NEVER add welcome messages or greetings\n"
                "2. ONLY describe the room and its atmosphere\n"
                "3. Keep all key information from the original\n"
                "4. Add time-specific atmospheric details\n"
                "5. Return ONLY the enhanced description\n\n"
                f"Time of day: {time_of_day}\n"
                f"Original description: {base_description}\n\n"
                "Enhance the description with sensory details appropriate for the time of day, "
                "including lighting, shadows, sounds, and atmosphere. "
                "Focus on how the time of day affects the scene."
            )
            
            enhanced = await self.ai_helper.generate_response(prompt, context)
            return enhanced if enhanced != prompt else base_description
            
        except Exception:
            return base_description

    async def get_room_description(self, room_id: str, show_long: bool = True) -> str:
        """Get the description of a room."""
        room = self.get_room(room_id)
        if not room:
            return "Error: Room not found"

        # Get the basic description
        base_desc = room["long_desc"] if show_long else room["short_desc"]
        
        # Enhance the description with AI if available
        description = base_desc
        if show_long and self.ai_helper:
            description = await self.get_enhanced_description(base_desc, room)
        
        # Add exits information
        exits = room.get("exits", {})
        if exits:
            normal_exits = []
            special_exits = []
            for direction, exit_data in exits.items():
                if isinstance(exit_data, dict) and exit_data.get("type") == "world_transition":
                    special_exits.append(f"{direction} ({exit_data['description']})")
                else:
                    normal_exits.append(direction)
            
            if normal_exits:
                description += f"\nExits: {', '.join(normal_exits)}"
            if special_exits:
                description += f"\nSpecial exits: {', '.join(special_exits)}"
        else:
            description += "\nThere are no obvious exits."

        # Add items information
        items = room.get("items", [])
        if items:
            item_descriptions = []
            for item_id in items:
                item = self.data_manager.get_item(item_id)
                if item:
                    item_descriptions.append(item["short_desc"])
            if item_descriptions:
                description += "\nYou see: " + ", ".join(item_descriptions)

        # Add NPCs information
        npcs = room.get("npcs", [])
        if npcs:
            npc_descriptions = []
            for npc_id in npcs:
                npc = self.data_manager.get_npc(npc_id)
                if npc:
                    npc_descriptions.append(f"{npc['name']} ({npc['short_desc']})")
            if npc_descriptions:
                description += "\nPresent here: " + ", ".join(npc_descriptions)

        # Add mobs information
        mobs_data = self.data_manager.load_json("mobs.json")
        present_mobs = []
        for mob in mobs_data.get("mobs", []):
            if room_id in mob.get("spawn_areas", []):
                # Skip if mob has been defeated in this room
                if hasattr(self.data_manager, 'character_manager') and \
                   self.data_manager.character_manager and \
                   self.data_manager.character_manager.is_mob_defeated(mob["id"]):
                    continue
                present_mobs.append(mob["short_desc"])
        if present_mobs:
            description += "\nEnemies here: " + ", ".join(present_mobs)

        return description

    def get_room(self, room_id: str, character: Optional[Dict] = None) -> Optional[Dict]:
        """Get room data by ID and check for item respawns."""
        world = self.loaded_worlds.get(self.current_world)
        if not world:
            return None

        for room in world.get("rooms", []):
            if room["id"] == room_id:
                # If character is provided, check their specific world state for respawns
                if character:
                    self.check_item_respawn(room_id, character)
                return room
        return None

    def get_exit_room_id(self, current_room_id: str, direction: str) -> Optional[Dict]:
        """Get the room ID for a given exit direction. Returns dict for world transitions."""
        room = self.get_room(current_room_id)
        if not room:
            return None

        exit_data = room.get("exits", {}).get(direction.lower())
        if not exit_data:
            return None

        # Handle world transition exits
        if isinstance(exit_data, dict) and exit_data.get("type") == "world_transition":
            return {
                "type": "world_transition",
                "target_world": exit_data["target_world"],
                "target_room": exit_data["target_room"],
                "description": exit_data.get("description", "A portal to another realm."),
                "requirements": exit_data.get("requirements", {})
            }

        # Regular room exit
        return {"type": "room", "target": exit_data}

    def add_item_to_room(self, room_id: str, item_id: str) -> bool:
        """Add an item to a room."""
        room = self.get_room(room_id)
        if not room:
            return False
        if "items" not in room:
            room["items"] = []
        room["items"].append(item_id)
        return True

    def remove_item_from_room(self, room_id: str, item_id: str, character: Dict) -> bool:
        """Remove an item from a room and track in character's world state."""
        room = self.get_room(room_id)
        if not room or "items" not in room:
            return False
            
        if item_id in room["items"]:
            room["items"].remove(item_id)
            
            # Initialize world_state if it doesn't exist
            if "world_state" not in character:
                character["world_state"] = {"removed_items": {}}
                
            # Track removal time for respawnable items in character's state
            item = self.data_manager.get_item(item_id)
            if item and item.get("properties", {}).get("respawnable", False):
                character["world_state"]["removed_items"][item_id] = {
                    "room": room_id,
                    "time": time.time(),
                    "world": self.current_world
                }
            return True
        return False

    def get_room_items(self, room_id: str, character: Optional[Dict] = None) -> List[str]:
        """Get list of item IDs in a room, considering character's world state."""
        room = self.get_room(room_id, character)
        if not room:
            return []
        return room.get("items", [])

    def get_room_npcs(self, room_id: str) -> List[str]:
        """Get list of NPC IDs in a room."""
        room = self.get_room(room_id)
        if not room:
            return []
        return room.get("npcs", [])

    def get_npc_in_room(self, room_id: str, search_name: str) -> Optional[Dict]:
        """Find an NPC in the room by name."""
        room = self.get_room(room_id)
        if not room:
            return None

        # Remove common articles and convert to lowercase
        search_terms = search_name.lower().replace("a ", "").replace("an ", "").replace("the ", "").split()
        
        for npc_id in room.get("npcs", []):
            npc = self.data_manager.get_npc(npc_id)
            if not npc:
                continue
                
            # Check against both name and short description
            npc_name = npc["name"].lower()
            npc_desc = npc["short_desc"].lower()
            
            # Match if all search terms are found in either name or description
            if (all(term in npc_name for term in search_terms) or 
                all(term in npc_desc for term in search_terms)):
                return npc
                
        return None

    def check_world_transition_requirements(self, character: Dict, requirements: Dict) -> Tuple[bool, str]:
        """Check if a character meets the requirements for a world transition."""
        if not requirements:
            return True, ""

        # Check level requirement
        if "level" in requirements:
            if character["stats"]["level"] < requirements["level"]:
                return False, f"You need to be level {requirements['level']} to use this portal."

        # Check item requirement
        if "item" in requirements:
            if requirements["item"] not in character["inventory"]:
                item = self.data_manager.get_item(requirements["item"])
                item_name = item["short_desc"] if item else requirements["item"]
                return False, f"You need {item_name} to use this portal."

        return True, ""

    def change_world(self, new_world: str) -> bool:
        """Change the current active world."""
        if new_world not in self.loaded_worlds:
            if not self.load_world(new_world):
                return False
        self.current_world = new_world
        return True

    def check_item_respawn(self, room_id: str, character: Dict) -> None:
        """Check and handle item respawning for a room based on character's world state."""
        if "world_state" not in character:
            character["world_state"] = {"removed_items": {}}
            
        current_time = time.time()
        items_to_respawn = []
        
        # Check all removed items in character's state that belong to this room
        for item_id, removal_data in list(character["world_state"]["removed_items"].items()):
            if removal_data["room"] != room_id or removal_data["world"] != self.current_world:
                continue
                
            item = self.data_manager.get_item(item_id)
            if not item:
                continue
                
            # Check if item is respawnable
            if not item.get("properties", {}).get("respawnable", False):
                continue
                
            # Check if enough time has passed
            respawn_time = item.get("properties", {}).get("respawn_time", 1800)  # Default 30 minutes
            if current_time - removal_data["time"] >= respawn_time:
                items_to_respawn.append(item_id)
                del character["world_state"]["removed_items"][item_id]
        
        # Add respawned items back to the room
        if items_to_respawn:
            room = self.get_room(room_id)
            if room:
                if "items" not in room:
                    room["items"] = []
                room["items"].extend(items_to_respawn)