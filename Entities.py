import pygame
import random
import Assets

# --- Global Gameplay Settings ---
UNIT_DAMAGE = {
    "McUncle": 50,      
    "Bob": 5,           
    "Dracula": 30,      
    "TheHamster": 20    
}

BOB_BOOST_PER_UNIT = 0.5
SEPARATION_RADIUS = 30.0
SEPARATION_FORCE = 200.0

# Map Boundaries (Set from main.py)
WORLD_WIDTH_PX = 1280
WORLD_HEIGHT_PX = 720

def set_world_dimensions(w, h):
    global WORLD_WIDTH_PX, WORLD_HEIGHT_PX
    WORLD_WIDTH_PX = w
    WORLD_HEIGHT_PX = h

# --- Global Castle Settings ---
CASTLE_HITBOX_WIDTH_TILES = 4
CASTLE_HITBOX_HEIGHT_TILES = 4
CASTLE_VISUAL_WIDTH_TILES = 4
CASTLE_VISUAL_HEIGHT_TILES = 4
CASTLE_VISUAL_OFFSET_X_TILES = 0.0
CASTLE_VISUAL_OFFSET_Y_TILES = 0.0
SHOW_CASTLE_BORDER = False
CASTLE_BORDER_COLOR = (255, 255, 0)

def set_castle_dimensions(hitbox_w, hitbox_h, visual_w, visual_h):
    global CASTLE_HITBOX_WIDTH_TILES, CASTLE_HITBOX_HEIGHT_TILES
    global CASTLE_VISUAL_WIDTH_TILES, CASTLE_VISUAL_HEIGHT_TILES
    CASTLE_HITBOX_WIDTH_TILES = hitbox_w
    CASTLE_HITBOX_HEIGHT_TILES = hitbox_h
    CASTLE_VISUAL_WIDTH_TILES = visual_w
    CASTLE_VISUAL_HEIGHT_TILES = visual_h

class Projectile:
    def __init__(self, start_pos, target, shooter_name):
        self.pos = pygame.Vector2(start_pos)
        self.target = target 
        self.speed = 8.0
        self.damage = UNIT_DAMAGE.get(shooter_name, 10)
        self.active = True
        self.image = None
        key = None
        if shooter_name == "McUncle": key = "McUncle"
        elif shooter_name == "Bob": key = "Bob"
        elif shooter_name == "Dracula": key = "Dracula"
        elif shooter_name == "TheHamster": key = "TheHamster"
        if key and key in Assets._loaded_projectiles:
            self.image = Assets._loaded_projectiles[key]
        
    def update(self, dt):
        if not self.active: return
        if self.target.health <= 0:
            self.active = False
            return
        target_center = pygame.Vector2(
            self.target.current_pixel_pos.x + self.target.tile_size/2,
            self.target.current_pixel_pos.y + self.target.tile_size/2
        )
        direction = target_center - self.pos
        dist = direction.length()
        if dist < self.speed:
            self.pos = target_center
            self.target.take_damage(self.damage)
            self.active = False
        else:
            self.pos += direction.normalize() * self.speed

    def draw(self, screen):
        if self.image and self.active:
            rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            screen.blit(self.image, rect)

class FlagPole:
    def __init__(self, grid_pos, tile_size):
        self.grid_r, self.grid_c = grid_pos
        self.tile_size = tile_size
        self.pos = pygame.Vector2(self.grid_c * tile_size, self.grid_r * tile_size)
        self.image = Assets._loaded_assets.get("flagpole")

    def set_pos(self, grid_r, grid_c):
        self.grid_r = grid_r
        self.grid_c = grid_c
        self.pos = pygame.Vector2(self.grid_c * self.tile_size, self.grid_r * self.tile_size)

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, (self.pos.x, self.pos.y))

class Windmill:
    def __init__(self, start_grid_pos, tile_size):
        self.grid_r, self.grid_c = start_grid_pos
        self.tile_size = tile_size
        self.width_tiles = 2
        self.height_tiles = 2
        
        self.current_pixel_pos = pygame.Vector2(
            self.grid_c * self.tile_size,
            self.grid_r * self.tile_size
        )
        
        self.sprites = Assets._loaded_assets.get("windmill", [])
        self.alfalfa_sprite = Assets._loaded_assets.get("alfalfa")
        
        self.masks = []
        for s in self.sprites:
            self.masks.append(pygame.mask.from_surface(s))
            
        self.animation_frame = 0
        self.animation_speed = 0.05 
        self.animation_timer = 0.0
        
        # Cheese Logic
        self.cheese_timer = 0.0
        self.CHEESE_GENERATION_TIME = 10.0
        
        self.static_llamas = [] 
        self._init_static_llamas()

    def _init_static_llamas(self):
        frames = []
        if "eat" in Assets._loaded_llama_sprites and "south" in Assets._loaded_llama_sprites["eat"]:
            frames = Assets._loaded_llama_sprites["eat"]["south"]
        if not frames: return

        alfalfa_coords = self.get_alfalfa_coords()
        if len(alfalfa_coords) >= 4:
            alfalfa_coords.sort()
            selected_coords = [
                alfalfa_coords[1], 
                alfalfa_coords[len(alfalfa_coords)//2 - 1], 
                alfalfa_coords[len(alfalfa_coords)//2 + 2], 
                alfalfa_coords[-2] 
            ]
        else:
            selected_coords = alfalfa_coords[:4]

        for r, c in selected_coords:
            sprite_w = self.tile_size * Assets.LLAMA_SCALE_FACTOR
            offset_x = (self.tile_size - sprite_w) / 2
            offset_y = (self.tile_size - sprite_w) / 2 

            px = c * self.tile_size + offset_x
            py = r * self.tile_size + offset_y
            
            start_frame = random.randint(0, len(frames) - 1)
            
            self.static_llamas.append({
                'frames': frames,
                'x': px,
                'y': py,
                'frame_idx': float(start_frame)
            })

    def get_alfalfa_coords(self):
        coords = []
        for dr in range(-1, self.height_tiles + 1):
            for dc in range(-1, self.width_tiles + 1):
                if 0 <= dr < self.height_tiles and 0 <= dc < self.width_tiles:
                    continue 
                coords.append((self.grid_r + dr, self.grid_c + dc))
        return coords

    def update(self, dt, hamsters=[]):
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            if self.sprites:
                self.animation_frame = (self.animation_frame + 1) % len(self.sprites)
            self.animation_timer = 0.0
            
        llama_anim_speed = 8.0 * dt 
        for llama in self.static_llamas:
            llama['frame_idx'] += llama_anim_speed
            if llama['frame_idx'] >= len(llama['frames']):
                llama['frame_idx'] = 0
        
        center = self.current_pixel_pos + pygame.Vector2(self.tile_size, self.tile_size)
        boost_multiplier = 1.0
        
        for h in hamsters:
            if h.name == "Bob":
                h_center = h.current_pixel_pos + pygame.Vector2(self.tile_size/2, self.tile_size/2)
                if center.distance_to(h_center) < 150: 
                    boost_multiplier += BOB_BOOST_PER_UNIT

        time_increment = dt * boost_multiplier
        self.cheese_timer += time_increment
        cheese_produced = 0
        if self.cheese_timer >= self.CHEESE_GENERATION_TIME:
            self.cheese_timer = 0.0
            cheese_produced = 1
            
        return cheese_produced

    def get_progress(self):
        return min(1.0, self.cheese_timer / self.CHEESE_GENERATION_TIME)

    def draw(self, screen):
        if self.alfalfa_sprite:
            for r, c in self.get_alfalfa_coords():
                draw_x = c * self.tile_size
                draw_y = r * self.tile_size
                screen.blit(self.alfalfa_sprite, (draw_x, draw_y))

        for llama in self.static_llamas:
            frames = llama['frames']
            idx = int(llama['frame_idx']) % len(frames)
            img = frames[idx]
            screen.blit(img, (llama['x'], llama['y']))

        if self.sprites:
            sprite = self.sprites[self.animation_frame]
            screen.blit(sprite, (self.current_pixel_pos.x, self.current_pixel_pos.y))
        
        bar_w = self.width_tiles * self.tile_size
        bar_h = 8
        x = self.current_pixel_pos.x
        y = self.current_pixel_pos.y - 12
        progress = self.get_progress()
        pygame.draw.rect(screen, (50, 50, 50), (x, y, bar_w, bar_h))
        pygame.draw.rect(screen, (255, 215, 0), (x, y, bar_w * progress, bar_h))
        pygame.draw.rect(screen, (255, 255, 255), (x, y, bar_w, bar_h), 1)

    def is_pixel_clicked(self, world_pos):
        if not self.sprites or not self.masks: return False
        local_x = int(world_pos[0] - self.current_pixel_pos.x)
        local_y = int(world_pos[1] - self.current_pixel_pos.y)
        current_mask = self.masks[self.animation_frame]
        width, height = current_mask.get_size()
        if 0 <= local_x < width and 0 <= local_y < height:
            return current_mask.get_at((local_x, local_y))
        return False

    def check_collision(self, pixel_point):
        return self.is_pixel_clicked(pixel_point)
    
    def get_occupied_coords(self):
        coords = []
        for r in range(self.grid_r, self.grid_r + self.height_tiles):
            for c in range(self.grid_c, self.grid_c + self.width_tiles):
                coords.append((r, c))
        return coords


class Castle:
    def __init__(self, start_grid_pos, tile_size):
        self.grid_r, self.grid_c = start_grid_pos
        self.tile_size = tile_size
        self.width_tiles = CASTLE_HITBOX_WIDTH_TILES
        self.height_tiles = CASTLE_HITBOX_HEIGHT_TILES
        self.current_pixel_pos = pygame.Vector2(self.grid_c * self.tile_size, self.grid_r * self.tile_size)
        self.sprites = []
        self.masks = [] 
        self.reload_sprites() 
        self.animation_frame = 0
        self.animation_speed = 0.15 
        self.animation_timer = 0.0
        self.training_queue = [] 
        self.training_timer = 0.0
        self.TOTAL_TRAINING_TIME = 5.0 
        self.spawned_units = [] 
        rally_r = self.grid_r + self.height_tiles // 2
        rally_c = max(0, self.grid_c - 2)
        self.rally_point = (rally_r, rally_c)
        self.flagpole = FlagPole(self.rally_point, self.tile_size)
        self.infinite_production = None 
        
        self.health = 1000
        self.max_health = 1000
        self.max_queue_size = 5
        
    def reload_sprites(self):
        raw_sprites = Assets._loaded_assets.get("castle", [])
        self.sprites = []
        self.masks = []
        target_w = CASTLE_VISUAL_WIDTH_TILES * self.tile_size
        target_h = CASTLE_VISUAL_HEIGHT_TILES * self.tile_size
        for s in raw_sprites:
            scaled = pygame.transform.scale(s, (int(target_w), int(target_h)))
            self.sprites.append(scaled)
            self.masks.append(pygame.mask.from_surface(scaled))

    def is_pixel_clicked(self, world_pos):
        if not self.sprites or not self.masks: return False
        sprite_x = self.current_pixel_pos.x + (CASTLE_VISUAL_OFFSET_X_TILES * self.tile_size)
        sprite_y = self.current_pixel_pos.y + (CASTLE_VISUAL_OFFSET_Y_TILES * self.tile_size)
        local_x = int(world_pos[0] - sprite_x)
        local_y = int(world_pos[1] - sprite_y)
        current_mask = self.masks[self.animation_frame]
        width, height = current_mask.get_size()
        if 0 <= local_x < width and 0 <= local_y < height:
            return current_mask.get_at((local_x, local_y))
        return False

    def check_collision(self, pixel_point):
        return self.is_pixel_clicked(pixel_point)

    def queue_unit(self, unit_name):
        if len(self.training_queue) < self.max_queue_size:
            self.training_queue.append(unit_name)
            return True
        else:
            return False

    def set_rally_point(self, grid_r, grid_c):
        self.rally_point = (grid_r, grid_c)
        self.flagpole.set_pos(grid_r, grid_c)
        
    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0: self.health = 0

    def get_repair_cost(self):
        pct = self.health / self.max_health
        if pct < 0.5: return 20
        else: return 10

    def repair(self):
        self.health = self.max_health

    def update(self, dt):
        if self.training_queue:
            self.training_timer += dt
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                if self.sprites:
                    self.animation_frame = (self.animation_frame + 1) % len(self.sprites)
                self.animation_timer = 0.0
            if self.training_timer >= self.TOTAL_TRAINING_TIME:
                self.training_timer = 0.0
                unit_name = self.training_queue.pop(0)
                self._spawn_unit(unit_name)
        else:
            self.animation_frame = 0
            self.training_timer = 0.0

    def _spawn_unit(self, name):
        spawn_r = self.grid_r + self.height_tiles
        spawn_c = self.grid_c + (self.width_tiles // 2)
        new_unit = None
        if name == "McUncle": new_unit = McUncle((spawn_r, spawn_c), self.tile_size)
        else: new_unit = Hamster(name, (spawn_r, spawn_c), self.tile_size)
        if new_unit:
            rr, rc = self.rally_point
            new_unit.set_target(rr, rc)
            self.spawned_units.append(new_unit)

    def draw(self, screen):
        if self.sprites:
            sprite = self.sprites[self.animation_frame]
            sprite_x = self.current_pixel_pos.x + (CASTLE_VISUAL_OFFSET_X_TILES * self.tile_size)
            sprite_y = self.current_pixel_pos.y + (CASTLE_VISUAL_OFFSET_Y_TILES * self.tile_size)
            screen.blit(sprite, (sprite_x, sprite_y))
        if SHOW_CASTLE_BORDER:
            rect = pygame.Rect(self.current_pixel_pos.x, self.current_pixel_pos.y, self.width_tiles * self.tile_size, self.height_tiles * self.tile_size)
            pygame.draw.rect(screen, CASTLE_BORDER_COLOR, rect, 2)
        if self.flagpole: self.flagpole.draw(screen)
        
        bar_width = self.tile_size * self.width_tiles
        bar_height = 8
        
        if self.health < self.max_health:
            hx = self.current_pixel_pos.x
            hy = self.current_pixel_pos.y - 25
            hp_pct = max(0, self.health / self.max_health)
            pygame.draw.rect(screen, (50, 0, 0), (hx, hy, bar_width, bar_height))
            pygame.draw.rect(screen, (0, 255, 0), (hx, hy, bar_width * hp_pct, bar_height))
            pygame.draw.rect(screen, (255, 255, 255), (hx, hy, bar_width, bar_height), 1)

        if self.training_queue:
            x = self.current_pixel_pos.x
            y = self.current_pixel_pos.y - 10
            progress = self.training_timer / self.TOTAL_TRAINING_TIME
            pygame.draw.rect(screen, (50, 50, 50), (x, y, bar_width, bar_height))
            pygame.draw.rect(screen, (0, 200, 255), (x, y, bar_width * progress, bar_height))
            pygame.draw.rect(screen, (255, 255, 255), (x, y, bar_width, bar_height), 1)

    def get_occupied_coords(self):
        coords = []
        for r in range(self.grid_r, self.grid_r + self.height_tiles):
            for c in range(self.grid_c, self.grid_c + self.width_tiles):
                coords.append((r, c))
        return coords


class Enemy:
    def __init__(self, start_grid_pos, tile_size, extra_health=0):
        self.grid_r, self.grid_c = start_grid_pos
        self.tile_size = tile_size
        self.name = "Piero"
        self.current_pixel_pos = pygame.Vector2(self.grid_c * self.tile_size, self.grid_r * self.tile_size)
        self.frames = []
        if "Piero" in Assets._loaded_enemies:
            self.frames = Assets._loaded_enemies["Piero"]
        self.animation_frame = 0
        self.animation_speed = 0.2
        self.animation_timer = 0.0
        self.health = 100 + extra_health
        self.max_health = 100 + extra_health
        self.facing_right = True 
        
        self.base_speed = 1.5
        self.speed_multiplier = 1.0 
        self.attack_cooldown = 1.0
        self.attack_timer = 0.0
        self.damage = 50

    def take_damage(self, amount):
        self.health -= amount

    def update(self, dt, obstacles=set(), castle=None, move_to_castle=False):
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            if self.frames:
                self.animation_frame = (self.animation_frame + 1) % len(self.frames)
            self.animation_timer = 0.0

        if move_to_castle and castle and self.health > 0:
            target_center = castle.current_pixel_pos + pygame.Vector2(
                (castle.width_tiles * castle.tile_size) / 2,
                (castle.height_tiles * castle.tile_size) / 2
            )
            my_center = self.current_pixel_pos + pygame.Vector2(self.tile_size/2, self.tile_size/2)
            
            direction = target_center - my_center
            dist = direction.length()
            
            if dist < 100: 
                self.attack_timer += dt
                if self.attack_timer >= self.attack_cooldown:
                    self.attack_timer = 0.0
                    castle.take_damage(self.damage)
            else:
                if dist > 0:
                    norm = direction.normalize()
                    if norm.x > 0: self.facing_right = True
                    else: self.facing_right = False
                    
                    current_speed = self.base_speed * self.speed_multiplier
                    
                    # Basic movement
                    self.current_pixel_pos += norm * current_speed
                    
                    # CLAMP to World Bounds
                    self.current_pixel_pos.x = max(0, min(self.current_pixel_pos.x, WORLD_WIDTH_PX - self.tile_size))
                    self.current_pixel_pos.y = max(0, min(self.current_pixel_pos.y, WORLD_HEIGHT_PX - self.tile_size))
        
        self.speed_multiplier = 1.0

    def draw(self, screen):
        if self.frames:
            current_img = self.frames[self.animation_frame]
            if not self.facing_right:
                current_img = pygame.transform.flip(current_img, True, False)
            screen.blit(current_img, (self.current_pixel_pos.x, self.current_pixel_pos.y))
        if self.health < self.max_health:
            bar_w = self.tile_size
            bar_h = 6
            pos_x = self.current_pixel_pos.x
            pos_y = self.current_pixel_pos.y - 10
            pygame.draw.rect(screen, (255, 0, 0), (pos_x, pos_y, bar_w, bar_h))
            health_pct = max(0, self.health / self.max_health)
            pygame.draw.rect(screen, (0, 255, 0), (pos_x, pos_y, bar_w * health_pct, bar_h))


class Llama:
    def __init__(self, start_grid_pos, tile_size, game_grid, llama_walkable_coords, all_llamas_ref):
        self.grid_r, self.grid_c = start_grid_pos
        self.target_grid_r, self.target_grid_c = start_grid_pos 
        self.tile_size = tile_size
        self.game_grid = game_grid 
        self.llama_walkable_coords = set(llama_walkable_coords) 
        self.all_llamas_ref = all_llamas_ref 
        llama_render_size = int(self.tile_size * Assets.LLAMA_SCALE_FACTOR)
        self.current_pixel_pos = pygame.Vector2(
            self.grid_c * self.tile_size + (self.tile_size - llama_render_size) / 2,
            self.grid_r * self.tile_size + (self.tile_size - llama_render_size) / 2
        )
        self.target_pixel_pos = pygame.Vector2(self.current_pixel_pos) 
        self.speed = 1.0 
        self.state = "idle" 
        self.direction = "south" 
        self.facing_right = True 
        self.animation_frame = 0
        self.animation_speed = 0.15 
        self.animation_timer = 0.0
        self.state_timer = 0.0
        self.state_duration = 0.0 
        self.loaded_sprites = Assets._loaded_llama_sprites 
        self.masks = {} 
        self._generate_masks()
        self.target_unit = None 
        
        self.assigned_zone = None 
        self._choose_next_action() 

    def _generate_masks(self):
        for state, dirs in self.loaded_sprites.items():
            self.masks[state] = {}
            for d, surface_list in dirs.items():
                mask_list = []
                for s in surface_list:
                    mask_list.append(pygame.mask.from_surface(s))
                self.masks[state][d] = mask_list
                
    def assign_zone(self, zone_coords):
        self.assigned_zone = set(zone_coords)
        self.state = "walk"
        self.state_duration = 20.0 
        self.target_unit = None

    def is_pixel_clicked(self, world_pos):
        current_state = self.state
        current_direction = self.direction
        if current_state not in self.masks or current_direction not in self.masks[current_state]:
             return False 
        mask_list = self.masks[current_state][current_direction]
        if not mask_list: return False
        current_mask = mask_list[self.animation_frame % len(mask_list)]
        local_x = int(world_pos[0] - self.current_pixel_pos.x)
        local_y = int(world_pos[1] - self.current_pixel_pos.y)
        width, height = current_mask.get_size()
        if 0 <= local_x < width and 0 <= local_y < height:
            return current_mask.get_at((local_x, local_y))
        return False

    def start_following(self, unit):
        self.target_unit = unit
        self.state = "walk"
        self.state_duration = 9999 

    def stop_following(self):
        self.target_unit = None
        self.state = "idle"
        self.state_duration = 1.0 
        self._choose_next_action()

    def _get_direction(self, next_r, next_c):
        dr = next_r - self.grid_r
        dc = next_c - self.grid_c
        if dc > 0: return "east"
        if dc < 0: return "west"
        if dr > 0: return "south"
        if dr < 0: return "north"
        return self.direction 

    def _find_next_walk_target(self, obstacles, pixel_obstacles, windmills):
        possible_moves = []
        directions_and_names = [(0, 1, "east"), (0, -1, "west"), (1, 0, "south"), (-1, 0, "north")]
        random.shuffle(directions_and_names) 

        target_coords = None
        
        if self.assigned_zone:
            if (self.grid_r, self.grid_c) in self.assigned_zone:
                pass
            else:
                min_dist = float('inf')
                closest_tile = None
                for zr, zc in self.assigned_zone:
                    dist = abs(self.grid_r - zr) + abs(self.grid_c - zc)
                    if dist < min_dist:
                        min_dist = dist
                        closest_tile = (zr, zc)
                target_coords = closest_tile

        best_move = None
        min_target_dist = float('inf')

        for dr, dc, direction_name in directions_and_names:
            nr, nc = self.grid_r + dr, self.grid_c + dc
            
            if self.assigned_zone and (self.grid_r, self.grid_c) in self.assigned_zone:
                if (nr, nc) not in self.assigned_zone:
                    continue

            if (nr, nc) not in self.llama_walkable_coords: 
                continue 
            
            if (nr, nc) in obstacles: continue
            
            center_x = (nc * self.tile_size) + (self.tile_size / 2)
            center_y = (nr * self.tile_size) + (self.tile_size / 2)
            pixel_collision = False
            for obj in pixel_obstacles:
                if obj and obj.check_collision((center_x, center_y)):
                    pixel_collision = True
                    break
            if pixel_collision: continue

            is_obstructed = False
            for other in self.all_llamas_ref:
                if other is not self and other.grid_r == nr and other.grid_c == nc:
                    is_obstructed = True
                    break
            if is_obstructed: continue
            
            if target_coords:
                dist_to_target = abs(nr - target_coords[0]) + abs(nc - target_coords[1])
                current_is_target = False
                if self.assigned_zone and (self.grid_r, self.grid_c) in self.assigned_zone:
                    current_is_target = True

                if current_is_target:
                    possible_moves.append(((nr, nc), direction_name))
                else:
                    if dist_to_target < min_target_dist:
                        min_target_dist = dist_to_target
                        best_move = ((nr, nc), direction_name)
            else:
                possible_moves.append(((nr, nc), direction_name))
        
        if target_coords:
            at_target = False
            if self.assigned_zone:
                 if (self.grid_r, self.grid_c) in self.assigned_zone: at_target = True
            
            if at_target:
                if possible_moves: return random.choice(possible_moves)
                return None, None
            else:
                if best_move: return best_move
                if possible_moves: return random.choice(possible_moves)
        
        if possible_moves: return random.choice(possible_moves)
        return None, None 

    def _choose_next_action(self, obstacles=set(), pixel_obstacles=[], windmills=[]):
        if self.target_unit: return 
        
        on_alfalfa_or_zone = False
        if self.assigned_zone:
            if (self.grid_r, self.grid_c) in self.assigned_zone:
                on_alfalfa_or_zone = True
        
        next_grid_pos, new_direction = self._find_next_walk_target(obstacles, pixel_obstacles, windmills) 
        
        should_walk = False
        if next_grid_pos is not None:
            if self.assigned_zone and not on_alfalfa_or_zone:
                should_walk = True 
            elif on_alfalfa_or_zone:
                if random.random() < 0.7: 
                    should_walk = True
            elif random.random() < 0.6:
                should_walk = True

        if should_walk: 
            self.state = "walk"
            self.state_duration = random.uniform(2, 6)
            if self.assigned_zone and not on_alfalfa_or_zone:
                 self.state_duration = 10.0 
                 
            self.target_grid_r, self.target_grid_c = next_grid_pos
            llama_render_size = int(self.tile_size * Assets.LLAMA_SCALE_FACTOR)
            self.target_pixel_pos = pygame.Vector2(
                self.target_grid_c * self.tile_size + (self.tile_size - llama_render_size) / 2,
                self.target_grid_r * self.tile_size + (self.tile_size - llama_render_size) / 2
            )
            self.direction = new_direction
        else:
            self.state = "idle" 
            self.state_duration = random.uniform(1, 4)
            if on_alfalfa_or_zone:
                 self.state_duration = 0.5 
            
            self.animation_frame = 0 
            self.animation_timer = 0.0 
            self.state_timer = 0.0 
            self.target_grid_r, self.target_grid_c = self.grid_r, self.grid_c
            llama_render_size = int(self.tile_size * Assets.LLAMA_SCALE_FACTOR)
            self.target_pixel_pos = pygame.Vector2(
                self.grid_c * self.tile_size + (self.tile_size - llama_render_size) / 2,
                self.grid_r * self.tile_size + (self.tile_size - llama_render_size) / 2
            )

    def _transition_to_eating(self, windmills=[]):
        if self.target_unit: return 
        self.state = "eat"
        
        on_alfalfa = False
        if self.assigned_zone:
             if (self.grid_r, self.grid_c) in self.assigned_zone:
                 on_alfalfa = True
        
        if on_alfalfa:
            self.state_duration = 100.0 
        else:
            self.state_duration = random.uniform(3, 7)
            
        self.animation_frame = 0
        self.animation_timer = 0.0
        self.state_timer = 0.0 

    def update(self, dt, obstacles=set(), pixel_obstacles=[], windmills=[]):
        self.animation_timer += dt
        self.state_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_frame = (self.animation_frame + 1) % 4 
            self.animation_timer = 0.0

        if self.target_unit:
            self.state = "walk"
            target_px = self.target_unit.current_pixel_pos
            direction_vec = target_px - self.current_pixel_pos
            distance = direction_vec.length()
            FOLLOW_DISTANCE = 70.0
            if distance > FOLLOW_DISTANCE:
                next_pos = self.current_pixel_pos + direction_vec.normalize() * self.speed
                collided = False
                for obj in pixel_obstacles:
                    if obj and obj.check_collision((next_pos.x + self.tile_size/2, next_pos.y + self.tile_size/2)):
                        collided = True
                        break
                if not collided:
                    self.current_pixel_pos = next_pos
                    # CLAMP
                    self.current_pixel_pos.x = max(0, min(self.current_pixel_pos.x, WORLD_WIDTH_PX - self.tile_size))
                    self.current_pixel_pos.y = max(0, min(self.current_pixel_pos.y, WORLD_HEIGHT_PX - self.tile_size))
                    
                    self.grid_c = int(self.current_pixel_pos.x // self.tile_size)
                    self.grid_r = int(self.current_pixel_pos.y // self.tile_size)
                if direction_vec.x > 0: 
                    self.direction = "east"
                    self.facing_right = True
                elif direction_vec.x < 0: 
                    self.direction = "west"
                    self.facing_right = False
                elif direction_vec.y > 0: self.direction = "south"
                elif direction_vec.y < 0: self.direction = "north"
            return 

        if self.state == "walk":
            if self.current_pixel_pos.distance_to(self.target_pixel_pos) < self.speed:
                self.current_pixel_pos = self.target_pixel_pos 
                self.grid_r = self.target_grid_r
                self.grid_c = self.target_grid_c
                if self.state_timer >= self.state_duration:
                    self._choose_next_action(obstacles, pixel_obstacles, windmills) 
                    self.state_timer = 0.0
                else:
                    next_grid_pos, new_direction = self._find_next_walk_target(obstacles, pixel_obstacles, windmills)
                    if next_grid_pos:
                        self.target_grid_r, self.target_grid_c = next_grid_pos
                        llama_render_size = int(self.tile_size * Assets.LLAMA_SCALE_FACTOR)
                        self.target_pixel_pos = pygame.Vector2(
                            self.target_grid_c * self.tile_size + (self.tile_size - llama_render_size) / 2,
                            self.target_grid_r * self.tile_size + (self.tile_size - llama_render_size) / 2
                        )
                        self.direction = new_direction
                    else:
                        self.state = "idle"
                        self.state_duration = 2.0
                        self.state_timer = 0.0
            else:
                move_vector = self.target_pixel_pos - self.current_pixel_pos
                if move_vector.length() > 0: 
                    self.current_pixel_pos += move_vector.normalize() * self.speed
                    # CLAMP
                    self.current_pixel_pos.x = max(0, min(self.current_pixel_pos.x, WORLD_WIDTH_PX - self.tile_size))
                    self.current_pixel_pos.y = max(0, min(self.current_pixel_pos.y, WORLD_HEIGHT_PX - self.tile_size))
                else: 
                    self.current_pixel_pos = self.target_pixel_pos

        elif self.state == "idle":
            if self.state_timer >= self.state_duration:
                self._transition_to_eating(windmills) 
                self.state_timer = 0.0 

        elif self.state == "eat":
            if self.state_timer >= self.state_duration:
                self._choose_next_action(obstacles, pixel_obstacles, windmills) 
                self.state_timer = 0.0 

    def get_current_sprite(self):
        current_state = self.state
        current_direction = self.direction
        if current_state not in self.loaded_sprites or current_direction not in self.loaded_sprites[current_state]:
             current_state = "walk"
             if current_direction not in self.loaded_sprites.get("walk", {}):
                 current_direction = "south"
        sprites = self.loaded_sprites.get(current_state, {}).get(current_direction, [])
        if not sprites: 
            return pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
        return sprites[self.animation_frame % len(sprites)]

    def draw(self, screen):
        sprite = self.get_current_sprite()
        screen.blit(sprite, (self.current_pixel_pos.x, self.current_pixel_pos.y))


class McUncle:
    def __init__(self, start_grid_pos, tile_size):
        self.grid_r, self.grid_c = start_grid_pos
        self.tile_size = tile_size
        self.current_pixel_pos = pygame.Vector2(self.grid_c * self.tile_size, self.grid_r * self.tile_size)
        self.target_pixel_pos = pygame.Vector2(self.current_pixel_pos)
        self.speed = 3.0 
        self.is_moving = False
        self.selected = False 
        self.name = "McUncle" 
        # Update sprite handling for state logic
        self.sprites = Assets._loaded_mcuncle_sprites # Dict {state: frames}
        self.state = "idle"
        
        self.animation_frame = 0
        self.animation_speed = 0.1 
        self.animation_timer = 0.0
        self.facing_right = True
        self.attack_range = 250
        self.attack_cooldown = 1.0 
        self.cooldown_timer = 0.0
        self.radius = 25 
        
    def set_target(self, grid_r, grid_c):
        self.target_pixel_pos = pygame.Vector2(grid_c * self.tile_size, grid_r * self.tile_size)
        self.is_moving = True

    def set_precise_target(self, x, y):
        self.target_pixel_pos = pygame.Vector2(x, y)
        self.is_moving = True

    def update(self, dt, enemies_list=None, projectiles_list=None, obstacles=set(), pixel_obstacles=[], friends=[]):
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            # Determine current frame list based on state
            frames = self.sprites.get(self.state, self.sprites.get("idle", []))
            if frames:
                self.animation_frame = (self.animation_frame + 1) % len(frames)
            self.animation_timer = 0.0
            
        # Movement & Collision
        if self.is_moving:
            self.state = "walk" # Update state
            direction = self.target_pixel_pos - self.current_pixel_pos
            distance = direction.length()
            
            if distance < 5:
                self.is_moving = False
                self.current_pixel_pos = self.target_pixel_pos
                self.state = "idle" # Stop
            else:
                if direction.x < 0: self.facing_right = False
                elif direction.x > 0: self.facing_right = True
                
                move_vec = direction.normalize() * self.speed
                
                sep_vec = pygame.Vector2(0, 0)
                for f in friends:
                    if f is not self:
                        dist = self.current_pixel_pos.distance_to(f.current_pixel_pos)
                        if dist < SEPARATION_RADIUS and dist > 0:
                            diff = self.current_pixel_pos - f.current_pixel_pos
                            sep_vec += diff.normalize() * (SEPARATION_FORCE / dist)
                
                proposed_pos = self.current_pixel_pos + move_vec + (sep_vec * 0.05)
                
                def is_blocked(pos):
                    cx = pos.x + self.tile_size/2
                    cy = pos.y + self.tile_size/2
                    if pos.x < 0 or pos.x > WORLD_WIDTH_PX - self.tile_size: return True
                    if pos.y < 0 or pos.y > WORLD_HEIGHT_PX - self.tile_size: return True
                    
                    for obj in pixel_obstacles:
                        if obj and obj.check_collision((cx, cy)):
                            return True
                    return False

                if not is_blocked(proposed_pos):
                    self.current_pixel_pos = proposed_pos
                else:
                    try_x = pygame.Vector2(proposed_pos.x, self.current_pixel_pos.y)
                    if not is_blocked(try_x):
                        self.current_pixel_pos = try_x
                    else:
                        try_y = pygame.Vector2(self.current_pixel_pos.x, proposed_pos.y)
                        if not is_blocked(try_y):
                            self.current_pixel_pos = try_y
                
                self.grid_c = int(self.current_pixel_pos.x // self.tile_size)
                self.grid_r = int(self.current_pixel_pos.y // self.tile_size)

        else:
            self.state = "idle" # Ensure idle state
            sep_vec = pygame.Vector2(0, 0)
            for f in friends:
                if f is not self:
                    dist = self.current_pixel_pos.distance_to(f.current_pixel_pos)
                    if dist < SEPARATION_RADIUS and dist > 0:
                        diff = self.current_pixel_pos - f.current_pixel_pos
                        sep_vec += diff.normalize() * (SEPARATION_FORCE / dist)
            
            if sep_vec.length() > 0.1:
                proposed_pos = self.current_pixel_pos + (sep_vec * 0.05)
                proposed_pos.x = max(0, min(proposed_pos.x, WORLD_WIDTH_PX - self.tile_size))
                proposed_pos.y = max(0, min(proposed_pos.y, WORLD_HEIGHT_PX - self.tile_size))
                
                blocked = False
                center_x = proposed_pos.x + self.tile_size/2
                center_y = proposed_pos.y + self.tile_size/2
                for obj in pixel_obstacles:
                    if obj and obj.check_collision((center_x, center_y)):
                        blocked = True
                        break
                
                if not blocked:
                    self.current_pixel_pos = proposed_pos

        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt
        
        if enemies_list is not None and projectiles_list is not None and self.cooldown_timer <= 0:
            closest_enemy = None
            min_dist = float('inf')
            my_center = self.current_pixel_pos + pygame.Vector2(self.tile_size/2, self.tile_size/2)
            for enemy in enemies_list:
                en_center = enemy.current_pixel_pos + pygame.Vector2(enemy.tile_size/2, enemy.tile_size/2)
                dist = my_center.distance_to(en_center)
                if dist < self.attack_range and dist < min_dist:
                    min_dist = dist
                    closest_enemy = enemy
            if closest_enemy:
                self.cooldown_timer = self.attack_cooldown
                proj = Projectile(my_center, closest_enemy, self.name)
                projectiles_list.append(proj)

    def draw(self, screen):
        frames = self.sprites.get(self.state, self.sprites.get("idle", []))
        if frames:
            sprite = frames[self.animation_frame % len(frames)]
            if not self.facing_right:
                sprite = pygame.transform.flip(sprite, True, False)
            screen.blit(sprite, (self.current_pixel_pos.x, self.current_pixel_pos.y))
        
        if self.selected:
            rect = pygame.Rect(self.current_pixel_pos.x, self.current_pixel_pos.y, self.tile_size, self.tile_size)
            pygame.draw.ellipse(screen, (0, 255, 0), rect, 2)

class Hamster:
    def __init__(self, name, start_grid_pos, tile_size):
        self.name = name
        self.grid_r, self.grid_c = start_grid_pos
        self.tile_size = tile_size
        self.current_pixel_pos = pygame.Vector2(self.grid_c * self.tile_size, self.grid_r * self.tile_size)
        self.target_pixel_pos = pygame.Vector2(self.current_pixel_pos)
        self.speed = 2.5 
        self.is_moving = False
        self.selected = False
        self.state = "idle" 
        self.animation_frame = 0
        self.animation_speed = 0.1 
        self.animation_timer = 0.0
        self.facing_right = True
        if name in Assets._loaded_hamsters:
            self.sprites = Assets._loaded_hamsters[name]
        else:
            self.sprites = {}
        self.attack_range = 250
        self.attack_cooldown = 1.0 
        self.cooldown_timer = 0.0
        self.radius = 25

    def set_target(self, grid_r, grid_c):
        self.target_pixel_pos = pygame.Vector2(grid_c * self.tile_size, grid_r * self.tile_size)
        self.is_moving = True
        self.state = "walk"
        self.animation_frame = 0
        self.animation_timer = 0.0

    def set_precise_target(self, x, y):
        self.target_pixel_pos = pygame.Vector2(x, y)
        self.is_moving = True
        self.state = "walk"

    def update(self, dt, enemies_list=None, projectiles_list=None, obstacles=set(), pixel_obstacles=[], friends=[]):
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            current_frames = self.sprites.get(self.state, [])
            if current_frames:
                self.animation_frame = (self.animation_frame + 1) % len(current_frames)
            self.animation_timer = 0.0

        if self.is_moving:
            direction = self.target_pixel_pos - self.current_pixel_pos
            distance = direction.length()
            
            if distance < 5:
                self.is_moving = False
                self.state = "idle"
                self.current_pixel_pos = self.target_pixel_pos
            else:
                if direction.x < 0: self.facing_right = False
                elif direction.x > 0: self.facing_right = True
                
                move_vec = direction.normalize() * self.speed
                
                sep_vec = pygame.Vector2(0, 0)
                for f in friends:
                    if f is not self:
                        dist = self.current_pixel_pos.distance_to(f.current_pixel_pos)
                        if dist < SEPARATION_RADIUS and dist > 0:
                            diff = self.current_pixel_pos - f.current_pixel_pos
                            sep_vec += diff.normalize() * (SEPARATION_FORCE / dist)
                
                proposed_pos = self.current_pixel_pos + move_vec + (sep_vec * 0.05)
                
                # Collision Check + Sliding
                def is_blocked(pos):
                    cx = pos.x + self.tile_size/2
                    cy = pos.y + self.tile_size/2
                    # Bounds
                    if pos.x < 0 or pos.x > WORLD_WIDTH_PX - self.tile_size: return True
                    if pos.y < 0 or pos.y > WORLD_HEIGHT_PX - self.tile_size: return True
                    
                    for obj in pixel_obstacles:
                        if obj and obj.check_collision((cx, cy)):
                            return True
                    return False

                if not is_blocked(proposed_pos):
                    self.current_pixel_pos = proposed_pos
                else:
                    try_x = pygame.Vector2(proposed_pos.x, self.current_pixel_pos.y)
                    if not is_blocked(try_x):
                        self.current_pixel_pos = try_x
                    else:
                        try_y = pygame.Vector2(self.current_pixel_pos.x, proposed_pos.y)
                        if not is_blocked(try_y):
                            self.current_pixel_pos = try_y

                self.grid_c = int(self.current_pixel_pos.x // self.tile_size)
                self.grid_r = int(self.current_pixel_pos.y // self.tile_size)
        else:
            sep_vec = pygame.Vector2(0, 0)
            for f in friends:
                if f is not self:
                    dist = self.current_pixel_pos.distance_to(f.current_pixel_pos)
                    if dist < SEPARATION_RADIUS and dist > 0:
                        diff = self.current_pixel_pos - f.current_pixel_pos
                        sep_vec += diff.normalize() * (SEPARATION_FORCE / dist)
            
            if sep_vec.length() > 0.1:
                proposed_pos = self.current_pixel_pos + (sep_vec * 0.05)
                # Bounds
                proposed_pos.x = max(0, min(proposed_pos.x, WORLD_WIDTH_PX - self.tile_size))
                proposed_pos.y = max(0, min(proposed_pos.y, WORLD_HEIGHT_PX - self.tile_size))
                
                blocked = False
                center_x = proposed_pos.x + self.tile_size/2
                center_y = proposed_pos.y + self.tile_size/2
                for obj in pixel_obstacles:
                    if obj and obj.check_collision((center_x, center_y)):
                        blocked = True
                        break
                
                if not blocked:
                    self.current_pixel_pos = proposed_pos

        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt
        
        if enemies_list is not None and projectiles_list is not None and self.cooldown_timer <= 0:
            closest_enemy = None
            min_dist = float('inf')
            my_center = self.current_pixel_pos + pygame.Vector2(self.tile_size/2, self.tile_size/2)
            for enemy in enemies_list:
                en_center = enemy.current_pixel_pos + pygame.Vector2(enemy.tile_size/2, enemy.tile_size/2)
                dist = my_center.distance_to(en_center)
                if dist < self.attack_range and dist < min_dist:
                    min_dist = dist
                    closest_enemy = enemy
            if closest_enemy:
                self.cooldown_timer = self.attack_cooldown
                proj = Projectile(my_center, closest_enemy, self.name)
                projectiles_list.append(proj)
        
        # Apply slow logic for "The Hamster"
        if self.name == "The Hamster" and enemies_list:
            my_center = self.current_pixel_pos + pygame.Vector2(self.tile_size/2, self.tile_size/2)
            for enemy in enemies_list:
                en_center = enemy.current_pixel_pos + pygame.Vector2(enemy.tile_size/2, enemy.tile_size/2)
                if my_center.distance_to(en_center) < 200:
                    enemy.speed_multiplier = 0.8 

    def draw(self, screen):
        frames = self.sprites.get(self.state, self.sprites.get("idle", []))
        if frames:
            sprite = frames[self.animation_frame % len(frames)]
            if not self.facing_right:
                sprite = pygame.transform.flip(sprite, True, False)
            screen.blit(sprite, (self.current_pixel_pos.x, self.current_pixel_pos.y))
        
        if self.selected:
            rect = pygame.Rect(self.current_pixel_pos.x, self.current_pixel_pos.y, self.tile_size, self.tile_size)
            pygame.draw.ellipse(screen, (0, 255, 0), rect, 2)