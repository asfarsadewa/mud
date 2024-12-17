import json
import os
import sys
from pathlib import Path

def load_json(file_path):
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"mobs": []}

def save_json(file_path, data):
    """Save JSON data to a file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def get_mob_template():
    """Return a template for a new mob."""
    return {
        "id": "",
        "name": "",
        "short_desc": "",
        "long_desc": "",
        "level": 1,
        "stats": {
            "max_hp": 20,
            "current_hp": 20,
            "attack": 5,
            "defense": 2,
            "xp_value": 15
        },
        "loot_table": {},
        "spawn_areas": []
    }

def list_mobs(mobs_data):
    """Display all mobs."""
    if not mobs_data["mobs"]:
        print("No mobs found.")
        return

    print("\n=== Existing Mobs ===")
    for mob in mobs_data["mobs"]:
        print(f"\nID: {mob['id']}")
        print(f"Name: {mob['name']}")
        print(f"Level: {mob['level']}")
        print(f"HP: {mob['stats']['max_hp']}")
        print(f"Attack: {mob['stats']['attack']}")
        print(f"Defense: {mob['stats']['defense']}")
        print(f"XP Value: {mob['stats']['xp_value']}")
        print("-" * 30)

def create_mob(mobs_data):
    """Create a new mob."""
    mob = get_mob_template()
    
    print("\n=== Create New Mob ===")
    
    # Basic Info
    mob["id"] = input("Enter mob ID (e.g., wolf_002): ").strip()
    if any(m["id"] == mob["id"] for m in mobs_data["mobs"]):
        print("Error: Mob ID already exists!")
        return
    
    mob["name"] = input("Enter mob name: ").strip()
    mob["short_desc"] = input("Enter short description: ").strip()
    mob["long_desc"] = input("Enter long description: ").strip()
    
    # Stats
    try:
        mob["level"] = int(input("Enter level (default 1): ") or "1")
        mob["stats"]["max_hp"] = int(input("Enter max HP (default 20): ") or "20")
        mob["stats"]["current_hp"] = mob["stats"]["max_hp"]
        mob["stats"]["attack"] = int(input("Enter attack value (default 5): ") or "5")
        mob["stats"]["defense"] = int(input("Enter defense value (default 2): ") or "2")
        mob["stats"]["xp_value"] = int(input("Enter XP value (default 15): ") or "15")
    except ValueError:
        print("Error: Please enter valid numbers for stats!")
        return
    
    # Loot Table
    print("\nLoot Table (Enter 'done' when finished)")
    while True:
        item_id = input("Enter item ID (or 'done'): ").strip()
        if item_id.lower() == 'done':
            break
        try:
            probability = float(input("Enter drop probability (0.0-1.0): "))
            if 0 <= probability <= 1:
                mob["loot_table"][item_id] = probability
            else:
                print("Probability must be between 0 and 1!")
        except ValueError:
            print("Error: Please enter a valid probability!")
    
    # Spawn Areas
    print("\nSpawn Areas (Enter 'done' when finished)")
    while True:
        area = input("Enter room ID (or 'done'): ").strip()
        if area.lower() == 'done':
            break
        mob["spawn_areas"].append(area)
    
    mobs_data["mobs"].append(mob)
    print("\nMob created successfully!")

def edit_mob(mobs_data):
    """Edit an existing mob."""
    print("\n=== Edit Mob ===")
    mob_id = input("Enter mob ID to edit: ").strip()
    
    mob = None
    for m in mobs_data["mobs"]:
        if m["id"] == mob_id:
            mob = m
            break
    
    if not mob:
        print("Mob not found!")
        return
    
    print("\nCurrent values (press Enter to keep current value)")
    
    # Basic Info
    new_name = input(f"Name [{mob['name']}]: ").strip()
    if new_name:
        mob["name"] = new_name
    
    new_short = input(f"Short description [{mob['short_desc']}]: ").strip()
    if new_short:
        mob["short_desc"] = new_short
    
    new_long = input(f"Long description [{mob['long_desc']}]: ").strip()
    if new_long:
        mob["long_desc"] = new_long
    
    # Stats
    try:
        new_level = input(f"Level [{mob['level']}]: ").strip()
        if new_level:
            mob["level"] = int(new_level)
        
        new_hp = input(f"Max HP [{mob['stats']['max_hp']}]: ").strip()
        if new_hp:
            mob["stats"]["max_hp"] = int(new_hp)
            mob["stats"]["current_hp"] = int(new_hp)
        
        new_attack = input(f"Attack [{mob['stats']['attack']}]: ").strip()
        if new_attack:
            mob["stats"]["attack"] = int(new_attack)
        
        new_defense = input(f"Defense [{mob['stats']['defense']}]: ").strip()
        if new_defense:
            mob["stats"]["defense"] = int(new_defense)
        
        new_xp = input(f"XP Value [{mob['stats']['xp_value']}]: ").strip()
        if new_xp:
            mob["stats"]["xp_value"] = int(new_xp)
    except ValueError:
        print("Error: Please enter valid numbers for stats!")
        return
    
    # Loot Table
    print("\nEdit Loot Table?")
    if input("(y/n): ").lower().startswith('y'):
        mob["loot_table"] = {}
        print("Enter new loot table (Enter 'done' when finished)")
        while True:
            item_id = input("Enter item ID (or 'done'): ").strip()
            if item_id.lower() == 'done':
                break
            try:
                probability = float(input("Enter drop probability (0.0-1.0): "))
                if 0 <= probability <= 1:
                    mob["loot_table"][item_id] = probability
                else:
                    print("Probability must be between 0 and 1!")
            except ValueError:
                print("Error: Please enter a valid probability!")
    
    # Spawn Areas
    print("\nEdit Spawn Areas?")
    if input("(y/n): ").lower().startswith('y'):
        mob["spawn_areas"] = []
        print("Enter new spawn areas (Enter 'done' when finished)")
        while True:
            area = input("Enter room ID (or 'done'): ").strip()
            if area.lower() == 'done':
                break
            mob["spawn_areas"].append(area)
    
    print("\nMob updated successfully!")

def delete_mob(mobs_data):
    """Delete an existing mob."""
    print("\n=== Delete Mob ===")
    mob_id = input("Enter mob ID to delete: ").strip()
    
    initial_count = len(mobs_data["mobs"])
    mobs_data["mobs"] = [m for m in mobs_data["mobs"] if m["id"] != mob_id]
    
    if len(mobs_data["mobs"]) < initial_count:
        print("Mob deleted successfully!")
    else:
        print("Mob not found!")

def main():
    # Get the path to the mobs.json file
    script_dir = Path(__file__).resolve().parent.parent
    mobs_file = script_dir / "data" / "mobs.json"
    
    while True:
        # Load fresh data each time
        mobs_data = load_json(mobs_file)
        
        print("\n=== Mob Editor ===")
        print("1. List all mobs")
        print("2. Create new mob")
        print("3. Edit mob")
        print("4. Delete mob")
        print("5. Save and exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            list_mobs(mobs_data)
        elif choice == "2":
            create_mob(mobs_data)
            save_json(mobs_file, mobs_data)
        elif choice == "3":
            edit_mob(mobs_data)
            save_json(mobs_file, mobs_data)
        elif choice == "4":
            delete_mob(mobs_data)
            save_json(mobs_file, mobs_data)
        elif choice == "5":
            print("Saving and exiting...")
            save_json(mobs_file, mobs_data)
            break
        else:
            print("Invalid choice! Please enter a number between 1 and 5.")

if __name__ == "__main__":
    main() 