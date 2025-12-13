import asyncio # Required for Pygbag/Web
import pygame
import random
import os
import sys
import math 
import Assets 
from Entities import Llama, McUncle, Hamster, Enemy, Projectile, Castle, Windmill, CASTLE_HITBOX_WIDTH_TILES, CASTLE_HITBOX_HEIGHT_TILES, set_world_dimensions
import MenuUI 

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 1280, 720
TILE_SIZE = 64 
COLUMNS = WIDTH // TILE_SIZE
ROWS = HEIGHT // TILE_SIZE 
TILES_SEARCH_FOLDERS = ["", "tiles", "assets"] 
SAVE_FOLDER = "saved_maps"

# Update Entities module with world size for boundary clamping
set_world_dimensions(WIDTH, HEIGHT)

# Stage Configuration
STAGE_DATA = {
    1: {"wave_enemies": 5,  "hp_add": 0,  "base_time": 250.0, "dec": 0},
    2: {"wave_enemies": 5,  "hp_add": 20, "base_time": 250.0, "dec": 50.0},
    3: {"wave_enemies": 10, "hp_add": 30,  "base_time": 200.0, "dec": 50.0},
    4: {"wave_enemies": 15, "hp_add": 40,  "base_time": 200.0, "dec": 50.0},
    5: {"wave_enemies": 15, "hp_add": 50,  "base_time": 150.0, "dec": 50.0},
    6: {"wave_enemies": 20, "hp_add": 60,  "base_time": 150.0, "dec": 50.0},
    7: {"wave_enemies": 20, "hp_add": 70,  "base_time": 100.0, "dec": 50.0},
    8: {"wave_enemies": 25, "hp_add": 80,  "base_time": 100.0, "dec": 50.0},
    9: {"wave_enemies": 30, "hp_add": 90,  "base_time": 50.0,  "dec": 10.0},
    10:{"wave_enemies": 30, "hp_add": 100,  "base_time": 50.0,  "dec": 10.0},
}

# ---------------- GLOBAL STATE ----------------
# Player Interaction
current_tool = "none" 
selected_asset_type = None 
selected_entity = None 
selected_llama_context = None
selection_drag_start = None
selection_rect = None
selected_units = [] 
active_formation = "none" 
selected_removable_object = None 
delete_button_rect = None 
repair_button_rect = None
skip_button_rect = None
btn_continue_rect = None
btn_restart_rect = None

# Game Objects
player_placed_objects = [] 
llamas = []
mcuncles = []
hamsters = [] 
enemies = []  
projectiles = []
windmills = [] 
castle = None 

# Map Data
map_data = {}
grid = []
features = []
castle_occupied = set()
seed = 0

# Game Progress
cheese_count = 5 
game_timer = 0.0
wave_number = 1 
stage_number = 1 
wave_in_stage = 1 # 1, 2, 3
enemies_attacking = False
game_over = False
waiting_for_next_stage = False
stage_cooldown_timer = 0.0
survival_mode = False
survival_wave = 1
victory_screen = False
next_windmill_cost = 0

# Camera
zoom_level = 1.0 
max_zoom = 4.0 
min_zoom = 1.0 
camera_x = 0.0 
camera_y = 0.0 
render_offset_x = 0.0 
render_offset_y = 0.0 
is_dragging = False
last_mouse_pos = None 

# UI Constants
DELETE_BUTTON_TEXT = "DELETE"
DELETE_BUTTON_COLOR = (200, 50, 50) 
DELETE_TEXT_COLOR = (255, 255, 255) 
DELETE_BUTTON_PADDING = 5 

# ------------------------------------------------------------

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hamster Path Defense")
font = pygame.font.Font(None, 28)
timer_font = pygame.font.Font(None, 32)
game_over_font = pygame.font.Font(None, 64)
stage_font = pygame.font.Font(None, 48)
delete_font = pygame.font.Font(None, 32)
clock = pygame.time.Clock()

# Global dictionary for all loaded tiles
tiles = {}

world_width_pixels = COLUMNS * TILE_SIZE
world_height_pixels = ROWS * TILE_SIZE
world_surface = pygame.Surface((world_width_pixels, world_height_pixels), pygame.SRCALPHA)

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
    grid_local = [["grass" for _ in range(columns)] for _ in range(rows)]
    seed_local = random.randint(100000, 999999)
    random.seed(seed_local)
    
    exclusion_coords = set()
    for _, r, c in player_placed_objects:
        exclusion_coords.add((r,c))
    for w in windmills:
        exclusion_coords.update(w.get_occupied_coords())
    
    if extra_exclusions:
        exclusion_coords.update(extra_exclusions)
        
    features_local = generate_random_features(grid_local, rows, columns, exclusion_coords)
    
    return {
        "grid": grid_local,
        "features": features_local,
        "seed": seed_local
    }

# --- Formation Helper ---
def get_formation_positions(center_pixel_pos, unit_count, formation_type, spacing=40):
    positions = []
    cx, cy = center_pixel_pos
    
    # Clamp Center to Map Boundaries
    cx = max(spacing, min(cx, world_width_pixels - spacing))
    cy = max(spacing, min(cy, world_height_pixels - spacing))

    if unit_count == 0: return []
    if unit_count == 1: return [(cx, cy)]

    if formation_type == "line":
        MAX_PER_COL = 10
        for i in range(unit_count):
            col = i // MAX_PER_COL
            row = i % MAX_PER_COL
            current_col_len = min(MAX_PER_COL, unit_count - col*MAX_PER_COL)
            start_y = cy - (current_col_len * spacing) / 2
            
            px = cx + col * spacing
            py = start_y + row * spacing
            positions.append((px, py))
            
    elif formation_type == "double":
        row1_count = math.ceil(unit_count / 2)
        row2_count = unit_count - row1_count
        start_x = cx - spacing/2
        
        start_y1 = cy - (row1_count * spacing) / 2
        for i in range(row1_count):
            positions.append((start_x, start_y1 + i * spacing))
            
        start_y2 = cy - (row2_count * spacing) / 2
        for i in range(row2_count):
            positions.append((start_x + spacing, start_y2 + i * spacing))
            
    elif formation_type == "square":
        side = math.ceil(math.sqrt(unit_count))
        start_x = cx - (side * spacing) / 2
        start_y = cy - (side * spacing) / 2
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
        for i in range(unit_count):
            positions.append((cx, cy))
            
    return positions

# --- Spawning Helpers (Global) ---
def spawn_entities():
    global llamas
    llamas.clear()
    
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

def spawn_enemy_wave(count=10, hp_add=0):
    global enemies
    spawn_candidates = []
    for r in range(ROWS):
        if grid[r][0] == "grass":
            spawn_candidates.append((r, 0))
    
    if not spawn_candidates:
            spawn_candidates = [(r, 0) for r in range(ROWS)]
            
    for _ in range(count):
        start_pos = random.choice(spawn_candidates)
        # Pass extra health to Enemy constructor
        enemies.append(Enemy(start_pos, TILE_SIZE, extra_health=hp_add))
    print(f"Spawned wave of {count} enemies (HP +{hp_add}) from the left!")


# --- draw ---
def draw(seed, grid, features, ui_control_panel): 
    global delete_button_rect, skip_button_rect, btn_continue_rect, btn_restart_rect
    global repair_button_rect

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

    # Draw UI Panel
    needs_repair = False
    if castle and castle.health < castle.max_health:
        needs_repair = True
    
    ui_control_panel.draw(screen, active_hamsters=hamsters, active_mcuncles=mcuncles, castle_needs_repair=needs_repair)
    
    # Expose repair button rect from UI panel to global for click detection
    if ui_control_panel.castle_menu_active and needs_repair:
        repair_button_rect = ui_control_panel.repair_button_rect
    else:
        repair_button_rect = None

    # --- Top Right Info ---
    ui_x_right = WIDTH - 80 
    ui_y_right = 20
    
    # 1. Cheese Icon & Count
    if "cheese" in tiles:
        cheese_icon = pygame.transform.scale(tiles["cheese"], (40, 40))
        screen.blit(cheese_icon, (ui_x_right, ui_y_right))
        # Text to left of icon
        cheese_text = font.render(f"{cheese_count}", True, (255, 255, 255))
        screen.blit(cheese_text, (ui_x_right - cheese_text.get_width() - 5, ui_y_right + 10))
        
        # Windmill Cost
        cost_txt = ui_control_panel.price_font.render(f"Next Mill: {next_windmill_cost}", True, (200, 200, 200))
        screen.blit(cost_txt, (ui_x_right - 40, ui_y_right + 45))

    ui_y_right += 80

    # 2. Queue List (Floating on top of Castle)
    if castle:
        if hasattr(castle, 'infinite_production') and castle.infinite_production:
            cx, cy = _world_to_screen_pixel(castle.current_pixel_pos.x, castle.current_pixel_pos.y)
            inf_txt = font.render(f"Inf: {castle.infinite_production}", True, (0, 255, 255))
            screen.blit(inf_txt, (cx, cy - 60))

        if castle.training_queue:
            cx, cy = _world_to_screen_pixel(castle.current_pixel_pos.x, castle.current_pixel_pos.y)
            queue_w = 30 
            total_w = len(castle.training_queue) * (queue_w + 2)
            castle_screen_w = castle.width_tiles * TILE_SIZE * zoom_level
            start_x = cx + (castle_screen_w - total_w) / 2
            start_y = cy - 40 
            
            current_qx = start_x
            for unit_name in castle.training_queue:
                unit_icon = None
                # FIX: Check if mcuncle is dict or list to avoid KeyError
                if unit_name == "McUncle" and "mcuncle" in tiles:
                    mc_data = tiles["mcuncle"]
                    if isinstance(mc_data, dict) and "idle" in mc_data:
                        unit_icon = mc_data["idle"][0]
                    elif isinstance(mc_data, list) and mc_data:
                        unit_icon = mc_data[0]
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
    if game_timer <= 5.0 and not enemies_attacking and not waiting_for_next_stage and not victory_screen:
        timer_color = (255, 50, 50) 
    
    timer_str = ""
    skip_button_rect = None
    
    if victory_screen:
        timer_str = ""
    elif enemies_attacking:
        timer_str = "Status: WAVE ATTACK!"
        timer_color = (255, 0, 0)
    elif waiting_for_next_stage:
        timer_str = "Status: STAGE CLEARED"
    else:
        timer_str = f"Time until Enemy attacks: {int(game_timer)}s"
        # Draw Skip Button
        txt_surf = timer_font.render(timer_str, True, timer_color)
        btn_x = ui_x_left + txt_surf.get_width() + 15
        skip_button_rect = pygame.Rect(btn_x, ui_y_left, 40, 30)
        
        pygame.draw.rect(screen, (50, 150, 50), skip_button_rect, border_radius=5)
        arrow_surf = font.render(">>", True, (255, 255, 255))
        screen.blit(arrow_surf, (skip_button_rect.centerx - arrow_surf.get_width()//2, skip_button_rect.centery - arrow_surf.get_height()//2))

    if timer_str:
        txt_timer = timer_font.render(timer_str, True, timer_color)
        screen.blit(txt_timer, (ui_x_left, ui_y_left))
    
    # Stage Info
    stage_text = ""
    if survival_mode:
        stage_text = f"SURVIVAL MODE | Wave: {survival_wave}"
    else:
        stage_text = f"Stage: {stage_number}/10 | Wave: {wave_in_stage}/3"
        
    txt_stage = font.render(stage_text, True, (200, 200, 255))
    screen.blit(txt_stage, (ui_x_left, ui_y_left + 40))
    
    # --- Stage Clear Overlay ---
    if waiting_for_next_stage:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        msg = stage_font.render("Stage cleared roller", True, (0, 255, 0))
        sub = font.render(f"Next stage starts in {int(stage_cooldown_timer)} seconds, hope you are ready", True, (255, 255, 255))
        
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 50))
        screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 20))

    # --- Victory Popup ---
    if victory_screen:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        msg1 = font.render("Congratulations Roller!", True, (255, 215, 0))
        msg2 = font.render("You just defeated El Piero the Cheese boss.", True, (255, 255, 255))
        msg3 = font.render("Would you like to continue playing or start a new game?", True, (255, 255, 255))
        msg4 = font.render("If you continue, Pieros will constantly attack!", True, (255, 100, 100))
        
        screen.blit(msg1, (WIDTH//2 - msg1.get_width()//2, HEIGHT//2 - 120))
        screen.blit(msg2, (WIDTH//2 - msg2.get_width()//2, HEIGHT//2 - 80))
        screen.blit(msg3, (WIDTH//2 - msg3.get_width()//2, HEIGHT//2 - 40))
        screen.blit(msg4, (WIDTH//2 - msg4.get_width()//2, HEIGHT//2))
        
        btn_continue_rect = pygame.Rect(WIDTH//2 - 160, HEIGHT//2 + 60, 140, 50)
        btn_restart_rect = pygame.Rect(WIDTH//2 + 20, HEIGHT//2 + 60, 140, 50)
        
        pygame.draw.rect(screen, (0, 100, 0), btn_continue_rect, border_radius=5)
        pygame.draw.rect(screen, (100, 0, 0), btn_restart_rect, border_radius=5)
        
        txt_cont = font.render("Continue", True, (255, 255, 255))
        txt_rest = font.render("New Game", True, (255, 255, 255))
        
        screen.blit(txt_cont, (btn_continue_rect.centerx - txt_cont.get_width()//2, btn_continue_rect.centery - txt_cont.get_height()//2))
        screen.blit(txt_rest, (btn_restart_rect.centerx - txt_rest.get_width()//2, btn_restart_rect.centery - txt_rest.get_height()//2))

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
    global wave_number, waiting_for_next_stage, stage_cooldown_timer
    global active_formation
    global stage_number, wave_in_stage, next_windmill_cost, skip_button_rect
    global victory_screen, survival_mode, survival_wave, btn_continue_rect, btn_restart_rect
    global grid, features, castle_occupied, map_data # Ensure globals are used

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
    
    # Set init timer
    conf = STAGE_DATA[1]
    game_timer = conf["base_time"]
    
    spawn_entities()
    _clamp_camera()
    
    ui_control_panel = MenuUI.UIControlPanel(TILE_SIZE, WIDTH, HEIGHT, tiles)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0 
        
        # --- Update Infinite Production ---
        if castle and hasattr(castle, 'infinite_production') and castle.infinite_production:
            if len(castle.training_queue) < castle.max_queue_size:
                prices = {"McUncle": 30, "Bob": 5, "Dracula": 15, "TheHamster": 10}
                cost = prices.get(castle.infinite_production, 999)
                if cheese_count >= cost:
                    success = castle.queue_unit(castle.infinite_production)
                    if success:
                        cheese_count -= cost

        # --- Game Flow Logic ---
        if not game_over and not victory_screen:
            
            # 1. Stage Break
            if waiting_for_next_stage:
                stage_cooldown_timer -= dt
                if stage_cooldown_timer <= 0:
                    waiting_for_next_stage = False
                    enemies_attacking = False
                    
                    if not survival_mode:
                        # Start Next Stage
                        stage_number += 1
                        wave_in_stage = 1
                        if stage_number > 10:
                            stage_number = 10 # Cap
                        conf = STAGE_DATA[stage_number]
                        game_timer = conf["base_time"] 
                        print(f"Starting Stage {stage_number}, Wave 1")
                    else:
                        survival_wave += 1
                        game_timer = 5.0 
                        print(f"Starting Survival Wave {survival_wave}")

            # 2. Timer Logic (Wait for attack)
            elif not enemies_attacking:
                game_timer -= dt
                if game_timer <= 0:
                    game_timer = 0
                    enemies_attacking = True
                    
                    if survival_mode:
                        count = 50 + (survival_wave * 5)
                        hp_add = 50 + (survival_wave * 10)
                        spawn_enemy_wave(int(count), hp_add)
                    else:
                        conf = STAGE_DATA[stage_number]
                        count = conf["wave_enemies"]
                        hp = conf["hp_add"]
                        spawn_enemy_wave(count, hp)

            # 3. Wave Clear Logic
            elif enemies_attacking:
                if len(enemies) == 0:
                    enemies_attacking = False
                    
                    if survival_mode:
                        game_timer = 10.0 
                        print(f"Survival Wave {survival_wave} Cleared. Cooldown 10s.")
                    else:
                        print(f"Stage {stage_number} - Wave {wave_in_stage} Cleared!")
                        wave_in_stage += 1
                        if wave_in_stage > 3: 
                            if stage_number == 10:
                                victory_screen = True
                            else:
                                waiting_for_next_stage = True
                                stage_cooldown_timer = 10.0 # 10 seconds break
                                print("Stage Cleared!")
                        else:
                            conf = STAGE_DATA[stage_number]
                            next_time = conf["base_time"] - ((wave_in_stage - 1) * conf["dec"])
                            if next_time < 10: next_time = 10
                            game_timer = next_time
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
                if event.key == pygame.K_r: 
                    print("\nRegenerating map...")
                    cheese_count = 5 
                    next_windmill_cost = 0
                    
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
                    
                    stage_number = 1
                    wave_in_stage = 1
                    survival_mode = False
                    survival_wave = 1
                    victory_screen = False
                    
                    conf = STAGE_DATA[1]
                    game_timer = conf["base_time"]
                    
                    enemies_attacking = False
                    game_over = False
                    waiting_for_next_stage = False
                    
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
                    if game_over or victory_screen:
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
                
                if victory_screen:
                    if btn_continue_rect and btn_continue_rect.collidepoint(event.pos):
                        victory_screen = False
                        survival_mode = True
                        game_timer = 5.0
                        print("Entering Survival Mode!")
                    elif btn_restart_rect and btn_restart_rect.collidepoint(event.pos):
                        # Force restart via recursion or event post
                        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
                    continue

                if skip_button_rect and skip_button_rect.collidepoint(event.pos) and not enemies_attacking and not waiting_for_next_stage:
                    game_timer = 0 
                    continue

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
                                    castle.infinite_production = None
                            else:
                                print("Not enough cheese!")
                                
                    elif ui_action == "train_unit_infinite":
                        if castle and isinstance(ui_data, dict):
                            name = ui_data["name"]
                            if castle.infinite_production == name:
                                castle.infinite_production = None
                            else:
                                castle.infinite_production = name

                    elif ui_action == "repair_castle":
                        if castle:
                            cost = castle.get_repair_cost()
                            if cheese_count >= cost:
                                cheese_count -= cost
                                castle.repair()
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

                if event.button == 3: # Right Click
                    # Cancel placement if active
                    if current_tool == "place":
                        current_tool = "none"
                        selected_asset_type = None
                        continue

                    mouse_screen_x, mouse_screen_y = event.pos
                    
                    if selected_units:
                        world_x, world_y = _screen_to_world_pixel(mouse_screen_x, mouse_screen_y)
                        world_x = max(0, min(world_x, world_width_pixels))
                        world_y = max(0, min(world_y, world_height_pixels))
                        
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

                    if current_tool != "none" or selected_removable_object or ui_control_panel.castle_menu_active or ui_control_panel.llama_menu_active:
                        current_tool = "none"
                        selected_asset_type = None
                        selected_removable_object = None
                        delete_button_rect = None
                        ui_control_panel.castle_menu_active = False
                        ui_control_panel.llama_menu_active = False
                        selected_llama_context = None
                        continue
                    
                    if zoom_level > min_zoom: 
                        is_dragging = True
                        last_mouse_pos = event.pos
                    continue

                if event.button == 1: # Left Click
                    mouse_screen_x, mouse_screen_y = event.pos
                    grid_r_click, grid_c_click = _screen_to_world_grid(mouse_screen_x, mouse_screen_y)
                    world_x_click, world_y_click = _screen_to_world_pixel(mouse_screen_x, mouse_screen_y)

                    if current_tool == "set_rally":
                        if castle:
                            if 0 <= grid_r_click < ROWS and 0 <= grid_c_click < COLUMNS:
                                castle.set_rally_point(grid_r_click, grid_c_click)
                                current_tool = "none"
                                continue

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

                    if current_tool == "place": 
                        if 0 <= grid_r_click < ROWS and 0 <= grid_c_click < COLUMNS:
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
                                    cost = next_windmill_cost
                                    if cheese_count >= cost:
                                        new_w = Windmill((grid_r_click, grid_c_click), TILE_SIZE)
                                        windmills.append(new_w)
                                        cheese_count -= cost
                                        if next_windmill_cost == 0: next_windmill_cost = 5
                                        else: next_windmill_cost += 5
                                    else:
                                        print("Not enough cheese for windmill!")
                                else:
                                    player_placed_objects.append((selected_asset_type, grid_r_click, grid_c_click)) 
                            else:
                                print("Cannot place here.")
                        continue
                    
                    if castle and castle.is_pixel_clicked((world_x_click, world_y_click)):
                        ui_control_panel.castle_menu_active = True
                        ui_control_panel.llama_menu_active = False
                        selected_llama_context = None
                        for u in selected_units: u.selected = False
                        selected_units = []
                        continue
                    
                    llama_clicked = False
                    for l in llamas:
                        if l.is_pixel_clicked((world_x_click, world_y_click)):
                            selected_llama_context = l
                            ui_control_panel.llama_menu_active = True
                            ui_control_panel.castle_menu_active = False
                            llama_clicked = True
                            break
                    if llama_clicked: continue
                    
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

                    selection_drag_start = event.pos
                    selected_removable_object = None
                    delete_button_rect = None
                    ui_control_panel.castle_menu_active = False
                    ui_control_panel.llama_menu_active = False
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and selection_drag_start:
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

        if not game_over and not victory_screen:
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