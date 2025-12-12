import pygame
import random
import os
import sys
from collections import deque

# --- Autotiling specific configuration (moved from MapRandomizer.py) ---
PATH_FILE_MAPPING = {
    # Bitmask: 1=Up, 2=Right, 4=Down, 8=Left
    10: "PathSpriteHorizontal.png",  # Left (8) + Right (2)
    5:  "PathSpriteVertical.png",    # Up (1) + Down (4)
    3:  "PathSpriteTopRight.png",    # Up (1) + Right (2)
    6:  "PathSpriteBottomRight.png", # Right (2) + Down (4)
    9:  "PathSpriteTopleft.png",     # Up (1) + Left (8)
    12: "PathSpriteBottomLeft.png",  # Left (8) + Down (4)
    11: "PathSprite1.png",           # Up (1) + Left (8) + Right (2) -> T-opens Down
    14: "PathSprite2.png",           # Right (2) + Down (4) + Left (8) -> T-opens Up
    13: "PathSprite4.png",           # Up (1) + Down (4) + Left (8) -> T-opens Right
    15: "PathSpriteCross.png",       # Up (1) + Right (2) + Down (4) + Left (8)
}

# The ONLY bitmasks that should visually appear as path segments in the final output.
DISPLAY_VALID_PATH_BITMASKS = set(PATH_FILE_MAPPING.keys())

# Allows all bitmasks during generation for maximum flexibility.
# Strictness is enforced by other checks in is_move_valid and by post_process_path.
GENERATION_ALLOWED_BITMASKS = set(range(16))

# --- Internal storage for loaded path tiles ---
_loaded_path_sprites = {} # Will store 'path_base_texture' and 'path_X' surfaces

# --- Helper: locate images in possible folders ---
def _find_image_file(name_with_extension, search_folders, subfolder_path=""):
    """
    Locates an image file within specified search folders.
    If subfolder_path is provided, it's joined with search_folder.
    """
    for folder in search_folders:
        if subfolder_path:
            path = os.path.join(folder, subfolder_path, name_with_extension)
        else:
            path = os.path.join(folder, name_with_extension)
        
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"Could not find '{name_with_extension}' in {search_folders} (or subfolder '{subfolder_path}')")


# --- Load path-specific tiles ---
def load_path_assets(tile_size, tiles_search_folders, path_tile_subfolder):
    """
    Loads and scales all path-related sprites into an internal dictionary.
    Called once during initialization.
    """
    global _loaded_path_sprites
    
    # Load the base path texture (PathSpriteGrass.png)
    try:
        path = _find_image_file("PathSpriteGrass.png", tiles_search_folders, path_tile_subfolder)
        img = pygame.image.load(path).convert_alpha()
        _loaded_path_sprites["path_base_texture"] = pygame.transform.scale(img, (tile_size, tile_size))
    except FileNotFoundError as e:
        print(f"CRITICAL ERROR: Could not find 'PathSpriteGrass.png' for base path texture: {e}")
        raise # Re-raise to stop program
    except Exception as e:
        print(f"An unexpected error occurred loading and scaling PathSpriteGrass.png: {e}")
        raise # Re-raise for unexpected errors

    # Load individual path tiles from subfolder
    magenta_surface = pygame.Surface((tile_size, tile_size))
    magenta_surface.fill((255, 0, 255)) # Bright Magenta for debugging
    
    for bitmask in range(16): # From 0 to 15
        if bitmask in PATH_FILE_MAPPING:
            tile_filename = PATH_FILE_MAPPING[bitmask]
            try:
                path = _find_image_file(tile_filename, tiles_search_folders, path_tile_subfolder)
                img = pygame.image.load(path).convert_alpha()
                _loaded_path_sprites[f"path_{bitmask}"] = pygame.transform.scale(img, (tile_size, tile_size))
            except FileNotFoundError as e:
                print(f"DEBUG_LOAD: Missing REQUIRED path tile for bitmask {bitmask} (file: '{os.path.join(path_tile_subfolder, tile_filename)}'). Rendering magenta.")
                _loaded_path_sprites[f"path_{bitmask}"] = magenta_surface # Fallback to magenta for debugging
            except Exception as e:
                print(f"DEBUG_LOAD: Error loading path tile '{tile_filename}': {e}. Rendering magenta.")
                _loaded_path_sprites[f"path_{bitmask}"] = magenta_surface # Fallback to magenta for other errors
        else:
            # For bitmasks not in PATH_FILE_MAPPING (e.g., 0, 1, 2, 4, 7, 8)
            # These are allowed for generation but will be removed by post_processing.
            _loaded_path_sprites[f"path_{bitmask}"] = magenta_surface 


# --- Autotiling logic: determine which path tile to use ---
def get_bitmask_for_cell(r, c, current_grid, rows, columns):
    bitmask = 0
    # Check Up neighbor (bit 0)
    if r > 0 and current_grid[r-1][c] == "path":
        bitmask |= 1
    # Check Right neighbor (bit 1)
    if c < columns - 1 and current_grid[r][c+1] == "path":
        bitmask |= 2
    # Check Down neighbor (bit 2)
    if r < rows - 1 and current_grid[r+1][c] == "path":
        bitmask |= 4
    # Check Left neighbor (bit 3)
    if c > 0 and current_grid[r][c-1] == "path":
        bitmask |= 8
    return bitmask

def get_autotile_path_surface(r, c, grid, rows, columns):
    """
    Returns the appropriate Pygame Surface for a path tile at (r,c) based on its neighbors.
    Includes visual overrides for map edges.
    """
    # Visual override for start/end points to appear as horizontal path
    if c == 0 and grid[r][c] == "path":
        return _loaded_path_sprites.get("path_10", _loaded_path_sprites["path_base_texture"]) # Force horizontal path for left edge
    if c == columns - 1 and grid[r][c] == "path":
        return _loaded_path_sprites.get("path_10", _loaded_path_sprites["path_base_texture"]) # Force horizontal path for right edge

    bitmask = get_bitmask_for_cell(r, c, grid, rows, columns)
    path_tile_key = f"path_{bitmask}"
    return _loaded_path_sprites.get(path_tile_key, _loaded_path_sprites["path_base_texture"]) # Fallback to base texture if specific bitmask not found (should be caught by post-processing)


# --- Validation for single-width path without unwanted elements ---

def _is_forming_full_2x2(test_grid, r_check, c_check, rows, columns):
    """
    Checks if the cell at (r_check, c_check) is part of a 2x2 square where
    all four cells are path tiles. This detects full 2x2 solid blocks.
    """
    if test_grid[r_check][c_check] != "path":
        return False

    potential_2x2_top_lefts = [
        (r_check, c_check),       # (r_check, c_check) is top-left
        (r_check, c_check - 1),   # (r_check, c_check) is top-right
        (r_check - 1, c_check),   # (r_check, c_check) is bottom-left
        (r_check - 1, c_check - 1) # (r_check, c_check) is bottom-right
    ]

    for tl_r, tl_c in potential_2x2_top_lefts:
        if not (0 <= tl_r < rows - 1 and 0 <= tl_c < columns - 1):
            continue

        if (test_grid[tl_r][tl_c] == "path" and
            test_grid[tl_r][tl_c + 1] == "path" and
            test_grid[tl_r + 1][tl_c] == "path" and
            test_grid[tl_r + 1][tl_c + 1] == "path"):
            return True
            
    return False

# Helper functions for general connectivity
def _has_general_horizontal_connectivity(grid, r, c, rows, columns):
    """Checks if a path tile at (r,c) is part of a generally horizontal segment (connected left & right)."""
    if not (0 <= r < rows and 0 <= c < columns and grid[r][c] == "path"): return False
    bitmask = get_bitmask_for_cell(r, c, grid, rows, columns)
    return (bitmask & 2 and bitmask & 8) # True if Right (2) and Left (8) bits are set

def _has_general_vertical_connectivity(grid, r, c, rows, columns):
    """Checks if a path tile at (r,c) is part of a generally vertical segment (connected up & down)."""
    if not (0 <= r < rows and 0 <= c < columns and grid[r][c] == "path"): return False
    bitmask = get_bitmask_for_cell(r, c, grid, rows, columns)
    return (bitmask & 1 and bitmask & 4) # True if Up (1) and Down (4) bits are set


def _is_forming_double_straight_explicit(test_grid, r, c, rows, columns):
    """
    Checks if a path tile at (r, c) creates a 'double' straight segment
    with an adjacent tile that also exhibits general straight orientation.
    This prevents two generally horizontal path segments from being vertically adjacent,
    or two generally vertical path segments from being horizontally adjacent.
    """
    if test_grid[r][c] != "path":
        return False

    # Check for double horizontal: current tile has general horizontal connectivity,
    # and an adjacent vertical neighbor also has general horizontal connectivity.
    if _has_general_horizontal_connectivity(test_grid, r, c, rows, columns):
        # Check cell above
        if r > 0 and test_grid[r-1][c] == "path":
            if _has_general_horizontal_connectivity(test_grid, r-1, c, rows, columns):
                return True
        # Check cell below
        if r < rows - 1 and test_grid[r+1][c] == "path":
            if _has_general_horizontal_connectivity(test_grid, r+1, c, rows, columns):
                return True

    # Check for double vertical: current tile has general vertical connectivity,
    # and an adjacent horizontal neighbor also has general vertical connectivity.
    if _has_general_vertical_connectivity(test_grid, r, c, rows, columns):
        # Check cell left
        if c > 0 and test_grid[r][c-1] == "path":
            if _has_general_vertical_connectivity(test_grid, r, c-1, rows, columns):
                return True
        # Check cell right
        if c < columns - 1 and test_grid[r][c+1] == "path":
            if _has_general_vertical_connectivity(test_grid, r, c+1, rows, columns):
                return True
                
    return False


def is_move_valid(current_grid, cur_row, cur_col, next_r, next_c, allowed_bitmasks_set, rows, columns):
    # 1. Basic bounds check
    if not (0 <= next_r < rows and 0 <= next_c < columns):
        return False

    # 2. Prevent revisiting already placed path tiles (ensures single path)
    if current_grid[next_r][next_c] == "path":
        return False

    # Create a temporary grid to simulate the move
    temp_grid = [row[:] for row in current_grid] # Deep copy
    temp_grid[next_r][next_c] = "path" # Simulate placing the new path tile

    # 3. Check for structural violations (full 2x2 blocks and double straights)
    # Apply these checks to the new tile and its immediate neighbors, as their inclusion
    # could complete a forbidden pattern.
    affected_cells_for_structure_check = set()
    affected_cells_for_structure_check.add((next_r, next_c))
    # Include 8 surrounding neighbors for comprehensive checks around the new tile.
    for dr, dc in [(-1,0), (1,0), (0,1), (0,-1), (-1,-1), (-1,1), (1,-1), (1,1)]: 
        nr, nc = next_r + dr, next_c + dc
        if 0 <= nr < rows and 0 <= nc < columns:
            affected_cells_for_structure_check.add((nr, nc))

    for r_check, c_check in affected_cells_for_structure_check:
        if temp_grid[r_check][c_check] == "path": # Only check path cells
            # Prevent full 2x2 solid blocks
            if _is_forming_full_2x2(temp_grid, r_check, c_check, rows, columns):
                return False
            # Prevent adjacent parallel *general* straight segments
            if _is_forming_double_straight_explicit(temp_grid, r_check, c_check, rows, columns):
                return False
    
    return True


# --- Debug Helper: Print Grid State ---
def print_grid_state(grid, message, rows, columns):
    print(f"\n--- {message} ---")
    for r in range(rows):
        row_str = ""
        for c in range(columns):
            if grid[r][c] == "path":
                row_str += "#"
            else:
                row_str += "."
        print(row_str)
    print("-------------------")


def post_process_path(grid, initial_path_start_coords, desired_bitmasks_set, rows, columns):
    """
    Iterates through the generated path and performs a two-stage cleanup:
    1. Removes any path segments not connected to the main path from its actual start to the right edge.
    2. For remaining connected internal tiles, reverts those that don't match desired
       displayable bitmasks back to grass, fixing "R-shapes" and broken connections.
    """
    # Create a copy of the grid for Stage 1 decisions, to avoid self-modifying issues
    decision_grid_stage1 = [row[:] for row in grid]
    
    # Stage 1: Identify the main connected path from its actual start point to the right edge
    main_connected_path_coords = set()
    q = deque() # Use deque for efficient BFS

    # Start BFS from the initial path placement cell (initial_r, initial_c)
    start_r, start_c = initial_path_start_coords
    if decision_grid_stage1[start_r][start_c] == "path": # Ensure the start point is still valid
        q.append((start_r, start_c))
        main_connected_path_coords.add((start_r, start_c))
    else:
        # If the actual start point got removed somehow before post_processing, the path is broken.
        # This will lead to generate_path_grid_attempt's final recheck failing.
        return 

    # Perform BFS to find all connected path tiles from the initial start point
    while q:
        r, c = q.popleft()
        
        for dr, dc in [(-1,0), (1,0), (0,1), (0,-1)]: # Up, Down, Right, Left
            nr, nc = r + dr, c + dc
            if (0 <= nr < rows and 0 <= nc < columns and
                decision_grid_stage1[nr][nc] == "path" and (nr, nc) not in main_connected_path_coords):
                main_connected_path_coords.add((nr, nc))
                q.append((nr, nc))
    
    # Collect coordinates for tiles to remove in Stage 1
    coords_to_remove_stage1 = set()
    for r in range(rows):
        for c in range(columns):
            # Only remove if it was a path in the decision_grid_stage1 and not part of the main connected path
            if decision_grid_stage1[r][c] == "path" and (r, c) not in main_connected_path_coords:
                coords_to_remove_stage1.add((r, c))
    
    # Apply Stage 1 removals to the actual grid
    for r, c in coords_to_remove_stage1:
        grid[r][c] = "grass"

    # Now, with disconnected segments removed, create a new decision_grid snapshot
    # for Stage 2, reflecting the grid after Stage 1's changes.
    decision_grid_after_stage1 = [row[:] for row in grid]

    # Stage 2: Validate visual shapes of remaining connected path tiles (fix "R-shapes")
    coords_to_remove_stage2 = set()
    for r in range(rows):
        for c in range(columns):
            # Only process if it's still a path tile after Stage 1 cleanup
            if decision_grid_after_stage1[r][c] == "path":
                
                # Special handling for cells on the far left (c=0) or far right (c=columns-1) edges.
                # Their visual is handled by get_autotile_path_surface override, and they are allowed
                # to be single-connected if they are the actual entrance/exit of the main path.
                # Do not apply strict bitmask validation to these special edge cells.
                if c == 0 or c == columns - 1:
                    continue

                # For all other internal path tiles (not on side edges):
                # Calculate its current bitmask based on its neighbors in the current decision_grid.
                bitmask = get_bitmask_for_cell(r, c, decision_grid_after_stage1, rows, columns)
                
                # If its bitmask is NOT one of the final desired displayable path types,
                # it's an unwanted segment (e.g., a single connection dead-end / "R-shape" or a broken corner).
                # Mark it for removal.
                if bitmask not in desired_bitmasks_set:
                    coords_to_remove_stage2.add((r, c))
    
    # Apply Stage 2 removals to the actual grid
    for r, c in coords_to_remove_stage2:
        grid[r][c] = "grass"


# --- Path Generator Entry Point ---
def generate_path_grid_attempt(seed, rows, columns, tiles_search_folders, path_tile_subfolder, min_path_length, edge_buffer):
    """
    Attempts to generate a single-line path grid.
    Returns {grid, start_edge, traversable_path_coords, seed, features} on success, None on failure.
    """
    random.seed(seed)

    grid = [["grass" for _ in range(columns)] for _ in range(rows)]
    visited = set()

    # Choose start edge (allowing left, top, bottom starts)
    start_edge = random.choice(["left", "top", "bottom"])
    
    initial_r, initial_c = -1, -1 # Store initial path coordinates
    if start_edge == "left":
        initial_c = 0
        initial_r = random.randint(1, rows-2) 
    elif start_edge == "top":
        initial_r = 0
        initial_c = random.randint(1, columns-2) 
    else: # bottom
        initial_r = rows-1
        initial_c = random.randint(1, columns-2) 

    cur_row, cur_col = initial_r, initial_c

    # Place the initial path segment
    grid[cur_row][cur_col] = "path"
    visited.add((cur_row, cur_col))
    path_length = 1
    # print(f"Placed path at ({cur_row}, {cur_col}) (Start)") # Debug print

    target_col = columns-1
    target_row = random.randint(1, rows-2) 

    max_steps_per_attempt = columns * rows * 5 
    steps = 0

    while (cur_col < target_col or path_length < min_path_length) and steps < max_steps_per_attempt:
        steps += 1
        
        directions = [(0,1), (1,0), (-1,0), (0,-1)] # Right, Down, Up, Left
        random.shuffle(directions) 
        
        weighted_moves = []
        for drow, dcol in directions:
            weight = 1 
            if dcol > 0: weight += 5 
            elif dcol < 0: weight -= 2 
            
            if (drow != 0) and ( (cur_row + drow <= edge_buffer) or (cur_row + drow >= rows - 1 - edge_buffer) ):
                weight -= 1 
            
            if (cur_row + drow, cur_col + dcol) in visited and dcol < 0: 
                weight -= 3

            for _ in range(max(1, weight)): 
                weighted_moves.append((drow, dcol))

        if not weighted_moves:
            break 

        random.shuffle(weighted_moves) 
        
        found_valid_move = False
        for drow, dcol in weighted_moves:
            next_r, next_c = cur_row + drow, cur_col + dcol 

            if is_move_valid(grid, cur_row, cur_col, next_r, next_c, GENERATION_ALLOWED_BITMASKS, rows, columns): 
                grid[next_r][next_c] = "path" 
                visited.add((next_r, next_c)) 
                cur_row, cur_col = next_r, next_c 
                path_length += 1 
                # print(f"Placed path at ({cur_row}, {cur_col})") # Debug print
                found_valid_move = True
                break 
        
        if not found_valid_move:
            break 


    # Post-generation connection reinforcement to the right edge.
    safety_break = 0
    while cur_col < target_col and safety_break < columns * 2: 
        safety_break += 1
        
        possible_edge_moves = [(0,1)] 
        if cur_row < target_row: possible_edge_moves.append((1,0)) 
        elif cur_row > target_row: possible_edge_moves.append((-1,0)) 
        
        random.shuffle(possible_edge_moves) 
        
        edge_move_found = False
        for drow, dcol in possible_edge_moves:
            next_r, next_c = cur_row + drow, cur_col + dcol
            if is_move_valid(grid, cur_row, cur_col, next_r, next_c, GENERATION_ALLOWED_BITMASKS, rows, columns): 
                grid[next_r][next_c] = "path"
                visited.add((next_r, next_c))
                cur_row, cur_col = next_r, next_c
                path_length += 1
                # print(f"Placed path at ({cur_row}, {cur_col}) (Edge connect)") # Debug print
                edge_move_found = True
                break
        
        if not edge_move_found and cur_col < target_col:
            break 
            
    # Final check for path success criteria
    connected_to_right_edge = False
    actual_path_len = 0 

    # print_grid_state(grid, "Path after initial generation (before post-processing)", rows, columns)

    if path_length >= min_path_length and cur_col == columns - 1:
        post_process_path(grid, (initial_r, initial_c), DISPLAY_VALID_PATH_BITMASKS, rows, columns)
        
        # print_grid_state(grid, "Path after post-processing", rows, columns)

        temp_visited_for_recheck = set()
        recheck_q = deque()
        
        # Start re-check BFS from the cleaned initial path cell
        if grid[initial_r][initial_c] == "path":
            recheck_q.append((initial_r, initial_c))
            temp_visited_for_recheck.add((initial_r, initial_c))
        else:
            return None # Start point was removed, path is definitely broken.
        
        # Track the sequential path for AI
        traversable_path_coords = []
        path_queue_for_traversal = deque()
        path_queue_for_traversal.append((initial_r, initial_c))
        traversable_visited = set([(initial_r, initial_c)])

        while path_queue_for_traversal:
            r, c = path_queue_for_traversal.popleft()
            traversable_path_coords.append((r, c)) # Add to sequential path
            
            if c == columns - 1:
                connected_to_right_edge = True
            
            # Prioritize moving right to ensure the AI gets a forward-moving path
            preferred_directions = [(0,1), (1,0), (-1,0), (0,-1)] # Right, Down, Up, Left
            
            for dr, dc in preferred_directions:
                nr, nc = r + dr, c + dc
                if (0 <= nr < rows and 0 <= nc < columns and
                    grid[nr][nc] == "path" and (nr, nc) not in traversable_visited):
                    traversable_visited.add((nr, nc))
                    path_queue_for_traversal.append((nr, nc))
        
        actual_path_len = len(traversable_path_coords) # Actual length after cleanup and BFS traversal

        if connected_to_right_edge and actual_path_len >= min_path_length / 2: 
            # Successfully generated and cleaned path, now add features
            features = []
            for r in range(rows):
                for c in range(columns):
                    if grid[r][c] == "grass": # Only place features on actual grass
                        roll = random.random()
                        if roll < 0.07: # 7% chance for a tree
                            features.append(("tree", r, c))
                        elif roll < 0.10: # 3% chance for a rock (7% + 3% = 10%)
                            features.append(("rock", r, c))
                        elif roll < 0.11: # 1% chance for a bonus (10% + 1% = 11%)
                            features.append(("bonus", r, c))

            return {
                "grid": grid,
                "start_edge": start_edge,
                "traversable_path_coords": traversable_path_coords,
                "seed": seed,
                "features": features
            }
    
    return None # Indicate failure
