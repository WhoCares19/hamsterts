import asyncio # Required for Pygbag/Web
import pygame
import random
import os
import sys
import math 
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
INITIAL_WAVE_TIMER = 200.0 
STAGE_COOLDOWN_TIME = 10.0

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
cheese_count = 5 # Start with 5 cheese
game_timer = INITIAL_WAVE_TIMER
current_wave_duration = INITIAL_WAVE_TIMER

stage_number = 1
wave_in_stage = 1
max_stages = 10

enemies_attacking = False
game_over = False
waiting_for_stage_start = False
stage_cooldown_timer = 0.0

# Windmill Economy
next_windmill_cost = 0

# Selection Variables
selected_entity = None 
selected_llama_context = None
selection_drag_start = None
selection_rect = None
selected_units = [] 
active_formation = "none" # Default formation is X (none)

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

# Castle Repair
repair_button_rect = None

# ------------------------------------------------------------


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hamster Path Defense")
font = pygame.font.Font(None, 28)
timer_font = pygame.font.Font(None, 32)
game_over_font = pygame.font.Font(None, 72)
stage_font = pygame.font.Font(None, 48)
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

# --- Formation Helper ---
def get_formation_positions(center_pixel_pos, unit_count, formation_type, spacing=40):
    positions = []
    cx, cy = center_pixel_pos
    
    if unit_count == 0: return []
    if unit_count == 1: return [center_pixel_pos]

    if formation_type == "line":
        # Vertical Formation
        MAX_PER_COL = 10
        num_cols = math.ceil(unit_count / MAX_PER_COL)
        total_width = (num_cols - 1) * spacing
        start_x = cx - total_width / 2
        
        for i in range(unit_count):
            col = i // MAX_PER_COL
            row = i % MAX_PER_COL
            current_col_size = min(MAX_PER_COL, unit_count - (col * MAX_PER_COL))
            start_y = cy - ((current_col_size - 1) * spacing) / 2
            
            px = start_x + col * spacing
            py = start_y + row * spacing
            positions.append((px, py))
            
    elif formation_type == "double":
        row1_count = math.ceil(unit_count / 2)
        row2_count = unit_count - row1_count
        start_x1 = cx - spacing / 2
        start_x2 = cx + spacing / 2
        
        height1 = (row1_count - 1) * spacing
        start_y1 = cy - height1 / 2
        for i in range(row1_count):
            positions.append((start_x1, start_y1 + i * spacing))
            
        height2 = (row2_count - 1) * spacing
        start_y2 = cy - height2 / 2
        for i in range(row2_count):
            positions.append((start_x2, start_y2 + i * spacing))
            
    elif formation_type == "square":
        side = math.ceil(math.sqrt(unit_count))
        start_x = cx - ((side - 1) * spacing) / 2
        start_y = cy - ((side - 1) * spacing) / 2
        idx = 0
        for r in range(side):
            for c in range(side):
                if idx < unit_count:
                    positions.append((start_x + c * spacing, start_y + r * spacing))
                    idx += 1
                    
    elif formation_type == "circle":
        circumference = spacing * unit_count
        radius = circumference / (2 * math.pi)
        if radius < spacing: radius = spacing
        for i in range(unit_count):
            angle = i * (2 * math.pi / unit_count)
            px = cx + radius * math.cos(angle)
            py = cy + radius * math.sin(angle)
            positions.append((px, py))
            
    else:
        # Default
        for i in range(unit_count):
            positions.append((cx, cy))
            
    return positions


# --- draw ---
def draw(seed, grid, features, ui_control_panel): 
    global delete_button_rect, repair_button_rect

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
    
    # Ghosts
    if current_tool == "place" and selected_asset_type:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_r, world_c = _screen_to_world_grid(mouse_x, mouse_y) 
        if 0 <= world_r < ROWS and 0 <= world_c < COLUMNS:
            ghost_image = None
            if selected_asset_type == "windmill":
                if tiles["windmill"]: ghost_image = tiles["windmill"][0].copy()
            elif selected_asset_type in tiles:
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

    # --- Render World to Screen ---
    scaled_world_width = int(world_width_pixels * zoom_level)
    scaled_world_height = int(world_height_pixels * zoom_level)
    scaled_world = pygame.transform.scale(world_surface, (scaled_world_width, scaled_world_height))
    screen.blit(scaled_world, (render_offset_x - camera_x * zoom_level, render_offset_y - camera_y * zoom_level))

    # --- UI & Overlays (Screen Space) ---

    # Selection Box
    if selection_rect:
        pygame.draw.rect(screen, (0, 255, 0), selection_rect, 1)
        surf = pygame.Surface((selection_rect.width, selection_rect.height), pygame.SRCALPHA)
        surf.fill((0, 255, 0, 50))
        screen.blit(surf, (selection_rect.x, selection_rect.y))

    # Repair Wrench Logic
    repair_button_rect = None
    if ui_control_panel.castle_menu_active and castle and castle.health < castle.max_health:
        wrench_img = tiles.get("wrench")
        if wrench_img:
            cx, cy = _world_to_screen_pixel(castle.current_pixel_pos.x, castle.current_pixel_pos.y)
            w_size = 64
            wrench_scaled = pygame.transform.scale(wrench_img, (w_size, w_size))
            
            rx = cx + (castle.width_tiles * TILE_SIZE * zoom_level)/2 - w_size/2
            ry = cy - w_size - 10
            
            screen.blit(wrench_scaled, (rx, ry))
            repair_button_rect = pygame.Rect(rx, ry, w_size, w_size)
            
            cost = castle.get_repair_cost()
            cost_txt = font.render(f"{cost}", True, (255, 255, 0))
            screen.blit(cost_txt, (rx + w_size + 5, ry + w_size//2 - 10))


    # Delete Button
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

    # Draw UI Panel (Bottom Center Icons + Menus)
    ui_control_panel.draw(screen, active_hamsters=hamsters, active_mcuncles=mcuncles)

    # --- Top Right Info ---
    ui_x_right = WIDTH - 80 
    ui_y_right = 20
    
    # 1. Cheese Icon & Count (Aligned Better)
    if "cheese" in tiles:
        cheese_icon = pygame.transform.scale(tiles["cheese"], (40, 40))
        # Draw Icon
        screen.blit(cheese_icon, (ui_x_right, ui_y_right))
        # Draw Text to the LEFT of icon or below? Request: "text of cheese is at the bottom... fix"
        # Let's put text to the LEFT of the icon
        cheese_text = font.render(f"{cheese_count}", True, (255, 255, 255))
        screen.blit(cheese_text, (ui_x_right - cheese_text.get_width() - 5, ui_y_right + 10))
        
        # Windmill Cost Tooltip (optional, showing next cost)
        cost_txt = ui_control_panel.price_font.render(f"Next Mill: {next_windmill_cost}", True, (200, 200, 200))
        screen.blit(cost_txt, (ui_x_right - 40, ui_y_right + 45))

    ui_y_right += 80

    # 2. Queue List (Floating on top of Castle)
    if castle and castle.training_queue:
        cx, cy = _world_to_screen_pixel(castle.current_pixel_pos.x, castle.current_pixel_pos.y)
        
        queue_w = 30 
        total_w = len(castle.training_queue) * (queue_w + 2)
        
        castle_screen_w = castle.width_tiles * TILE_SIZE * zoom_level
        start_x = cx + (castle_screen_w - total_w) / 2
        
        start_y = cy - 40 
        
        current_qx = start_x
        for unit_name in castle.training_queue:
            unit_icon = None
            if unit_name == "McUncle" and "mcuncle" in tiles and tiles["mcuncle"]:
                unit_icon = tiles["mcuncle"][0]
            elif unit_name in ["Bob", "Dracula", "TheHamster"] and "hamsters" in tiles:
                if unit_name in tiles["hamsters"] and "idle" in tiles["hamsters"][unit_name]:
                    unit_icon = tiles["hamsters"][unit_name]["idle"][0]
            
            if unit_icon:
                scaled_icon = pygame.transform.scale(unit_icon, (queue_w, queue_w))
                screen.blit(scaled_icon, (current_qx, start_y))
            else:
                pygame.draw.rect(screen, (100,100,100), (current_qx, start_y, queue_w, queue_w))
            
            current_qx += queue_w + 2


    # --- Left Side Info (Timer & Stage) ---
    ui_x_left = 20
    ui_y_left = 20
    
    timer_color = (255, 255, 255)
    if game_timer <= 5.0 and not enemies_attacking and not waiting_for_stage_start:
        timer_color = (255, 50, 50) 
    
    if enemies_attacking:
        timer_str = "Status: WAVE ATTACK!"
        timer_color = (255, 0, 0)
    elif waiting_for_stage_start:
        timer_str = "Status: STAGE CLEARED"
    else:
        timer_str = f"Time until Enemy attacks: {int(game_timer)}s"
        
    txt_timer = timer_font.render(timer_str, True, timer_color)
    screen.blit(txt_timer, (ui_x_left, ui_y_left))
    
    # Stage Info
    stage_str = f"Stage: {stage_number} | Wave: {wave_in_stage}/5"
    txt_stage = font.render(stage_str, True, (200, 200, 255))
    screen.blit(txt_stage, (ui_x_left, ui_y_left + 35))
    
    # --- Stage Clear Overlay ---
    if waiting_for_stage_start:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        msg = stage_font.render("Stage cleared roller", True, (0, 255, 0))
        sub = font.render(f"Next stage starts in {int(stage_cooldown_timer)} seconds, hope you are ready", True, (255, 255, 255))
        
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 50))
        screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 20))

    # --- Game Over Overlay ---
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
    global game_timer, enemies_attacking, game_over, repair_button_rect
    global selection_drag_start, selection_rect, selected_units
    global current_wave_duration, wave_number, waiting_for_continue
    global active_formation
    global stage_number, wave_in_stage, waiting_for_stage_start, stage_cooldown_timer, next_windmill_cost

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
        
        # --- Game Flow Logic ---
        if not game_over:
            # 1. Stage Break
            if waiting_for_stage_start:
                stage_cooldown_timer -= dt
                if stage_cooldown_timer <= 0:
                    waiting_for_stage_start = False
                    enemies_attacking = False
                    
                    # Start Next Stage
                    stage_number += 1
                    wave_in_stage = 1
                    current_wave_duration = INITIAL_WAVE_TIMER * (0.9 ** (stage_number - 1)) # Slightly faster each stage
                    game_timer = current_wave_duration
                    print(f"Starting Stage {stage_number}, Wave 1")

            # 2. Timer Logic (Wait for attack)
            elif not enemies_attacking:
                game_timer -= dt
                if game_timer <= 0:
                    game_timer = 0
                    enemies_attacking = True
                    
                    # Calculate Wave Size: Base 10 + scaling
                    wave_size = 10 + (stage_number * 5) + (wave_in_stage * 2)
                    spawn_enemy_wave(int(wave_size))

            # 3. Combat/Wave Clear Logic
            elif enemies_attacking:
                if len(enemies) == 0:
                    # Wave Cleared
                    print(f"Wave {wave_in_stage} Cleared!")
                    enemies_attacking = False
                    
                    wave_in_stage += 1
                    if wave_in_stage > 5:
                        # Stage Cleared
                        waiting_for_stage_start = True
                        stage_cooldown_timer = STAGE_COOLDOWN_TIME
                        print("Stage Cleared!")
                    else:
                        # Next Wave in same stage
                        # Reduce timer by 50% for next wave in same stage
                        current_wave_duration *= 0.5
                        game_timer = current_wave_duration
                        print(f"Next wave in {game_timer:.2f}s")

            if castle and castle.health <= 0:
                game_over = True
                print("GAME OVER")

        # --- Event Handling ---
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
                    cheese_count = 5 # Reset to default 5
                    next_windmill_cost = 0 # Reset cost
                    
                    player_placed_objects = [] 
                    windmills = [] 
                    llamas = [] 
                    mcuncles = []
                    hamsters = []
                    enemies = []
                    projectiles = []
                    selected_entity = None
                    selected_units = []
                    selected_removable_object = None 
                    delete_button_rect = None 
                    selected_llama_context = None
                    repair_button_rect = None
                    active_formation = "none" 
                    
                    # Reset Wave/Stage State
                    game_timer = INITIAL_WAVE_TIMER
                    current_wave_duration = INITIAL_WAVE_TIMER
                    stage_number = 1
                    wave_in_stage = 1
                    enemies_attacking = False
                    game_over = False
                    waiting_for_stage_start = False
                    
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
                        selected_units = [] 
                        for u in mcuncles + hamsters: u.selected = False
                        
                        ui_control_panel.build_menu_active = False 
                        ui_control_panel.castle_menu_active = False
                        ui_control_panel.llama_menu_active = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game_over: continue 

                # 1. UI Check
                if ui_control_panel.is_mouse_over(event.pos):
                    ui_action, ui_data = ui_control_panel.handle_event(event)
                    
                    if ui_action == "change_formation":
                        active_formation = ui_data
                    
                    elif ui_action == "select_asset":
                        current_tool = "place"
                        selected_asset_type = ui_data 
                        selected_removable_object = None
                        delete_button_rect = None
                        for u in selected_units: u.selected = False
                        selected_units = []
                    
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
                        for u in selected_units: u.selected = False
                        selected_units = []
                        
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
                    
                    elif ui_action == "select_all_type":
                        target_type = ui_data
                        keys = pygame.key.get_pressed()
                        shift_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
                        
                        if not shift_held:
                            for u in selected_units: u.selected = False
                            selected_units = []
                        
                        new_selection = []
                        all_units = mcuncles + hamsters
                        for u in all_units:
                            if u.name == target_type:
                                u.selected = True
                                new_selection.append(u)
                        selected_units.extend(new_selection)
                        
                        current_tool = "none"

                    continue 

                # 2. Repair Button Check
                if repair_button_rect and repair_button_rect.collidepoint(event.pos):
                    cost = castle.get_repair_cost()
                    if cheese_count >= cost:
                        cheese_count -= cost
                        castle.repair()
                        print("Castle repaired!")
                    else:
                        print("Not enough cheese to repair!")
                    continue

                if event.button == 3: # Right Click
                    mouse_screen_x, mouse_screen_y = event.pos
                    
                    # Move Command for Selected Units with Formations
                    if selected_units:
                        world_x, world_y = _screen_to_world_pixel(mouse_screen_x, mouse_screen_y)
                        
                        if active_formation == "none":
                            for u in selected_units:
                                u.set_precise_target(world_x, world_y)
                        else:
                            positions = get_formation_positions((world_x, world_y), len(selected_units), active_formation)
                            for i, unit in enumerate(selected_units):
                                if i < len(positions):
                                    tx, ty = positions[i]
                                    unit.set_precise_target(tx, ty)
                        continue

                    # If no units selected, Right Click Deselects UI/Tools
                    if current_tool != "none" or selected_removable_object or ui_control_panel.castle_menu_active or ui_control_panel.llama_menu_active:
                        current_tool = "none"
                        selected_asset_type = None
                        selected_removable_object = None
                        delete_button_rect = None
                        ui_control_panel.castle_menu_active = False
                        ui_control_panel.llama_menu_active = False
                        selected_llama_context = None
                        continue
                    
                    # Camera Pan (last resort)
                    if zoom_level > min_zoom: 
                        is_dragging = True
                        last_mouse_pos = event.pos
                    continue

                if event.button == 1: # Left Click
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

                    # Delete Logic
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
                                    # Cost Check
                                    cost = next_windmill_cost
                                    if cheese_count >= cost:
                                        new_w = Windmill((grid_r_click, grid_c_click), TILE_SIZE)
                                        windmills.append(new_w)
                                        cheese_count -= cost
                                        
                                        # Increase next cost (0 -> 5 -> 10 ...)
                                        if next_windmill_cost == 0: next_windmill_cost = 0
                                        else: next_windmill_cost += 0
                                    else:
                                        print("Not enough cheese for windmill!")
                                else:
                                    player_placed_objects.append((selected_asset_type, grid_r_click, grid_c_click)) 
                            else:
                                print("Cannot place here.")
                        continue
                    
                    # --- Normal Click Interaction ---
                    
                    # 1. Check Castle Click
                    if castle and castle.is_pixel_clicked((world_x_click, world_y_click)):
                        ui_control_panel.castle_menu_active = True
                        ui_control_panel.llama_menu_active = False
                        selected_llama_context = None
                        for u in selected_units: u.selected = False
                        selected_units = []
                        continue
                    
                    # 2. Check Llama Click
                    llama_clicked = False
                    for l in llamas:
                        if l.is_pixel_clicked((world_x_click, world_y_click)):
                            selected_llama_context = l
                            ui_control_panel.llama_menu_active = True
                            ui_control_panel.castle_menu_active = False
                            llama_clicked = True
                            break
                    if llama_clicked: continue
                    
                    # 3. Check Windmill/Static Selection
                    found_removable = False
                    for w in windmills:
                        if w.is_pixel_clicked((world_x_click, world_y_click)):
                            selected_removable_object = ("windmill", w.grid_r, w.grid_c)
                            found_removable = True
                            break
                    if not found_removable:
                        for asset_type, r, c in player_placed_objects:
                            if r == grid_r_click and c == grid_c_click:
                                selected_removable_object = (asset_type, r, c)
                                found_removable = True
                                break
                    if found_removable: 
                        for u in selected_units: u.selected = False
                        selected_units = []
                        continue
                    
                    # 4. Check Unit Click (Select)
                    clicked_unit = None
                    all_units = mcuncles + hamsters
                    for unit in all_units:
                        ux = unit.current_pixel_pos.x
                        uy = unit.current_pixel_pos.y
                        if ux <= world_x_click <= ux + TILE_SIZE and uy <= world_y_click <= uy + TILE_SIZE:
                            clicked_unit = unit
                            break
                    
                    if clicked_unit:
                        keys = pygame.key.get_pressed()
                        shift_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
                        
                        if not shift_held:
                            for u in selected_units: u.selected = False
                            selected_units = []
                        
                        if clicked_unit not in selected_units:
                            clicked_unit.selected = True
                            selected_units.append(clicked_unit)
                        elif shift_held:
                            clicked_unit.selected = False
                            selected_units.remove(clicked_unit)
                        
                        continue

                    # 5. Empty Ground Click -> Drag Selection
                    selection_drag_start = event.pos
                    selected_removable_object = None
                    delete_button_rect = None
                    ui_control_panel.castle_menu_active = False
                    ui_control_panel.llama_menu_active = False
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and selection_drag_start:
                    # Finish Drag Selection
                    drag_end = event.pos
                    x1 = min(selection_drag_start[0], drag_end[0])
                    y1 = min(selection_drag_start[1], drag_end[1])
                    w = abs(drag_end[0] - selection_drag_start[0])
                    h = abs(drag_end[1] - selection_drag_start[1])
                    
                    if w > 5 and h > 5:
                        selection_rect = pygame.Rect(x1, y1, w, h)
                        keys = pygame.key.get_pressed()
                        shift_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
                        
                        if not shift_held:
                            for u in selected_units: u.selected = False
                            selected_units = []
                            
                        all_units = mcuncles + hamsters
                        for unit in all_units:
                            unit_screen_x, unit_screen_y = _world_to_screen_pixel(
                                unit.current_pixel_pos.x + TILE_SIZE/2, 
                                unit.current_pixel_pos.y + TILE_SIZE/2
                            )
                            if selection_rect.collidepoint(unit_screen_x, unit_screen_y):
                                if unit not in selected_units:
                                    unit.selected = True
                                    selected_units.append(unit)
                    else:
                        keys = pygame.key.get_pressed()
                        shift_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
                        if not shift_held:
                             for u in selected_units: u.selected = False
                             selected_units = []

                    selection_drag_start = None
                    selection_rect = None

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
                
                if selection_drag_start:
                    drag_end = event.pos
                    x1 = min(selection_drag_start[0], drag_end[0])
                    y1 = min(selection_drag_start[1], drag_end[1])
                    w = abs(drag_end[0] - selection_drag_start[0])
                    h = abs(drag_end[1] - selection_drag_start[1])
                    selection_rect = pygame.Rect(x1, y1, w, h)

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
            
            all_friends = mcuncles + hamsters
            
            for w in windmills:
                produced = w.update(dt, hamsters=all_friends)
                if produced:
                    cheese_count += 1

            for llama in llamas: llama.update(dt, current_obstacles, pixel_obstacles, windmills)
            
            for mcuncle in mcuncles: 
                mcuncle.update(dt, enemies, projectiles, current_obstacles, pixel_obstacles, friends=all_friends)
                
            for hamster in hamsters: 
                hamster.update(dt, enemies, projectiles, current_obstacles, pixel_obstacles, friends=all_friends)
                
            for enemy in enemies: 
                enemy.update(dt, current_obstacles, castle, move_to_castle=enemies_attacking) 
            
            enemies = [e for e in enemies if e.health > 0]

        screen.fill((0, 0, 0)) 
        draw(map_data["seed"], map_data["grid"], map_data["features"], ui_control_panel)
        pygame.display.flip()
        
        await asyncio.sleep(0) 

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())