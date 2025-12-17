import threading
import time
import pygame
import numpy as np
from settings import *
from utils import hsv2rgb
from svg_handler import SVGHandler
from fourier_engine import FourierEpicycles

# ====== LOADER THREAD ======
class DataLoader(threading.Thread):
    """
    Thread séparé pour charger le SVG et calculer Fourier sans geler l'interface.
    """
    def __init__(self, filename, n_coeffs):
        super().__init__()
        self.filename = filename
        self.n_coeffs = n_coeffs
        self.progress = 0.0
        self.done = False
        self.data = None

    def run(self):
        def svg_progress(p):
            self.progress = p * 0.5
            
        points, total_length = SVGHandler.load_svg(self.filename, progress_callback=svg_progress)
        
        if total_length == 0: total_length = 1
        
        def fourier_progress(p):
            self.progress = 0.5 + (p * 0.5)

        coeffs = FourierEpicycles.compute_coeffs_static(points, self.n_coeffs, progress_callback=fourier_progress)
        
        self.progress = 1.0
        time.sleep(0.2)
        
        self.data = (points, total_length, coeffs)
        self.done = True

# ====== MINI INFINITY LOADER ======
class MiniInfinityLoader:
    """Petite animation d'attente pendant le calcul."""
    def __init__(self):
        # Création de la forme infini
        t = np.linspace(0, 2*np.pi, 200)
        scale = 60
        x = scale * np.cos(t)
        y = scale * np.sin(t) * np.cos(t)
        points = x + 1j * y
        
        self.coeffs = FourierEpicycles.compute_coeffs_static(points, 5)
        self.time = 0.0
        self.trail = []
        self.trail_length = 150

    def update(self):
        self.time += 0.005 
        if self.time > 1: self.time -= 1

    def draw(self, screen, font, progress):
        cx, cy = WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2 - 50 
        
        loading_txt = font.render("Génération de Fourier...", True, (220, 220, 220))
        loading_rect = loading_txt.get_rect(center=(WINDOW_SIZE[0]//2, cy - 90))
        screen.blit(loading_txt, loading_rect)

        # Dessin du loader
        current_pos = 0+0j
        for c in self.coeffs:
            prev_pos = current_pos
            angle = c["freq"] * (2*np.pi*self.time) + c["phase"]
            current_pos += c["amp"] * np.exp(1j * angle)
            
            p1 = (cx + prev_pos.real, cy + prev_pos.imag)
            p2 = (cx + current_pos.real, cy + current_pos.imag)
            radius = c["amp"]
            
            if radius > 1:
                pygame.draw.circle(screen, (40, 40, 40), (int(p1[0]), int(p1[1])), int(radius), 1)
            pygame.draw.line(screen, (80, 80, 80), p1, p2, 1)

        self.trail.append((cx + current_pos.real, cy + current_pos.imag))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)

        if len(self.trail) > 1:
            for i in range(len(self.trail) - 1):
                hue = (i * 0.003 + 0.5) % 1.0
                color = hsv2rgb(hue, 0.6, 1.0)
                fade_col = tuple(max(0, c * (i/len(self.trail))) for c in color)
                pygame.draw.line(screen, fade_col, self.trail[i], self.trail[i+1], 2)

        # Barre de progression
        bar_width = 300
        bar_height = 4
        bar_rect = pygame.Rect(WINDOW_SIZE[0]//2 - bar_width//2, cy + 80, bar_width, bar_height)
        fill_rect = pygame.Rect(WINDOW_SIZE[0]//2 - bar_width//2, cy + 80, bar_width * progress, bar_height)
        
        pygame.draw.rect(screen, (40, 40, 60), bar_rect)
        pygame.draw.rect(screen, (100, 200, 100), fill_rect)

        pct_text = f"{int(progress * 100)}%"
        txt_surf = font.render(pct_text, True, (200, 200, 200))
        txt_rect = txt_surf.get_rect(center=(WINDOW_SIZE[0]//2, cy + 100))
        screen.blit(txt_surf, txt_rect)

        # RAPPEL DES COMMANDES
        controls_help = [
            "COMMANDES DU PROGRAMME :",
            "[F] : Caméra suiveuse (Follow)",
            "[H] : Cacher/Montrer les vecteurs",
            "[R] : Réinitialiser le tracé",
            "[+/-] : Zoomer / Dézoomer",
            "[Haut/Bas] : Vitesse de tracé"
        ]
        
        max_width = 0
        temp_font_small = pygame.font.SysFont("consolas", 14)
        for i, line in enumerate(controls_help):
            f = font if i == 0 else temp_font_small
            w, h = f.size(line)
            if w > max_width: max_width = w
        
        block_x_start = (WINDOW_SIZE[0] - max_width) // 2
        start_y_help = cy + 150
        
        for i, line in enumerate(controls_help):
            color = (150, 150, 255) if i == 0 else (100, 100, 120)
            f_size = font if i == 0 else temp_font_small
            help_surf = f_size.render(line, True, color)
            screen.blit(help_surf, (block_x_start, start_y_help + i * 20))