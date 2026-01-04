"""
svg_handler.py
Projet Mathématiques : Gestionnaire de fichiers SVG.
Ce module assure la conversion d'un fichier vectoriel (XML/SVG) en une suite 
de nombres complexes échantillonnés, optimisée pour le tracé par épicycles.
"""

import numpy as np
from xml.dom import minidom
from svg.path import parse_path
import time

class SVGHandler:
    """
    Classe utilitaire pour la lecture, le parsing et l'optimisation des chemins SVG.
    Elle transforme les balises <path> en coordonnées mathématiques exploitables.
    """
    
    @staticmethod
    def generate_heart():
        """
        Génère une forme de cœur via ses équations paramétriques.
        Sert de solution de secours (fallback) si le fichier SVG est invalide.
        
        Équations utilisées :
        x = 16 * sin^3(t)
        y = 13*cos(t) - 5*cos(2t) - 2*cos(3t) - cos(4t)
        """
        t = np.linspace(0, 2*np.pi, 1000)
        x = 16 * np.sin(t)**3
        y = -(13 * np.cos(t) - 5 * np.cos(2*t) - 2 * np.cos(3*t) - np.cos(4*t))
        return x + 1j * y, 1000.0

    @staticmethod
    def sort_paths(paths_list, progress_callback=None):
        """
        Algorithme glouton (Heuristique du plus proche voisin).
        
        Un fichier SVG contient souvent des tracés dans le désordre. Pour que 
        le moteur de Fourier ne fasse pas des "sauts" incessants, on réorganise 
        les tracés pour que la fin d'un chemin soit la plus proche possible 
        du début du suivant.
        
        :param paths_list: Liste de listes de points complexes.
        :param progress_callback: Fonction de mise à jour de la barre de progression.
        :return: Liste de chemins triés logiquement.
        """
        if not paths_list: return []
        
        count = len(paths_list)
        # On commence par le premier chemin trouvé
        sorted_paths = [paths_list.pop(0)]
        total_initial = count + 1
        
        while paths_list:
            last_point = sorted_paths[-1][-1]
            best_idx = 0
            min_dist = float('inf')
            
            # Recherche du voisin le plus proche (Complexité O(N^2))
            for i, p in enumerate(paths_list):
                dist = abs(p[0] - last_point) # Distance Euclidienne entre complexes
                if dist < min_dist:
                    min_dist = dist
                    best_idx = i
            
            sorted_paths.append(paths_list.pop(best_idx))

            # Optimisation : évite de bloquer l'éxécution sur des gros fichiers
            if len(sorted_paths) % 20 == 0:
                time.sleep(0.0001)
            
            if progress_callback and len(sorted_paths) % 5 == 0:
                # On réserve les derniers 10% de la barre pour le tri
                base_pct = 0.9
                local_pct = len(sorted_paths) / total_initial
                progress_callback(base_pct + (local_pct * 0.1))
        
        return sorted_paths

    @staticmethod
    def load_svg(filepath, progress_callback=None):
        """
        Charge et traite un fichier SVG pour Fourier.
        
        Étapes :
        1. Extraction des chaînes 'd' des balises <path> via minidom.
        2. Échantillonnage (Sampling) des courbes en points discrets.
        3. Tri des chemins pour minimiser les distances à vide.
        4. Normalisation : centrage sur l'origine (0,0) et mise à l'échelle.
        """
        try:
            if progress_callback: progress_callback(0.1) 
            
            # Analyse du fichier XML
            doc = minidom.parse(filepath)
            path_strings = [p.getAttribute('d') for p in doc.getElementsByTagName('path')]
            doc.unlink()
            
            if not path_strings: 
                return SVGHandler.generate_heart()

            raw_paths = []
            total_length = 0.0
            total_paths = len(path_strings)

            # Étape 1 : Parsing et échantillonnage numérique
            for idx, d in enumerate(path_strings):
                path = parse_path(d)
                length = path.length()
                
                if idx % 5 == 0: time.sleep(0.0001)

                if length == 0: continue
                total_length += length
                
                # Densité de points : on crée environ 1 point par unité de longueur + 10
                n_points = int(length) + 10 
                pts = []
                for i in range(n_points):
                    # Transformation de la coordonnée (x, y) en nombre complexe z = x + iy
                    p = path.point(i / n_points)
                    pts.append(complex(p.real, p.imag))
                
                if pts:
                    raw_paths.append(pts)
                
                if progress_callback and idx % 2 == 0:
                    # On alloue 80% de la progression au parsing
                    current_pct = 0.1 + (idx / total_paths) * 0.8
                    progress_callback(current_pct)

            # Étape 2 : Tri intelligent pour un tracé fluide
            sorted_paths = SVGHandler.sort_paths(raw_paths, progress_callback)
            
            # Étape 3 : Consolidation dans un seul tableau NumPy
            final_points = []
            for p_list in sorted_paths:
                final_points.extend(p_list)
            
            pts = np.array(final_points)
            
            # Étape 4 : Post-traitement Géométrique
            if len(pts) > 0:
                # Centrage : On soustrait la moyenne des positions pour centrer sur (0,0)
                pts -= np.mean(pts)
                
                # Normalisation : On ajuste la taille pour qu'elle tienne dans l'écran
                m = np.max(np.abs(pts))
                if m > 0: 
                    pts = pts / m * 300 # Rayon de 300 pixels environ
            
            # Calcul de la longueur totale réelle du tracé pour la simulation
            diffs = np.abs(np.diff(pts))
            estimated_math_length = np.sum(diffs)
            
            if progress_callback: progress_callback(1.0)
            return pts, estimated_math_length

        except Exception as e:
            print(f"[ERREUR] Échec du chargement SVG : {e}")
            return SVGHandler.generate_heart()