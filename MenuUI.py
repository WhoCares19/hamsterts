import pygame
import math
import os

class UIControlPanel:
    def __init__(self, tile_size, screen_width, screen_height, loaded_tiles_dict):
        self.tile_size = tile_size
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.tiles = loaded_tiles_dict 

        self.font = pygame.font.Font(None, 24)
        self.button_font = pygame.font.Font(None, 28)
        self.price_font = pygame.font.Font(None, 20)
        self.tooltip_font = pygame.font.Font(None, 22)

        # UI Colors
        self.COLOR_BG = (50, 50, 50, 230) 
        self.COLOR_BORDER = (100, 100, 100)
        self.COLOR_BUTTON_NORMAL = (70, 70, 70)
        self.COLOR_BUTTON_HIGHLIGHT = (120, 120, 120)
        self.COLOR_TAB_ACTIVE = (90, 90, 140)
        self.COLOR_TAB_INACTIVE = (60, 60, 60)
        self.COLOR_TEXT = (255, 255, 255)
        self.COLOR_PRICE = (255, 215, 0) # Gold/Yellow
        self.COLOR_TOOLTIP_BG = (20, 20, 20, 240)

        # --- Castle Menu (Tabs: Hamsters | Buildings) ---
        self.castle_menu_active = False
        self.castle_menu_tab = "Hamsters" 
        
        self.icon_size = 48 
        self.padding = 10
        self.icon_spacing = 15

        # Calculate Menu Dimensions
        num_hamster_items = 4 
        self.castle_menu_width = (self.icon_size + self.padding) * num_hamster_items + self.padding + (self.icon_spacing * (num_hamster_items - 1)) + 40
        self.castle_menu_height = 160 

        self.castle_menu_x = (self.screen_width - self.castle_menu_width) // 2
        self.castle_menu_y = self.screen_height - self.castle_menu_height - 70 
        self.castle_menu_rect = pygame.Rect(self.castle_menu_x, self.castle_menu_y, self.castle_menu_width, self.castle_menu_height)

        # Tab Rects
        tab_w = self.castle_menu_width // 2
        tab_h = 30
        self.tab_hamsters_rect = pygame.Rect(self.castle_menu_x, self.castle_menu_y, tab_w, tab_h)
        self.tab_buildings_rect = pygame.Rect(self.castle_menu_x + tab_w, self.castle_menu_y, tab_w, tab_h)

        # Content Area Start Y
        content_y = self.castle_menu_y + tab_h + 20

        # -- Hamster Tab Assets (With Descriptions) --
        self.hamster_buttons = []
        
        # McUncle (30)
        self.train_mcuncle_rect = pygame.Rect(self.castle_menu_x + self.padding, content_y, self.icon_size, self.icon_size)
        img_mcuncle = None
        if "mcuncle" in self.tiles and self.tiles["mcuncle"]:
             img_mcuncle = pygame.transform.scale(self.tiles["mcuncle"][0], (self.icon_size, self.icon_size))
        self.hamster_buttons.append({
            "rect": self.train_mcuncle_rect, 
            "img": img_mcuncle, 
            "name": "McUncle", 
            "price": 30,
            "desc": "Deadly horseman that deals 50 dmg at the enemy."
        })

        # Bob (5)
        self.train_bob_rect = pygame.Rect(self.train_mcuncle_rect.right + self.icon_spacing, content_y, self.icon_size, self.icon_size)
        img_bob = None
        if "hamsters" in self.tiles and "Bob" in self.tiles["hamsters"]:
            img_bob = pygame.transform.scale(self.tiles["hamsters"]["Bob"]["idle"][0], (self.icon_size, self.icon_size))
        self.hamster_buttons.append({
            "rect": self.train_bob_rect, 
            "img": img_bob, 
            "name": "Bob", 
            "price": 5,
            "desc": "This useless RAT, gives 50% boost to cheese production. Deals 5 dmg to the enemy."
        })

        # Dracula (15)
        self.train_drac_rect = pygame.Rect(self.train_bob_rect.right + self.icon_spacing, content_y, self.icon_size, self.icon_size)
        img_drac = None
        if "hamsters" in self.tiles and "Dracula" in self.tiles["hamsters"]:
            img_drac = pygame.transform.scale(self.tiles["hamsters"]["Dracula"]["idle"][0], (self.icon_size, self.icon_size))
        self.hamster_buttons.append({
            "rect": self.train_drac_rect, 
            "img": img_drac, 
            "name": "Dracula", 
            "price": 15,
            "desc": "Deadly blood sucker. Deals 30 dmg to the enemy."
        })

        # TheHamster (10)
        self.train_ham_rect = pygame.Rect(self.train_drac_rect.right + self.icon_spacing, content_y, self.icon_size, self.icon_size)
        img_ham = None
        if "hamsters" in self.tiles and "TheHamster" in self.tiles["hamsters"]:
            img_ham = pygame.transform.scale(self.tiles["hamsters"]["TheHamster"]["idle"][0], (self.icon_size, self.icon_size))
        self.hamster_buttons.append({
            "rect": self.train_ham_rect, 
            "img": img_ham, 
            "name": "TheHamster", 
            "price": 10,
            "desc": "Deadly hobo, deals 20 dmg to the enemy and slows them down by 20%"
        })

        # Rally Point
        self.rally_point_button_rect = pygame.Rect(self.castle_menu_rect.right - 40, self.castle_menu_rect.bottom - 40, 32, 32)
        self.img_flagpole = None
        if "flagpole" in self.tiles:
             self.img_flagpole = pygame.transform.scale(self.tiles["flagpole"], (32, 32))


        # -- Buildings Tab Assets --
        self.building_buttons = []
        
        # Windmill
        self.build_windmill_rect = pygame.Rect(self.castle_menu_x + self.padding, content_y, self.icon_size, self.icon_size)
        img_mill = None
        if "windmill" in self.tiles and self.tiles["windmill"]: 
            img_mill = pygame.transform.scale(self.tiles["windmill"][0], (self.icon_size, self.icon_size))
        self.building_buttons.append({"rect": self.build_windmill_rect, "img": img_mill, "type": "windmill", "label": "Mill"})


        # --- Llama Interaction Menu ---
        self.llama_menu_active = False
        self.llama_menu_width = 220
        self.llama_menu_height = 80
        self.llama_menu_x = (self.screen_width - self.llama_menu_width) // 2
        self.llama_menu_y = self.screen_height - self.llama_menu_height - 120
        self.llama_menu_rect = pygame.Rect(self.llama_menu_x, self.llama_menu_y, self.llama_menu_width, self.llama_menu_height)
        
        btn_w = 100
        btn_h = 30
        self.llama_follow_rect = pygame.Rect(self.llama_menu_x + 5, self.llama_menu_y + 40, btn_w, btn_h)
        self.llama_stop_rect = pygame.Rect(self.llama_menu_x + 115, self.llama_menu_y + 40, btn_w, btn_h)
        
        self.build_menu_active = False
        
        # --- Army Summary UI ---
        self.army_summary_rects = {}

        # --- Formation UI (Under Cheese - Vertical) ---
        self.formation_active = "none" 
        self.formation_buttons = []
        
        form_btn_w = 30
        form_btn_h = 30
        form_spacing = 5
        
        start_x = self.screen_width - 50 
        start_y = 120 
        
        formations = ["none", "line", "double", "circle", "square"]
        for i, name in enumerate(formations):
            rect = pygame.Rect(start_x, start_y + i * (form_btn_h + form_spacing), form_btn_w, form_btn_h)
            self.formation_buttons.append({"name": name, "rect": rect})


    def draw_formation_icon(self, screen, rect, formation_name, color):
        cx, cy = rect.center
        r = 3 
        
        if formation_name == "none":
            off = 6
            pygame.draw.line(screen, color, (cx - off, cy - off), (cx + off, cy + off), 2)
            pygame.draw.line(screen, color, (cx + off, cy - off), (cx - off, cy + off), 2)
        elif formation_name == "line":
            pygame.draw.circle(screen, color, (cx, cy - 8), r)
            pygame.draw.circle(screen, color, (cx, cy), r)
            pygame.draw.circle(screen, color, (cx, cy + 8), r)
        elif formation_name == "double":
            off = 5
            for x in [cx - off, cx + off]:
                pygame.draw.circle(screen, color, (x, cy - 8), r)
                pygame.draw.circle(screen, color, (x, cy), r)
                pygame.draw.circle(screen, color, (x, cy + 8), r)
        elif formation_name == "circle":
            radius = 8
            for i in range(6):
                angle = i * (2 * 3.14159 / 6)
                dx = radius * math.cos(angle)
                dy = radius * math.sin(angle)
                pygame.draw.circle(screen, color, (cx + dx, cy + dy), 2)
        elif formation_name == "square":
            off = 6
            pygame.draw.circle(screen, color, (cx - off, cy - off), r)
            pygame.draw.circle(screen, color, (cx + off, cy - off), r)
            pygame.draw.circle(screen, color, (cx - off, cy + off), r)
            pygame.draw.circle(screen, color, (cx + off, cy + off), r)

    def draw_tooltip(self, screen, text, pos):
        # Break text into multiple lines if too long (simple wrapping)
        words = text.split(' ')
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(" ".join(current_line)) > 25: # Char limit per line
                lines.append(" ".join(current_line[:-1]))
                current_line = [word]
        lines.append(" ".join(current_line))

        # Calculate box size
        line_height = 20
        max_w = 0
        total_h = len(lines) * line_height + 10
        surfaces = []
        for line in lines:
            s = self.tooltip_font.render(line, True, self.COLOR_TEXT)
            if s.get_width() > max_w: max_w = s.get_width()
            surfaces.append(s)
        
        box_w = max_w + 20
        
        # Keep tooltip on screen
        x, y = pos
        if x + box_w > self.screen_width: x = self.screen_width - box_w
        if y - total_h < 0: y += 30 # Show below cursor if too high
        else: y -= total_h # Show above cursor
        
        # Draw
        bg_rect = pygame.Rect(x, y, box_w, total_h)
        s = pygame.Surface((box_w, total_h), pygame.SRCALPHA)
        s.fill(self.COLOR_TOOLTIP_BG)
        screen.blit(s, (x, y))
        pygame.draw.rect(screen, self.COLOR_BORDER, bg_rect, 1)
        
        for i, surf in enumerate(surfaces):
            screen.blit(surf, (x + 10, y + 5 + i * line_height))


    def draw(self, screen, active_hamsters=[], active_mcuncles=[]):
        mouse_pos = pygame.mouse.get_pos()

        # --- Draw Formation Buttons ---
        for btn in self.formation_buttons:
            if self.formation_active == btn["name"]:
                color = self.COLOR_TAB_ACTIVE
                border_color = (255, 255, 0)
                icon_color = (255, 255, 255)
            elif btn["rect"].collidepoint(mouse_pos):
                color = self.COLOR_BUTTON_HIGHLIGHT
                border_color = self.COLOR_BORDER
                icon_color = (200, 200, 200)
            else:
                color = self.COLOR_BG
                border_color = self.COLOR_BORDER
                icon_color = (150, 150, 150)
            
            pygame.draw.rect(screen, color, btn["rect"], border_radius=5)
            pygame.draw.rect(screen, border_color, btn["rect"], 1, border_radius=5)
            
            self.draw_formation_icon(screen, btn["rect"], btn["name"], icon_color)

        # --- Draw Army Summary ---
        counts = {}
        if active_mcuncles: counts["McUncle"] = len(active_mcuncles)
        for h in active_hamsters:
            name = h.name
            counts[name] = counts.get(name, 0) + 1
            
        self.army_summary_rects = {}
        if counts:
            icon_w, icon_h = 50, 50
            gap = 10
            total_w = len(counts) * (icon_w + gap)
            start_x = (self.screen_width - total_w) // 2
            start_y = self.screen_height - icon_h - 10
            current_x = start_x
            sorted_keys = sorted(counts.keys())
            
            for name in sorted_keys:
                count = counts[name]
                rect = pygame.Rect(current_x, start_y, icon_w, icon_h)
                self.army_summary_rects[name] = rect
                
                color = (60, 60, 60, 200)
                if rect.collidepoint(mouse_pos):
                    color = (100, 100, 100, 200)
                
                surf = pygame.Surface((icon_w, icon_h), pygame.SRCALPHA)
                pygame.draw.rect(surf, color, surf.get_rect(), border_radius=5)
                pygame.draw.rect(surf, (150, 150, 150), surf.get_rect(), 1, border_radius=5)
                screen.blit(surf, rect.topleft)
                
                icon = None
                if name == "McUncle":
                    if "mcuncle" in self.tiles and self.tiles["mcuncle"]: icon = self.tiles["mcuncle"][0]
                elif "hamsters" in self.tiles and name in self.tiles["hamsters"]:
                     if "idle" in self.tiles["hamsters"][name] and self.tiles["hamsters"][name]["idle"]:
                         icon = self.tiles["hamsters"][name]["idle"][0]
                
                if icon:
                    scaled = pygame.transform.scale(icon, (40, 40))
                    screen.blit(scaled, (current_x + 5, start_y + 5))
                else:
                    txt = self.price_font.render(name[:2], True, self.COLOR_TEXT)
                    screen.blit(txt, (current_x + 5, start_y + 15))
                
                if count > 1:
                    count_surf = self.price_font.render(f"x{count}", True, self.COLOR_PRICE)
                    screen.blit(count_surf, (current_x + icon_w - count_surf.get_width() - 2, start_y + icon_h - count_surf.get_height() - 2))
                
                current_x += icon_w + gap

        # --- Draw Castle Menu ---
        tooltip_to_draw = None
        if self.castle_menu_active:
            menu_surface = pygame.Surface(self.castle_menu_rect.size, pygame.SRCALPHA)
            menu_surface.fill(self.COLOR_BG)
            pygame.draw.rect(menu_surface, self.COLOR_BORDER, menu_surface.get_rect(), 2)
            screen.blit(menu_surface, self.castle_menu_rect.topleft)
            
            color_h = self.COLOR_TAB_ACTIVE if self.castle_menu_tab == "Hamsters" else self.COLOR_TAB_INACTIVE
            pygame.draw.rect(screen, color_h, self.tab_hamsters_rect)
            pygame.draw.rect(screen, self.COLOR_BORDER, self.tab_hamsters_rect, 1)
            txt_h = self.font.render("Hamsters", True, self.COLOR_TEXT)
            screen.blit(txt_h, (self.tab_hamsters_rect.centerx - txt_h.get_width()//2, self.tab_hamsters_rect.centery - txt_h.get_height()//2))

            color_b = self.COLOR_TAB_ACTIVE if self.castle_menu_tab == "Buildings" else self.COLOR_TAB_INACTIVE
            pygame.draw.rect(screen, color_b, self.tab_buildings_rect)
            pygame.draw.rect(screen, self.COLOR_BORDER, self.tab_buildings_rect, 1)
            txt_b = self.font.render("Buildings", True, self.COLOR_TEXT)
            screen.blit(txt_b, (self.tab_buildings_rect.centerx - txt_b.get_width()//2, self.tab_buildings_rect.centery - txt_b.get_height()//2))

            if self.castle_menu_tab == "Hamsters":
                for btn in self.hamster_buttons:
                    rect = btn["rect"]
                    color = self.COLOR_BUTTON_HIGHLIGHT if rect.collidepoint(mouse_pos) else self.COLOR_BUTTON_NORMAL
                    pygame.draw.rect(screen, color, rect, border_radius=3)
                    if btn["img"]:
                        screen.blit(btn["img"], rect.topleft)
                    
                    price_txt = self.price_font.render(f"{btn['price']} Ch.", True, self.COLOR_PRICE)
                    screen.blit(price_txt, (rect.centerx - price_txt.get_width()//2, rect.bottom + 5))
                    
                    # Check for tooltip
                    if rect.collidepoint(mouse_pos):
                        tooltip_to_draw = (btn["desc"], mouse_pos)

                if self.img_flagpole:
                    rect = self.rally_point_button_rect
                    color = self.COLOR_BUTTON_HIGHLIGHT if rect.collidepoint(mouse_pos) else self.COLOR_BUTTON_NORMAL
                    pygame.draw.rect(screen, color, rect, border_radius=3)
                    screen.blit(self.img_flagpole, rect.topleft)
                    
            elif self.castle_menu_tab == "Buildings":
                for btn in self.building_buttons:
                    rect = btn["rect"]
                    color = self.COLOR_BUTTON_HIGHLIGHT if rect.collidepoint(mouse_pos) else self.COLOR_BUTTON_NORMAL
                    pygame.draw.rect(screen, color, rect, border_radius=3)
                    if btn["img"]:
                        screen.blit(btn["img"], rect.topleft)
                    
                    label_txt = self.price_font.render(btn["label"], True, self.COLOR_TEXT)
                    screen.blit(label_txt, (rect.centerx - label_txt.get_width()//2, rect.bottom + 5))

        # --- Draw Llama Menu ---
        if self.llama_menu_active:
            menu_surface = pygame.Surface(self.llama_menu_rect.size, pygame.SRCALPHA)
            menu_surface.fill(self.COLOR_BG)
            pygame.draw.rect(menu_surface, self.COLOR_BORDER, menu_surface.get_rect(), 2)
            screen.blit(menu_surface, self.llama_menu_rect.topleft)
            
            title = self.font.render("Llama Actions", True, self.COLOR_TEXT)
            screen.blit(title, (self.llama_menu_rect.x + 10, self.llama_menu_rect.y + 10))

            rect = self.llama_follow_rect
            color = self.COLOR_BUTTON_HIGHLIGHT if rect.collidepoint(mouse_pos) else self.COLOR_BUTTON_NORMAL
            pygame.draw.rect(screen, color, rect, border_radius=3)
            txt = self.font.render("Follow", True, self.COLOR_TEXT)
            screen.blit(txt, (rect.x + 15, rect.y + 7))

            rect = self.llama_stop_rect
            color = self.COLOR_BUTTON_HIGHLIGHT if rect.collidepoint(mouse_pos) else self.COLOR_BUTTON_NORMAL
            pygame.draw.rect(screen, color, rect, border_radius=3)
            txt = self.font.render("Stop", True, self.COLOR_TEXT)
            screen.blit(txt, (rect.x + 20, rect.y + 7))

        # Draw Tooltip Last
        if tooltip_to_draw:
            self.draw_tooltip(screen, tooltip_to_draw[0], tooltip_to_draw[1])

    def is_mouse_over(self, pos):
        if self.castle_menu_active and self.castle_menu_rect.collidepoint(pos): return True
        if self.llama_menu_active and self.llama_menu_rect.collidepoint(pos): return True
        for rect in self.army_summary_rects.values():
            if rect.collidepoint(pos): return True
        for btn in self.formation_buttons:
            if btn["rect"].collidepoint(pos): return True
        return False

    def handle_event(self, event):
        action = None
        data = None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: 
            mouse_pos = event.pos

            for btn in self.formation_buttons:
                if btn["rect"].collidepoint(mouse_pos):
                    self.formation_active = btn["name"]
                    return "change_formation", btn["name"]

            for name, rect in self.army_summary_rects.items():
                if rect.collidepoint(mouse_pos):
                    return "select_all_type", name

            if self.castle_menu_active:
                if self.tab_hamsters_rect.collidepoint(mouse_pos):
                    self.castle_menu_tab = "Hamsters"
                    return action, data
                elif self.tab_buildings_rect.collidepoint(mouse_pos):
                    self.castle_menu_tab = "Buildings"
                    return action, data

                if self.castle_menu_tab == "Hamsters":
                    if self.rally_point_button_rect.collidepoint(mouse_pos):
                        action = "set_rally_point"
                        self.castle_menu_active = False 
                    
                    for btn in self.hamster_buttons:
                        if btn["rect"].collidepoint(mouse_pos):
                            action = "train_unit"
                            data = {"name": btn["name"], "price": btn["price"]}
                            
                elif self.castle_menu_tab == "Buildings":
                     for btn in self.building_buttons:
                         if btn["rect"].collidepoint(mouse_pos):
                             action = "select_asset"
                             data = btn["type"]
                             self.castle_menu_active = False 

            elif self.llama_menu_active:
                if self.llama_follow_rect.collidepoint(mouse_pos):
                    action = "llama_follow"
                elif self.llama_stop_rect.collidepoint(mouse_pos):
                    action = "llama_stop"

        return action, data