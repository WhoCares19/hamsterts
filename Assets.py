import pygame
import os
import sys
from collections import deque 

# --- Configuration for non-pathway assets ---
ASSET_FILES = {
    "grass": ("MainGrass.png", ""),  
    # "tree", "rock", "bonus" removed as requested
    "sand": ("sand.png", ""),
    "fence": ("Fence.png", "Assets"), 
    "flagpole": ("FlagPole.png", "Assets"),
    "alfalfa": ("alfalfa.png", "tiles"), 
    "cheese": ("cheese.png", "tiles"), 
}

# --- Configuration for Llama assets ---
LLAMA_BASE_FOLDER = os.path.join("Assets", "Llama")
LLAMA_EATING_SUBFOLDER = os.path.join(LLAMA_BASE_FOLDER, "Eating")

LLAMA_ANIMATION_INFO = {
    "walk": { 
        "north": [f"Llama_{i:02d}.png" for i in range(4)],  
        "west":  [f"Llama_{i:02d}.png" for i in range(4, 8)], 
        "south": [f"Llama_{i:02d}.png" for i in range(8, 12)], 
        "east":  [f"Llama_{i:02d}.png" for i in range(12, 16)], 
    },
    "eat": { 
        "north": [f"llama_eat__{i:02d}.png" for i in range(4)], 
        "west":  [f"llama_eat__{i:02d}.png" for i in range(4, 8)], 
        "south": [f"llama_eat__{i:02d}.png" for i in range(8, 12)], 
        "east":  [f"llama_eat__{i:02d}.png" for i in range(12, 16)], 
    }
}
LLAMA_SCALE_FACTOR = 1.5 

# --- Configuration for Windmill assets ---
WINDMILL_BASE_FOLDER = os.path.join("Assets", "Windmill")
WINDMILL_ANIMATION_FRAMES = 52 
WINDMILL_SCALE_FACTOR = 2.0 

# --- Configuration for Castle assets ---
CASTLE_FILENAME = "castlesprite.png"
CASTLE_FOLDER = "Assets" 
CASTLE_FRAMES = 9
CASTLE_ORIGINAL_SIZE = 500 
CASTLE_SCALE_FACTOR = 4.0 

# --- Configuration for McUncle assets ---
MCUNCLE_BASE_FOLDER = os.path.join("Hamsters", "Mcunle") 
MCUNCLE_FRAME_COUNT = 6 
MCUNCLE_SCALE_FACTOR = 1.0 

# --- Configuration for Hamsters (Bob, Dracula, TheHamster) ---
HAMSTER_ROOT_FOLDER = "Hamsters"
HAMSTER_SCALE_FACTOR = 1.0

HAMSTER_CONFIG = {
    "Bob": {
        "subfolder": "Bob",
        "type": "animated_spritesheets",
        "actions": {
             "idle":  {"file": "bob_idle.png",  "w": 160, "h": 160, "count": 6},
             "walk":  {"file": "bob_walk.png",  "w": 160, "h": 160, "count": 8},
             "sleep": {"file": "bob_sleep.png", "w": 160, "h": 160, "count": 8},
             "win":   {"file": "bob_win.png",   "w": 160, "h": 160, "count": 24}
        }
    },
    "Dracula": {
        "subfolder": "Dracula",
        "type": "animated_spritesheets",
        "actions": {
             "idle":  {"file": "dracula_idle.png",  "w": 160, "h": 160, "count": 6},
             "walk":  {"file": "dracula_walk.png",  "w": 160, "h": 160, "count": 8},
             "sleep": {"file": "dracula_sleep.png", "w": 160, "h": 160, "count": 8},
             "win":   {"file": "dracula_win.png",   "w": 160, "h": 160, "count": 24}
        }
    },
    "TheHamster": {
        "subfolder": "TheHamster",
        "type": "animated_spritesheets", 
        "actions": {
             "idle":  {"file": "thehamster_idle.png",  "w": 160, "h": 160, "count": 6},
             "walk":  {"file": "thehamster_walk.png",  "w": 160, "h": 160, "count": 8},
             "sleep": {"file": "thehamster_sleep.png", "w": 160, "h": 160, "count": 8},
             "win":   {"file": "thehamster_win.png",   "w": 160, "h": 160, "count": 24}
        }
    }
}

# --- Configuration for Projectiles ---
PROJECTILES_FOLDER = os.path.join("Hamsters", "Projectiles")
PROJECTILE_FILES = {
    "TheHamster": "TheHamsterBag.png",
    "McUncle": "Mcunle_whip.png",
    "Dracula": "DracTeeth.png",
    "Bob": "BobCakeSlice.png"
}
PROJECTILE_SCALE_FACTOR = 0.5 

# --- Configuration for Enemies ---
ENEMY_FOLDER = "Enemy" 
ENEMY_CONFIG = {
    "Piero": {
        "file": "piero_walk.png",
        "w": 90,
        "h": 90,
        "count": 4
    }
}
ENEMY_SCALE_FACTOR = 1.0


# Internal dictionaries to store loaded Pygame surfaces
_loaded_assets = {} 
_loaded_llama_sprites = {} 
_loaded_mcuncle_sprites = [] 
_loaded_hamsters = {} 
_loaded_projectiles = {} 
_loaded_enemies = {} 
_loaded_forest_sprites = [] # Stores list of tree images


# --- Helper: Remove Background (Flood Fill) ---
def _remove_white_background_floodfill(surface):
    surface = surface.convert_alpha()
    width, height = surface.get_size()
    pixels = pygame.PixelArray(surface)
    target_color = surface.map_rgb((255, 255, 255))
    queue = deque()
    corners = [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]
    for x, y in corners:
        if pixels[x, y] == target_color:
            queue.append((x, y))
    visited = set(queue)
    while queue:
        x, y = queue.popleft()
        pixels[x, y] = 0 
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                if (nx, ny) not in visited:
                    if pixels[nx, ny] == target_color:
                        visited.add((nx, ny))
                        queue.append((nx, ny))
    pixels.close() 
    return surface


# --- Helper: locate images in possible folders ---
def _find_image_file(name_with_extension, search_folders, subfolder_path=""):
    for folder in search_folders:
        if subfolder_path:
            path = os.path.join(folder, subfolder_path, name_with_extension)
        else:
            path = os.path.join(folder, name_with_extension)
        
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"Could not find '{name_with_extension}' in {search_folders} (or subfolder '{subfolder_path}')")


# --- Load non-pathway assets ---
def load_game_assets(tile_size, screen_width, screen_height, search_folders):
    global _loaded_assets
    # Load grass
    grass_filename, grass_subfolder = ASSET_FILES["grass"]
    try:
        path = _find_image_file(grass_filename, search_folders, grass_subfolder) 
        img = pygame.image.load(path).convert_alpha()
        _loaded_assets["grass"] = pygame.transform.scale(img, (screen_width, screen_height))
    except FileNotFoundError as e:
        print(f"CRITICAL ERROR in Assets.py: {e}")
        raise 
    except Exception as e:
        print(f"An unexpected error occurred loading '{grass_filename}': {e}")
        raise 

    # Load features
    feature_names = [name for name in ASSET_FILES if name != "grass"]
    for name in feature_names:
        asset_filename, asset_subfolder = ASSET_FILES[name]
        try:
            path = _find_image_file(asset_filename, search_folders, asset_subfolder) 
            img = pygame.image.load(path).convert_alpha()
            _loaded_assets[name] = pygame.transform.scale(img, (tile_size, tile_size))
        except FileNotFoundError as e:
            print(f"CRITICAL ERROR in Assets.py: {e}")
            raise 
        except Exception as e:
            print(f"An unexpected error occurred loading feature tile '{asset_filename}': {e}")
            raise 

# --- Load Forest assets ---
def load_forest_assets(search_folders):
    global _loaded_forest_sprites
    _loaded_forest_sprites = []
    
    forest_folder_path = None
    for folder in search_folders:
        potential_path = os.path.join(folder, "Forest")
        if os.path.exists(potential_path) and os.path.isdir(potential_path):
            forest_folder_path = potential_path
            break
            
    if not forest_folder_path:
        print("WARNING: Could not find 'Forest' folder in search paths. Forest generation will be skipped.")
        return

    print(f"DEBUG: Loading forest assets from {forest_folder_path}")
    count = 0
    for filename in os.listdir(forest_folder_path):
        if filename.lower().endswith(".png"):
            try:
                full_path = os.path.join(forest_folder_path, filename)
                img = pygame.image.load(full_path).convert_alpha()
                _loaded_forest_sprites.append(img)
                count += 1
            except Exception as e:
                print(f"Error loading forest tree '{filename}': {e}")
    
    print(f"DEBUG: Loaded {count} forest tree sprites.")


# --- Load Llama-specific assets ---
def load_llama_assets(tile_size, search_folders):
    global _loaded_llama_sprites
    _loaded_llama_sprites = {"walk": {}, "eat": {}} 
    llama_sprite_size = int(tile_size * LLAMA_SCALE_FACTOR)

    for action, directions_info in LLAMA_ANIMATION_INFO.items():
        for direction, filenames in directions_info.items():
            _loaded_llama_sprites[action][direction] = []
            current_subfolder = LLAMA_EATING_SUBFOLDER if action == "eat" else LLAMA_BASE_FOLDER
            for filename in filenames:
                try:
                    path = _find_image_file(filename, search_folders, current_subfolder)
                    img = pygame.image.load(path).convert_alpha()
                    _loaded_llama_sprites[action][direction].append(pygame.transform.scale(img, (llama_sprite_size, llama_sprite_size))) 
                except FileNotFoundError as e:
                    print(f"CRITICAL ERROR in Assets.py: {e}")
                    raise 
                except Exception as e:
                    print(f"An unexpected error occurred loading Llama asset '{filename}': {e}")
                    raise 

# --- Load Windmill-specific assets ---
def load_windmill_assets(tile_size, search_folders):
    global _loaded_assets
    _loaded_assets["windmill"] = [] 
    windmill_sprite_size = int(tile_size * WINDMILL_SCALE_FACTOR)

    for i in range(WINDMILL_ANIMATION_FRAMES):
        filename = f"Windmill__{i:02d}.png"
        try:
            path = _find_image_file(filename, search_folders, WINDMILL_BASE_FOLDER)
            img = pygame.image.load(path).convert_alpha()
            _loaded_assets["windmill"].append(pygame.transform.scale(img, (windmill_sprite_size, windmill_sprite_size)))
        except FileNotFoundError as e:
            print(f"CRITICAL ERROR in Assets.py: {e}")
            raise 
        except Exception as e:
            print(f"An unexpected error occurred loading Windmill asset '{filename}': {e}")
            raise 
    print(f"DEBUG: Loaded {len(_loaded_assets['windmill'])} windmill animation frames.")

# --- Load Castle Assets ---
def load_castle_assets(tile_size, search_folders):
    global _loaded_assets
    _loaded_assets["castle"] = []
    castle_final_size = int(tile_size * CASTLE_SCALE_FACTOR)
    
    try:
        path = _find_image_file(CASTLE_FILENAME, search_folders, CASTLE_FOLDER)
        sheet = pygame.image.load(path).convert_alpha()
        
        frame_w = CASTLE_ORIGINAL_SIZE
        frame_h = CASTLE_ORIGINAL_SIZE
        
        for i in range(CASTLE_FRAMES):
            rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
            if rect.x + rect.w > sheet.get_width():
                print(f"WARNING: Castle frame {i} exceeds sprite sheet width.")
                break
                
            frame_surf = sheet.subsurface(rect)
            _loaded_assets["castle"].append(pygame.transform.scale(frame_surf, (castle_final_size, castle_final_size)))
            
    except FileNotFoundError as e:
        print(f"CRITICAL ERROR in Assets.py: {e}")
        raise 
    except Exception as e:
        print(f"An unexpected error occurred loading Castle asset: {e}")
        raise 
    print(f"DEBUG: Loaded {len(_loaded_assets['castle'])} castle animation frames.")


# --- Load McUncle assets ---
def load_mcuncle_assets(tile_size, search_folders):
    global _loaded_mcuncle_sprites
    _loaded_mcuncle_sprites = []
    sprite_size = int(tile_size * MCUNCLE_SCALE_FACTOR)

    for i in range(1, MCUNCLE_FRAME_COUNT + 1): 
        filename = f"Mcunle_{i}.png" 
        try:
            path = _find_image_file(filename, search_folders, MCUNCLE_BASE_FOLDER)
            img = pygame.image.load(path).convert_alpha()
            _loaded_mcuncle_sprites.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        except FileNotFoundError as e:
            print(f"CRITICAL ERROR in Assets.py: {e}")
            raise 
        except Exception as e:
            print(f"An unexpected error occurred loading McUncle asset '{filename}': {e}")
            raise
    print(f"DEBUG: Loaded {len(_loaded_mcuncle_sprites)} McUncle animation frames.")


# --- Load Hamster Assets ---
def load_hamster_assets(tile_size, search_folders):
    global _loaded_hamsters
    _loaded_hamsters = {}
    
    sprite_size = int(tile_size * HAMSTER_SCALE_FACTOR)
    
    for name, config in HAMSTER_CONFIG.items():
        _loaded_hamsters[name] = {}
        base_subfolder = os.path.join(HAMSTER_ROOT_FOLDER, config['subfolder'])
        
        if config["type"] == "static":
            for state, filename in config['files'].items():
                try:
                    path = _find_image_file(filename, search_folders, base_subfolder)
                    img = pygame.image.load(path).convert_alpha()
                    _loaded_hamsters[name][state] = [pygame.transform.scale(img, (sprite_size, sprite_size))]
                except FileNotFoundError as e:
                    print(f"CRITICAL ERROR: Could not find {name} asset '{filename}' in '{base_subfolder}': {e}")
                    raise

        elif config["type"] == "animated":
            for state, anim_info in config['actions'].items():
                folder_name = anim_info["folder"]
                prefix = anim_info["prefix"]
                count = anim_info["count"]
                
                full_anim_folder = os.path.join(base_subfolder, folder_name)
                _loaded_hamsters[name][state] = []
                
                for i in range(count):
                    filename = f"{prefix}{i:02d}.png" 
                    try:
                        path = _find_image_file(filename, search_folders, full_anim_folder)
                        img = pygame.image.load(path).convert_alpha()
                        _loaded_hamsters[name][state].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
                    except FileNotFoundError as e:
                        print(f"CRITICAL ERROR: Could not find frame '{filename}' for {name}: {e}")
                        raise

        elif config["type"] == "animated_spritesheets":
            for state, info in config['actions'].items():
                filename = info["file"]
                frame_w = info["w"]
                frame_h = info["h"]
                count = info["count"]
                
                try:
                    path = _find_image_file(filename, search_folders, base_subfolder)
                    sheet = pygame.image.load(path).convert_alpha()
                    
                    frames = []
                    for i in range(count):
                        rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
                        if rect.x + rect.w > sheet.get_width():
                            print(f"WARNING: Frame {i} exceeds sprite sheet width for {name} ({state})")
                            break
                        
                        frame_surf = sheet.subsurface(rect)
                        frames.append(pygame.transform.scale(frame_surf, (sprite_size, sprite_size)))
                    
                    _loaded_hamsters[name][state] = frames
                    
                except FileNotFoundError as e:
                    print(f"CRITICAL ERROR: Could not find sprite sheet '{filename}' for {name}: {e}")
                    raise

    print(f"DEBUG: Loaded Hamsters: {list(_loaded_hamsters.keys())}")


# --- Load Projectile Assets ---
def load_projectile_assets(tile_size, search_folders):
    global _loaded_projectiles
    _loaded_projectiles = {}
    sprite_size = int(tile_size * PROJECTILE_SCALE_FACTOR)
    
    for key, filename in PROJECTILE_FILES.items():
        try:
            path = _find_image_file(filename, search_folders, PROJECTILES_FOLDER)
            img = pygame.image.load(path).convert_alpha()
            _loaded_projectiles[key] = pygame.transform.scale(img, (sprite_size, sprite_size))
        except FileNotFoundError as e:
             print(f"CRITICAL ERROR in Assets.py: {e}")
             raise
    print(f"DEBUG: Loaded Projectiles: {list(_loaded_projectiles.keys())}")


# --- Load Enemy Assets ---
def load_enemy_assets(tile_size, search_folders):
    global _loaded_enemies
    _loaded_enemies = {}
    sprite_size = int(tile_size * ENEMY_SCALE_FACTOR)
    
    for name, config in ENEMY_CONFIG.items():
        filename = config["file"]
        frame_w = config["w"]
        frame_h = config["h"]
        count = config["count"]
        
        try:
            path = _find_image_file(filename, search_folders, ENEMY_FOLDER)
            sheet = pygame.image.load(path).convert_alpha()
            
            frames = []
            for i in range(count):
                rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
                if rect.x + rect.w > sheet.get_width():
                    print(f"WARNING: Enemy frame {i} exceeds width for {name}")
                    break
                
                frame_surf = sheet.subsurface(rect)
                frame_surf = _remove_white_background_floodfill(frame_surf)
                frames.append(pygame.transform.scale(frame_surf, (sprite_size, sprite_size)))
            
            _loaded_enemies[name] = frames
            
        except FileNotFoundError as e:
             print(f"CRITICAL ERROR in Assets.py: Could not find Enemy sheet '{filename}': {e}")
             raise

    print(f"DEBUG: Loaded Enemies: {list(_loaded_enemies.keys())}")