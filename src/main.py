"""Main game module."""

import os
import sys
import asyncio
from typing import Optional, Tuple
from dotenv import load_dotenv
from .data_manager import DataManager
from .character_manager import CharacterManager
from .world_manager import WorldManager
from .combat_manager import CombatManager
from .commands import CommandHandler
from .ai_helper import GeminiHelper

# Load environment variables from .env file
load_dotenv()

class Game:
    """Main game class."""
    
    def __init__(self):
        """Initialize the game."""
        self.data_manager = DataManager()
        self.character_manager = CharacterManager(self.data_manager)
        self.world_manager = WorldManager(self.data_manager)
        self.combat_manager = CombatManager(self.data_manager, self.world_manager)
        self.command_handler = CommandHandler(
            self.data_manager,
            self.character_manager,
            self.world_manager
        )
        self.current_character = None
        self.running = True
        
        # Set up cross-references
        self.character_manager.set_world_manager(self.world_manager)
        self.data_manager.character_manager = self.character_manager
        self.command_handler.combat_manager = self.combat_manager
        self.combat_manager.set_character_manager(self.character_manager)
        
        # Initialize AI helper
        print("\nInitializing Gemini AI...", end="", flush=True)
        try:
            self.ai_helper = GeminiHelper()
            self.world_manager.set_ai_helper(self.ai_helper)
            print("\033[32m [OK]\033[0m")  # Green OK
        except Exception as e:
            print("\033[31m [FAILED]\033[0m")  # Red FAILED
            print(f"Warning: AI features not available - {e}")
            self.ai_helper = None
            
    def show_welcome_banner(self):
        """Display the welcome banner with ASCII art."""
        banner = """
███╗   ███╗██╗   ██╗██████╗ ███████╗██╗    ██╗ █████╗ 
████╗ ████║██║   ██║██╔══██╗██╔════╝██║    ██║██╔══██╗
██╔████╔██║██║   ██║██║  ██║█████╗  ██║ █╗ ██║███████║
██║ ██╔╝██║██║   ██║██║  ██║██╔══╝  ██║███╗██║██╔══██║
██║ ╚═╝ ██║╚██████╔╝██████╔╝███████╗╚███╔███╔╝██║  ██║
╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝
                                                        
     ⚔️  A Nostalgic Text Adventure from Saru2.com  🏰
══════════════════���═════════════════════════════════════
        This is a solo player MUD, so probably
           should have been called SUD, but...
════════════════════════════════════════════════════════
"""
        print(banner)
            
    async def process_command(self, command: str) -> Tuple[bool, str]:
        """Process a command and return the result."""
        if not command:
            return False, ""
            
        try:
            # Use the command handler's handle_command method and await it
            quit_game, response = await self.command_handler.handle_command(self.current_character, command)
            return quit_game, response
            
        except Exception as e:
            return False, f"Error executing command: {e}"

    async def start(self):
        """Start the game."""
        while True:
            self.show_welcome_banner()
            print("\nMain Menu:")
            print("1. Play Game")
            print("2. Content Editors")
            print("3. Exit")
            
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                await self.play_game()
            elif choice == "2":
                self.content_editors()
            elif choice == "3":
                print("\nThanks for playing! Goodbye!")
                break
            else:
                print("\nInvalid choice. Please try again.")

    def content_editors(self):
        """Show content editors menu."""
        while True:
            print("\nContent Editors")
            print("=" * 40)
            print("1. Item Editor")
            print("2. NPC Editor")
            print("3. World Editor")
            print("4. Mob Editor")
            print("5. Back to Main Menu")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == "1":
                self._run_editor("item_editor.py")
            elif choice == "2":
                self._run_editor("npc_editor.py")
            elif choice == "3":
                self._run_editor("world_editor.py")
            elif choice == "4":
                self._run_editor("mob_editor.py")
            elif choice == "5":
                break
            else:
                print("Invalid choice. Please try again.")

    def _run_editor(self, editor_file: str):
        """Run a specific editor tool."""
        # Get the absolute path of the current script
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        editor_path = os.path.join(current_dir, "tools", editor_file)
        
        if not os.path.exists(editor_path):
            print(f"\nError: Editor tool not found at {editor_path}")
            return
        
        print(f"\nLaunching {editor_file}...")
        print("=" * 40)
        
        # Store current directory
        original_dir = os.getcwd()
        
        try:
            # Change to the project root directory
            os.chdir(current_dir)
            
            # Run the editor
            if sys.platform.startswith('win'):
                os.system(f"python tools\\{editor_file}")
            else:
                os.system(f"python tools/{editor_file}")
        finally:
            # Restore original directory
            os.chdir(original_dir)
        
        input("\nPress Enter to continue...")

    def _get_player_choice(self) -> str:
        """Get the player's choice for character creation/loading."""
        print("\nWhat would you like to do?")
        print("1. Create a new character")
        print("2. Load existing character")
        print("3. Delete character")
        print("4. Back to main menu")
        return input("Enter your choice (1-4): ").strip()

    def _create_character(self) -> None:
        """Handle character creation."""
        name = input("\nEnter your character's name: ").strip()
        if not name:
            return

        # Show available classes
        print("\nAvailable Classes:")
        classes = self.character_manager.get_available_classes()
        for i, class_data in enumerate(classes, 1):
            print(f"{i}. {class_data['name']}")
            print(f"   {class_data['description']}")
            print(f"   Base Stats: HP +{class_data['base_stats']['hp_bonus']}, " +
                  f"Attack +{class_data['base_stats']['attack_bonus']}, " +
                  f"Defense +{class_data['base_stats']['defense_bonus']}")
            print()

        while True:
            try:
                choice = int(input("Choose your class (1-3): ").strip())
                if 1 <= choice <= len(classes):
                    class_id = classes[choice - 1]["id"]
                    self.character_manager.create_character(name, class_id)
                    self.current_character = name
                    break
                else:
                    print("Invalid choice.")
            except ValueError:
                print("Please enter a valid number.")

    def _load_character(self) -> None:
        """Handle character loading."""
        characters = self.data_manager.list_characters()
        if not characters:
            print("\nNo existing characters found.")
            return

        print("\nExisting characters:")
        for i, name in enumerate(characters, 1):
            print(f"{i}. {name}")

        try:
            choice = int(input("Enter the number of your character: ").strip())
            if 1 <= choice <= len(characters):
                self.current_character = characters[choice - 1]
                self.character_manager.load_character(self.current_character)
            else:
                print("Invalid choice.")
        except ValueError:
            print("Please enter a valid number.")

    def _delete_character(self) -> None:
        """Handle character deletion."""
        characters = self.data_manager.list_characters()
        if not characters:
            print("\nNo existing characters found.")
            return

        print("\nExisting characters:")
        for i, name in enumerate(characters, 1):
            print(f"{i}. {name}")

        try:
            choice = int(input("Enter the number of character to delete (0 to cancel): ").strip())
            if choice == 0:
                return
            if 1 <= choice <= len(characters):
                name = characters[choice - 1]
                confirm = input(f"Are you sure you want to delete '{name}'? (yes/no): ").strip().lower()
                if confirm == "yes":
                    if self.data_manager.delete_character(name):
                        print(f"\nCharacter '{name}' has been deleted.")
                    else:
                        print("\nFailed to delete character.")
            else:
                print("Invalid choice.")
        except ValueError:
            print("Please enter a valid number.")
            
    async def play_game(self):
        """Start the actual game."""
        # Character selection/creation menu
        while not self.current_character:
            choice = self._get_player_choice()
            if choice == "1":
                self._create_character()
            elif choice == "2":
                self._load_character()
            elif choice == "3":
                self._delete_character()
            elif choice == "4":
                return  # Return to main menu
            else:
                print("Invalid choice. Please try again.")

        # Initial look at the room (without welcome message)
        _, description = await self.process_command("look")
        print(f"\nWelcome, {self.current_character}!")  # Single welcome message
        print(f"\n{description}")
        
        # Main game loop
        self.running = True
        while self.running:
            try:
                command = input("\n> ").strip()
                if not command:
                    continue
                    
                quit_game, response = await self.process_command(command)
                if response:
                    print(f"\n{response}")
                if quit_game:
                    self.running = False
                    
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit the game.")
            except Exception as e:
                print(f"\nError: {e}")
                
        if self.ai_helper:
            await self.ai_helper.close_session()

def main():
    """Entry point for the game."""
    game = Game()
    asyncio.run(game.start())

if __name__ == "__main__":
    main() 