import numpy as np
from xml.dom import minidom
from svg.path import parse_path
import time

# ====== SVG HANDLER ======
class SVGHandler:
    """Gère la lecture, le parsing et l'optimisation des fichiers SVG."""
    
    @staticmethod
    def generate_heart():
        """Génère une forme de coeur mathématique si le fichier SVG est introuvable."""
        t = np.linspace(0, 2*np.pi, 1000)
        x = 16 * np.sin(t)**3
        y = -(13 * np.cos(t) - 5 * np.cos(2*t) - 2 * np.cos(3*t) - np.cos(4*t))
        return x + 1j * y, 1000.0

    @staticmethod
    def sort_paths(paths_list, progress_callback=None):
        """
        Algorithme glouton (Greedy) pour trier les chemins.
        Relie la fin d'un tracé au début du tracé le plus proche.
        """
        if not paths_list: return []
        
        count = len(paths_list)
        sorted_paths = [paths_list.pop(0)]
        total_initial = count + 1
        
        while paths_list:
            last_point = sorted_paths[-1][-1]
            best_idx = 0
            min_dist = float('inf')
            
            # Recherche du voisin le plus proche
            for i, p in enumerate(paths_list):
                dist = abs(p[0] - last_point)
                if dist < min_dist:
                    min_dist = dist
                    best_idx = i
            
            sorted_paths.append(paths_list.pop(best_idx))

            # === OPTIMISATION LAG ===
            # Petite pause pour laisser le CPU respirer
            if len(sorted_paths) % 20 == 0:
                time.sleep(0.0001)
            
            # Mise à jour de la barre de progression
            if progress_callback and len(sorted_paths) % 5 == 0:
                base_pct = 0.9
                local_pct = len(sorted_paths) / total_initial
                progress_callback(base_pct + (local_pct * 0.1))
        
        return sorted_paths

    @staticmethod
    def load_svg(filepath, progress_callback=None):
        """Charge le fichier, extrait les chemins et les convertit en points complexes."""
        try:
            # Feedback immédiat
            if progress_callback: progress_callback(0.1) 
            
            doc = minidom.parse(filepath)
            path_strings = [p.getAttribute('d') for p in doc.getElementsByTagName('path')]
            doc.unlink()
            
            if not path_strings: 
                return SVGHandler.generate_heart()

            raw_paths = []
            total_length = 0.0
            total_paths = len(path_strings)

            # Étape 1 : Parsing & Sampling
            for idx, d in enumerate(path_strings):
                path = parse_path(d)
                length = path.length()
                
                # Anti-Freeze
                if idx % 5 == 0:
                    time.sleep(0.0001)

                if length == 0: continue
                total_length += length
                
                n_points = int(length) + 10 
                pts = []
                for i in range(n_points):
                    p = path.point(i / n_points)
                    pts.append(complex(p.real, p.imag))
                
                if pts:
                    raw_paths.append(pts)
                
                if progress_callback and idx % 2 == 0:
                    current_pct = 0.1 + (idx / total_paths) * 0.8
                    progress_callback(current_pct)

            # Étape 2 : Tri intelligent
            sorted_paths = SVGHandler.sort_paths(raw_paths, progress_callback)
            
            # Aplatir la liste
            final_points = []
            for p_list in sorted_paths:
                final_points.extend(p_list)
            
            pts = np.array(final_points)
            
            # Centrer et Normaliser
            if len(pts) > 0:
                pts -= np.mean(pts)
                m = np.max(np.abs(pts))
                if m > 0: pts = pts / m * 300
            
            diffs = np.abs(np.diff(pts))
            estimated_math_length = np.sum(diffs)
            
            if progress_callback: progress_callback(1.0)
            return pts, estimated_math_length

        except Exception as e:
            print(f"Erreur chargement SVG: {e}")
            return SVGHandler.generate_heart()