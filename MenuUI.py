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
        self.COLOR_SEGMENT_LINE = (150, 150, 150)

        # --- Main Control Circle ---
        self.control_panel_radius = 50
        self.control_panel_center_x = self.screen_width - self.control_panel_radius - 10
        self.control_panel_center_y = self.screen_height - self.control_panel_radius - 10
        self.control_panel_rect = pygame.Rect(
            self.control_panel_center_x - self.control_panel_radius,
            self.control_panel_center_y - self.control_panel_radius,
            self.control_panel_radius * 2,
            self.control_panel_radius * 2
        )

        # --- Segmented Buttons ---
        self.segment_padding = 5 
        self.segment_radius = self.control_panel_radius - self.segment_padding
        self.segment_buttons = {} 
        segment_center_offset = self.control_panel_radius / 2.5 

        # B - Top (Now functionally redundant but kept for UI structure)
        b_text_surf = self.button_font.render("B", True, self.COLOR_TEXT)
        b_text_rect = b_text_surf.get_rect(center=(self.control_panel_center_x, self.control_panel_center_y - segment_center_offset))
        self.segment_buttons['B'] = {'rect': b_text_rect.inflate(10,10), 'text_surf': b_text_surf, 'text_rect': b_text_rect}
        
        # S - Right
        s_text_surf = self.button_font.render("S", True, self.COLOR_TEXT)
        s_text_rect = s_text_surf.get_rect(center=(self.control_panel_center_x + segment_center_offset, self.control_panel_center_y))
        self.segment_buttons['S'] = {'rect': s_text_rect.inflate(10,10), 'text_surf': s_text_surf, 'text_rect': s_text_rect}

        # M - Bottom
        m_text_surf = self.button_font.render("M", True, self.COLOR_TEXT)
        m_text_rect = m_text_surf.get_rect(center=(self.control_panel_center_x, self.control_panel_center_y + segment_center_offset))
        self.segment_buttons['M'] = {'rect': m_text_rect.inflate(10,10), 'text_surf': m_text_surf, 'text_rect': m_text_rect}


        # --- Castle Menu (Tabs: Hamsters | Buildings) ---
        self.castle_menu_active = False
        self.castle_menu_tab = "Hamsters" # Default Tab
        
        self.icon_size = 48 
        self.padding = 10
        self.icon_spacing = 15

        # Calculate Menu Dimensions
        num_hamster_items = 4 
        # Width based on hamster tab (widest)
        self.castle_menu_width = (self.icon_size + self.padding) * num_hamster_items + self.padding + (self.icon_spacing * (num_hamster_items - 1)) + 40
        self.castle_menu_height = 160 # Taller for tabs + icons + prices

        self.castle_menu_x = (self.screen_width - self.castle_menu_width) // 2
        self.castle_menu_y = self.screen_height - self.castle_menu_height - 20
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
        self.hamster_buttons.append({"rect": self.train_drac_rect, "img": img_drac, "name": "Dracula", "price": 5})

        # TheHamster (10)
        self.train_ham_rect = pygame.Rect(self.train_drac_rect.right + self.icon_spacing, content_y, self.icon_size, self.icon_size)
        img_ham = None
        if "hamsters" in self.tiles and "TheHamster" in self.tiles["hamsters"]:
            img_ham = pygame.transform.scale(self.tiles["hamsters"]["TheHamster"]["idle"][0], (self.icon_size, self.icon_size))
        self.hamster_buttons.append({"rect": self.train_ham_rect, "img": img_ham, "name": "TheHamster", "price": 5})

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
        self.llama_menu_y = self.screen_height - self.llama_menu_height - 20
        self.llama_menu_rect = pygame.Rect(self.llama_menu_x, self.llama_menu_y, self.llama_menu_width, self.llama_menu_height)
        
        btn_w = 100
        btn_h = 30
        self.llama_follow_rect = pygame.Rect(self.llama_menu_x + 5, self.llama_menu_y + 40, btn_w, btn_h)
        self.llama_stop_rect = pygame.Rect(self.llama_menu_x + 115, self.llama_menu_y + 40, btn_w, btn_h)
        
        # We assume build_menu_active is no longer needed/deprecated as requested
        self.build_menu_active = False
        self.build_menu_rect = pygame.Rect(0,0,0,0) # Placeholder


    def draw(self, screen):
        # Draw Main Control Circle
        pygame.draw.circle(screen, self.COLOR_BG, (self.control_panel_center_x, self.control_panel_center_y), self.control_panel_radius)
        pygame.draw.circle(screen, self.COLOR_BORDER, (self.control_panel_center_x, self.control_panel_center_y), self.control_panel_radius, 2)

        pygame.draw.line(screen, self.COLOR_SEGMENT_LINE, 
                         (self.control_panel_center_x - self.control_panel_radius, self.control_panel_center_y),
                         (self.control_panel_center_x + self.control_panel_radius, self.control_panel_center_y), 2)
        pygame.draw.line(screen, self.COLOR_SEGMENT_LINE, 
                         (self.control_panel_center_x, self.control_panel_center_y - self.control_panel_radius),
                         (self.control_panel_center_x, self.control_panel_center_y + self.control_panel_radius), 2)

        for key, button_info in self.segment_buttons.items():
            screen.blit(button_info['text_surf'], button_info['text_rect'])

        mouse_pos = pygame.mouse.get_pos()

        # Draw Castle Menu
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

                # Rally Point (Only in Hamsters or General?) Let's keep it visible in Hamsters tab or always? 
                # Prompt didn't specify, but rally point is for units. Logic says Hamsters tab.
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
        if self.control_panel_rect.collidepoint(pos): return True
        if self.castle_menu_active and self.castle_menu_rect.collidepoint(pos): return True
        if self.llama_menu_active and self.llama_menu_rect.collidepoint(pos): return True
        return False

    def handle_event(self, event):
        action = None
        data = None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: 
            mouse_pos = event.pos

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
                            # Don't close menu immediately so they can buy multiple
                            
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

            # Handle Main Buttons
            else: 
                # B button removed/no-op as per plan to move building to castle
                # S and M still print
                if self.segment_buttons['S']['rect'].collidepoint(mouse_pos):
                    print("UI: 'S' clicked")
                elif self.segment_buttons['M']['rect'].collidepoint(mouse_pos):
                    print("UI: 'M' clicked")

        return action, data