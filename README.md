# Visualisateur de Séries de Fourier (SVG)

Ce projet est un visualisateur interactif de séries de Fourier appliquées à des formes vectorielles.
À partir d’un fichier SVG, le programme extrait un chemin, calcule sa Transformée de Fourier Discrète, puis reconstruit la forme à l’aide d’une suite d’épicycles (cercles en rotation).

La visualisation montre comment une somme de rotations complexes permet de reproduire des dessins avec un rendu en temps réel.
<hr>

## Fonctionnalités

**Lecture SVG :** Chargement dynamique de fichiers vectoriels (par défaut dragon.svg).

**Traitement asynchrone :** Calcul des coefficients en arrière-plan (multithreading) pour une interface fluide.

**Moteur de rendu optimisé :** Système de "batching" permettant d'afficher des milliers de segments sans perte de performance.

**Caméra dynamique :** Mode "suivi" (follow mode) pour rester focalisé sur la tête du vecteur de dessin.

**Interface interactive :** Contrôle total sur la vitesse, le zoom et l'affichage des vecteurs.

<hr>

## Contrôles (Clavier)

| Touche | Action | 
|--------|--------|
|   H    | Afficher / Cacher les vecteurs |
|   F    | Activer / Désactiver le suivi de la caméra (Follow Mode) |
|   R    | Réinitialiser le dessin (effacer le tracé) |
| + / -  | Zoom avant / Zoom arrière  |
| Haut/bas  | Augmenter / Réduire la vitesse de dessin | 
| Échap  | Quitter le programme | 

<hr>

## Installation

Assurez-vous d'avoir Python installé

Clonnez ce depôt Github

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

*Note : Si le fichier n'est pas trouvé, le programme générera automatiquement une courbe mathématique en forme de cœur.*

<hr>

## Structure du projet

**Loader Thread :** 
Charge les données en arrière-plan pour ne pas figer la fenêtre.

**SVGHandler :** 
Lit le fichier SVG, trie les chemins pour optimiser le trajet du "stylo".

**FourierEpicycles :** 
Calcule les mathématiques complexes (DFT).

**TrailBatcher :** 
Optimise l'affichage du tracé en "gelant" les anciens points.

<hr>

## Pour aller plus loin

Le fichier ```settings.py``` est conçu pour vous permettre de jouer avec les mathématiques de la simulation. Voici les paramètres clés à modifier pour observer différents comportements :

```N_COEFFS``` C'est le nombre de cercles utilisés.

**Test :** Réduisez-le à 10 pour voir une approximation grossière, ou montez-le à 1000 pour une grande précision (attention au temps de calcul préliminaire).

```THRESHOLD_VELOCITY_FACTOR``` : Définit la sensibilité de détection des "sauts" (quand le stylo se lève).

**Test :** Si votre dessin a des traits parasites qui relient des zones qui devraient être séparées, augmentez cette valeur.

**Attention :** sur un gros SVG avec un petit ```N_COEFFS```, le gribouillage est inévitable. Le dessin ne sera juste pas assez précis (pas assez de coeffs) pour permettre des sauts clairs. Dans ce cas, changer ce threshold ne changera rien !

```MIN_DRAW_DIST``` : Distance minimale entre deux points du tracé.

**Test :** Augmentez cette valeur pour consommer moins de mémoire sur de très longs dessins, au prix d'un tracé un peu plus "anguleux".