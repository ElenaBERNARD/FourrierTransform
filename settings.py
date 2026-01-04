"""
settings.py
Configuration globale.
Ce fichier centralise tous les paramètres de l'application :
1. Paramètres d'affichage et interface (UI)
2. Paramètres de précision pour les séries de Fourier
3. Optimisations du moteur de rendu
"""

# --- CONFIGURATION DE L'INTERFACE (GUI) ---
# Dimensions de la fenêtre d'affichage (en pixels)
WINDOW_SIZE = (1200, 900)

# Calcul du centre de l'écran pour le positionnement relatif des éléments
CENTER_SCREEN = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)

# Thème de couleurs (Format RGB)
BG_COLOR = (5, 5, 10)       # Fond bleu nuit très sombre
GRID_COLOR = (20, 30, 70)   # Couleur des lignes de la grille

# --- GESTION DES FICHIERS ---
# Chemin vers le fichier SVG par défaut si aucun argument n'est passé en ligne de commande
DEFAULT_INPUT_PATH = "images/dragon.svg" 

# --- PARAMÈTRES MATHÉMATIQUES (FOURIER) ---
"""
N_COEFFS définit le nombre de phaseurs (cercles tournants).
- Plus ce nombre est élevé, plus le dessin final sera fidèle au SVG d'origine.
- Mathématiquement, cela correspond à l'ordre de troncature de la série de Fourier.
- Attention : Une valeur trop élevée peut ralentir les calculs de l'intégrale numérique.
Une valeur de 200 donne des résultats correcte sur des SVG simples (une seule forme)
Une valeur de 500 donne de tres bon résultats sur des SVG avec quelques formes
Une valeur de 1000+ sera presque toujours satisfaisante
"""
N_COEFFS = 1000

# --- OPTIMISATION DU TRACÉ ---
"""
THRESHOLD_VELOCITY_FACTOR : Seuil de détection de 'saut'.
Dans un SVG, il y a parfois des coupures (lever de stylo). 
Si la vitesse instantanée entre deux points calculés dépasse ce facteur 
par rapport à la moyenne, on considère qu'il ne faut pas tracer de ligne.
A conserver entre 3.0 et 4.0 en règle générale
"""
THRESHOLD_VELOCITY_FACTOR = 3.0

"""
MIN_DRAW_DIST : Distance minimale de déplacement (en pixels).
Optimisation permettant d'éviter d'ajouter des points dans le 'batch' de dessin
si la tête du vecteur n'a quasiment pas bougé. Cela réduit la consommation mémoire.
"""
MIN_DRAW_DIST = 0.5 

# --- PARAMÈTRES DE LA GRILLE (DÉCORATION) ---
GRID_STEP = 100  # Espacement entre les lignes de la grille en pixels