import json
import os
from typing import Dict, List, Optional

class ItemEditor:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.items_file = os.path.join(data_dir, "items.json")
        self.items_data = self.load_items()

    def load_items(self) -> Dict:
        """Load items from JSON file."""
        try:
            with open(self.items_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"items": []}

    def save_items(self) -> None:
        """Save items to JSON file."""
        with open(self.items_file, 'w') as f:
            json.dump(self.items_data, f, indent=2)

    def list_items(self) -> None:
        """List all items."""
        print("\nCurrent Items:")
        print("=" * 40)
        for item in self.items_data["items"]:
            print(f"\nID: {item['id']}")
            print(f"Short Description: {item['short_desc']}")
            print(f"Type: {item['properties'].get('type', 'unknown')}")
            print(f"Weight: {item['properties'].get('weight', 0.0)} units")
            if item['properties'].get('respawnable', False):
                print(f"Respawn Time: {item['properties'].get('respawn_time', 1800)} seconds")

    def get_item(self, item_id: str) -> Optional[Dict]:
        """Get item by ID."""
        for item in self.items_data["items"]:
            if item["id"] == item_id:
                return item
        return None

    def create_item(self) -> None:
        """Create a new item interactively."""
        print("\nCreate New Item")
        print("=" * 40)

        # Get basic item information
        item_id = input("Enter item ID (e.g., sword_002): ").strip()
        if self.get_item(item_id):
            print("Error: Item ID already exists!")
            return

        short_desc = input("Enter short description: ").strip()
        long_desc = input("Enter long description: ").strip()

        # Get item type
        print("\nAvailable item types:")
        print("1. weapon")
        print("2. armor")
        print("3. consumable")
        print("4. tool")
        print("5. key")
        print("6. magic")
        print("7. material")
        print("8. treasure")
        
        type_choice = input("Choose item type (1-8): ").strip()
        type_map = {
            "1": "weapon",
            "2": "armor",
            "3": "consumable",
            "4": "tool",
            "5": "key",
            "6": "magic",
            "7": "material",
            "8": "treasure"
        }
        item_type = type_map.get(type_choice, "misc")

        # Get common properties for all items
        properties = {"type": item_type}
        
        # Get weight (required for all items)
        while True:
            try:
                weight = float(input("Enter item weight (in units): ").strip() or "0.0")
                properties["weight"] = weight
                break
            except ValueError:
                print("Please enter a valid number for weight.")

        # Get respawn settings
        respawnable = input("Is this item respawnable? (y/n): ").strip().lower() == 'y'
        properties["respawnable"] = respawnable
        
        if respawnable:
            while True:
                try:
                    respawn_time = int(input("Enter respawn time in seconds (default 1800): ").strip() or "1800")
                    properties["respawn_time"] = respawn_time
                    break
                except ValueError:
                    print("Please enter a valid number for respawn time.")

        # Get type-specific properties
        if item_type == "weapon":
            damage = int(input("Enter damage value: ").strip() or "5")
            properties["damage"] = damage
            magic = input("Is it magical? (y/n): ").strip().lower() == 'y'
            if magic:
                properties["magic"] = True
        elif item_type == "armor":
            defense = int(input("Enter defense value: ").strip() or "3")
            properties["defense"] = defense
        elif item_type == "consumable":
            effect = input("Enter effect (heal/mana/strength): ").strip()
            value = int(input("Enter effect value: ").strip() or "10")
            properties["effect"] = effect
            properties["value"] = value
        elif item_type == "magic":
            spell = input("Enter spell effect: ").strip()
            properties["spell"] = spell
        elif item_type in ["material", "treasure"]:
            value = int(input("Enter item value: ").strip() or "10")
            properties["value"] = value

        # Create the item
        new_item = {
            "id": item_id,
            "short_desc": short_desc,
            "long_desc": long_desc,
            "properties": properties
        }

        self.items_data["items"].append(new_item)
        self.save_items()
        print(f"\nItem '{item_id}' created successfully!")

    def edit_item(self) -> None:
        """Edit an existing item."""
        self.list_items()
        item_id = input("\nEnter ID of item to edit: ").strip()
        
        item = self.get_item(item_id)
        if not item:
            print("Error: Item not found!")
            return

        print("\nEdit Item")
        print("=" * 40)
        print("Press Enter to keep current value")

        # Edit basic properties
        new_short = input(f"Short description [{item['short_desc']}]: ").strip()
        if new_short:
            item['short_desc'] = new_short

        new_long = input(f"Long description [{item['long_desc']}]: ").strip()
        if new_long:
            item['long_desc'] = new_long

        # Edit weight
        current_weight = item['properties'].get('weight', 0.0)
        while True:
            new_weight = input(f"Weight [{current_weight}]: ").strip()
            if not new_weight:
                break
            try:
                item['properties']['weight'] = float(new_weight)
                break
            except ValueError:
                print("Please enter a valid number for weight.")

        # Edit respawn settings
        current_respawnable = item['properties'].get('respawnable', False)
        new_respawnable = input(f"Respawnable (y/n) [{current_respawnable}]: ").strip()
        if new_respawnable.lower() in ['y', 'n']:
            item['properties']['respawnable'] = new_respawnable.lower() == 'y'
            if new_respawnable.lower() == 'y':
                current_respawn_time = item['properties'].get('respawn_time', 1800)
                while True:
                    new_respawn_time = input(f"Respawn time in seconds [{current_respawn_time}]: ").strip()
                    if not new_respawn_time:
                        break
                    try:
                        item['properties']['respawn_time'] = int(new_respawn_time)
                        break
                    except ValueError:
                        print("Please enter a valid number for respawn time.")

        # Edit properties based on type
        item_type = item['properties']['type']
        if item_type == "weapon":
            new_damage = input(f"Damage [{item['properties'].get('damage', 5)}]: ").strip()
            if new_damage:
                item['properties']['damage'] = int(new_damage)
            
            is_magic = input(f"Magical (y/n) [{item['properties'].get('magic', False)}]: ").strip()
            if is_magic.lower() in ['y', 'n']:
                item['properties']['magic'] = is_magic.lower() == 'y'
        
        elif item_type == "consumable":
            new_effect = input(f"Effect [{item['properties'].get('effect', 'heal')}]: ").strip()
            if new_effect:
                item['properties']['effect'] = new_effect
            
            new_value = input(f"Value [{item['properties'].get('value', 10)}]: ").strip()
            if new_value:
                item['properties']['value'] = int(new_value)

        elif item_type in ["material", "treasure"]:
            new_value = input(f"Value [{item['properties'].get('value', 10)}]: ").strip()
            if new_value:
                item['properties']['value'] = int(new_value)

        self.save_items()
        print(f"\nItem '{item_id}' updated successfully!")

    def delete_item(self) -> None:
        """Delete an existing item."""
        self.list_items()
        item_id = input("\nEnter ID of item to delete: ").strip()
        
        for i, item in enumerate(self.items_data["items"]):
            if item["id"] == item_id:
                confirm = input(f"Are you sure you want to delete '{item_id}'? (y/n): ").strip().lower()
                if confirm == 'y':
                    self.items_data["items"].pop(i)
                    self.save_items()
                    print(f"\nItem '{item_id}' deleted successfully!")
                return
        
        print("Error: Item not found!")

def main():
    editor = ItemEditor()
    
    while True:
        print("\nItem Editor")
        print("=" * 40)
        print("1. List Items")
        print("2. Create Item")
        print("3. Edit Item")
        print("4. Delete Item")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            editor.list_items()
        elif choice == "2":
            editor.create_item()
        elif choice == "3":
            editor.edit_item()
        elif choice == "4":
            editor.delete_item()
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main() 