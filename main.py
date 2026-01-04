"""
main.oy
Dessin par épicycles de Fourier.
Fichier principal (main) gérant la boucle de rendu, les entrées utilisateur
et la coordination entre le chargement des données et le moteur de calcul.

Ce script utilise Pygame pour la visualisation et NumPy pour les calculs vectoriels.
"""

import sys
import pygame
import numpy as np

# Importations des modules internes au projet
from settings import *
from utils import draw_grid
from loader_ui import DataLoader, MiniInfinityLoader
from fourier_engine import FourierEpicycles

def main():
    """
    Fonction principale orchestrant le cycle de vie de l'application.
    
    Déroulement :
    1. Initialisation de Pygame et des ressources graphiques.
    2. Gestion du chargement asynchrone du fichier SVG.
    3. Boucle de calcul et de rendu (State Machine : LOADING -> RUNNING).
    4. Nettoyage des ressources à la fermeture.
    """
    
    # --- INITIALISATION PYGAME ---
    pygame.init()
    # Utilisation de DOUBLEBUF pour éviter le scintillement (tearing)
    screen = pygame.display.set_mode(WINDOW_SIZE, pygame.DOUBLEBUF) 
    pygame.display.set_caption("Fourier SVG Renderer - Math Project")
    clock = pygame.time.Clock()
    
    # Polices pour l'interface utilisateur (UI)
    font = pygame.font.SysFont("consolas", 16)
    big_font = pygame.font.SysFont("consolas", 20)

    # --- GESTION DES ARGUMENTS DE LA LIGNE DE COMMANDE ---
    input_file = DEFAULT_INPUT_PATH
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        print(f"[INFO] Chargement du fichier spécifié : {input_file}")
    else:
        print(f"[INFO] Aucun argument, utilisation du fichier par défaut : {input_file}")

    # --- INITIALISATION DES COMPOSANTS ---
    # Mini-animation de chargement (Feedback visuel)
    mini_loader = MiniInfinityLoader()
    
    # DataLoader gère le parsing SVG et le calcul des coefficients dans un thread séparé
    loader = DataLoader(input_file, N_COEFFS)
    loader.start()
    
    # Variables d'état de la simulation
    fourier = None
    camera = np.array([0.0, 0.0])  # Position de la vue
    zoom = 1.0                     # Facteur d'échelle
    visual_speed = 2.0             # Multiplicateur de vitesse de rotation
    follow = False                 # Mode "Suivi de la tête du vecteur"
    
    running = True
    app_state = "LOADING"  # États possibles : LOADING, RUNNING
    
    # --- BOUCLE PRINCIPALE ---
    while running:
        # GESTION DES ÉVÉNEMENTS
        for e in pygame.event.get():
            if e.type == pygame.QUIT: 
                running = False
                
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: 
                    running = False
                
                # Commandes actives uniquement pendant la simulation
                if app_state == "RUNNING":
                    if e.key == pygame.K_f: 
                        follow = not follow  # Toggle suivi caméra
                    if e.key == pygame.K_r: 
                        fourier.batcher.reset()  # Efface le tracé actuel
                    if e.key == pygame.K_h: 
                        fourier.show_vectors = not fourier.show_vectors  # Affiche/Masque les cercles
                    
                    # Contrôles de zoom (Clavier numérique et standard)
                    if e.key in (pygame.K_KP_PLUS, pygame.K_PLUS): 
                        zoom *= 1.1
                    if e.key in (pygame.K_KP_MINUS, pygame.K_MINUS): 
                        zoom /= 1.1
                    
                    # Contrôles de vitesse (Flèches Haut/Bas)
                    if e.key == pygame.K_UP: 
                        visual_speed = min(10, visual_speed + 0.5)
                    if e.key == pygame.K_DOWN: 
                        visual_speed = max(0.1, visual_speed - 0.5)

        # MISE À JOUR ET RENDU (LOGIQUE D'ÉTAT)
        if app_state == "LOADING":
            # --- ÉTAT : CHARGEMENT ---
            screen.fill(BG_COLOR)
            mini_loader.update()
            mini_loader.draw(screen, big_font, loader.progress)
            
            # Vérification de la complétion du thread de calcul
            if loader.done:
                points, total_length, coeffs = loader.data
                # Initialisation du moteur de Fourier avec les données calculées
                fourier = FourierEpicycles(points, total_length, coeffs)
                app_state = "RUNNING"
                
        elif app_state == "RUNNING":
            # --- ÉTAT : SIMULATION ---
            screen.fill(BG_COLOR)
            
            # Calcul de l'incrément temporel (dt)
            # On utilise un sous-échantillonnage (sub-stepping) pour maintenir la précision
            # mathématique même à haute vitesse visuelle.
            dt_frame = visual_speed / fourier.total_length 
            steps_dynamic = int(max(2, min(50, visual_speed * 3)))
            sub_dt = dt_frame / steps_dynamic
            
            current_head_pos = 0+0j
            for _ in range(steps_dynamic):
                # Mise à jour de la physique (somme des phaseurs de Fourier)
                current_head_pos = fourier.update_physics(sub_dt)

            # Gestion de la caméra (Interpolation linéaire pour la fluidité)
            if follow:
                # La caméra suit le dernier vecteur (tête du dessin)
                target_cam = np.array([-current_head_pos.real, -current_head_pos.imag])
                camera = camera + (target_cam - camera) * 0.05
            else:
                # Retour progressif au centre
                camera = camera + (np.array([0.0, 0.0]) - camera) * 0.1

            # Rendu des éléments graphiques
            draw_grid(screen, camera, zoom)
            fourier.draw(screen, camera, zoom)

            # --- INTERFACE UTILISATEUR (HUD) ---
            # Calcul du pourcentage de progression du dessin
            pct_complete = 0
            if fourier.estimated_simulation_points > 0:
                pct_complete = (fourier.batcher.total_points_count / fourier.estimated_simulation_points) * 100

            # Affichage des informations techniques (Haut gauche)
            infos = [
                f"FPS: {int(clock.get_fps())}",
                f"Number of coeffs. : {N_COEFFS}",
                f"Batches: {len(fourier.batcher.batches)}",
                f"Points tracés: {fourier.batcher.total_points_count} ({pct_complete:.1f}%)",
                f"Vitesse : {visual_speed:.2f}x",
            ]
            for i, info in enumerate(infos):
                txt = font.render(info, True, (200, 200, 200))
                screen.blit(txt, (10, 10 + i * 20))
                
            # Affichage des contrôles (Haut droite)
            controls = [
                f"[F] - Suivre ({'Activé' if follow else 'Désactivé'})",
                f"[H] - Cercles/Vecteurs ({'Visibles' if fourier.show_vectors else 'Masqués'})",
                "[R] - Réinitialiser le tracé",
                f"[+/-] Zoom ({zoom:.2f}x)",
                "[Haut/Bas] Ajuster Vitesse",
            ]
            for i, ctrl in enumerate(controls):
                txt = font.render(ctrl, True, (150, 150, 150))
                txt_rect = txt.get_rect(topright=(WINDOW_SIZE[0] - 10, 10 + i * 20))
                screen.blit(txt, txt_rect)

        # Mise à jour de l'affichage
        pygame.display.flip()
        clock.tick(60) # Limite à 60 FPS

    # --- NETTOYAGE FINAL ---
    # On s'assure que le thread de chargement est fermé proprement
    if loader.is_alive():
        loader.join(timeout=1.0)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()