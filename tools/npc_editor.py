import json
import os
from typing import Dict, List, Optional

class NPCEditor:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.npcs_file = os.path.join(data_dir, "npcs.json")
        self.npcs_data = self.load_npcs()

    def load_npcs(self) -> Dict:
        """Load NPCs from JSON file."""
        try:
            with open(self.npcs_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"npcs": []}

    def save_npcs(self) -> None:
        """Save NPCs to JSON file."""
        with open(self.npcs_file, 'w') as f:
            json.dump(self.npcs_data, f, indent=2)

    def list_npcs(self) -> None:
        """List all NPCs."""
        print("\nCurrent NPCs:")
        print("=" * 40)
        for npc in self.npcs_data["npcs"]:
            print(f"\nID: {npc['id']}")
            print(f"Name: {npc['name']}")
            print(f"Type: {'Merchant' if 'merchant_data' in npc else 'Regular NPC'}")

    def get_npc(self, npc_id: str) -> Optional[Dict]:
        """Get NPC by ID."""
        for npc in self.npcs_data["npcs"]:
            if npc["id"] == npc_id:
                return npc
        return None

    def create_dialogue(self) -> Dict:
        """Create dialogue structure interactively."""
        dialogue = {
            "greeting": input("Enter NPC's greeting: ").strip(),
            "topics": {}
        }

        while True:
            print("\nAdd Dialogue Topic")
            print("=" * 40)
            topic_id = input("Enter topic ID (or press Enter to finish): ").strip()
            if not topic_id:
                break

            topic = {
                "prompt": input("Enter topic prompt: ").strip(),
                "response": input("Enter NPC's response: ").strip()
            }

            # Optional fields
            if input("Does this topic require another topic? (y/n): ").strip().lower() == 'y':
                topic["requires_topic"] = input("Enter required topic ID: ").strip()

            if input("Does this topic lead to other topics? (y/n): ").strip().lower() == 'y':
                leads_to = []
                while True:
                    next_topic = input("Enter topic ID it leads to (or press Enter to finish): ").strip()
                    if not next_topic:
                        break
                    leads_to.append(next_topic)
                if leads_to:
                    topic["leads_to"] = leads_to

            if input("Is this a trade topic? (y/n): ").strip().lower() == 'y':
                topic["is_trade"] = True

            dialogue["topics"][topic_id] = topic

        return dialogue

    def create_merchant_data(self) -> Dict:
        """Create merchant data structure interactively."""
        merchant_data = {
            "inventory": {},
            "buy_multiplier": float(input("Enter buy multiplier (e.g., 0.5 for 50%): ").strip() or "0.5"),
            "unlocked": input("Is premium inventory unlocked? (y/n): ").strip().lower() == 'y',
            "premium_inventory": {}
        }

        # Regular inventory
        print("\nAdd Regular Inventory Items")
        while True:
            item_id = input("Enter item ID (or press Enter to finish): ").strip()
            if not item_id:
                break

            merchant_data["inventory"][item_id] = {
                "price": int(input("Enter price: ").strip()),
                "quantity": int(input("Enter quantity: ").strip())
            }

        # Premium inventory
        if input("\nAdd premium inventory items? (y/n): ").strip().lower() == 'y':
            print("\nAdd Premium Inventory Items")
            while True:
                item_id = input("Enter item ID (or press Enter to finish): ").strip()
                if not item_id:
                    break

                merchant_data["premium_inventory"][item_id] = {
                    "price": int(input("Enter price: ").strip()),
                    "quantity": int(input("Enter quantity: ").strip())
                }

        return merchant_data

    def create_npc(self) -> None:
        """Create a new NPC interactively."""
        print("\nCreate New NPC")
        print("=" * 40)

        # Get basic NPC information
        npc_id = input("Enter NPC ID (e.g., merchant_002): ").strip()
        if self.get_npc(npc_id):
            print("Error: NPC ID already exists!")
            return

        name = input("Enter NPC name: ").strip()
        short_desc = input("Enter short description: ").strip()
        long_desc = input("Enter long description: ").strip()

        # Create dialogue
        print("\nCreate NPC Dialogue")
        dialogue = self.create_dialogue()

        # Create NPC data
        npc_data = {
            "id": npc_id,
            "name": name,
            "short_desc": short_desc,
            "long_desc": long_desc,
            "dialogue": dialogue
        }

        # Add merchant data if it's a merchant
        if input("\nIs this NPC a merchant? (y/n): ").strip().lower() == 'y':
            print("\nCreate Merchant Data")
            npc_data["merchant_data"] = self.create_merchant_data()

        self.npcs_data["npcs"].append(npc_data)
        self.save_npcs()
        print(f"\nNPC '{name}' created successfully!")

    def edit_npc(self) -> None:
        """Edit an existing NPC."""
        self.list_npcs()
        npc_id = input("\nEnter ID of NPC to edit: ").strip()
        
        npc = self.get_npc(npc_id)
        if not npc:
            print("Error: NPC not found!")
            return

        print("\nEdit NPC")
        print("=" * 40)
        print("Press Enter to keep current value")

        # Edit basic properties
        new_name = input(f"Name [{npc['name']}]: ").strip()
        if new_name:
            npc['name'] = new_name

        new_short = input(f"Short description [{npc['short_desc']}]: ").strip()
        if new_short:
            npc['short_desc'] = new_short

        new_long = input(f"Long description [{npc['long_desc']}]: ").strip()
        if new_long:
            npc['long_desc'] = new_long

        # Edit dialogue
        if input("\nEdit dialogue? (y/n): ").strip().lower() == 'y':
            npc['dialogue'] = self.create_dialogue()

        # Edit merchant data
        if 'merchant_data' in npc and input("\nEdit merchant data? (y/n): ").strip().lower() == 'y':
            npc['merchant_data'] = self.create_merchant_data()

        self.save_npcs()
        print(f"\nNPC '{npc['name']}' updated successfully!")

    def delete_npc(self) -> None:
        """Delete an existing NPC."""
        self.list_npcs()
        npc_id = input("\nEnter ID of NPC to delete: ").strip()
        
        for i, npc in enumerate(self.npcs_data["npcs"]):
            if npc["id"] == npc_id:
                confirm = input(f"Are you sure you want to delete '{npc['name']}'? (y/n): ").strip().lower()
                if confirm == 'y':
                    self.npcs_data["npcs"].pop(i)
                    self.save_npcs()
                    print(f"\nNPC '{npc['name']}' deleted successfully!")
                return
        
        print("Error: NPC not found!")

def main():
    editor = NPCEditor()
    
    while True:
        print("\nNPC Editor")
        print("=" * 40)
        print("1. List NPCs")
        print("2. Create NPC")
        print("3. Edit NPC")
        print("4. Delete NPC")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            editor.list_npcs()
        elif choice == "2":
            editor.create_npc()
        elif choice == "3":
            editor.edit_npc()
        elif choice == "4":
            editor.delete_npc()
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main() 