from typing import Optional
import os
import sys
from .data_manager import DataManager
from .character_manager import CharacterManager
from .world_manager import WorldManager
from .commands import CommandHandler

class Game:
    def __init__(self):
        self.data_manager = DataManager()
        self.character_manager = CharacterManager(self.data_manager)
        self.world_manager = WorldManager(self.data_manager)
        self.command_handler = CommandHandler(
            self.data_manager,
            self.character_manager,
            self.world_manager
        )
        
        # Set up cross-references
        self.character_manager.set_world_manager(self.world_manager)
        self.data_manager.character_manager = self.character_manager
        self.command_handler.combat_manager.set_character_manager(self.character_manager)

    def show_welcome_banner(self):
        """Display the welcome banner with ASCII art."""
        banner = """
███╗   ███╗██╗   ██╗██████╗ ███████╗██╗    ██╗ █████╗ 
████╗ ████║██║   ██║██╔══██╗██╔════╝██║    ██║██╔══██╗
██╔████╔██║██║   ██║██║  ██║█████╗  ██║ █╗ ██║███████║
██║╚██╔╝██║██║   ██║██║  ██║██╔══╝  ██║███╗██║██╔══██║
██║ ╚═╝ ██║╚██████╔╝██████╔╝███████╗╚███╔███╔╝██║  ██║
╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝
                                                       
     ⚔️  A Nostalgic Text Adventure from Saru2.com  🏰
════════════════════════════════════════════════════════
        This is a solo player MUD, so probably
           should have been called SUD, but...
════════════════════════════════════════════════════════
"""
        print(banner)

    def start(self):
        """Start the game."""
        while True:
            self.show_welcome_banner()
            print("\nMain Menu:")
            print("1. Play Game")
            print("2. Content Editors")
            print("3. Exit")
            
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                self.play_game()
            elif choice == "2":
                self.content_editors()
            elif choice == "3":
                print("\nThanks for playing! Goodbye!")
                break
            else:
                print("\nInvalid choice. Please try again.")

    def play_game(self):
        """Start the actual game."""
        # Character selection/creation menu
        while not self.character_manager.current_character:
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

        # Main game loop
        self._game_loop()

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
        if name:
            self.character_manager.create_character(name)

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
                self.character_manager.load_character(characters[choice - 1])
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

    def _game_loop(self) -> None:
        """Main game loop."""
        # Show initial room description
        current_room = self.character_manager.get_current_room()
        print("\n" + self.world_manager.get_room_description(current_room))

        while True:
            try:
                command = input("\n> ").strip()
                character_name = self.character_manager.current_character["name"]
                should_quit, message = self.command_handler.handle_command(character_name, command)
                
                if message:
                    print("\n" + message)
                
                if should_quit:
                    break

            except KeyboardInterrupt:
                print("\nUse 'quit' to exit the game.")
            except Exception as e:
                print(f"\nAn error occurred: {str(e)}")

def main():
    """Entry point for the game."""
    game = Game()
    try:
        game.start()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        print("Game terminated unexpectedly.")

if __name__ == "__main__":
    main() 