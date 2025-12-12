import pygame
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

        # UI Colors
        self.COLOR_BG = (50, 50, 50, 230) 
        self.COLOR_BORDER = (100, 100, 100)
        self.COLOR_BUTTON_NORMAL = (70, 70, 70)
        self.COLOR_BUTTON_HIGHLIGHT = (120, 120, 120)
        self.COLOR_TAB_ACTIVE = (90, 90, 140)
        self.COLOR_TAB_INACTIVE = (60, 60, 60)
        self.COLOR_TEXT = (255, 255, 255)
        self.COLOR_PRICE = (255, 215, 0) # Gold/Yellow

        # --- Castle Menu (Tabs: Hamsters | Buildings) ---
        self.castle_menu_active = False
        self.castle_menu_tab = "Hamsters" # Default Tab
        
        self.icon_size = 48 
        self.padding = 10
        self.icon_spacing = 15

        # Calculate Menu Dimensions
        num_hamster_items = 4 
        self.castle_menu_width = (self.icon_size + self.padding) * num_hamster_items + self.padding + (self.icon_spacing * (num_hamster_items - 1)) + 40
        self.castle_menu_height = 160 

        self.castle_menu_x = (self.screen_width - self.castle_menu_width) // 2
        # Move menu up slightly to leave space for bottom bar
        self.castle_menu_y = self.screen_height - self.castle_menu_height - 70 
        self.castle_menu_rect = pygame.Rect(self.castle_menu_x, self.castle_menu_y, self.castle_menu_width, self.castle_menu_height)

        # Tab Rects
        tab_w = self.castle_menu_width // 2
        tab_h = 30
        self.tab_hamsters_rect = pygame.Rect(self.castle_menu_x, self.castle_menu_y, tab_w, tab_h)
        self.tab_buildings_rect = pygame.Rect(self.castle_menu_x + tab_w, self.castle_menu_y, tab_w, tab_h)

        # Content Area Start Y
        content_y = self.castle_menu_y + tab_h + 20

        # -- Hamster Tab Assets --
        self.hamster_buttons = []
        
        # McUncle (30)
        self.train_mcuncle_rect = pygame.Rect(self.castle_menu_x + self.padding, content_y, self.icon_size, self.icon_size)
        img_mcuncle = None
        if "mcuncle" in self.tiles and self.tiles["mcuncle"]:
             img_mcuncle = pygame.transform.scale(self.tiles["mcuncle"][0], (self.icon_size, self.icon_size))
        self.hamster_buttons.append({"rect": self.train_mcuncle_rect, "img": img_mcuncle, "name": "McUncle", "price": 30})

        # Bob (5)
        self.train_bob_rect = pygame.Rect(self.train_mcuncle_rect.right + self.icon_spacing, content_y, self.icon_size, self.icon_size)
        img_bob = None
        if "hamsters" in self.tiles and "Bob" in self.tiles["hamsters"]:
            img_bob = pygame.transform.scale(self.tiles["hamsters"]["Bob"]["idle"][0], (self.icon_size, self.icon_size))
        self.hamster_buttons.append({"rect": self.train_bob_rect, "img": img_bob, "name": "Bob", "price": 5})

        # Dracula (15)
        self.train_drac_rect = pygame.Rect(self.train_bob_rect.right + self.icon_spacing, content_y, self.icon_size, self.icon_size)
        img_drac = None
        if "hamsters" in self.tiles and "Dracula" in self.tiles["hamsters"]:
            img_drac = pygame.transform.scale(self.tiles["hamsters"]["Dracula"]["idle"][0], (self.icon_size, self.icon_size))
        self.hamster_buttons.append({"rect": self.train_drac_rect, "img": img_drac, "name": "Dracula", "price": 15})

        # TheHamster (10)
        self.train_ham_rect = pygame.Rect(self.train_drac_rect.right + self.icon_spacing, content_y, self.icon_size, self.icon_size)
        img_ham = None
        if "hamsters" in self.tiles and "TheHamster" in self.tiles["hamsters"]:
            img_ham = pygame.transform.scale(self.tiles["hamsters"]["TheHamster"]["idle"][0], (self.icon_size, self.icon_size))
        self.hamster_buttons.append({"rect": self.train_ham_rect, "img": img_ham, "name": "TheHamster", "price": 10})

        # Rally Point (Small button in corner)
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

        # --- Formation UI (Top Center) ---
        self.formation_active = "line"
        self.formation_buttons = []
        
        form_btn_w = 60
        form_btn_h = 30
        form_spacing = 5
        form_total_w = (form_btn_w * 4) + (form_spacing * 3)
        form_start_x = (self.screen_width - form_total_w) // 2
        form_y = 10
        
        formations = ["Line", "Circle", "Square", "Double"]
        for i, name in enumerate(formations):
            rect = pygame.Rect(form_start_x + i * (form_btn_w + form_spacing), form_y, form_btn_w, form_btn_h)
            self.formation_buttons.append({"name": name.lower(), "label": name, "rect": rect})


    def draw(self, screen, active_hamsters=[], active_mcuncles=[]):
        mouse_pos = pygame.mouse.get_pos()

        # --- Draw Formation Buttons (Top Center) ---
        for btn in self.formation_buttons:
            # Highlight if selected
            if self.formation_active == btn["name"]:
                color = self.COLOR_TAB_ACTIVE
                border_color = (255, 255, 0)
            elif btn["rect"].collidepoint(mouse_pos):
                color = self.COLOR_BUTTON_HIGHLIGHT
                border_color = self.COLOR_BORDER
            else:
                color = self.COLOR_BG
                border_color = self.COLOR_BORDER
            
            pygame.draw.rect(screen, color, btn["rect"], border_radius=5)
            pygame.draw.rect(screen, border_color, btn["rect"], 1, border_radius=5)
            
            txt = self.price_font.render(btn["label"], True, self.COLOR_TEXT)
            screen.blit(txt, (btn["rect"].centerx - txt.get_width()//2, btn["rect"].centery - txt.get_height()//2))


        # --- Draw Army Summary (Bottom Center) ---
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
            # Sort for consistent order
            sorted_keys = sorted(counts.keys())
            
            for name in sorted_keys:
                count = counts[name]
                rect = pygame.Rect(current_x, start_y, icon_w, icon_h)
                self.army_summary_rects[name] = rect
                
                # Interaction Highlight
                color = (60, 60, 60, 200)
                if rect.collidepoint(mouse_pos):
                    color = (100, 100, 100, 200)
                
                # Draw Box
                surf = pygame.Surface((icon_w, icon_h), pygame.SRCALPHA)
                pygame.draw.rect(surf, color, surf.get_rect(), border_radius=5)
                pygame.draw.rect(surf, (150, 150, 150), surf.get_rect(), 1, border_radius=5)
                screen.blit(surf, rect.topleft)
                
                # Draw Icon
                icon = None
                if name == "McUncle":
                    if "mcuncle" in self.tiles and self.tiles["mcuncle"]: icon = self.tiles["mcuncle"][0]
                elif "hamsters" in self.tiles and name in self.tiles["hamsters"]:
                     # Use walk or idle
                     if "idle" in self.tiles["hamsters"][name] and self.tiles["hamsters"][name]["idle"]:
                         icon = self.tiles["hamsters"][name]["idle"][0]
                
                if icon:
                    scaled = pygame.transform.scale(icon, (40, 40))
                    screen.blit(scaled, (current_x + 5, start_y + 5))
                else:
                    # Fallback text
                    txt = self.price_font.render(name[:2], True, self.COLOR_TEXT)
                    screen.blit(txt, (current_x + 5, start_y + 15))
                
                # Draw Count
                if count > 1:
                    count_surf = self.price_font.render(f"x{count}", True, self.COLOR_PRICE)
                    screen.blit(count_surf, (current_x + icon_w - count_surf.get_width() - 2, start_y + icon_h - count_surf.get_height() - 2))
                
                current_x += icon_w + gap


        # --- Draw Castle Menu ---
        if self.castle_menu_active:
            # Background
            menu_surface = pygame.Surface(self.castle_menu_rect.size, pygame.SRCALPHA)
            menu_surface.fill(self.COLOR_BG)
            pygame.draw.rect(menu_surface, self.COLOR_BORDER, menu_surface.get_rect(), 2)
            screen.blit(menu_surface, self.castle_menu_rect.topleft)
            
            # Draw Tabs
            # Hamsters Tab
            color_h = self.COLOR_TAB_ACTIVE if self.castle_menu_tab == "Hamsters" else self.COLOR_TAB_INACTIVE
            pygame.draw.rect(screen, color_h, self.tab_hamsters_rect)
            pygame.draw.rect(screen, self.COLOR_BORDER, self.tab_hamsters_rect, 1)
            txt_h = self.font.render("Hamsters", True, self.COLOR_TEXT)
            screen.blit(txt_h, (self.tab_hamsters_rect.centerx - txt_h.get_width()//2, self.tab_hamsters_rect.centery - txt_h.get_height()//2))

            # Buildings Tab
            color_b = self.COLOR_TAB_ACTIVE if self.castle_menu_tab == "Buildings" else self.COLOR_TAB_INACTIVE
            pygame.draw.rect(screen, color_b, self.tab_buildings_rect)
            pygame.draw.rect(screen, self.COLOR_BORDER, self.tab_buildings_rect, 1)
            txt_b = self.font.render("Buildings", True, self.COLOR_TEXT)
            screen.blit(txt_b, (self.tab_buildings_rect.centerx - txt_b.get_width()//2, self.tab_buildings_rect.centery - txt_b.get_height()//2))

            # Content
            if self.castle_menu_tab == "Hamsters":
                for btn in self.hamster_buttons:
                    rect = btn["rect"]
                    color = self.COLOR_BUTTON_HIGHLIGHT if rect.collidepoint(mouse_pos) else self.COLOR_BUTTON_NORMAL
                    pygame.draw.rect(screen, color, rect, border_radius=3)
                    if btn["img"]:
                        screen.blit(btn["img"], rect.topleft)
                    
                    # Price
                    price_txt = self.price_font.render(f"{btn['price']} Ch.", True, self.COLOR_PRICE)
                    screen.blit(price_txt, (rect.centerx - price_txt.get_width()//2, rect.bottom + 5))

                # Rally Point
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


        # Draw Llama Menu
        if self.llama_menu_active:
            menu_surface = pygame.Surface(self.llama_menu_rect.size, pygame.SRCALPHA)
            menu_surface.fill(self.COLOR_BG)
            pygame.draw.rect(menu_surface, self.COLOR_BORDER, menu_surface.get_rect(), 2)
            screen.blit(menu_surface, self.llama_menu_rect.topleft)
            
            title = self.font.render("Llama Actions", True, self.COLOR_TEXT)
            screen.blit(title, (self.llama_menu_rect.x + 10, self.llama_menu_rect.y + 10))

            # Follow Button
            rect = self.llama_follow_rect
            color = self.COLOR_BUTTON_HIGHLIGHT if rect.collidepoint(mouse_pos) else self.COLOR_BUTTON_NORMAL
            pygame.draw.rect(screen, color, rect, border_radius=3)
            txt = self.font.render("Follow", True, self.COLOR_TEXT)
            screen.blit(txt, (rect.x + 15, rect.y + 7))

            # Stop Button
            rect = self.llama_stop_rect
            color = self.COLOR_BUTTON_HIGHLIGHT if rect.collidepoint(mouse_pos) else self.COLOR_BUTTON_NORMAL
            pygame.draw.rect(screen, color, rect, border_radius=3)
            txt = self.font.render("Stop", True, self.COLOR_TEXT)
            screen.blit(txt, (rect.x + 20, rect.y + 7))


    def is_mouse_over(self, pos):
        if self.castle_menu_active and self.castle_menu_rect.collidepoint(pos): return True
        if self.llama_menu_active and self.llama_menu_rect.collidepoint(pos): return True
        # Check Army Summary
        for rect in self.army_summary_rects.values():
            if rect.collidepoint(pos): return True
        # Check Formations
        for btn in self.formation_buttons:
            if btn["rect"].collidepoint(pos): return True
        return False

    def handle_event(self, event):
        action = None
        data = None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: 
            mouse_pos = event.pos

            # Handle Formation Clicks
            for btn in self.formation_buttons:
                if btn["rect"].collidepoint(mouse_pos):
                    self.formation_active = btn["name"]
                    return "change_formation", btn["name"]

            # Handle Army Summary Click
            for name, rect in self.army_summary_rects.items():
                if rect.collidepoint(mouse_pos):
                    return "select_all_type", name

            # Handle Castle Menu
            if self.castle_menu_active:
                # Tab Switching
                if self.tab_hamsters_rect.collidepoint(mouse_pos):
                    self.castle_menu_tab = "Hamsters"
                    return action, data
                elif self.tab_buildings_rect.collidepoint(mouse_pos):
                    self.castle_menu_tab = "Buildings"
                    return action, data

                # Content Interaction
                if self.castle_menu_tab == "Hamsters":
                    if self.rally_point_button_rect.collidepoint(mouse_pos):
                        action = "set_rally_point"
                        self.castle_menu_active = False 
                    
                    # Check unit buttons
                    for btn in self.hamster_buttons:
                        if btn["rect"].collidepoint(mouse_pos):
                            action = "train_unit"
                            data = {"name": btn["name"], "price": btn["price"]}
                            
                elif self.castle_menu_tab == "Buildings":
                     for btn in self.building_buttons:
                         if btn["rect"].collidepoint(mouse_pos):
                             action = "select_asset"
                             data = btn["type"]
                             self.castle_menu_active = False # Close menu to place

            # Handle Llama Menu
            elif self.llama_menu_active:
                if self.llama_follow_rect.collidepoint(mouse_pos):
                    action = "llama_follow"
                elif self.llama_stop_rect.collidepoint(mouse_pos):
                    action = "llama_stop"

        return action, data