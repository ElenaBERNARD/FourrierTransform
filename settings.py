# ====== CONSTANTS & CONFIG ======
# Ce fichier contient toutes les variables globales de configuration.

# Taille de la fenêtre et calcul du centre
WINDOW_SIZE = (1200, 900)
CENTER_SCREEN = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)

# Couleurs (Thème sombre)
BG_COLOR = (5, 5, 10)
GRID_COLOR = (20, 30, 70)

# Fichier par défaut (si aucun argument n'est donné)
DEFAULT_INPUT_PATH = "images/dragon.svg" 

# Précision de la simulation
N_COEFFS = 400            # Nombre de cercles (épicycles).

# Paramètres de dessin
THRESHOLD_VELOCITY_FACTOR = 3.0 # Seuil pour détecter un "saut" (lever le stylo)
MIN_DRAW_DIST = 0.5             # Distance min pour ajouter un point (optimisation)