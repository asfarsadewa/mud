import json
import os
from typing import Dict, List, Optional, Any

class DataManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.items_data: Dict = {}
        self.characters_data: Dict = {}
        self.npcs_data: Dict = {}
        self.load_all_data()

    def load_all_data(self) -> None:
        """Load all JSON data files into memory."""
        self.items_data = self._load_json_file("items.json")
        self.characters_data = self._load_json_file("characters.json")
        self.npcs_data = self._load_json_file("npcs.json")

    def _load_json_file(self, filename: str) -> Dict:
        """Load a JSON file and return its contents."""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {filename} not found. Creating empty structure.")
            return {}
        except json.JSONDecodeError:
            print(f"Error: {filename} is not valid JSON.")
            return {}

    def save_characters(self) -> None:
        """Save the current characters data back to file."""
        filepath = os.path.join(self.data_dir, "characters.json")
        with open(filepath, 'w') as f:
            json.dump(self.characters_data, f, indent=2)

    def get_item(self, item_id: str) -> Optional[Dict]:
        """Get item data by ID."""
        for item in self.items_data.get("items", []):
            if item["id"] == item_id:
                return item
        return None

    def get_npc(self, npc_id: str) -> Optional[Dict]:
        """Get NPC data by ID."""
        for npc in self.npcs_data.get("npcs", []):
            if npc["id"] == npc_id:
                return npc
        return None

    def get_npc_by_name(self, name: str) -> Optional[Dict]:
        """Get NPC data by name (case-insensitive)."""
        name = name.lower()
        for npc in self.npcs_data.get("npcs", []):
            if npc["name"].lower() == name or npc["short_desc"].lower() == name:
                return npc
        return None

    def get_character(self, name: str) -> Optional[Dict]:
        """Get character data by name."""
        for char in self.characters_data.get("characters", []):
            if char["name"].lower() == name.lower():
                return char
        return None

    def add_character(self, character_data: Dict) -> None:
        """Add a new character to the data."""
        if "characters" not in self.characters_data:
            self.characters_data["characters"] = []
        self.characters_data["characters"].append(character_data)
        self.save_characters()

    def update_character(self, character_data: Dict) -> None:
        """Update an existing character's data."""
        chars = self.characters_data.get("characters", [])
        for i, char in enumerate(chars):
            if char["name"] == character_data["name"]:
                chars[i] = character_data
                break
        self.save_characters()

    def list_characters(self) -> List[str]:
        """Return a list of all character names."""
        return [char["name"] for char in self.characters_data.get("characters", [])]

    def get_npc_dialogue_topics(self, npc_id: str, known_topics: Optional[List[str]] = None) -> List[Dict]:
        """Get available dialogue topics for an NPC."""
        npc = self.get_npc(npc_id)
        if not npc or "dialogue" not in npc:
            return []

        known_topics = known_topics or []
        available_topics = []
        
        for topic_id, topic_data in npc["dialogue"]["topics"].items():
            # Skip topics that require other topics if requirements aren't met
            if "requires_topic" in topic_data and topic_data["requires_topic"] not in known_topics:
                continue
            
            topic_info = {
                "id": topic_id,
                "prompt": topic_data["prompt"]
            }
            available_topics.append(topic_info)

        return available_topics

    def get_npc_response(self, npc_id: str, topic_id: str) -> Optional[Dict]:
        """Get an NPC's response for a specific topic."""
        npc = self.get_npc(npc_id)
        if not npc or "dialogue" not in npc:
            return None

        topic = npc["dialogue"]["topics"].get(topic_id)
        if not topic:
            return None

        return {
            "response": topic["response"],
            "leads_to": topic.get("leads_to", [])
        }

    def load_json(self, filepath: str) -> Dict:
        """Load any JSON file from the data directory."""
        # If the full path is provided, extract just the filename
        filename = os.path.basename(filepath)
        return self._load_json_file(filename)

    def save_json(self, filepath: str, data: Dict) -> None:
        """Save data to a JSON file in the data directory."""
        # If the full path is provided, extract just the filename
        filename = os.path.basename(filepath)
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving {filename}: {str(e)}") 

    def delete_character(self, name: str) -> bool:
        """Delete a character from characters.json."""
        try:
            # Find and remove character by name (case-insensitive)
            self.characters_data["characters"] = [
                char for char in self.characters_data.get("characters", [])
                if char["name"].lower() != name.lower()
            ]
            # Save updated characters file
            self.save_characters()
            return True
        except Exception as e:
            print(f"Error deleting character: {e}")
            return False