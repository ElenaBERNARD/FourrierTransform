import colorsys
import pygame
from settings import *

# ====== UTILS ======
def hsv2rgb(h, s, v):
    """Convertit une couleur HSV (Teinte, Saturation, Valeur) en RGB pour Pygame."""
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h, s, v))

def draw_grid(surf, cam, zoom):
    """Dessine une grille infinie en fond qui bouge avec la caméra."""
    spacing = int(100 * zoom)
    if spacing < 20: spacing = 20 # Évite que la grille devienne un mur de pixels si on dézoome trop
    
    # Calcul du décalage pour donner l'illusion d'infinité
    offset_x = int(cam[0] * zoom + CENTER_SCREEN[0]) % spacing
    offset_y = int(cam[1] * zoom + CENTER_SCREEN[1]) % spacing
    
    # Lignes verticales
    for x in range(offset_x, WINDOW_SIZE[0], spacing):
        pygame.draw.line(surf, GRID_COLOR, (x, 0), (x, WINDOW_SIZE[1]), 1)
    # Lignes horizontales
    for y in range(offset_y, WINDOW_SIZE[1], spacing):
        pygame.draw.line(surf, GRID_COLOR, (0, y), (WINDOW_SIZE[0], y), 1)