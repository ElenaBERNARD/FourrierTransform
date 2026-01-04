"""
loader_ui.py
Interface de chargement et multithreading.
Ce module gère le chargement asynchrone des fichiers SVG et propose une 
animation visuelle basée sur les épicycles pour patienter durant les calculs.
"""

import threading
import time
import pygame
import numpy as np
from settings import *
from utils import hsv2rgb
from svg_handler import SVGHandler
from fourier_engine import FourierEpicycles

class DataLoader(threading.Thread):
    """
    Thread dédié au traitement des données.
    
    Le calcul des coefficients de Fourier est une opération intensive (O(N*M)).
    L'utilisation d'un thread séparé permet de maintenir la boucle principale 
    de Pygame active, évitant ainsi que l'OS considère que le programme "ne répond pas".
    """
    def __init__(self, filename, n_coeffs):
        """
        Initialise le chargeur.
        :param filename: Chemin du fichier SVG à traiter.
        :param n_coeffs: Nombre de coefficients (cercles) à calculer.
        """
        super().__init__()
        self.filename = filename
        self.n_coeffs = n_coeffs
        self.progress = 0.0  # Progression de 0.0 à 1.0
        self.done = False    # Drapeau de complétion
        self.data = None     # Stockage des résultats finaux

    def run(self):
        """
        Exécution du thread. Découpe le travail en deux phases :
        1. Parsing du SVG (50% de la barre de progression).
        2. Calcul des intégrales de Fourier (50% de la barre).
        """
        # Phase 1 : Chargement et échantillonnage du SVG
        def svg_progress(p):
            self.progress = p * 0.5
            
        points, total_length = SVGHandler.load_svg(self.filename, progress_callback=svg_progress)
        
        # Sécurité pour éviter la division par zéro
        if total_length == 0: 
            total_length = 1
        
        # Phase 2 : Calcul des coefficients (Phaseurs)
        def fourier_progress(p):
            self.progress = 0.5 + (p * 0.5)

        # Appel à la méthode statique du moteur de Fourier
        coeffs = FourierEpicycles.compute_coeffs_static(points, self.n_coeffs, progress_callback=fourier_progress)
        
        # Petite pause pour laisser le temps à l'utilisateur de voir le 100%
        self.progress = 1.0
        time.sleep(0.2)
        
        # Stockage des résultats pour récupération par le main
        self.data = (points, total_length, coeffs)
        self.done = True

class MiniInfinityLoader:
    """
    Animation "Infinity" jouée pendant le chargement.
    
    Il s'agit d'une démonstration "meta" : on utilise un petit nombre 
    d'épicycles de Fourier (5) pour dessiner une courbe de Lissajous 
    en forme de signe infini.
    """
    def __init__(self):
        # Création mathématique de la forme "Infini" (Lémniscate de Bernoulli simplifiée)
        t = np.linspace(0, 2*np.pi, 200)
        scale = 60
        x = scale * np.cos(t)
        y = scale * np.sin(t) * np.cos(t) # L'oscillation en Y est deux fois plus rapide
        points = x + 1j * y
        
        # Calcul préalable des coefficients pour cette forme simple
        self.coeffs = FourierEpicycles.compute_coeffs_static(points, 5)
        self.time = 0.0
        self.trail = []            # Liste des points pour l'effet de traînée
        self.trail_length = 150    # Longueur de la queue de l'animation

    def update(self):
        """Met à jour l'horloge interne de l'animation."""
        self.time += 0.005 
        if self.time > 1: self.time -= 1

    def draw(self, screen, font, progress):
        """
        Affiche l'animation et la barre de progression.
        :param screen: Surface Pygame de destination.
        :param font: Police pour le texte.
        :param progress: Valeur actuelle de progression (0 à 1).
        """
        cx, cy = WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2 - 50 
        
        # Affichage du titre de chargement
        loading_txt = font.render("Calcul des intégrales de Fourier...", True, (220, 220, 220))
        loading_rect = loading_txt.get_rect(center=(WINDOW_SIZE[0]//2, cy - 90))
        screen.blit(loading_txt, loading_rect)

        # --- DESSIN DES ÉPICYCLES DU LOADER ---
        current_pos = 0+0j
        for c in self.coeffs:
            prev_pos = current_pos
            # Formule : e^(i * (fréquence * temps + phase))
            angle = c["freq"] * (2*np.pi*self.time) + c["phase"]
            current_pos += c["amp"] * np.exp(1j * angle)
            
            p1 = (cx + prev_pos.real, cy + prev_pos.imag)
            p2 = (cx + current_pos.real, cy + current_pos.imag)
            radius = c["amp"]
            
            # Dessin du cercle guide et du vecteur
            if radius > 1:
                pygame.draw.circle(screen, (40, 40, 40), (int(p1[0]), int(p1[1])), int(radius), 1)
            pygame.draw.line(screen, (80, 80, 80), p1, p2, 1)

        # --- GESTION DE LA TRAÎNÉE COLORÉE ---
        self.trail.append((cx + current_pos.real, cy + current_pos.imag))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)

        if len(self.trail) > 1:
            for i in range(len(self.trail) - 1):
                # Effet arc-en-ciel basé sur l'index dans la traînée
                hue = (i * 0.003 + 0.5) % 1.0
                color = hsv2rgb(hue, 0.6, 1.0)
                # Fondu vers le noir pour la fin de la traînée
                fade_col = tuple(max(0, int(c * (i/len(self.trail)))) for c in color)
                pygame.draw.line(screen, fade_col, self.trail[i], self.trail[i+1], 2)

        # --- BARRE DE PROGRESSION ---
        bar_width = 300
        bar_height = 6
        bar_rect = pygame.Rect(WINDOW_SIZE[0]//2 - bar_width//2, cy + 80, bar_width, bar_height)
        fill_rect = pygame.Rect(WINDOW_SIZE[0]//2 - bar_width//2, cy + 80, bar_width * progress, bar_height)
        
        # Fond de la barre
        pygame.draw.rect(screen, (40, 40, 60), bar_rect, border_radius=3)
        # Remplissage (Vert)
        pygame.draw.rect(screen, (100, 200, 100), fill_rect, border_radius=3)

        # Texte du pourcentage
        pct_text = f"{int(progress * 100)}%"
        txt_surf = font.render(pct_text, True, (200, 200, 200))
        txt_rect = txt_surf.get_rect(center=(WINDOW_SIZE[0]//2, cy + 105))
        screen.blit(txt_surf, txt_rect)

        # --- RAPPEL DES COMMANDES (Aide contextuelle) ---
        controls_help = [
            "COMMANDES DU PROGRAMME :",
            "[F] : Activer/Désactiver le suivi de la caméra",
            "[H] : Afficher/Masquer les cercles",
            "[R] : Réinitialiser le tracé",
            "[+/-] : Zoomer / Dézoomer",
            "[Haut/Bas] : Ajuster la vitesse de rotation"
        ]
        
        # Calcul de la largeur max pour centrer le bloc d'aide
        temp_font_small = pygame.font.SysFont("consolas", 14)
        max_w = max([temp_font_small.size(line)[0] for line in controls_help])
        
        block_x_start = (WINDOW_SIZE[0] - max_w) // 2
        start_y_help = cy + 150
        
        for i, line in enumerate(controls_help):
            is_title = (i == 0)
            color = (150, 150, 255) if is_title else (100, 100, 120)
            curr_font = font if is_title else temp_font_small
            help_surf = curr_font.render(line, True, color)
            screen.blit(help_surf, (block_x_start, start_y_help + i * 20))