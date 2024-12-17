from typing import Dict, List, Optional, Tuple
from .data_manager import DataManager
from .character_manager import CharacterManager
from .world_manager import WorldManager
from .combat_manager import CombatManager
import asyncio

class CommandHandler:
    def __init__(self, data_manager: DataManager, character_manager: CharacterManager, world_manager: WorldManager):
        self.data_manager = data_manager
        self.character_manager = character_manager
        self.world_manager = world_manager
        self.combat_manager = CombatManager(data_manager, world_manager)  # Pass both managers
        
    async def handle_command(self, character_name: str, command: str) -> Tuple[bool, str]:
        """Handle a command from a player."""
        parts = command.lower().split()
        if not parts:
            return False, "Please enter a command."
            
        cmd = parts[0]
        args = parts[1:]
        
        # Get fresh character data
        character = self.character_manager.get_character(character_name)
        if not character:
            return False, "Character not found."
            
        # If in combat, only allow combat-related commands
        if character.get("combat_state", {}).get("in_combat", False):
            return self.handle_combat_command(character_name, cmd, args)
        
        # Normal commands when not in combat
        commands = {
            "look": lambda args: self.cmd_look(character_name, args),
            "l": lambda args: self.cmd_look(character_name, args),
            "inventory": lambda args: self.cmd_inventory(character_name, args),
            "i": lambda args: self.cmd_inventory(character_name, args),
            "examine": lambda args: self.cmd_examine(character_name, args),
            "equip": lambda args: self.cmd_equip(character_name, args),
            "eq": lambda args: self.cmd_equip(character_name, args),
            "unequip": lambda args: self.cmd_unequip(character_name, args),
            "uneq": lambda args: self.cmd_unequip(character_name, args),
            "use": lambda args: self.cmd_use(character_name, args),
            "go": lambda args: self.cmd_go(character_name, args),
            "north": lambda args: self.cmd_go(character_name, ["north"]),
            "n": lambda args: self.cmd_go(character_name, ["north"]),
            "south": lambda args: self.cmd_go(character_name, ["south"]),
            "s": lambda args: self.cmd_go(character_name, ["south"]),
            "east": lambda args: self.cmd_go(character_name, ["east"]),
            "e": lambda args: self.cmd_go(character_name, ["east"]),
            "west": lambda args: self.cmd_go(character_name, ["west"]),
            "w": lambda args: self.cmd_go(character_name, ["west"]),
            "up": lambda args: self.cmd_go(character_name, ["up"]),
            "u": lambda args: self.cmd_go(character_name, ["up"]),
            "down": lambda args: self.cmd_go(character_name, ["down"]),
            "d": lambda args: self.cmd_go(character_name, ["down"]),
            "take": lambda args: self.cmd_take(character_name, args),
            "drop": lambda args: self.cmd_drop(character_name, args),
            "talk": lambda args: self.cmd_talk(character_name, args),
            "list": lambda args: self.cmd_list(character_name, args),
            "buy": lambda args: self.cmd_buy(character_name, args),
            "sell": lambda args: self.cmd_sell(character_name, args),
            "attack": lambda args: self.cmd_attack(character_name, args),
            "a": lambda args: self.cmd_attack(character_name, args),
            "kill": lambda args: self.cmd_attack(character_name, args),
            "k": lambda args: self.cmd_attack(character_name, args),
            "stats": lambda args: self.cmd_stats(character_name, args),
            "st": lambda args: self.cmd_stats(character_name, args),
            "map": lambda args: self.cmd_map(character_name, args),
            "help": lambda args: self.cmd_help(character_name, args),
            "sacrifice": lambda args: self.cmd_sacrifice(character_name, args),
            "sac": lambda args: self.cmd_sacrifice(character_name, args),
            "ask": lambda args: self.cmd_ask(character_name, args),
            "quit": lambda args: self.cmd_quit(character_name, args),
            "q": lambda args: self.cmd_quit(character_name, args)
        }
        
        if cmd in commands:
            result = commands[cmd](args)
            # If it's an async command, await it
            if asyncio.iscoroutine(result):
                return await result
            return result
        
        return False, "Unknown command. Type 'help' for a list of commands."

    async def cmd_go(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Handle the go command."""
        if not args:
            return False, "Go where? Please specify a direction."

        direction = args[0].lower()
        current_room = self.character_manager.get_current_room()
        exit_data = self.world_manager.get_exit_room_id(current_room, direction)

        if not exit_data:
            return False, f"You cannot go {direction} from here."

        # Handle world transitions
        if exit_data["type"] == "world_transition":
            character = self.character_manager.get_character(character_name)
            if not character:
                return False, "Character not found."

            # Check requirements
            can_transition, reason = self.world_manager.check_world_transition_requirements(
                character, exit_data["requirements"]
            )
            if not can_transition:
                return False, reason

            # Change world and move to new room
            if not self.world_manager.change_world(exit_data["target_world"]):
                return False, "Error: Could not load target world."

            self.character_manager.set_current_room(exit_data["target_room"])
            description = await self.world_manager.get_room_description(exit_data["target_room"], show_long=True)
            return False, f"{exit_data['description']}\n\n{description}"

        # Handle regular room movement
        self.character_manager.set_current_room(exit_data["target"])
        description = await self.world_manager.get_room_description(exit_data["target"], show_long=True)
        return False, description

    async def cmd_look(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Handle the look command."""
        # Set the current character first
        self.character_manager.load_character(character_name)
        current_room = self.character_manager.get_current_room()
        description = await self.world_manager.get_room_description(current_room)
        return False, description

    def cmd_inventory(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Handle the inventory command."""
        character = self.data_manager.get_character(character_name)
        if not character:
            return False, "Character not found."

        inventory = character.get("inventory", [])
        if not inventory:
            return False, "Your inventory is empty."

        # Calculate total weight carried
        total_weight = 0.0
        
        # Add weights from inventory
        for item_id in inventory:
            item = self.data_manager.get_item(item_id)
            if item and "weight" in item.get("properties", {}):
                total_weight += item["properties"]["weight"]
        
        # Add weights from equipped items
        for slot, equipped_id in character["equipment"].items():
            if equipped_id:
                item = self.data_manager.get_item(equipped_id)
                if item and "weight" in item.get("properties", {}):
                    total_weight += item["properties"]["weight"]

        # Group items and count quantities
        item_counts = {}
        item_details = {}  # Store full item details for display
        
        for item_id in inventory:
            item = self.data_manager.get_item(item_id)
            if not item:
                continue
            
            # Use short_desc as the display key
            display_name = item["short_desc"]
            item_counts[display_name] = item_counts.get(display_name, 0) + 1
            item_details[display_name] = item

        # Build the fancy inventory display
        sections = []
        sections.append("╔══════════════════════════════╦═════════════════════╗")
        sections.append(f"║                     INVENTORY                           ║")
        sections.append("╠══════════════════════════════════════════════════════════╣")
        sections.append(f"║  Total Weight: {total_weight:.1f}kg                                    ║")
        sections.append("║                                                          ║")

        # Equipment Section
        equipped_found = False
        for slot, equipped_id in character["equipment"].items():
            if equipped_id:
                if not equipped_found:
                    sections.append("║  EQUIPPED ITEMS                                         ║")
                    sections.append("║  ──────────────                                        ║")
                    equipped_found = True
                item = self.data_manager.get_item(equipped_id)
                if item:
                    weight_str = f" ({item['properties'].get('weight', 0):.1f}kg)"
                    item_str = f"{slot.title():<8}: {item['short_desc']}{weight_str}"
                    sections.append(f"║  {item_str:<52}║")
        if equipped_found:
            sections.append("║                                                          ║")

        # Categorize remaining items
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
            for equipped_id in character["equipment"].values():
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

        # Add categories to display
        for category, items in categories.items():
            if items:
                sections.append(f"║  {category:<52}║")
                sections.append("║  ──────────────                                        ║")
                for item in sorted(items):
                    sections.append(f"║  {item:<52}║")
                sections.append("║                                                          ║")

        # Add money at the bottom
        money = character.get("money", 0)
        sections.append("╠═══════════════════════════════════════════════════════════╣")
        sections.append(f"║  Money: {money:<47} coins ��")
        sections.append("╚══════════════════════════════════════════════════════════╝")

        return False, "\n".join(sections)

    def cmd_drop(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Handle the drop command."""
        if not args:
            return False, "Drop what?"

        item_name = " ".join(args).lower()
        inventory = self.character_manager.get_inventory()

        # Find the item in inventory that matches the name
        for item_id in inventory:
            item = self.data_manager.get_item(item_id)
            if item and item["short_desc"].lower() == item_name:
                current_room = self.character_manager.get_current_room()
                if self.character_manager.drop_item(item_id):
                    return False, f"You drop {item['short_desc']}."
                return False, "Failed to drop item."

        return False, "You don't have that."

    def cmd_talk(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Handle the talk command."""
        if not args:
            return False, "Talk to whom?"

        npc_name = " ".join(args).lower()
        current_room = self.character_manager.get_current_room()
        npc = self.world_manager.get_npc_in_room(current_room, npc_name)

        if not npc:
            return False, f"You don't see {npc_name} here."

        # Get NPC's dialogue
        dialogue = npc.get("dialogue", {})
        greeting = dialogue.get("greeting", "The NPC has nothing to say.")
        topics = dialogue.get("topics", {})
        known_topics = self.character_manager.get_known_topics(npc["id"])

        # Format response with greeting and available topics
        response = [
            f"{npc['name']} says: \"{greeting}\""
        ]
        
        # Only show topics if they exist
        if topics:
            response.append("\nAvailable topics:")
            for topic_id, topic_data in topics.items():
                # Handle both dictionary and string formats
                if isinstance(topic_data, dict):
                    # Only show topics that don't have requirements or whose requirements are met
                    if not topic_data.get("requires_topic") or topic_data["requires_topic"] in known_topics:
                        response.append(f"- {topic_data['prompt']} (say 'ask {npc['name'].lower()} about {topic_id}')")
                else:
                    # For string-only topics, use the topic_id as the prompt
                    response.append(f"- Ask about {topic_id} (say 'ask {npc['name'].lower()} about {topic_id}')")

        return False, "\n".join(response)

    def cmd_list(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Handle the list command for merchant inventory."""
        merchant = self._get_merchant_in_room()
        if not merchant:
            return False, "There is no merchant here."

        # Check if merchant is ready to trade
        if not self.character_manager.get_known_topics(merchant["id"]):
            return False, f"{merchant['name']} isn't ready to trade. Try talking to them first."

        inventory = merchant["merchant_data"]["inventory"]
        response = [f"{merchant['name']}'s wares:"]

        # List regular inventory
        for item_id, data in inventory.items():
            if data["quantity"] > 0:
                item = self.data_manager.get_item(item_id)
                if item:
                    response.append(f"- {item['short_desc']}: {self._format_price(data['price'])} ({data['quantity']} available)")

        # List premium inventory if unlocked
        if merchant["merchant_data"]["unlocked"]:
            premium = merchant["merchant_data"]["premium_inventory"]
            if premium:
                response.append("\nPremium items:")
                for item_id, data in premium.items():
                    if data["quantity"] > 0:
                        item = self.data_manager.get_item(item_id)
                        if item:
                            response.append(f"- {item['short_desc']}: {self._format_price(data['price'])} ({data['quantity']} available)")

        response.append(f"\nYour money: {self._format_price(self.character_manager.get_money())}")
        return False, "\n".join(response)

    def cmd_buy(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Handle the buy command."""
        if not args:
            return False, "Buy what?"

        merchant = self._get_merchant_in_room()
        if not merchant:
            return False, "There is no merchant here."

        # Check if merchant is ready to trade
        if not self.character_manager.get_known_topics(merchant["id"]):
            return False, f"{merchant['name']} isn't ready to trade. Try talking to them first."

        item_name = " ".join(args).lower()
        inventory = merchant["merchant_data"]["inventory"]
        premium = merchant["merchant_data"]["premium_inventory"] if merchant["merchant_data"]["unlocked"] else {}
        
        # Find the item in merchant's inventory
        for item_id in {**inventory, **premium}:
            item = self.data_manager.get_item(item_id)
            if not item:
                continue

            # Make item matching more flexible by checking if search terms are in the item name
            item_desc = item["short_desc"].lower()
            # Remove common articles for better matching
            search_terms = item_name.replace("a ", "").replace("an ", "").replace("the ", "").split()
            
            # Check if all search terms are found in the item description
            if all(term in item_desc for term in search_terms):
                # Check if it's in regular or premium inventory
                item_data = inventory.get(item_id) or premium.get(item_id)
                if not item_data or item_data["quantity"] <= 0:
                    return False, f"{merchant['name']} is out of stock of that item."

                # Check if player has enough money
                if not self.character_manager.remove_money(item_data["price"]):
                    return False, f"You can't afford that. It costs {self._format_price(item_data['price'])}."

                # Add item to player's inventory and reduce merchant's stock
                self.character_manager.add_to_inventory(item_id)
                item_data["quantity"] -= 1

                return False, f"You buy {item['short_desc']} for {self._format_price(item_data['price'])}."

        return False, f"{merchant['name']} doesn't have that item."

    def cmd_sell(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Handle the sell command."""
        if not args:
            return False, "Sell what?"

        merchant = self._get_merchant_in_room()
        if not merchant:
            return False, "There is no merchant here."

        # Check if merchant is ready to trade
        if not self.character_manager.get_known_topics(merchant["id"]):
            return False, f"{merchant['name']} isn't ready to trade. Try talking to them first."

        item_name = " ".join(args).lower()
        inventory = self.character_manager.get_inventory()

        # Find the item in player's inventory
        for item_id in inventory:
            item = self.data_manager.get_item(item_id)
            if not item:
                continue

            if item["short_desc"].lower() == item_name:
                # Calculate sell price
                buy_multiplier = merchant["merchant_data"]["buy_multiplier"]
                merchant_inv = merchant["merchant_data"]["inventory"]
                premium_inv = merchant["merchant_data"]["premium_inventory"]
                
                # Find original price
                if item_id in merchant_inv:
                    original_price = merchant_inv[item_id]["price"]
                elif item_id in premium_inv:
                    original_price = premium_inv[item_id]["price"]
                else:
                    original_price = 10  # Default price for items not in merchant's inventory
                
                sell_price = int(original_price * buy_multiplier)

                # Remove from inventory and add money
                self.character_manager.remove_from_inventory(item_id)
                self.character_manager.add_money(sell_price)

                return False, f"You sell {item['short_desc']} for {self._format_price(sell_price)}."

        return False, "You don't have that item."

    def cmd_attack(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Start combat with a mob in the room."""
        # Get character's current room
        character = self.character_manager.get_character(character_name)
        if not character:
            return False, "Character not found."
            
        # Load mobs data
        mobs_data = self.data_manager.load_json("mobs.json")
        current_room = character["current_room"]
        
        # Find mobs that can spawn in this room
        possible_mobs = []
        for mob in mobs_data["mobs"]:
            if current_room in mob["spawn_areas"]:
                possible_mobs.append(mob)
        
        if not possible_mobs:
            return False, "There are no enemies here."
        
        # If a specific target was given, try to match it
        if args:
            target_name = " ".join(args).lower()
            for mob in possible_mobs:
                if mob["name"].lower() == target_name:
                    return False, self.combat_manager.start_combat(character_name, mob["id"])
            # If no match found, use first mob (default behavior)
            
        # For now, just pick the first possible mob
        target_mob = possible_mobs[0]
        
        return False, self.combat_manager.start_combat(character_name, target_mob["id"])

    def cmd_stats(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Show character stats."""
        try:
            return False, self.character_manager.get_fancy_stats()
        except RuntimeError as e:
            return False, str(e)

    def cmd_take(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Handle the take command."""
        if not args:
            return False, "Take what?"

        current_room = self.character_manager.get_current_room()
        room_items = self.world_manager.get_room_items(current_room)

        if not room_items:
            return False, "There is nothing here to take."

        # Handle 'take all'
        if args[0].lower() == "all":
            if not room_items:
                return False, "There is nothing here to take."
            
            taken_items = []
            failed_items = []
            for item_id in room_items[:]:  # Create a copy to iterate over
                item = self.data_manager.get_item(item_id)
                if item:
                    # Check weight limit
                    item_weight = item.get("properties", {}).get("weight", 0)
                    if not self.character_manager.can_carry_weight(item_weight):
                        failed_items.append(item["short_desc"])
                        continue
                        
                    if self.character_manager.add_to_inventory(item_id):
                        self.world_manager.remove_item_from_room(current_room, item_id, self.character_manager.current_character)
                        taken_items.append(item["short_desc"])
            
            response = []
            if taken_items:
                response.append(f"You take: {', '.join(taken_items)}")
            if failed_items:
                response.append(f"Too heavy to take: {', '.join(failed_items)}")
            
            if not taken_items and not failed_items:
                return False, "There is nothing here to take."
                
            return False, "\n".join(response)

        # Normal take single item
        item_name = " ".join(args).lower()
        search_terms = item_name.replace("a ", "").replace("an ", "").replace("the ", "").split()
        for item_id in room_items:
            item = self.data_manager.get_item(item_id)
            if not item:
                continue
            item_desc = item["short_desc"].lower()
            if all(term in item_desc for term in search_terms):
                # Check weight limit
                item_weight = item.get("properties", {}).get("weight", 0)
                if not self.character_manager.can_carry_weight(item_weight):
                    current_weight = self.character_manager.calculate_total_weight()
                    weight_limit = self.character_manager.current_character["stats"]["weight_limit"]
                    return False, f"That's too heavy! ({current_weight:.1f}/{weight_limit:.1f}kg carried)"
                    
                if self.character_manager.add_to_inventory(item_id):
                    self.world_manager.remove_item_from_room(current_room, item_id, self.character_manager.current_character)
                    return False, f"You take {item['short_desc']}."
                return False, "Failed to take item."

        return False, "You don't see that here."

    def cmd_help(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Show available commands."""
        commands = [
            "Movement:",
            "  north (n), south (s), east (e), west (w), up (u), down (d)",
            "  go <direction>",
            "",
            "Looking:",
            "  look (l) - Look around",
            "  examine <target> - Examine an item, mob, or NPC",
            "  map - Show world map with your location",
            "",
            "Items:",
            "  inventory (i) - Show inventory",
            "  take <item> - Pick up an item",
            "  take all - Pick up all items in the room",
            "  drop <item> - Drop an item",
            "  equip (eq) <item> - Equip an item",
            "  unequip (uneq) <item> - Unequip an item",
            "  use <item> - Use a consumable item",
            "  sacrifice (sac) <item> - Sacrifice an item for 1 XP",
            "",
            "NPCs:",
            "  talk <npc> - Talk to an NPC",
            "  list - View merchant's wares",
            "  buy <item> - Buy an item from a merchant",
            "  sell <item> - Sell an item to a merchant",
            "",
            "Combat:",
            "  attack (a) <target> - Attack a target",
            "  flee (f) - Try to escape from combat",
            "  stats (st) - Show your character stats",
            "  godkill (gk/god) - Instantly defeat target (cheat)",
            "",
            "Other:",
            "  help - Show this help message",
            "  quit - Exit the game"
        ]
        return False, "\n".join(commands)

    def handle_combat_command(self, character_name: str, cmd: str, args: List[str]) -> Tuple[bool, str]:
        """Handle commands during combat."""
        character = self.character_manager.get_character(character_name)
        if not character:
            return False, "Character not found."

        # For stats command, we need to handle the tuple return value differently
        if cmd in ["stats", "st"]:
            return self.cmd_stats(character_name, args)

        combat_commands = {
            "attack": lambda: self.combat_manager.process_combat_turn(character_name, character["combat_state"]["target"]),
            "a": lambda: self.combat_manager.process_combat_turn(character_name, character["combat_state"]["target"]),
            "flee": lambda: self.combat_manager.flee(character_name),
            "f": lambda: self.combat_manager.flee(character_name),
            "godkill": lambda: self.combat_manager.instant_kill(character_name, character["combat_state"]["target"]),
            "gk": lambda: self.combat_manager.instant_kill(character_name, character["combat_state"]["target"]),
            "god": lambda: self.combat_manager.instant_kill(character_name, character["combat_state"]["target"])
        }

        if cmd in combat_commands:
            result = combat_commands[cmd]()
            # Force refresh character data after combat command
            character = self.character_manager.get_character(character_name)
            # If combat ended, force save the state
            if not character["combat_state"]["in_combat"]:
                # Double-check combat state is cleared
                character["combat_state"]["target"] = None
                character["combat_state"]["turns_in_combat"] = 0
                self.character_manager.save_character()
            return False, result
        else:
            return False, "In combat, you can only: attack (a), flee (f), check stats (st), or godkill (gk/god)"

    def _get_merchant_in_room(self) -> Optional[Dict]:
        """Helper method to get merchant NPC in current room."""
        current_room = self.character_manager.get_current_room()
        npcs = self.world_manager.get_room_npcs(current_room)
        
        for npc_id in npcs:
            npc = self.data_manager.get_npc(npc_id)
            if npc and "merchant_data" in npc:
                return npc
        return None

    def _format_price(self, price: int) -> str:
        """Helper method to format prices."""
        return f"{price} coins"

    def cmd_use(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Handle using items like potions."""
        if not args:
            return False, "Use what?"

        item_name = " ".join(args).lower()
        character = self.character_manager.get_character(character_name)
        if not character:
            return False, "Character not found."

        # Find the item in inventory
        inventory = character.get("inventory", [])
        for item_id in inventory:
            item = self.data_manager.get_item(item_id)
            if not item:
                continue

            # Make item matching more flexible by checking if search terms are in the item name
            item_desc = item["short_desc"].lower()
            # Remove common articles for better matching
            search_terms = item_name.replace("a ", "").replace("an ", "").replace("the ", "").split()
            
            # Check if all search terms are in the item description
            if all(term in item_desc for term in search_terms):
                # Check if item is usable
                if "use_effect" not in item:
                    return False, f"You can't use the {item['short_desc']}."

                effect = item["use_effect"]
                if effect["type"] == "heal":
                    # Handle healing items
                    heal_amount = effect["amount"]
                    old_hp = character["stats"]["current_hp"]
                    character["stats"]["current_hp"] = min(
                        character["stats"]["current_hp"] + heal_amount,
                        character["stats"]["max_hp"]
                    )
                    actual_heal = character["stats"]["current_hp"] - old_hp
                    
                    # Remove the item after use
                    self.character_manager.remove_from_inventory(item_id)
                    self.character_manager.save_character()
                    
                    return False, f"You use {item['short_desc']} and recover {actual_heal} HP."
                
                # Add other effect types here (buffs, etc)
                return False, f"This item's effect is not implemented yet."

        return False, "You don't have that item."

    def cmd_equip(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Handle equipping items."""
        if not args:
            return False, "Equip what?"

        item_name = " ".join(args).lower()
        character = self.character_manager.get_character(character_name)
        if not character:
            return False, "Character not found."

        # Find the item in inventory
        inventory = character.get("inventory", [])
        for item_id in inventory:
            item = self.data_manager.get_item(item_id)
            if not item:
                continue

            # Make item matching more flexible
            item_desc = item["short_desc"].lower()
            search_terms = item_name.replace("a ", "").replace("an ", "").replace("the ", "").split()
            
            if all(term in item_desc for term in search_terms):
                # Check if item is equippable
                if "type" not in item["properties"]:
                    return False, f"You can't equip the {item['short_desc']}."

                item_type = item["properties"]["type"]
                equipment_slot = None
                
                # Determine equipment slot based on item type
                if item_type == "weapon":
                    equipment_slot = "weapon"
                elif item_type == "armor":
                    equipment_slot = "armor"
                elif item_type == "ring":
                    equipment_slot = "ring"
                elif item_type == "amulet":
                    equipment_slot = "amulet"
                else:
                    return False, f"You can't equip the {item['short_desc']}."

                # Unequip current item in that slot if any
                current_equipped = character["equipment"][equipment_slot]
                if current_equipped:
                    old_item = self.data_manager.get_item(current_equipped)
                    character["inventory"].append(current_equipped)
                    # Remove old item's stats
                    self._update_stats_from_equipment(character, old_item, remove=True)

                # Equip new item
                character["equipment"][equipment_slot] = item_id
                character["inventory"].remove(item_id)
                # Add new item's stats
                self._update_stats_from_equipment(character, item)
                
                self.character_manager.save_character()
                return False, f"You equip {item['short_desc']}."

        return False, "You don't have that item."

    def cmd_unequip(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Handle unequipping items."""
        if not args:
            return False, "Unequip what?"

        item_name = " ".join(args).lower()
        character = self.character_manager.get_character(character_name)
        if not character:
            return False, "Character not found."

        # Check all equipment slots
        for slot, item_id in character["equipment"].items():
            if not item_id:
                continue
                
            item = self.data_manager.get_item(item_id)
            if not item:
                continue

            item_desc = item["short_desc"].lower()
            search_terms = item_name.replace("a ", "").replace("an ", "").replace("the ", "").split()
            
            if all(term in item_desc for term in search_terms):
                # Move item to inventory
                character["inventory"].append(item_id)
                character["equipment"][slot] = None
                # Remove item's stats
                self._update_stats_from_equipment(character, item, remove=True)
                
                self.character_manager.save_character()
                return False, f"You unequip {item['short_desc']}."

        return False, "You don't have that equipped."

    def _update_stats_from_equipment(self, character: Dict, item: Dict, remove: bool = False) -> None:
        """Update character stats based on equipment."""
        multiplier = -1 if remove else 1  # Subtract stats if removing item
        
        if "properties" not in item:
            return
            
        props = item["properties"]
        
        # Update attack if weapon
        if "damage" in props:
            character["stats"]["attack"] = character["base_stats"]["attack"] + (props["damage"] * multiplier)
            
        # Update defense if armor
        if "defense" in props:
            character["stats"]["defense"] = character["base_stats"]["defense"] + (props["defense"] * multiplier)
            
        # Could add more stat modifications here (HP, magic, etc)

    def cmd_examine(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Handle examining items, mobs, or NPCs."""
        if not args:
            return False, "Examine what?"

        target_name = " ".join(args).lower()
        # Remove common articles for better matching
        search_terms = target_name.replace("a ", "").replace("an ", "").replace("the ", "").split()
        
        # Check inventory first
        inventory = self.character_manager.get_inventory()
        for item_id in inventory:
            item = self.data_manager.get_item(item_id)
            if not item:
                continue
            item_desc = item["short_desc"].lower()
            if all(term in item_desc for term in search_terms):
                # Format item properties
                props = []
                for key, value in item["properties"].items():
                    if key == "type":
                        props.append(f"Type: {value}")
                    elif key == "damage":
                        props.append(f"Damage: {value}")
                    elif key == "defense":
                        props.append(f"Defense: {value}")
                    elif key == "value":
                        props.append(f"Value: {value} coins")
                    elif key == "magic" and value:
                        props.append("Magical")
                
                properties = "\n".join(props)
                return False, f"{item['long_desc']}\n\n{properties}"

        # Check room items
        current_room = self.character_manager.get_current_room()
        room_items = self.world_manager.get_room_items(current_room)
        for item_id in room_items:
            item = self.data_manager.get_item(item_id)
            if not item:
                continue
            item_desc = item["short_desc"].lower()
            if all(term in item_desc for term in search_terms):
                # Format item properties (same as inventory items)
                props = []
                for key, value in item["properties"].items():
                    if key == "type":
                        props.append(f"Type: {value}")
                    elif key == "damage":
                        props.append(f"Damage: {value}")
                    elif key == "defense":
                        props.append(f"Defense: {value}")
                    elif key == "value":
                        props.append(f"Value: {value} coins")
                    elif key == "magic" and value:
                        props.append("Magical")
                
                properties = "\n".join(props)
                return False, f"{item['long_desc']}\n\n{properties}"

        # Check NPCs in room
        npc = self.world_manager.get_npc_in_room(current_room, target_name)
        if npc:
            return False, npc["long_desc"]

        # Check for mobs in room
        mobs_data = self.data_manager.load_json("mobs.json")
        for mob in mobs_data.get("mobs", []):
            if current_room in mob.get("spawn_areas", []):
                # Check both name and short description with flexible matching
                mob_name = mob["name"].lower()
                mob_desc = mob["short_desc"].lower()
                if (all(term in mob_name for term in search_terms) or 
                    all(term in mob_desc for term in search_terms)):
                    # Format mob stats
                    stats = mob["stats"]
                    mob_info = [
                        f"{mob['name']}",
                        mob["long_desc"],
                        f"\nLevel: {mob['level']}",
                        f"HP: {stats['max_hp']}",
                        f"Attack: {stats['attack']}",
                        f"Defense: {stats['defense']}",
                        f"XP Value: {stats['xp_value']}"
                    ]
                    return False, "\n".join(mob_info)

        return False, "You don't see that here."

    def cmd_map(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Show a 2D ASCII map of the current world with player's location."""
        character = self.character_manager.get_character(character_name)
        if not character:
            return False, "Character not found."

        current_room = character["current_room"]
        current_world = self.world_manager.current_world
        rooms = self.world_manager.loaded_worlds[current_world].get("rooms", [])

        # Create a grid to hold room positions
        grid = {}
        room_positions = {}
        
        # Start with the current room at (0,0)
        to_visit = [(current_room, 0, 0)]  # (room_id, x, y)
        visited = set()

        # Map directions to coordinate changes
        dir_to_coords = {
            "north": (0, -1),
            "south": (0, 1),
            "east": (1, 0),
            "west": (-1, 0),
            "up": (0, -1),  # Treat up as north for 2D representation
            "down": (0, 1)  # Treat down as south for 2D representation
        }

        # First pass: Assign coordinates to rooms
        while to_visit:
            room_id, x, y = to_visit.pop(0)
            if room_id in visited:
                continue

            visited.add(room_id)
            room_positions[room_id] = (x, y)
            grid[(x, y)] = room_id

            # Find the room data
            room = None
            for r in rooms:
                if r["id"] == room_id:
                    room = r
                    break

            if not room:
                continue

            # Add connected rooms to visit
            for direction, target in room.get("exits", {}).items():
                if isinstance(target, dict):  # Skip portal exits
                    continue
                if direction in dir_to_coords:
                    dx, dy = dir_to_coords[direction]
                    new_x, new_y = x + dx, y + dy
                    if (new_x, new_y) not in grid:
                        to_visit.append((target, new_x, new_y))

        # If no rooms were mapped, return an error
        if not grid:
            return False, f"Could not generate map - room {current_room} not found in world {current_world}."

        # Find grid boundaries
        min_x = min(x for x, y in grid.keys())
        max_x = max(x for x, y in grid.keys())
        min_y = min(y for x, y in grid.keys())
        max_y = max(y for x, y in grid.keys())

        # Build the ASCII map
        map_lines = []
        map_lines.append(f"\nWorld Map: {current_world.title()}")
        map_lines.append("=" * 40)
        map_lines.append("Legend: * = You are here")
        map_lines.append("       → ↑ ↓ = Regular connections")
        map_lines.append("       ⊗ = Portal to another realm")
        map_lines.append("")

        # Create the map with connections
        for y in range(min_y, max_y + 1):
            # Room ID line
            room_line = ""
            connection_line = ""
            for x in range(min_x, max_x + 1):
                if (x, y) in grid:
                    room_id = grid[(x, y)]
                    marker = "*" if room_id == current_room else " "
                    room_line += f"{marker}{room_id:<20}"
                    
                    # Add horizontal connections
                    room = next((r for r in rooms if r["id"] == room_id), None)
                    if room and "east" in room.get("exits", {}):
                        if (x + 1, y) in grid:
                            connection_line += "----" + "─" * 16
                        else:
                            connection_line += " " * 20
                    else:
                        connection_line += " " * 20
                else:
                    room_line += " " * 20
                    connection_line += " " * 20

            map_lines.append(room_line)
            if y < max_y:
                # Add vertical connections
                vertical_line = ""
                for x in range(min_x, max_x + 1):
                    if (x, y) in grid:
                        room_id = grid[(x, y)]
                        room = next((r for r in rooms if r["id"] == room_id), None)
                        if room and ("south" in room.get("exits", {}) or "down" in room.get("exits", {})):
                            if (x, y + 1) in grid:
                                vertical_line += "     |" + " " * 14
                            else:
                                vertical_line += " " * 20
                        else:
                            vertical_line += " " * 20
                    else:
                        vertical_line += " " * 20
                map_lines.append(connection_line)
                map_lines.append(vertical_line)

        return False, "\n".join(map_lines)

    def cmd_sacrifice(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Handle sacrificing items for XP."""
        if not args:
            return False, "Sacrifice what?"

        item_name = " ".join(args).lower()
        character = self.character_manager.get_character(character_name)
        if not character:
            return False, "Character not found."

        # Find all matching items in inventory
        inventory = character.get("inventory", [])
        matching_items = []
        
        for item_id in inventory:
            item = self.data_manager.get_item(item_id)
            if not item:
                continue

            # Make item matching more flexible
            item_desc = item["short_desc"].lower()
            search_terms = item_name.replace("a ", "").replace("an ", "").replace("the ", "").split()
            
            if all(term in item_desc for term in search_terms):
                matching_items.append((item_id, item))

        if not matching_items:
            return False, "You don't have that item."

        # Take the first matching item
        item_id, item = matching_items[0]
        
        # Remove the item from inventory
        if not self.character_manager.remove_from_inventory(item_id):
            return False, "Failed to sacrifice item."
        
        # Add 1 XP
        character["stats"]["xp"] += 1
        
        # Check if this XP gain triggers a level up
        while character["stats"]["xp"] >= character["stats"]["xp_to_next_level"]:
            self.character_manager.level_up(character)
            # Save character state
            self.character_manager.save_character()
            return False, f"You sacrifice {item['short_desc']} to the gods. (+1 XP)\nLevel up! You are now level {character['stats']['level']}!"

        self.character_manager.save_character()
        return False, f"You sacrifice {item['short_desc']} to the gods. (+1 XP)"

    def cmd_ask(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Handle the ask command."""
        if not args:
            return False, "Ask who about what?"

        # Split into NPC name and topic
        *npc_words, topic = args
        if not npc_words:
            return False, "Ask who?"
        if not topic:
            return False, "Ask about what?"

        npc_name = " ".join(npc_words)
        topic = topic.lower()

        # Get current room
        current_room = self.character_manager.get_current_room()
        if not current_room:
            return False, "Error: No current room"

        # Find NPC in room
        npc = self.world_manager.get_npc_in_room(current_room, npc_name)
        if not npc:
            return False, f"You don't see {npc_name} here."

        # Get NPC's dialogue
        dialogue = npc.get("dialogue", {})
        topics = dialogue.get("topics", {})
        if not topics:
            return False, f"{npc['name']} has nothing to say about that."

        # Find matching topic
        topic_id = None
        for tid, data in topics.items():
            if tid.lower() == topic:
                topic_id = tid
                break

        if not topic_id:
            return False, f"{npc['name']} has nothing to say about that."

        # Get the topic data
        topic_data = topics[topic_id]

        # Handle string-only topics
        if isinstance(topic_data, str):
            response = topic_data
            # Add topic to known topics
            self.character_manager.add_known_topic(npc["id"], topic_id)
            return False, f"{npc['name']} says: \"{response}\""

        # Handle dictionary topics
        if "requires_topic" in topic_data:
            known_topics = self.character_manager.get_known_topics(npc["id"])
            if topic_data["requires_topic"] not in known_topics:
                return False, f"{npc['name']} isn't ready to discuss that yet."

        # Get base response
        response = topic_data["response"]
        
        # Handle quest item requirements and effects
        if "item_requirement" in topic_data:
            inventory = self.character_manager.get_inventory()
            required_item = topic_data["item_requirement"]
            if required_item in inventory:
                # If item found, use alternate response if provided
                if "success_response" in topic_data:
                    response = topic_data["success_response"]
                    
                # Apply any effects defined for having the item
                if "effects" in topic_data:
                    effects = topic_data["effects"]
                    if "unlock_merchant" in effects and "merchant_data" in npc:
                        npc["merchant_data"]["unlocked"] = True
                    if "remove_item" in effects and effects["remove_item"]:
                        self.character_manager.remove_from_inventory(required_item)
                    if "add_item" in effects:
                        self.character_manager.add_to_inventory(effects["add_item"])
                    if "add_money" in effects:
                        self.character_manager.add_money(effects["add_money"])
                    if "unlock_topics" in effects:
                        for new_topic in effects["unlock_topics"]:
                            self.character_manager.add_known_topic(npc["id"], new_topic)

        # Add topic to known topics
        self.character_manager.add_known_topic(npc["id"], topic_id)

        # Handle special merchant unlock if this is a trade topic
        if topic_data.get("is_trade") and "merchant_data" in npc:
            npc["merchant_data"]["unlocked"] = True

        return False, f"{npc['name']} says: \"{response}\""

    def cmd_quit(self, character_name: str, args: List[str]) -> Tuple[bool, str]:
        """Handle the quit command."""
        return True, "Thanks for playing! Goodbye!"