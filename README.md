# Visualisateur de Séries de Fourier (SVG)

Ce projet est un visualisateur interactif de séries de Fourier appliquées à des formes vectorielles.
À partir d’un fichier SVG, le programme extrait un chemin, calcule sa Transformée de Fourier Discrète, puis reconstruit la forme à l’aide d’une suite d’épicycles (cercles en rotation).

La visualisation montre comment une somme de rotations complexes permet de reproduire des dessins détaillés, tout en offrant un rendu fluide et interactif en temps réel.

## Fonctionnalités

**Lecture SVG :** Charge n'importe quel fichier SVG (par défaut dragon.svg).

**Écran de chargement amélioré :** Barre de progression fluide avec feedback visuel.

**Optimisation :** Utilise un système de "Batching" pour garder un framerate élevé même avec des milliers de points.

**Contrôles interactifs :** Zoom, vitesse, caméra.

## Contrôles (Clavier)

| Touche | Action | 
|--------|--------|
|   H    | Afficher / Cacher les vecteurs (les bras rotatifs) |
|   F    | Activer / Désactiver la caméra suiveuse (Follow Mode) |
|   R    | Réinitialiser le dessin (effacer le tracé) |
| + / -  | Zoom avant / Zoom arrière (Pavé numérique) | 
| Haut/bas  | Augmenter / Réduire la vitesse de dessin | 
| Échap  | Quitter le programme | 

## Installation

Assurez-vous d'avoir Python installé

Installez les dépendances via pip :
```Bash
pip install -r requirements.txt
```
<hr>

Lancer le programme
```Bash
python main.py
```
chargera une image /images/dragon.svg (si présente dans /images)

OU

```Bash
python main.py /chemin/vers/une/image.svg
```
qui utilisera le chemin en paramètre pour charger une image

## Structure du projet

**Loader Thread :** 
Charge les données en arrière-plan pour ne pas figer la fenêtre.

**SVGHandler :** 
Lit le fichier SVG, trie les chemins pour optimiser le trajet du "stylo".

**FourierEpicycles :** 
Calcule les mathématiques complexes (DFT).

**TrailBatcher :** 
Optimise l'affichage du tracé en "gelant" les anciens points.

## Note

Si aucun fichier correspondant au chemin vers votre image (.svg) n'est trouvé, le programme générera automatiquement une forme de cœur