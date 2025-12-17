import pygame
import numpy as np
from settings import *
from utils import hsv2rgb

# ====== BATCHER ======
class TrailBatcher:
    """
    Système d'optimisation du rendu.
    Gère les "lots" de points statiques pour éviter de tout redessiner.
    """
    def __init__(self, dynamic_batch_size):
        self.batches = [] 
        self.current_points = []
        self.batch_start_time = 0.0
        self.total_points_count = 0
        self.batch_size = dynamic_batch_size
        
    def reset(self):
        self.batches = []
        self.current_points = []
        self.batch_start_time = 0.0
        self.total_points_count = 0
        
    def add_point(self, point, time_progression):
        if len(self.current_points) == 0:
            self.batch_start_time = time_progression
        self.current_points.append(point)
        self.total_points_count += 1
        
        if len(self.current_points) >= self.batch_size:
            self.flush_batch(time_progression)
            
    def flush_batch(self, current_time):
        """Transforme les points actifs en un lot statique."""
        if len(self.current_points) < 2: return 
        hue = (self.batch_start_time * 1.5) % 1.0
        color = hsv2rgb(hue, 0.7, 1.0)
        self.batches.append({'points': np.array(self.current_points), 'color': color})
        
        last_pt = self.current_points[-1]
        self.current_points = [last_pt]
        self.batch_start_time = current_time

    def cut(self, current_time):
        """Coupe le trait (lever le stylo)."""
        if len(self.current_points) > 1:
            hue = (self.batch_start_time * 1.5) % 1.0
            color = hsv2rgb(hue, 0.7, 1.0)
            self.batches.append({'points': np.array(self.current_points), 'color': color})
        self.current_points = []

    def draw(self, surf, apply_transform_func, cam, zoom):
        for batch in self.batches:
            raw_pts = batch['points']
            x = (raw_pts.real + cam[0]) * zoom + CENTER_SCREEN[0]
            y = (raw_pts.imag + cam[1]) * zoom + CENTER_SCREEN[1]
            screen_pts = np.column_stack((x, y))
            if len(screen_pts) > 1:
                pygame.draw.lines(surf, batch['color'], False, screen_pts, 2)
            
        if len(self.current_points) > 1:
            pts = [apply_transform_func(p, cam, zoom) for p in self.current_points]
            pygame.draw.lines(surf, (255, 255, 255), False, pts, 2)

# ====== FOURIER ======
class FourierEpicycles:
    """Le coeur mathématique qui gère les cercles tournants."""
    def __init__(self, points, total_length, precomputed_coeffs):
        self.time = 0 
        self.total_length = total_length
        self.estimated_simulation_points = int(total_length / MIN_DRAW_DIST)
        
        target_batches = 150
        calculated_batch_size = int(self.estimated_simulation_points / target_batches) if target_batches > 0 else 100
        final_batch_size = max(100, calculated_batch_size)
        
        self.estimated_total_batches = int(self.estimated_simulation_points / final_batch_size)
        self.batcher = TrailBatcher(final_batch_size)
        
        self.overlay = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        self.velocity_threshold = total_length * THRESHOLD_VELOCITY_FACTOR
        
        coeffs = precomputed_coeffs
        self.freqs = np.array([c["freq"] for c in coeffs])
        self.amps = np.array([c["amp"] for c in coeffs])
        self.phases = np.array([c["phase"] for c in coeffs])
        self.draw_coeffs = coeffs 
        
        self.prev_pos_physics = None 
        self.last_saved_pos = None

        self.show_vectors = True 

    @staticmethod
    def compute_coeffs_static(points, n, progress_callback=None):
        """Calcule la Transformée de Fourier Discrète (DFT)."""
        N = len(points)
        freqs = [0] + [k for i in range(1, n + 1) for k in (i, -i)]
        t = np.arange(N)
        coeffs = []
        total_freqs = len(freqs)
        
        for idx, k in enumerate(freqs):
            c = np.sum(points * np.exp(-2j * np.pi * k * t / N)) / N
            coeffs.append({"freq": k, "amp": abs(c), "phase": np.angle(c)})
            if progress_callback and idx % 20 == 0:
                progress_callback(idx / total_freqs)
                
        coeffs.sort(key=lambda x: x["amp"], reverse=True)
        return coeffs

    def get_position_at(self, t):
        angles = self.freqs * (2 * np.pi * t) + self.phases
        vectors = self.amps * np.exp(1j * angles)
        return np.sum(vectors)

    def update_physics(self, dt):
        self.time += dt
        if self.time > 1:
            self.time -= 1
            self.batcher.reset()
            self.prev_pos_physics = None
            self.last_saved_pos = None
            
        pos = self.get_position_at(self.time)
        
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
            should_add = False
            if self.last_saved_pos is None:
                should_add = True
            else:
                dist_from_last_saved = abs(pos - self.last_saved_pos)
                if dist_from_last_saved > MIN_DRAW_DIST:
                    should_add = True
            
            if should_add:
                self.batcher.add_point(pos, self.time)
                self.last_saved_pos = pos
            
        return pos

    def apply_transform(self, v, cam, zoom):
        x = (v.real + cam[0]) * zoom + CENTER_SCREEN[0]
        y = (v.imag + cam[1]) * zoom + CENTER_SCREEN[1]
        return (x, y)

    def draw(self, surf, cam, zoom):
        current_math = 0 + 0j
        self.overlay.fill((0,0,0,0))
        
        for c in self.draw_coeffs:
            prev_math = current_math
            r = c["amp"]
            angle = c["freq"] * (2*np.pi*self.time) + c["phase"]
            current_math += c["amp"] * np.exp(1j * angle) 

            if self.show_vectors:
                screen_r = r * zoom
                screen_prev = self.apply_transform(prev_math, cam, zoom)
                screen_curr = self.apply_transform(current_math, cam, zoom)
                
                if screen_r > 5:
                    pygame.draw.circle(self.overlay, (20, 150, 20, 40), (int(screen_prev[0]), int(screen_prev[1])), int(screen_r), 1)
                    pygame.draw.aaline(self.overlay, (100, 150, 100, 100), screen_prev, screen_curr)
                elif screen_r > 2:
                    pygame.draw.circle(self.overlay, (20, 150, 20, 30), (int(screen_prev[0]), int(screen_prev[1])), int(screen_r), 1)
                elif screen_r > 0.5:
                    pygame.draw.aaline(self.overlay, (100, 150, 100, 40), screen_prev, screen_curr)

        surf.blit(self.overlay, (0,0))
        self.batcher.draw(surf, self.apply_transform, cam, zoom)
        
        cp = self.apply_transform(current_math, cam, zoom)
        pygame.draw.circle(surf, (255, 255, 255), (int(cp[0]), int(cp[1])), 4)
            
        return current_math