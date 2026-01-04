"""
Projet Mathématiques : Moteur de Calcul de Fourier.
Ce module contient :
1. Le 'TrailBatcher' : Optimise le rendu en regroupant les points par lots.
2. 'FourierEpicycles' : Le coeur mathématique calculant la position des cercles.
"""

import pygame
import numpy as np
from settings import *
from utils import hsv2rgb

class TrailBatcher:
    """
    Système d'optimisation du rendu (Batch Rendering).
    
    Dessiner des milliers de lignes individuelles à chaque frame avec Pygame
    est extrêmement coûteux pour le CPU. Cette classe regroupe les segments de 
    droite par 'lots' (batches) statiques pour maintenir un framerate élevé.
    """
    def __init__(self, dynamic_batch_size):
        self.batches = []           # Liste des lots déjà calculés et fixés
        self.current_points = []    # Points du lot en cours de construction
        self.batch_start_time = 0.0 # Temps de début pour la couleur
        self.total_points_count = 0
        self.batch_size = dynamic_batch_size
        
    def reset(self):
        """Réinitialise tout le tracé (utilisé lors du bouclage ou par touche R)."""
        self.batches = []
        self.current_points = []
        self.batch_start_time = 0.0
        self.total_points_count = 0
        
    def add_point(self, point, time_progression):
        """Ajoute un point au lot actuel et le 'fige' s'il est plein."""
        if len(self.current_points) == 0:
            self.batch_start_time = time_progression
        self.current_points.append(point)
        self.total_points_count += 1
        
        if len(self.current_points) >= self.batch_size:
            self.flush_batch(time_progression)
            
    def flush_batch(self, current_time):
        """Transforme les points actifs en un lot statique avec une couleur fixe."""
        if len(self.current_points) < 2: return 
        
        # Attribution d'une couleur basée sur la progression temporelle (effet arc-en-ciel)
        hue = (self.batch_start_time * 1.5) % 1.0
        color = hsv2rgb(hue, 0.7, 1.0)
        
        # On convertit en tableau NumPy pour accélérer les opérations de dessin futures
        self.batches.append({'points': np.array(self.current_points), 'color': color})
        
        # On garde le dernier point pour assurer la continuité avec le lot suivant
        last_pt = self.current_points[-1]
        self.current_points = [last_pt]
        self.batch_start_time = current_time

    def cut(self, current_time):
        """Force la fin d'un lot sans liaison (simule un levé de stylo)."""
        if len(self.current_points) > 1:
            self.flush_batch(current_time)
        self.current_points = []

    def draw(self, surf, apply_transform_func, cam, zoom):
        """Dessine tous les lots accumulés ainsi que le trait en cours."""
        for batch in self.batches:
            raw_pts = batch['points']
            # Transformation vectorisée (NumPy) pour les performances
            x = (raw_pts.real + cam[0]) * zoom + CENTER_SCREEN[0]
            y = (raw_pts.imag + cam[1]) * zoom + CENTER_SCREEN[1]
            screen_pts = np.column_stack((x, y))
            
            if len(screen_pts) > 1:
                pygame.draw.lines(surf, batch['color'], False, screen_pts, 2)
            
        # Dessin du segment "actif" (en blanc)
        if len(self.current_points) > 1:
            pts = [apply_transform_func(p, cam, zoom) for p in self.current_points]
            pygame.draw.lines(surf, (255, 255, 255), False, pts, 2)

class FourierEpicycles:
    """
    Le moteur mathématique gérant les séries de Fourier complexes.
    
    Le principe est de représenter n'importe quelle courbe fermée comme une 
    somme de vecteurs tournants (phaseurs) : 
    $f(t) = \sum c_n e^{i n \omega t}$
    """
    def __init__(self, points, total_length, precomputed_coeffs):
        self.time = 0 
        self.total_length = total_length
        self.estimated_simulation_points = int(total_length / MIN_DRAW_DIST)
        
        # Calcul dynamique de la taille des lots pour équilibrer fluidité et mémoire
        target_batches = 150
        calculated_batch_size = int(self.estimated_simulation_points / target_batches)
        final_batch_size = max(100, calculated_batch_size)
        
        self.batcher = TrailBatcher(final_batch_size)
        self.precomputed_coeffs = precomputed_coeffs
        # Surface avec canal alpha (transparence) pour l'effet de flou des cercles
        self.overlay = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        self.velocity_threshold = total_length * THRESHOLD_VELOCITY_FACTOR
        
        # Extraction des paramètres des coefficients (amplitudes, fréquences, phases)
        coeffs = precomputed_coeffs
        self.freqs = np.array([c["freq"] for c in coeffs])
        self.amps = np.array([c["amp"] for c in coeffs])
        self.phases = np.array([c["phase"] for c in coeffs])
        self.draw_coeffs = precomputed_coeffs 
        
        self.prev_pos_physics = None 
        self.last_saved_pos = None
        self.show_vectors = True 

    @staticmethod
    def compute_coeffs_static(points, n, progress_callback=None):
        """
        Calcule la Transformée de Fourier Discrète (DFT).
        
        Formule mathématique :
        $c_k = \frac{1}{N} \sum_{n=0}^{N-1} p_n e^{-i \frac{2\pi}{N} kn}$
        
        Chaque $c_k$ est un nombre complexe dont :
        - Le module ($abs(c_k)$) est l'amplitude (rayon du cercle).
        - L'argument ($angle(c_k)$) est la phase initiale.
        """
        N = len(points)
        # On génère des fréquences : [0, 1, -1, 2, -2, ..., n, -n]
        freqs = [0] + [k for i in range(1, n + 1) for k in (i, -i)]
        t = np.arange(N)
        coeffs = []
        total_freqs = len(freqs)
        
        for idx, k in enumerate(freqs):
            # Calcul de l'intégrale numérique via somme de Riemann
            c = np.sum(points * np.exp(-2j * np.pi * k * t / N)) / N
            coeffs.append({"freq": k, "amp": abs(c), "phase": np.angle(c)})
            
            if progress_callback and idx % 20 == 0:
                progress_callback(idx / total_freqs)
                
        # Tri par amplitude décroissante pour un effet visuel plus esthétique
        coeffs.sort(key=lambda x: x["amp"], reverse=True)
        return coeffs

    def get_position_at(self, t):
        """Reconstruit le point complexe au temps t par la somme des phaseurs."""
        # Somme de : amplitude * e^(i * (fréquence * temps + phase))
        angles = self.freqs * (2 * np.pi * t) + self.phases
        vectors = self.amps * np.exp(1j * angles)
        return np.sum(vectors)

    def update_physics(self, dt):
        """
        Gère l'évolution temporelle et la logique de tracé.
        :param dt: Incrément de temps.
        :return: Position complexe actuelle du bout de la chaîne.
        """
        self.time += dt
        if self.time > 1: # Bouclage de la simulation
            self.time -= 1
            self.batcher.reset()
            self.prev_pos_physics = None
            self.last_saved_pos = None
            
        pos = self.get_position_at(self.time)
        
        # Détection de "saut" (MoveTo dans le SVG)
        # Si la distance parcourue est trop grande par rapport au temps, c'est une discontinuité
        is_jumping = False
        if self.prev_pos_physics is not None:
            dist_physics = abs(pos - self.prev_pos_physics)
            velocity = dist_physics / (dt + 1e-9)
            if velocity > self.velocity_threshold:
                is_jumping = True
        
        self.prev_pos_physics = pos 

        if is_jumping:
            self.batcher.cut(self.time)
            self.last_saved_pos = None 
        else:
            # Optimisation : on n'ajoute un point que si on a bougé d'une distance minimale
            should_add = False
            if self.last_saved_pos is None:
                should_add = True
            else:
                if abs(pos - self.last_saved_pos) > MIN_DRAW_DIST:
                    should_add = True
            
            if should_add:
                self.batcher.add_point(pos, self.time)
                self.last_saved_pos = pos
            
        return pos

    def apply_transform(self, v, cam, zoom):
        """Transforme une coordonnée complexe mathématique en coordonnée écran Pygame."""
        x = (v.real + cam[0]) * zoom + CENTER_SCREEN[0]
        y = (v.imag + cam[1]) * zoom + CENTER_SCREEN[1]
        return (x, y)

    def draw(self, surf, cam, zoom):
        """Affiche les cercles (épicycles) et les vecteurs sur l'overlay."""
        current_math = 0 + 0j
        self.overlay.fill((0,0,0,0)) # Effacer la couche transparente
        
        for c in self.draw_coeffs:
            prev_math = current_math
            r = c["amp"]
            angle = c["freq"] * (2*np.pi*self.time) + c["phase"]
            current_math += c["amp"] * np.exp(1j * angle) 

            if self.show_vectors:
                screen_r = r * zoom
                screen_prev = self.apply_transform(prev_math, cam, zoom)
                screen_curr = self.apply_transform(current_math, cam, zoom)
                
                # Rendu adaptatif : on ne dessine pas les détails trop petits pour l'écran
                if screen_r > 5:
                    pygame.draw.circle(self.overlay, (20, 150, 20, 40), (int(screen_prev[0]), int(screen_prev[1])), int(screen_r), 1)
                    pygame.draw.aaline(self.overlay, (100, 150, 100, 100), screen_prev, screen_curr)
                elif screen_r > 0.5:
                    pygame.draw.aaline(self.overlay, (100, 150, 100, 40), screen_prev, screen_curr)

        # Fusion de l'overlay avec la surface principale
        surf.blit(self.overlay, (0,0))
        # Dessin du tracé mémorisé
        self.batcher.draw(surf, self.apply_transform, cam, zoom)
        
        # Point final (tête du vecteur)
        cp = self.apply_transform(current_math, cam, zoom)
        pygame.draw.circle(surf, (255, 255, 255), (int(cp[0]), int(cp[1])), 4)
            
        return current_math