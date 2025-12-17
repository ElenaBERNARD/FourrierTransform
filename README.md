# Visualisateur de Séries de Fourier (SVG)

Ce programme lit un fichier vectoriel (SVG) et tente de le redessiner en utilisant une série d'épicycles (cercles tournants), basé sur le principe de la Transformée de Fourier Discrète.

C'est une visualisation mathématique de la manière dont une somme de rotations simples peut créer des formes complexes.

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