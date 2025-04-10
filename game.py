import pygame
import random
import sys
import os
import time
from pygame.locals import *

class TileMatchingGame:
    def __init__(self, config=None):
        # Initialize pygame
        pygame.init()
        pygame.font.init()
        
        # Default configuration
        self.default_config = {
            "window_width": 1024,  # Increased window size to accommodate larger tiles
            "window_height": 768,
            "num_levels": 10,
            "level_duration": 180,  # 3 minutes per level
            "tile_types": 10,
            "grid_sizes": [
                (4, 4),    # Level 1: 4x4 grid
                (4, 5),    # Level 2: 4x5 grid
                (5, 6),    # Level 3: 5x6 grid
                (6, 6),    # Level 4: 6x6 grid
                (6, 7),    # Level 5: 6x7 grid
                (7, 8),    # Level 6: 7x8 grid
                (8, 8),    # Level 7: 8x8 grid
                (8, 9),    # Level 8: 8x9 grid
                (9, 10),   # Level 9: 9x10 grid
                (10, 10)   # Level 10: 10x10 grid
            ],
            "secret_texts": [
                "Level 1 secret text revealed!",
                "Level 2 secret text revealed!",
                "Level 3 secret text revealed!",
                "Level 4 secret text revealed!",
                "Level 5 secret text revealed!",
                "Level 6 secret text revealed!",
                "Level 7 secret text revealed!",
                "Level 8 secret text revealed!",
                "Level 9 secret text revealed!",
                "Final level completed! Congratulations!"
            ],
            "assets_folder": "assets",  # Folder where tile images are stored
            "background_color": (240, 240, 240),
            "text_color": (10, 10, 10),
            "highlight_color": (255, 215, 0)  # Gold color for highlighting
        }
        
        # Use provided config or default
        self.config = config if config else self.default_config
        
        # Set up the display
        self.width = self.config["window_width"]
        self.height = self.config["window_height"]
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("НАЙДИ ПАРУ")
        
        # Game state
        self.state = "start"  # "start", "playing", "level_completing", "level_complete", "game_over", "game_complete"
        self.current_level = 1
        self.score = 0
        self.time_left = self.config["level_duration"]
        self.start_time = 0
        self.revealed_texts = [""] * self.config["num_levels"]
        self.level_complete_delay = 2000  # 2 seconds delay before showing level complete screen
        self.level_complete_timer = 0
        
        # Load fonts
        self.title_font = pygame.font.SysFont('comicsansms', 40)
        self.normal_font = pygame.font.SysFont('Arial', 24)
        self.small_font = pygame.font.SysFont('Arial', 18)
        
        # Game grid
        self.grid = []
        self.selected_tiles = []
        
        # Load tile images
        self.load_tile_images()
    
    def load_tile_images(self):
        """Load image assets for tiles"""
        self.tile_images = []
        assets_folder = self.config["assets_folder"]
        
        # First check if assets folder exists
        if not os.path.exists(assets_folder):
            os.makedirs(assets_folder)
            print(f"Created assets folder at {os.path.abspath(assets_folder)}")
            print("Please add your tile images to this folder and restart the game.")
            print("Images should be named: tile0.png, tile1.png, ..., tile9.png")
        
        # Default size for tiles is now larger - we'll resize them in initialize_grid
        default_tile_size = 200  # Set this as a base size that will be adjusted later
        
        # Try to load images tile0.png through tile9.png (or however many are specified)
        for i in range(self.config["tile_types"]):
            image_path = os.path.join(assets_folder, f"tile{i}.png")
            try:
                image = pygame.image.load(image_path)
                # Just load the original image, we'll resize when creating the grid
                self.tile_images.append(image)
            except pygame.error:
                # If image not found, create a colored rectangle as fallback
                color = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
                         (255, 0, 255), (0, 255, 255), (128, 0, 0), (0, 128, 0),
                         (0, 0, 128), (128, 128, 0)][i % 10]
                surface = pygame.Surface((default_tile_size, default_tile_size))
                surface.fill(color)
                # Draw the index number on the surface
                text = self.normal_font.render(str(i), True, (255, 255, 255))
                text_rect = text.get_rect(center=(default_tile_size//2, default_tile_size//2))
                surface.blit(text, text_rect)
                self.tile_images.append(surface)
                print(f"Warning: Could not load {image_path}, using fallback colored tile")
        
        # Create back-of-tile image (used when tile is face down)
        self.tile_back = pygame.Surface((default_tile_size, default_tile_size))
        self.tile_back.fill((115, 79, 150))  # Purple color
        inner_rect = pygame.Rect(10, 10, default_tile_size-20, default_tile_size-20)
        pygame.draw.rect(self.tile_back, (0, 0, 0), inner_rect, 5)  # Border
    
    def initialize_grid(self):
        """Create a grid of tiles for the current level with optimized tile sizes"""
        cols, rows = self.config["grid_sizes"][self.current_level - 1]
        
        # Calculate available space - use more of the screen
        ui_height = 100  # Space for UI elements (top and bottom)
        game_area_width = self.width - 40  # 20px padding on each side
        game_area_height = self.height - ui_height  # Less space for UI
        
        # Calculate tile size to maximize usage of available space
        # Leave a small gap between tiles
        tile_width = game_area_width // cols - 10
        tile_height = game_area_height // rows - 10
        tile_size = min(tile_width, tile_height)
        
        # Ensure tiles are reasonably sized
        tile_size = max(60, min(tile_size, 300))  # Between 60 and 300px
        
        # Resize tile images for this level
        scaled_tile_images = []
        for image in self.tile_images:
            scaled_image = pygame.transform.scale(image, (tile_size, tile_size))
            scaled_tile_images.append(scaled_image)
        
        # Save the scaled images for this level
        self.scaled_tile_images = scaled_tile_images
        
        # Also scale the tile back image
        self.scaled_tile_back = pygame.transform.scale(self.tile_back, (tile_size, tile_size))
        
        # Calculate grid offset to center it
        grid_width = cols * (tile_size + 10) - 10  # Account for gaps between tiles
        grid_height = rows * (tile_size + 10) - 10
        self.grid_offset_x = (self.width - grid_width) // 2
        self.grid_offset_y = (self.height - grid_height) // 2
        
        # Create pairs of tiles
        tile_values = []
        total_tiles = rows * cols
        pairs_needed = total_tiles // 2
        
        for i in range(pairs_needed):
            tile_type = i % self.config["tile_types"]
            tile_values.append(tile_type)
            tile_values.append(tile_type)
        
        # Shuffle tiles
        random.shuffle(tile_values)
        
        # Create grid
        self.grid = []
        for r in range(rows):
            row = []
            for c in range(cols):
                index = r * cols + c
                if index < len(tile_values):
                    # Position tiles with gaps between them
                    row.append({
                        "type": tile_values[index],
                        "revealed": False,
                        "matched": False,
                        "rect": pygame.Rect(
                            self.grid_offset_x + c * (tile_size + 10), 
                            self.grid_offset_y + r * (tile_size + 10),
                            tile_size, tile_size
                        )
                    })
                else:
                    row.append(None)  # Empty space
            self.grid.append(row)
    
    def handle_click(self, pos):
        """Handle mouse click on the grid"""
        if self.state != "playing":
            return
        
        # Check if a tile was clicked
        for r in range(len(self.grid)):
            for c in range(len(self.grid[r])):
                tile = self.grid[r][c]
                if tile and tile["rect"].collidepoint(pos):
                    if not tile["matched"] and not tile["revealed"]:
                        # Reveal the tile
                        tile["revealed"] = True
                        self.selected_tiles.append((r, c))
                        
                        # If we've selected 2 tiles, check for a match
                        if len(self.selected_tiles) == 2:
                            r1, c1 = self.selected_tiles[0]
                            r2, c2 = self.selected_tiles[1]
                            tile1 = self.grid[r1][c1]
                            tile2 = self.grid[r2][c2]
                            
                            if tile1["type"] == tile2["type"]:
                                # Match!
                                tile1["matched"] = True
                                tile2["matched"] = True
                                self.score += 10 * self.current_level
                                self.selected_tiles = []
                                
                                # Check if level complete
                                if self.is_level_complete():
                                    # Set state to level_completing and start the timer
                                    self.state = "level_completing"
                                    self.level_complete_timer = pygame.time.get_ticks()
                                    self.revealed_texts[self.current_level - 1] = self.config["secret_texts"][self.current_level - 1]
                            else:
                                # No match, hide tiles after a delay
                                pygame.time.set_timer(USEREVENT + 1, 1000)  # 1 second delay
    
    def is_level_complete(self):
        """Check if all tiles are matched"""
        for row in self.grid:
            for tile in row:
                if tile and not tile["matched"]:
                    return False
        return True
    
    def hide_selected_tiles(self):
        """Hide the currently selected tiles"""
        for r, c in self.selected_tiles:
            self.grid[r][c]["revealed"] = False
        self.selected_tiles = []
    
    def draw_grid(self):
        """Draw the game grid on the screen"""
        for row in self.grid:
            for tile in row:
                if tile:
                    if tile["matched"]:
                        # Draw matched tile (with gold highlight)
                        pygame.draw.rect(self.screen, self.config["highlight_color"], 
                                        tile["rect"].inflate(10, 10), 3)
                        self.screen.blit(self.scaled_tile_images[tile["type"]], tile["rect"])
                    elif tile["revealed"]:
                        # Draw revealed tile
                        self.screen.blit(self.scaled_tile_images[tile["type"]], tile["rect"])
                    else:
                        # Draw face-down tile
                        self.screen.blit(self.scaled_tile_back, tile["rect"])
    
    def draw_text_centered(self, text, font, color, y_offset):
        """Draw text centered horizontally on the screen"""
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(self.width // 2, y_offset))
        self.screen.blit(text_surface, text_rect)
    
    def draw_start_screen(self):
        """Draw the start screen"""
        self.screen.fill(self.config["background_color"])
        self.draw_text_centered('Игра НАЙДИ ПАРУ', self.title_font, self.config["text_color"], 100)
        self.draw_text_centered("Соотнеси пары картинок, чтобы найти все секретики", 
                               self.normal_font, self.config["text_color"], 150)
        self.draw_text_centered("Нажми ПРОБЕЛ, чтобы начать", self.normal_font, self.config["text_color"], 250)
    
    def draw_game_screen(self):
        """Draw the main game screen"""
        self.screen.fill(self.config["background_color"])
        
        # Draw HUD (Heads Up Display)
        level_text = f"Level: {self.current_level}/{self.config['num_levels']}"
        score_text = f"Score: {self.score}"
        time_text = f"Time: {self.format_time(self.time_left)}"
        
        level_surface = self.normal_font.render(level_text, True, self.config["text_color"])
        score_surface = self.normal_font.render(score_text, True, self.config["text_color"])
        time_surface = self.normal_font.render(time_text, True, self.config["text_color"])
        
        self.screen.blit(level_surface, (20, 20))
        self.screen.blit(score_surface, (self.width // 2 - score_surface.get_width() // 2, 20))
        self.screen.blit(time_surface, (self.width - 20 - time_surface.get_width(), 20))
        
        # Draw the grid
        self.draw_grid()
    
    def draw_level_complete_screen(self):
        """Draw the level complete screen"""
        self.screen.fill(self.config["background_color"])
        self.draw_text_centered(f"Уровень {self.current_level} пройден!", self.title_font, self.config["text_color"], 100)
        self.draw_text_centered("Ты узнала секретик:", self.normal_font, self.config["text_color"], 170)
        self.draw_text_centered(self.revealed_texts[self.current_level - 1], 
                               self.normal_font, (0, 100, 0), 220)  # Dark green text
        
        if self.current_level < self.config["num_levels"]:
            self.draw_text_centered("Нажми ПРОБЕЛ для следующего уровня", self.normal_font, self.config["text_color"], 300)
        else:
            self.draw_text_centered("Нажми ПРОБЕЛ чтобы прочитать все секретики", self.normal_font, self.config["text_color"], 300)
    
    def draw_game_over_screen(self):
        """Draw the game over screen"""
        self.screen.fill(self.config["background_color"])
        self.draw_text_centered("Game Over!", self.title_font, (200, 0, 0), 100)  # Red text
        self.draw_text_centered("You ran out of time", self.normal_font, self.config["text_color"], 170)
        self.draw_text_centered(f"Final Score: {self.score}", self.normal_font, self.config["text_color"], 220)
        self.draw_text_centered("Press SPACE to play again", self.normal_font, self.config["text_color"], 300)
    
    def draw_game_complete_screen(self):
        """Draw the game complete screen with all revealed messages"""
        self.screen.fill(self.config["background_color"])
        self.draw_text_centered("Поздравляю!", self.title_font, (0, 100, 0), 60)  # Dark green
        self.draw_text_centered("Ты прошла все уровни!", self.normal_font, self.config["text_color"], 110)
        
        # Display all revealed messages
        y_offset = 160
        self.draw_text_centered("ВСЕ СЕКРЕТИКИ:", self.normal_font, self.config["text_color"], y_offset)
        y_offset += 40
        
        for i, text in enumerate(self.revealed_texts):
            message_text = f"Level {i+1}: {text}"
            self.draw_text_centered(message_text, self.small_font, self.config["text_color"], y_offset)
            y_offset += 30
        
        self.draw_text_centered("Нажми ПРОБЕЛ чтобы начать заново", self.normal_font, self.config["text_color"], 550)
    
    def format_time(self, seconds):
        """Format time as MM:SS"""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def next_level(self):
        """Move to the next level"""
        self.current_level += 1
        self.time_left = self.config["level_duration"]
        self.start_time = pygame.time.get_ticks()
        self.selected_tiles = []
        self.initialize_grid()
        self.state = "playing"
    
    def reset_game(self):
        """Reset the game to start a new session"""
        self.current_level = 1
        self.score = 0
        self.time_left = self.config["level_duration"]
        self.revealed_texts = [""] * self.config["num_levels"]
        self.selected_tiles = []
        self.state = "playing"
        self.start_time = pygame.time.get_ticks()
        self.initialize_grid()
    
    def update_time(self):
        """Update the time remaining"""
        if self.state == "playing":
            elapsed = (pygame.time.get_ticks() - self.start_time) // 1000
            self.time_left = max(0, self.config["level_duration"] - elapsed)
            
            if self.time_left == 0:
                self.state = "game_over"
        
        # Check if level_completing state should transition to level_complete
        elif self.state == "level_completing":
            current_time = pygame.time.get_ticks()
            if current_time - self.level_complete_timer >= self.level_complete_delay:
                self.state = "level_complete"
    
    def run(self):
        """Main game loop"""
        clock = pygame.time.Clock()
        running = True
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                    
                    # Cheat key: CTRL+N to skip level
                    if event.key == K_n and pygame.key.get_mods() & KMOD_CTRL:
                        if self.state == "playing":
                            # Skip to level completing
                            self.state = "level_completing"
                            self.level_complete_timer = pygame.time.get_ticks()
                            self.revealed_texts[self.current_level - 1] = self.config["secret_texts"][self.current_level - 1]
                    
                    if event.key == K_SPACE:
                        if self.state == "start":
                            self.reset_game()
                        elif self.state == "level_complete":
                            if self.current_level < self.config["num_levels"]:
                                self.next_level()
                            else:
                                self.state = "game_complete"
                        elif self.state == "game_over" or self.state == "game_complete":
                            self.state = "start"
                
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        self.handle_click(event.pos)
                
                elif event.type == USEREVENT + 1:  # Custom timer for hiding unmatched tiles
                    pygame.time.set_timer(USEREVENT + 1, 0)  # Cancel the timer
                    self.hide_selected_tiles()
            
            # Update game state
            self.update_time()
            
            # Draw the game based on current state
            if self.state == "start":
                self.draw_start_screen()
            elif self.state == "playing":
                self.draw_game_screen()
            elif self.state == "level_completing":
                # During the delay, keep showing the game board with all tiles matched
                self.draw_game_screen()
                # Optionally add some visual effect to indicate completion
                completion_text = "Уровень пройден!"
                text_surface = self.title_font.render(completion_text, True, (0, 100, 0))
                text_rect = text_surface.get_rect(center=(self.width // 2, self.height // 2))
                # Add a semi-transparent background behind the text
                bg_rect = text_rect.inflate(40, 40)
                bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                bg_surface.fill((255, 255, 255, 180))  # White with 70% opacity
                self.screen.blit(bg_surface, bg_rect)
                self.screen.blit(text_surface, text_rect)
            elif self.state == "level_complete":
                self.draw_level_complete_screen()
            elif self.state == "game_over":
                self.draw_game_over_screen()
            elif self.state == "game_complete":
                self.draw_game_complete_screen()
            
            # Update the display
            pygame.display.flip()
            clock.tick(60)  # 60 FPS
        
        pygame.quit()
        sys.exit()

def load_config_from_file(config_file):
    """Load game configuration from a file"""
    try:
        import json
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file: {e}")
        return None

def main():
    # Check for command line arguments
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
        config = load_config_from_file(config_file)
    else:
        config = load_config_from_file('config.json')  # Use default config
    
    # Initialize and run the game
    game = TileMatchingGame(config)
    game.run()

if __name__ == "__main__":
    main()