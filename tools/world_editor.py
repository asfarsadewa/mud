import json
import os
from typing import Dict, List, Optional, Set

class WorldEditor:
    def __init__(self, data_dir: str = "data/worlds"):
        self.data_dir = data_dir
        self.current_world: Optional[str] = None
        self.world_data: Dict = {}
        
        # Create worlds directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)

    def list_worlds(self) -> List[str]:
        """List all available world files."""
        worlds = []
        for file in os.listdir(self.data_dir):
            if file.endswith('.json'):
                worlds.append(file[:-5])  # Remove .json extension
        return worlds

    def load_world(self, world_name: str) -> bool:
        """Load a world file."""
        file_path = os.path.join(self.data_dir, f"{world_name}.json")
        try:
            with open(file_path, 'r') as f:
                self.world_data = json.load(f)
                self.current_world = world_name
                return True
        except FileNotFoundError:
            if input(f"World '{world_name}' doesn't exist. Create it? (y/n): ").strip().lower() == 'y':
                self.world_data = {"rooms": []}
                self.current_world = world_name
                self.save_world()
                return True
            return False
        except json.JSONDecodeError:
            print(f"Error: {world_name}.json is not valid JSON.")
            return False

    def save_world(self) -> None:
        """Save the current world to file."""
        if not self.current_world:
            return
        
        file_path = os.path.join(self.data_dir, f"{self.current_world}.json")
        with open(file_path, 'w') as f:
            json.dump(self.world_data, f, indent=2)

    def validate_world(self) -> List[str]:
        """Validate the current world for errors."""
        if not self.current_world:
            return ["No world is currently loaded"]

        errors = []
        room_ids = {room["id"] for room in self.world_data.get("rooms", [])}

        # Check for duplicate room IDs
        seen_ids = set()
        for room in self.world_data.get("rooms", []):
            if room["id"] in seen_ids:
                errors.append(f"Duplicate room ID: {room['id']}")
            seen_ids.add(room["id"])

        # Check for invalid exits
        for room in self.world_data.get("rooms", []):
            for direction, target_id in room.get("exits", {}).items():
                if target_id not in room_ids:
                    errors.append(f"Room {room['id']} has invalid exit {direction} to non-existent room {target_id}")

        return errors

    def list_rooms(self) -> None:
        """List all rooms in the current world."""
        if not self.current_world:
            print("No world is currently loaded!")
            return

        print(f"\nRooms in world '{self.current_world}':")
        print("=" * 40)
        for room in self.world_data.get("rooms", []):
            print(f"\nID: {room['id']}")
            print(f"Short Description: {room['short_desc']}")
            exits = ", ".join(room.get("exits", {}).keys())
            print(f"Exits: {exits or 'none'}")

    def get_room(self, room_id: str) -> Optional[Dict]:
        """Get room by ID."""
        for room in self.world_data.get("rooms", []):
            if room["id"] == room_id:
                return room
        return None

    def create_room(self) -> None:
        """Create a new room interactively."""
        if not self.current_world:
            print("No world is currently loaded!")
            return

        print("\nCreate New Room")
        print("=" * 40)

        # Get basic room information
        room_id = input("Enter room ID (e.g., cave_001): ").strip()
        if self.get_room(room_id):
            print("Error: Room ID already exists!")
            return

        short_desc = input("Enter short description: ").strip()
        long_desc = input("Enter long description: ").strip()

        # Get exits
        exits = {}
        print("\nAdd exits (leave blank to finish)")
        directions = ["north", "south", "east", "west", "up", "down"]
        for direction in directions:
            target = input(f"Room ID for {direction} exit (or press Enter to skip): ").strip()
            if target:
                exits[direction] = target

        # Get items and NPCs
        items = []
        print("\nAdd items (leave blank to finish)")
        while True:
            item_id = input("Enter item ID: ").strip()
            if not item_id:
                break
            items.append(item_id)

        npcs = []
        print("\nAdd NPCs (leave blank to finish)")
        while True:
            npc_id = input("Enter NPC ID: ").strip()
            if not npc_id:
                break
            npcs.append(npc_id)

        # Create the room
        new_room = {
            "id": room_id,
            "short_desc": short_desc,
            "long_desc": long_desc,
            "exits": exits
        }
        if items:
            new_room["items"] = items
        if npcs:
            new_room["npcs"] = npcs

        self.world_data["rooms"].append(new_room)
        self.save_world()
        print(f"\nRoom '{room_id}' created successfully!")

    def edit_room(self) -> None:
        """Edit an existing room."""
        if not self.current_world:
            print("No world is currently loaded!")
            return

        self.list_rooms()
        room_id = input("\nEnter ID of room to edit: ").strip()
        
        room = self.get_room(room_id)
        if not room:
            print("Error: Room not found!")
            return

        print("\nEdit Room")
        print("=" * 40)
        print("Press Enter to keep current value")

        # Edit basic properties
        new_short = input(f"Short description [{room['short_desc']}]: ").strip()
        if new_short:
            room['short_desc'] = new_short

        new_long = input(f"Long description [{room['long_desc']}]: ").strip()
        if new_long:
            room['long_desc'] = new_long

        # Edit exits
        if input("\nEdit exits? (y/n): ").strip().lower() == 'y':
            room['exits'] = {}
            print("\nAdd exits (leave blank to skip)")
            for direction in ["north", "south", "east", "west", "up", "down"]:
                target = input(f"Room ID for {direction} exit: ").strip()
                if target:
                    room['exits'][direction] = target

        # Edit items
        if input("\nEdit items? (y/n): ").strip().lower() == 'y':
            room['items'] = []
            print("\nAdd items (leave blank to finish)")
            while True:
                item_id = input("Enter item ID: ").strip()
                if not item_id:
                    break
                room['items'].append(item_id)

        # Edit NPCs
        if input("\nEdit NPCs? (y/n): ").strip().lower() == 'y':
            room['npcs'] = []
            print("\nAdd NPCs (leave blank to finish)")
            while True:
                npc_id = input("Enter NPC ID: ").strip()
                if not npc_id:
                    break
                room['npcs'].append(npc_id)

        self.save_world()
        print(f"\nRoom '{room_id}' updated successfully!")

    def delete_room(self) -> None:
        """Delete an existing room."""
        if not self.current_world:
            print("No world is currently loaded!")
            return

        self.list_rooms()
        room_id = input("\nEnter ID of room to delete: ").strip()
        
        for i, room in enumerate(self.world_data.get("rooms", [])):
            if room["id"] == room_id:
                # Check if any other rooms have exits to this room
                has_references = False
                for other_room in self.world_data.get("rooms", []):
                    if room_id in other_room.get("exits", {}).values():
                        has_references = True
                        print(f"Warning: Room {other_room['id']} has an exit to this room!")

                if has_references:
                    if input("Delete anyway? This will create invalid exits! (y/n): ").strip().lower() != 'y':
                        return

                confirm = input(f"Are you sure you want to delete room '{room_id}'? (y/n): ").strip().lower()
                if confirm == 'y':
                    self.world_data["rooms"].pop(i)
                    self.save_world()
                    print(f"\nRoom '{room_id}' deleted successfully!")
                return
        
        print("Error: Room not found!")

    def visualize_world(self) -> None:
        """Display a simple ASCII visualization of the world."""
        if not self.current_world:
            print("No world is currently loaded!")
            return

        print(f"\nWorld Map: {self.current_world}")
        print("=" * 40)
        print("Room connections (→ ← ↑ ↓):")
        
        for room in self.world_data.get("rooms", []):
            print(f"\n{room['id']}:")
            for direction, target in room.get("exits", {}).items():
                symbol = {
                    "north": "↑",
                    "south": "↓",
                    "east": "→",
                    "west": "←",
                    "up": "⇑",
                    "down": "⇓"
                }.get(direction, "-")
                print(f"  {symbol} {target}")

def main():
    editor = WorldEditor()
    
    while True:
        print("\nWorld Editor")
        print("=" * 40)
        
        # Show current world
        if editor.current_world:
            print(f"Current World: {editor.current_world}")
        
        print("\n1. List Worlds")
        print("2. Create/Load World")
        print("3. List Rooms")
        print("4. Create Room")
        print("5. Edit Room")
        print("6. Delete Room")
        print("7. Validate World")
        print("8. Visualize World")
        print("9. Exit")
        
        choice = input("\nEnter your choice (1-9): ").strip()
        
        if choice == "1":
            worlds = editor.list_worlds()
            if worlds:
                print("\nAvailable worlds:")
                for world in worlds:
                    print(f"- {world}")
            else:
                print("\nNo worlds found.")
        
        elif choice == "2":
            world_name = input("Enter world name: ").strip()
            if editor.load_world(world_name):
                print(f"\nWorld '{world_name}' loaded successfully!")
        
        elif choice == "3":
            editor.list_rooms()
        
        elif choice == "4":
            editor.create_room()
        
        elif choice == "5":
            editor.edit_room()
        
        elif choice == "6":
            editor.delete_room()
        
        elif choice == "7":
            errors = editor.validate_world()
            if errors:
                print("\nValidation errors found:")
                for error in errors:
                    print(f"- {error}")
            else:
                print("\nWorld validation passed!")
        
        elif choice == "8":
            editor.visualize_world()
        
        elif choice == "9":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main() 