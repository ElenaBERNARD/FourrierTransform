import pygame
import numpy as np
from xml.dom import minidom
from svg.path import parse_path
import sys

# ====== CONSTANTS ======
WINDOW_SIZE = (1000, 800)

BG_COLOR = (10, 10, 15)
TRACE_COLOR = (255, 240, 180)
VECTOR_COLOR = (80, 120, 200)
CIRCLE_COLOR = (60, 60, 80)

INPUT_PATH = "dragon.svg"
N_COEFFS = 10
TIME_MULT = 0.002
SCALE_FACTOR = 1.0
PEN_LIFT_THRESHOLD = 20


# ===== SVG =====
class SVGHandler:
    def generate_heart():
        t = np.linspace(0, 2*np.pi, 1000)
        x = 16 * np.sin(t)**3
        y = -(13 * np.cos(t) - 5 * np.cos(2*t) - 2 * np.cos(3*t) - np.cos(4*t))
        return x + 1j * y

    def load_svg(filepath):
        try:
            doc = minidom.parse(filepath)
            path_strings = [p.getAttribute('d') for p in doc.getElementsByTagName('path')]
            doc.unlink()

            if not path_strings:
                print("Aucun path trouvé, utilisation du coeur.")
                return SVGHandler.generate_heart()

            pts = []
            for d in path_strings:
                path = parse_path(d)
                length = path.length()
                if length == 0:
                    continue
                n = int(length) + 50
                for i in range(n):
                    p = path.point(i / n)
                    pts.append(complex(p.real, p.imag))

            pts = np.array(pts)
            pts -= np.mean(pts)

            m = np.max(np.abs(pts))
            if m > 0:
                pts = pts / m * 300

            return pts

        except Exception as e:
            print("Erreur SVG:", e)
            return SVGHandler.generate_heart()


# ===== FOURIER =====
class FourierEpicycles:
    def __init__(self, points, n):
        self.points = points
        self.coeffs = self.compute(points, n)
        self.path = []
        self.prev_point = None
        self.time = 0

    def compute(self, points, n):
        N = len(points)
        freqs = [0] + [k for i in range(1, n + 1) for k in (i, -i)]
        coeffs = []

        for k in freqs:
            idx = np.arange(N)
            c = np.sum(points * np.exp(-2j * np.pi * k * idx / N)) / N
            coeffs.append({
                "freq": k,
                "amp": abs(c),
                "phase": np.angle(c),
                "c": c,
            })

        coeffs.sort(key=lambda x: x["amp"], reverse=True)
        return coeffs

    # apply offset + zoom
    def apply(self, v, cam, zoom):
        return (
            int((v.real + cam[0]) * zoom),
            int((v.imag + cam[1]) * zoom)
        )

    def glow(self, surf, pos, color, zoom):
        for r, alpha in [(8, 40), (5, 80), (3, 120)]:
            R = max(1, int(r * zoom))
            g = pygame.Surface((R*2, R*2), pygame.SRCALPHA)
            pygame.draw.circle(g, (*color, alpha), (R, R), R)
            surf.blit(g, (pos[0]-R, pos[1]-R))

    def update_and_draw(self, surf, center_world, cam, zoom):
        current = complex(center_world[0], center_world[1])

        # Epicycles
        for c in self.coeffs:
            prev = current
            r = c["amp"] * SCALE_FACTOR
            angle = c["freq"] * (2*np.pi*self.time) + c["phase"]
            current += complex(r*np.cos(angle), r*np.sin(angle))

            if r >= 3:
                pygame.draw.circle(surf, CIRCLE_COLOR,
                    self.apply(prev, cam, zoom), int(r * zoom), 1
                )
                pygame.draw.aaline(
                    surf, VECTOR_COLOR,
                    self.apply(prev, cam, zoom),
                    self.apply(current, cam, zoom)
                )

        # Drawing path
        if self.prev_point is not None:
            if abs(current - self.prev_point) < PEN_LIFT_THRESHOLD:
                self.path.append(current)
            else:
                self.path.append(None)
        self.prev_point = current

        s = []
        for p in self.path:
            if p is None:
                if len(s) > 1:
                    pygame.draw.aalines(
                        surf, TRACE_COLOR, False,
                        [self.apply(pt, cam, zoom) for pt in s]
                    )
                s = []
            else:
                s.append(p)
        if len(s) > 1:
            pygame.draw.aalines(
                surf, TRACE_COLOR, False,
                [self.apply(pt, cam, zoom) for pt in s]
            )

        # Glow + dot
        cp = self.apply(current, cam, zoom)
        self.glow(surf, cp, (255, 80, 80), zoom)
        pygame.draw.circle(surf, (255, 100, 100), cp, max(1, int(3 * zoom)))

        # Time step
        self.time += TIME_MULT
        if self.time > 1:
            self.time = 0
            self.path = []
            self.prev_point = None

        return current


# ===== MAIN =====
def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Fourier Epicycles - Follow & Zoom UwU")
    clock = pygame.time.Clock()

    print("Loading SVG...")
    points = SVGHandler.load_svg(INPUT_PATH)
    fourier = FourierEpicycles(points, N_COEFFS)
    print("Ready.")

    follow = False
    camera = np.array([0.0, 0.0])
    zoom = 1.0  # 50% → 200%

    running = True

    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False

                if e.key == pygame.K_f:
                    follow = not follow

                # zoom in
                if e.key in (pygame.K_PLUS, pygame.K_KP_PLUS):
                    zoom *= 1.1
                    zoom = min(2.0, zoom)

                # zoom out
                if e.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    zoom /= 1.1
                    zoom = max(0.5, zoom)

        screen.fill(BG_COLOR)

        # Compute center *in world coordinates*
        center_world = (
            WINDOW_SIZE[0] / 2 / zoom,
            WINDOW_SIZE[1] / 2 / zoom
        )

        pen_pos = fourier.update_and_draw(screen, center_world, camera, zoom)

        if follow:
            camera = np.array([
                WINDOW_SIZE[0] / 2 / zoom - pen_pos.real,
                WINDOW_SIZE[1] / 2 / zoom - pen_pos.imag,
            ])
        else:
            camera = np.array([0.0, 0.0])

        font = pygame.font.SysFont("monospace", 15)
        txt = font.render(
            f"FPS {int(clock.get_fps())}  |  Zoom {zoom:.2f}x  |  Follow {'ON' if follow else 'OFF'}  (F to toggle)",
            True, (200, 200, 200)
        )
        screen.blit(txt, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
