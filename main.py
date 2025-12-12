import asyncio # Required for Pygbag/Web
import pygame
import random
import os
import sys
import Assets 
from Entities import Llama, McUncle, Hamster, Enemy, Projectile, Castle, Windmill, CASTLE_HITBOX_WIDTH_TILES, CASTLE_HITBOX_HEIGHT_TILES
import MenuUI 

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 1280, 720
TILE_SIZE = 64 
COLUMNS = WIDTH // TILE_SIZE
ROWS = HEIGHT // TILE_SIZE 
TILES_SEARCH_FOLDERS = ["", "tiles", "assets"] 
SAVE_FOLDER = "saved_maps"
GAME_TIMER_DURATION = 300.0 # Seconds before enemies attack

# ---------------- PLAYER INTERACTION STATE ----------------
current_tool = "none" 
selected_asset_type = None 

# List to store player-placed objects: (asset_type, grid_r, grid_c)
player_placed_objects = [] 

# List to store Entity objects
llamas = []
mcuncles = []
hamsters = [] 
enemies = []  
projectiles = []
windmills = [] 
castle = None 

# Game State
cheese_count = 0
game_timer = GAME_TIMER_DURATION
enemies_attacking = False
game_over = False

# Unified selection variable
selected_entity = None 
selected_llama_context = None

# For selecting and deleting fences
selected_removable_object = None 
delete_button_rect = None 
DELETE_BUTTON_TEXT = "DELETE"
DELETE_BUTTON_COLOR = (200, 50, 50) 
DELETE_TEXT_COLOR = (255, 255, 255) 
DELETE_BUTTON_PADDING = 5 

# Camera/Zoom variables
zoom_level = 1.0 
max_zoom = 4.0 
min_zoom = 1.0 
camera_x = 0.0 
camera_y = 0.0 
render_offset_x = 0.0 
render_offset_y = 0.0 

# Dragging variables
is_dragging = False
last_mouse_pos = None 

# ------------------------------------------------------------


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hamster Path Defense")
font = pygame.font.Font(None, 28)
timer_font = pygame.font.Font(None, 32) 
game_over_font = pygame.font.Font(None, 72)
delete_font = pygame.font.Font(None, 32)
clock = pygame.time.Clock()

# Global dictionary for all loaded tiles
tiles = {}

# Off-screen surface for drawing the game world
world_width_pixels = COLUMNS * TILE_SIZE
world_height_pixels = ROWS * TILE_SIZE
world_surface = pygame.Surface((world_width_pixels, world_height_pixels), pygame.SRCALPHA)

# Calculate min_zoom dynamically
calculated_min_zoom_x = WIDTH / world_width_pixels
calculated_min_zoom_y = HEIGHT / world_height_pixels
min_zoom = min(calculated_min_zoom_x, calculated_min_zoom_y)
zoom_level = min_zoom 


# --- Camera Helper Functions ---
def _world_to_screen_pixel(world_x, world_y):
    screen_x = (world_x - camera_x) * zoom_level + render_offset_x
    screen_y = (world_y - camera_y) * zoom_level + render_offset_y
    return screen_x, screen_y

def _screen_to_world_pixel(screen_x, screen_y):
    world_x = ((screen_x - render_offset_x) / zoom_level) + camera_x
    world_y = ((screen_y - render_offset_y) / zoom_level) + camera_y
    return world_x, world_y

def _screen_to_world_grid(screen_x, screen_y):
    world_x, world_y = _screen_to_world_pixel(screen_x, screen_y)
    grid_c = int(world_x // TILE_SIZE)
    grid_r = int(world_y // TILE_SIZE)
    return grid_r, grid_c

def _clamp_camera():
    global camera_x, camera_y, render_offset_x, render_offset_y
    
    scaled_world_width = world_width_pixels * zoom_level
    scaled_world_height = world_height_pixels * zoom_level

    if scaled_world_width < WIDTH: 
        render_offset_x = (WIDTH - scaled_world_width) / 2.0 
        camera_x = 0.0 
    else: 
        render_offset_x = 0.0 
        camera_x = max(0.0, min(camera_x, world_width_pixels - (WIDTH / zoom_level)))

    if scaled_world_height < HEIGHT: 
        render_offset_y = (HEIGHT - scaled_world_height) / 2.0 
        camera_y = 0.0 
    else: 
        render_offset_y = 0.0 
        camera_y = max(0.0, min(camera_y, world_height_pixels - (HEIGHT / zoom_level)))


# --- load all assets ---
def load_all_assets():
    global tiles 
    
    try:
        Assets.load_game_assets(TILE_SIZE, WIDTH, HEIGHT, TILES_SEARCH_FOLDERS)
        tiles.update(Assets._loaded_assets) 
        
        Assets.load_llama_assets(TILE_SIZE, TILES_SEARCH_FOLDERS)

        Assets.load_windmill_assets(TILE_SIZE, TILES_SEARCH_FOLDERS)
        tiles.update({"windmill": Assets._loaded_assets["windmill"]}) 
        
        Assets.load_castle_assets(TILE_SIZE, TILES_SEARCH_FOLDERS)

        Assets.load_mcuncle_assets(TILE_SIZE, TILES_SEARCH_FOLDERS)
        tiles["mcuncle"] = Assets._loaded_mcuncle_sprites 

        Assets.load_hamster_assets(TILE_SIZE, TILES_SEARCH_FOLDERS)
        tiles["hamsters"] = Assets._loaded_hamsters 

        Assets.load_projectile_assets(TILE_SIZE, TILES_SEARCH_FOLDERS)
        tiles["projectiles"] = Assets._loaded_projectiles 

        Assets.load_enemy_assets(TILE_SIZE, TILES_SEARCH_FOLDERS)
        tiles["enemies"] = Assets._loaded_enemies 

    except FileNotFoundError as e:
        print(f"CRITICAL ERROR: Asset loading failed: {e}")
        # In asyncio/web context, sys.exit() might not work as expected, but kept for local
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during asset loading: {e}")
        sys.exit(1)

try:
    load_all_assets()
except Exception as e:
    sys.exit(1)


# --- Helper: Generates random non-path features ---
def generate_random_features(grid, rows, columns, exclusion_coords):
    features = []
    # Logic for Rock and Bonus removed as requested
    return features

# --- Map Generation Helper ---
def generate_grass_map(rows, columns, extra_exclusions=None):
    grid = [["grass" for _ in range(columns)] for _ in range(rows)]
    seed = random.randint(100000, 999999)
    random.seed(seed)
    
    exclusion_coords = set()
    for _, r, c in player_placed_objects:
        exclusion_coords.add((r,c))
    for w in windmills:
        exclusion_coords.update(w.get_occupied_coords())
    
    if extra_exclusions:
        exclusion_coords.update(extra_exclusions)
        
    features = generate_random_features(grid, rows, columns, exclusion_coords)
    
    return {
        "grid": grid,
        "features": features,
        "seed": seed
    }

# --- draw ---
def draw(seed, grid, features, ui_control_panel): 
    global delete_button_rect 

    world_surface.fill((0,0,0,0)) 

    # Draw grass everywhere
    world_surface.blit(tiles["grass"], (0,0)) 
    
    for name, r, c in features:
        if name in tiles:
            world_surface.blit(tiles[name], (c * TILE_SIZE, r * TILE_SIZE)) 
    
    if castle:
        castle.draw(world_surface)

    # Draw Windmills
    for w in windmills:
        w.draw(world_surface)

    # Draw Static Player Objects
    for asset_type, r, c in player_placed_objects:
        if asset_type != "windmill": 
            if asset_type in tiles:
                original_image = tiles[asset_type] 
                world_surface.blit(original_image, (c * TILE_SIZE, r * TILE_SIZE))

        if selected_removable_object and selected_removable_object == (asset_type, r, c):
            pygame.draw.rect(world_surface, (255, 255, 0), (c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE), 2) 
    
    # Highlight selected windmill
    if selected_removable_object and selected_removable_object[0] == "windmill":
        wr, wc = selected_removable_object[1], selected_removable_object[2]
        pygame.draw.rect(world_surface, (255, 255, 0), (wc * TILE_SIZE, wr * TILE_SIZE, TILE_SIZE*2, TILE_SIZE*2), 2)

    for enemy in enemies:
        enemy.draw(world_surface)

    for llama in llamas:
        llama.draw(world_surface)
        
    for mcuncle in mcuncles:
        mcuncle.draw(world_surface)

    for hamster in hamsters:
        hamster.draw(world_surface)
        
    for proj in projectiles:
        proj.draw(world_surface)
    
    if current_tool == "place" and selected_asset_type:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_r, world_c = _screen_to_world_grid(mouse_x, mouse_y) 
        
        if 0 <= world_r < ROWS and 0 <= world_c < COLUMNS:
            ghost_image = None
            if selected_asset_type == "windmill":
                if tiles["windmill"]:
                    ghost_image = tiles["windmill"][0].copy()
            else:
                if selected_asset_type in tiles:
                    ghost_image = tiles[selected_asset_type].copy()
            
            if ghost_image:
                ghost_image.set_alpha(128) 
                offset_x = (TILE_SIZE - ghost_image.get_width()) / 2
                offset_y = (TILE_SIZE - ghost_image.get_height()) / 2
                world_surface.blit(ghost_image, (world_c * TILE_SIZE + offset_x, world_r * TILE_SIZE + offset_y))
    
    elif current_tool == "set_rally":
        if "flagpole" in tiles:
            ghost_image = tiles["flagpole"].copy()
            if ghost_image:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                world_r, world_c = _screen_to_world_grid(mouse_x, mouse_y) 
                if 0 <= world_r < ROWS and 0 <= world_c < COLUMNS:
                    ghost_image.set_alpha(128) 
                    offset_x = (TILE_SIZE - ghost_image.get_width()) / 2
                    offset_y = (TILE_SIZE - ghost_image.get_height()) / 2
                    world_surface.blit(ghost_image, (world_c * TILE_SIZE + offset_x, world_r * TILE_SIZE + offset_y))

    scaled_world_width = int(world_width_pixels * zoom_level)
    scaled_world_height = int(world_height_pixels * zoom_level)
    
    scaled_world = pygame.transform.scale(world_surface, (scaled_world_width, scaled_world_height))
    screen.blit(scaled_world, (render_offset_x - camera_x * zoom_level, render_offset_y - camera_y * zoom_level))

    if selected_removable_object:
        asset_type, r, c = selected_removable_object
        obj_world_x = c * TILE_SIZE
        obj_world_y = r * TILE_SIZE
        button_screen_x, button_screen_y = _world_to_screen_pixel(obj_world_x, obj_world_y)
        
        if asset_type == "windmill":
            button_screen_x += TILE_SIZE * zoom_level 
            button_screen_y += TILE_SIZE * zoom_level 
        else:
            button_screen_x += TILE_SIZE * zoom_level + DELETE_BUTTON_PADDING
            button_screen_y += TILE_SIZE * zoom_level + DELETE_BUTTON_PADDING

        delete_text_surface = delete_font.render(DELETE_BUTTON_TEXT, True, DELETE_TEXT_COLOR)
        text_width, text_height = delete_text_surface.get_size()

        delete_button_rect = pygame.Rect(button_screen_x, button_screen_y, 
                                         text_width + 2 * DELETE_BUTTON_PADDING, 
                                         text_height + 2 * DELETE_BUTTON_PADDING)
        delete_button_rect.x = max(0, min(delete_button_rect.x, WIDTH - delete_button_rect.width))
        delete_button_rect.y = max(0, min(delete_button_rect.y, HEIGHT - delete_button_rect.height))

        pygame.draw.rect(screen, DELETE_BUTTON_COLOR, delete_button_rect, border_radius=3)
        screen.blit(delete_text_surface, 
                    (delete_button_rect.x + DELETE_BUTTON_PADDING, 
                     delete_button_rect.y + DELETE_BUTTON_PADDING))
    else:
        delete_button_rect = None 

    ui_control_panel.draw(screen)

    # --- UI Layout: Left Side (Seed, Timer) ---
    ui_x_left = 20
    ui_y_left = 20
    
    # 1. Seed Text
    status_text = f"Seed: {seed}"
    txt_seed = font.render(status_text, True, (255,255,255))
    screen.blit(txt_seed, (ui_x_left, ui_y_left))
    ui_y_left += 30

    # 2. Timer Text
    timer_color = (255, 255, 255)
    if game_timer <= 5.0 and not enemies_attacking:
        timer_color = (255, 50, 50) 
    
    if enemies_attacking:
        timer_str = "WAR!"
        timer_color = (255, 0, 0)
    else:
        timer_str = f"Time until Enemy attacks: {int(game_timer)}s"
        
    txt_timer = timer_font.render(timer_str, True, timer_color)
    screen.blit(txt_timer, (ui_x_left, ui_y_left))

    # --- UI Layout: Top Right Corner (Cheese, Queue) ---
    ui_x_right = WIDTH - 90 
    ui_y_right = 20

    # 1. Cheese Icon & Count
    if "cheese" in tiles:
        cheese_icon = pygame.transform.scale(tiles["cheese"], (48, 48))
        screen.blit(cheese_icon, (ui_x_right - 10, ui_y_right))
        
        cheese_text = font.render(f"x {cheese_count}", True, (255, 255, 255))
        screen.blit(cheese_text, (ui_x_right, ui_y_right + 50))
        ui_y_right += 80

    # 2. Queue List
    if castle:
        if castle.training_queue:
            queue_label = font.render("Queue:", True, (200, 200, 200))
            screen.blit(queue_label, (ui_x_right - 10, ui_y_right))
            ui_y_right += 25
            
            for unit_name in castle.training_queue:
                # Draw a small icon for the unit
                unit_icon = None
                if unit_name == "McUncle" and "mcuncle" in tiles and tiles["mcuncle"]:
                    unit_icon = tiles["mcuncle"][0]
                elif unit_name in ["Bob", "Dracula", "TheHamster"] and "hamsters" in tiles:
                    if unit_name in tiles["hamsters"] and "idle" in tiles["hamsters"][unit_name]:
                        unit_icon = tiles["hamsters"][unit_name]["idle"][0]
                
                # Placeholder if no icon
                if unit_icon:
                    scaled_icon = pygame.transform.scale(unit_icon, (40, 40))
                    screen.blit(scaled_icon, (ui_x_right, ui_y_right))
                else:
                    txt_name = font.render(unit_name[:2], True, (255,255,255))
                    pygame.draw.rect(screen, (100,100,100), (ui_x_right, ui_y_right, 40, 40))
                    screen.blit(txt_name, (ui_x_right+5, ui_y_right+10))
                    
                ui_y_right += 45


    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        msg = game_over_font.render("GAME OVER", True, (255, 0, 0))
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 100))
        
        sub = font.render("Press R to Restart (New Map) or ESC to Quit", True, (255, 255, 255))
        screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 20))


# --- main (Async for Pygbag) ---
async def main():
    global current_tool, selected_asset_type, player_placed_objects, llamas, mcuncles, hamsters, enemies, selected_entity, projectiles, castle, selected_llama_context, windmills, cheese_count
    global selected_removable_object, delete_button_rect, zoom_level, camera_x, camera_y, render_offset_x, render_offset_y, is_dragging, last_mouse_pos
    global game_timer, enemies_attacking, game_over

    # Init generation
    castle_c = max(0, COLUMNS - CASTLE_HITBOX_WIDTH_TILES - 3)
    max_r = max(CASTLE_HITBOX_HEIGHT_TILES, ROWS - CASTLE_HITBOX_HEIGHT_TILES - 2)
    castle_r = random.randint(2, max_r)
    
    castle = Castle((castle_r, castle_c), TILE_SIZE)
    castle_occupied = set(castle.get_occupied_coords())

    map_data = generate_grass_map(ROWS, COLUMNS, castle_occupied)
    seed = map_data["seed"]
    grid = map_data["grid"]
    features = map_data["features"]
    print(f"Generated map. Seed: {seed}")

    # Spawning Logic Helper
    def spawn_entities():
        llamas.clear()
        enemies.clear()
        projectiles.clear()
        
        walkable_coords = []
        occupied = set([(r,c) for _, r, c in features])
        for _, r, c in player_placed_objects: occupied.add((r,c))
        for w in windmills: occupied.update(w.get_occupied_coords())
        occupied.update(castle_occupied) 
        
        for r in range(ROWS):
            for c in range(COLUMNS):
                if grid[r][c] == "grass" and (r,c) not in occupied:
                    walkable_coords.append((r,c))
        
        if walkable_coords:
            for _ in range(3): 
                start_r, start_c = random.choice(walkable_coords)
                llamas.append(Llama((start_r, start_c), TILE_SIZE, grid, walkable_coords, llamas))
        
    def spawn_enemy_wave(count=10):
        # Spawn from Left Side (Column 0)
        spawn_candidates = []
        for r in range(ROWS):
            if grid[r][0] == "grass":
                spawn_candidates.append((r, 0))
        
        if not spawn_candidates:
             spawn_candidates = [(r, 0) for r in range(ROWS)]
             
        for _ in range(count):
            start_pos = random.choice(spawn_candidates)
            enemies.append(Enemy(start_pos, TILE_SIZE))
        print(f"Spawned wave of {count} enemies from the left!")

    spawn_entities()
    _clamp_camera()
    
    ui_control_panel = MenuUI.UIControlPanel(TILE_SIZE, WIDTH, HEIGHT, tiles)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0 
        
        # --- Game Timer Logic ---
        if not game_over:
            if game_timer > 0:
                game_timer -= dt
                if game_timer <= 0:
                    game_timer = 0
                    enemies_attacking = True
                    spawn_enemy_wave(10) # Spawn 10 Pieros

            if castle and castle.health <= 0:
                game_over = True
                print("GAME OVER")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEWHEEL:
                if not game_over:
                    mouse_screen_x, mouse_screen_y = pygame.mouse.get_pos()
                    old_zoom_level = zoom_level
                    old_render_offset_x = render_offset_x
                    old_render_offset_y = render_offset_y

                    new_zoom_candidate = zoom_level
                    if event.y > 0: new_zoom_candidate *= 1.1 
                    else: new_zoom_candidate /= 1.1 
                    
                    zoom_level = max(min_zoom, min(new_zoom_candidate, max_zoom)) 
                    _clamp_camera()
                    
                    camera_x = camera_x + ((mouse_screen_x - old_render_offset_x) / old_zoom_level) - ((mouse_screen_x - render_offset_x) / zoom_level)
                    camera_y = camera_y + ((mouse_screen_y - old_render_offset_y) / old_zoom_level) - ((mouse_screen_y - render_offset_y) / zoom_level)
                    _clamp_camera()

            elif event.type == pygame.KEYDOWN: 
                if event.key == pygame.K_r: # Regenerate / Restart
                    print("\nRegenerating map...")
                    # Reset Game State
                    player_placed_objects = [] 
                    windmills = [] 
                    llamas = [] 
                    mcuncles = []
                    hamsters = []
                    enemies = []
                    projectiles = []
                    selected_entity = None
                    selected_removable_object = None 
                    delete_button_rect = None 
                    selected_llama_context = None
                    cheese_count = 0
                    game_timer = GAME_TIMER_DURATION
                    enemies_attacking = False
                    game_over = False
                    
                    castle_c = max(0, COLUMNS - CASTLE_HITBOX_WIDTH_TILES - 3)
                    max_r = max(CASTLE_HITBOX_HEIGHT_TILES, ROWS - CASTLE_HITBOX_HEIGHT_TILES - 2)
                    castle_r = random.randint(2, max_r)
                    
                    castle = Castle((castle_r, castle_c), TILE_SIZE)
                    castle_occupied = set(castle.get_occupied_coords())

                    map_data = generate_grass_map(ROWS, COLUMNS, castle_occupied)
                    seed = map_data["seed"]
                    grid = map_data["grid"]
                    features = map_data["features"]
                    
                    spawn_entities()
                    _clamp_camera()
                    
                elif event.key == pygame.K_s: 
                    if os.path.exists(SAVE_FOLDER):
                        pygame.image.save(screen, os.path.join(SAVE_FOLDER, f"map_{seed}.png"))
                
                elif event.key == pygame.K_ESCAPE: 
                    if game_over:
                        running = False
                    else:
                        current_tool = "none"
                        selected_asset_type = None
                        selected_removable_object = None 
                        delete_button_rect = None 
                        selected_llama_context = None
                        if selected_entity:
                            selected_entity.selected = False
                            selected_entity = None
                        ui_control_panel.build_menu_active = False 
                        ui_control_panel.castle_menu_active = False
                        ui_control_panel.llama_menu_active = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game_over: continue # Block clicks on game over

                if ui_control_panel.is_mouse_over(event.pos):
                    ui_action, ui_data = ui_control_panel.handle_event(event)
                    
                    if ui_action == "select_asset":
                        current_tool = "place"
                        selected_asset_type = ui_data 
                        selected_removable_object = None
                        delete_button_rect = None
                        if selected_entity:
                            selected_entity.selected = False
                            selected_entity = None
                    
                    elif ui_action == "train_unit":
                        if castle and isinstance(ui_data, dict) and "name" in ui_data:
                            cost = ui_data.get("price", 0)
                            if cheese_count >= cost:
                                success = castle.queue_unit(ui_data["name"])
                                if success:
                                    cheese_count -= cost
                            else:
                                print("Not enough cheese!")

                    elif ui_action == "set_rally_point":
                        current_tool = "set_rally"
                        selected_entity = None
                        selected_removable_object = None
                        
                    elif ui_action == "llama_follow":
                        if selected_llama_context:
                            bob_unit = None
                            for h in hamsters:
                                if h.name == "Bob": 
                                    bob_unit = h
                                    break
                            if bob_unit:
                                selected_llama_context.start_following(bob_unit)
                            ui_control_panel.llama_menu_active = False
                            
                    elif ui_action == "llama_stop":
                        if selected_llama_context:
                            selected_llama_context.stop_following()
                            ui_control_panel.llama_menu_active = False

                    continue 

                # Right Click Deselect
                if event.button == 3: 
                    if current_tool != "none" or selected_entity or selected_removable_object or ui_control_panel.castle_menu_active or ui_control_panel.llama_menu_active:
                        current_tool = "none"
                        selected_asset_type = None
                        if selected_entity:
                            selected_entity.selected = False
                            selected_entity = None
                        selected_removable_object = None
                        delete_button_rect = None
                        ui_control_panel.castle_menu_active = False
                        ui_control_panel.llama_menu_active = False
                        selected_llama_context = None
                        continue
                    else:
                        if zoom_level > min_zoom: 
                            is_dragging = True
                            last_mouse_pos = event.pos
                            continue

                if event.button == 1: 
                    mouse_screen_x, mouse_screen_y = event.pos
                    grid_r_click, grid_c_click = _screen_to_world_grid(mouse_screen_x, mouse_screen_y)
                    world_x_click, world_y_click = _screen_to_world_pixel(mouse_screen_x, mouse_screen_y)

                    # Handle Rally Point Setting
                    if current_tool == "set_rally":
                        if castle:
                            if 0 <= grid_r_click < ROWS and 0 <= grid_c_click < COLUMNS:
                                castle.set_rally_point(grid_r_click, grid_c_click)
                                current_tool = "none"
                                continue

                    # Check Castle Click (Pixel Perfect)
                    if castle:
                        if castle.is_pixel_clicked((world_x_click, world_y_click)):
                            ui_control_panel.castle_menu_active = True
                            ui_control_panel.llama_menu_active = False
                            print("Castle Selected")
                            selected_entity = None
                            selected_removable_object = None
                            continue
                        else:
                            ui_control_panel.castle_menu_active = False

                    # Check Llama Click (Pixel Perfect)
                    llama_clicked = False
                    for l in llamas:
                        if l.is_pixel_clicked((world_x_click, world_y_click)):
                            bob_unit = None
                            for h in hamsters:
                                if h.name == "Bob": bob_unit = h; break
                            
                            dist = 9999
                            if bob_unit:
                                dist = l.current_pixel_pos.distance_to(bob_unit.current_pixel_pos)
                            
                            if dist < 200: 
                                selected_llama_context = l
                                ui_control_panel.llama_menu_active = True
                                ui_control_panel.castle_menu_active = False
                                print("Llama clicked & Bob is near")
                            else:
                                print("Llama clicked but Bob is too far")
                            
                            llama_clicked = True
                            break
                    
                    if llama_clicked: continue
                    else: ui_control_panel.llama_menu_active = False


                    if delete_button_rect and delete_button_rect.collidepoint(event.pos):
                        if selected_removable_object:
                            atype, ar, ac = selected_removable_object
                            if atype == "windmill":
                                to_remove = None
                                for w in windmills:
                                    if w.grid_r == ar and w.grid_c == ac:
                                        to_remove = w
                                        break
                                if to_remove: windmills.remove(to_remove)
                            else:
                                player_placed_objects.remove(selected_removable_object)
                        selected_removable_object = None 
                        delete_button_rect = None 
                        continue 

                    # Place Static Assets / Windmills
                    if current_tool == "place": 
                        if 0 <= grid_r_click < ROWS and 0 <= grid_c_click < COLUMNS:
                            # Check Castle Collision
                            if (grid_r_click, grid_c_click) in castle_occupied:
                                print("Cannot place object on the Castle!")
                                continue
                            
                            is_spot_free = (map_data["grid"][grid_r_click][grid_c_click] == "grass")
                            for _, pr, pc in player_placed_objects:
                                if pr == grid_r_click and pc == grid_c_click:
                                    is_spot_free = False
                                    break
                            for w in windmills:
                                if (grid_r_click, grid_c_click) in w.get_occupied_coords():
                                    is_spot_free = False
                                    break

                            if is_spot_free:
                                if selected_asset_type == "windmill":
                                    new_w = Windmill((grid_r_click, grid_c_click), TILE_SIZE)
                                    windmills.append(new_w)
                                else:
                                    player_placed_objects.append((selected_asset_type, grid_r_click, grid_c_click)) 
                            else:
                                print("Cannot place here.")
                    
                    else: 
                        # Selection / Movement Logic
                        clicked_unit = None
                        
                        for unit in mcuncles:
                            if unit.grid_r == grid_r_click and unit.grid_c == grid_c_click:
                                clicked_unit = unit
                                break
                        if not clicked_unit:
                            for unit in hamsters:
                                if unit.grid_r == grid_r_click and unit.grid_c == grid_c_click:
                                    clicked_unit = unit
                                    break
                        
                        if clicked_unit:
                            if selected_entity and selected_entity != clicked_unit:
                                selected_entity.selected = False
                            selected_entity = clicked_unit
                            selected_entity.selected = True
                            print(f"Selected {selected_entity.name}.")
                            selected_removable_object = None
                            delete_button_rect = None
                        
                        elif selected_entity and not clicked_unit:
                            # Move command
                            if (grid_r_click, grid_c_click) in castle_occupied:
                                print("Cannot move into the Castle!")
                            else:
                                print(f"Commanding {selected_entity.name} to move to ({grid_r_click}, {grid_c_click})")
                                selected_entity.set_target(grid_r_click, grid_c_click)
                        
                        else:
                            # Select Static Object or Windmill
                            found_removable = False
                            for w in windmills:
                                if w.is_pixel_clicked((world_x_click, world_y_click)):
                                    selected_removable_object = ("windmill", w.grid_r, w.grid_c)
                                    found_removable = True
                                    print("Windmill selected")
                                    break
                            
                            if not found_removable:
                                for asset_type, r, c in player_placed_objects:
                                    if r == grid_r_click and c == grid_c_click:
                                        selected_removable_object = (asset_type, r, c)
                                        found_removable = True
                                        break
                            
                            if found_removable:
                                if selected_entity:
                                    selected_entity.selected = False
                                    selected_entity = None
                            else:
                                selected_removable_object = None
                                delete_button_rect = None
                                if selected_entity:
                                    selected_entity.selected = False
                                    selected_entity = None
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3: 
                    is_dragging = False
                    last_mouse_pos = None

            elif event.type == pygame.MOUSEMOTION:
                if is_dragging and last_mouse_pos:
                    dx = event.pos[0] - last_mouse_pos[0]
                    dy = event.pos[1] - last_mouse_pos[1]
                    camera_x -= dx / zoom_level
                    camera_y -= dy / zoom_level
                    _clamp_camera() 
                    last_mouse_pos = event.pos 

        # Gather Obstacles
        current_obstacles = set()
        for asset_type, r, c in player_placed_objects:
            current_obstacles.add((r, c))
        
        pixel_obstacles = []
        if castle: pixel_obstacles.append(castle)
        pixel_obstacles.extend(windmills)

        # Update Projectiles
        for proj in projectiles:
            proj.update(dt)
        projectiles = [p for p in projectiles if p.active] 

        if not game_over:
            # Update Entities
            if castle: 
                castle.update(dt)
                while castle.spawned_units:
                    new_unit = castle.spawned_units.pop(0)
                    if isinstance(new_unit, McUncle):
                        mcuncles.append(new_unit)
                    else:
                        hamsters.append(new_unit)
            
            for w in windmills:
                produced = w.update(dt, llamas)
                if produced:
                    cheese_count += 1
                    print(f"Cheese produced! Total: {cheese_count}")

            for llama in llamas: llama.update(dt, current_obstacles, pixel_obstacles, windmills)
            
            for mcuncle in mcuncles: 
                mcuncle.update(dt, enemies, projectiles, current_obstacles, pixel_obstacles)
                
            for hamster in hamsters: 
                hamster.update(dt, enemies, projectiles, current_obstacles, pixel_obstacles)
                
            for enemy in enemies: 
                # Move to castle if timer is up
                enemy.update(dt, current_obstacles, castle, move_to_castle=enemies_attacking) 
            
            enemies = [e for e in enemies if e.health > 0]

        screen.fill((0, 0, 0)) 
        draw(map_data["seed"], map_data["grid"], map_data["features"], ui_control_panel)
        pygame.display.flip()
        
        await asyncio.sleep(0) # Required for Pygbag to not block browser loop

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())