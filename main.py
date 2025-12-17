import sys
import pygame
import numpy as np
from settings import *
from utils import draw_grid
from loader_ui import DataLoader, MiniInfinityLoader
from fourier_engine import FourierEpicycles

# ====== MAIN ======
def main():
    """Point d'entrée principal du programme."""
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE, pygame.DOUBLEBUF) 
    pygame.display.set_caption("Fourier - Accurate Loader & Classic GUI")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 16)
    big_font = pygame.font.SysFont("consolas", 20)

    # === GESTION ARGUMENTS ===
    # Si un argument est passé, on l'utilise, sinon on prend le défaut
    input_file = DEFAULT_INPUT_PATH
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        print(f"Chargement du fichier : {input_file}")
    else:
        print(f"Aucun argument, chargement par défaut : {input_file}")

    # Initialisation
    mini_loader = MiniInfinityLoader()
    # On utilise 'input_file' défini ci-dessus
    loader = DataLoader(input_file, N_COEFFS)
    loader.start()
    
    fourier = None
    camera = np.array([0.0, 0.0])
    zoom = 1.0
    visual_speed = 2.0 
    follow = False
    
    running = True
    app_state = "LOADING"
    
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: running = False
                if app_state == "RUNNING":
                    if e.key == pygame.K_f: follow = not follow
                    if e.key == pygame.K_r: fourier.batcher.reset()
                    if e.key == pygame.K_h: fourier.show_vectors = not fourier.show_vectors
                    if e.key in (pygame.K_KP_PLUS, pygame.K_PLUS): zoom *= 1.1
                    if e.key in (pygame.K_KP_MINUS, pygame.K_MINUS): zoom /= 1.1
                    if e.key == pygame.K_UP: visual_speed = min(10, visual_speed + 0.5)
                    if e.key == pygame.K_DOWN: visual_speed = max(0.5, visual_speed - 0.5)

        if app_state == "LOADING":
            screen.fill(BG_COLOR)
            mini_loader.update()
            mini_loader.draw(screen, big_font, loader.progress)
            
            if loader.done:
                points, total_length, coeffs = loader.data
                fourier = FourierEpicycles(points, total_length, coeffs)
                app_state = "RUNNING"
                
        elif app_state == "RUNNING":
            screen.fill(BG_COLOR)
            
            dt_frame = visual_speed / fourier.total_length 
            steps_dynamic = int(max(2, min(50, visual_speed * 3)))
            sub_dt = dt_frame / steps_dynamic
            
            current_head_pos = 0+0j
            for _ in range(steps_dynamic):
                current_head_pos = fourier.update_physics(sub_dt)

            if follow:
                target_cam = np.array([-current_head_pos.real, -current_head_pos.imag])
                camera = camera + (target_cam - camera) * 0.05
            else:
                camera = camera + (np.array([0.0, 0.0]) - camera) * 0.1

            draw_grid(screen, camera, zoom)
            fourier.draw(screen, camera, zoom)

            pct_complete = 0
            if fourier.estimated_simulation_points > 0:
                pct_complete = (fourier.batcher.total_points_count / fourier.estimated_simulation_points) * 100

            infos = [
                f"FPS: {int(clock.get_fps())}",
                f"Batches: {len(fourier.batcher.batches)}",
                f"Points tracés: {fourier.batcher.total_points_count} ({pct_complete:.1f}%)",
                f"Vitesse : {visual_speed:.2f}x",
            ]
            for i, info in enumerate(infos):
                txt = font.render(info, True, (200, 200, 200))
                screen.blit(txt, (10, 10 + i * 20))
                
            controls = [
                f"[F] - Suivre ({'ON' if follow else 'OFF'})",
                f"[H] - Vecteurs ({'ON' if fourier.show_vectors else 'OFF'})",
                "[R] - Reset",
                f"[+/-] Zoom ({zoom:.2f}x)",
                "[Haut/Bas] Vitesse",
            ]
            for i, ctrl in enumerate(controls):
                txt = font.render(ctrl, True, (150, 150, 150))
                txt_rect = txt.get_rect(topright=(WINDOW_SIZE[0] - 10, 10 + i * 20))
                screen.blit(txt, txt_rect)

        pygame.display.flip()
        clock.tick(60)

    if loader.is_alive():
        loader.join(timeout=1.0)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()