"""
Fonctions utilitaires.
Ce module regroupe les outils d'aide pour la gestion des couleurs et les 
calculs de rendu graphique, notamment la grille dynamique et les dégradés.
"""

import colorsys
import pygame
from settings import *

def hsv2rgb(h, s, v):
    """
    Convertit une couleur du modèle HSV (Teinte, Saturation, Valeur) vers le modèle RGB.
    
    En mathématiques et en programmation graphique, le modèle HSV est souvent 
    privilégié pour créer des dégradés arc-en-ciel fluides (en faisant varier 
    uniquement la teinte 'h').
    
    :param h: Teinte (Hue) normalisée entre 0.0 et 1.0.
    :param s: Saturation normalisée entre 0.0 et 1.0.
    :param v: Valeur (Luminosité) normalisée entre 0.0 et 1.0.
    :return: Un tuple (R, G, B) d'entiers entre 0 et 255 compatible avec Pygame.
    """
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h, s, v))

def draw_grid(surf, cam, zoom):
    """
    Affiche une grille de référence "infinie" sur la surface de rendu.
    
    La grille réagit aux déplacements de la caméra (translation) et au zoom
    (mise à l'échelle), ce qui permet de conserver un repère spatial fixe 
    pendant la simulation des épicycles de Fourier.
    
    Logique mathématique :
    1. L'espacement des lignes est proportionnel au zoom.
    2. L'utilisation de l'opérateur modulo (%) sur les coordonnées de la caméra
       permet de créer l'illusion d'une grille qui se répète indéfiniment sans
       avoir à stocker des milliers de lignes en mémoire.
    
    :param surf: Surface Pygame de destination.
    :param cam: Vecteur position de la caméra [x, y].
    :param zoom: Facteur de zoom actuel (multiplicateur d'échelle).
    """
    # L'espacement de base est défini dans settings.py (GRID_STEP)
    spacing = int(GRID_STEP * zoom)
    
    # Sécurité visuelle : évite que la grille ne devienne illisible si on dézoome trop
    if spacing < 20: 
        spacing = 20
    
    # Calcul du décalage (offset) relatif pour l'illusion d'infinité
    # On intègre CENTER_SCREEN pour que l'origine (0,0) soit bien au centre de la vue
    offset_x = int(cam[0] * zoom + CENTER_SCREEN[0]) % spacing
    offset_y = int(cam[1] * zoom + CENTER_SCREEN[1]) % spacing
    
    # Tracé des lignes verticales (Axe X)
    for x in range(offset_x, WINDOW_SIZE[0], spacing):
        pygame.draw.line(surf, GRID_COLOR, (x, 0), (x, WINDOW_SIZE[1]), 1)
        
    # Tracé des lignes horizontales (Axe Y)
    for y in range(offset_y, WINDOW_SIZE[1], spacing):
        pygame.draw.line(surf, GRID_COLOR, (0, y), (WINDOW_SIZE[0], y), 1)