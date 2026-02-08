# Introduction

## Structure du projet

Le fichier principal du projet est `main.py`, qui importe et appelle les scripts dans `./Modules/Scripts`.

Le fichier `run.py`sert à lancer le projet sans avoir à importer les librairies (stockée dans `./lib`)

Le fichier `./Modules/Interface.py` contient les fonctions d'affichage dans le terminal réutilisée dans les autres scripts.

## Lancer le projet

La meilleure façon de lancer le projet est de le faire depuis un invite de commande **bash** en plein écran.

```bash
python run.py # Pas besoin d'installer les librairies au préalable
```

ou pour ne pas utiliser les librairies locales incluses:

```bash
uv run run.py
```

_si vous utiliser uv pour gérer vos dépendances_

ou encore

```bash
pip install -r requirements.txt
python run.py
```

**Spyder utilise une version python modifiée où le terminal intégré entre en conflit avec l'affichage de rich, il n'est donc pas possible de lancer le projet depuis Spyder.**

Un environment virtuel est aussi inclus (./venv)

## Librairies utilisées

- [rich](https://rich.readthedocs.io/en/stable/) pour l'affichage dans le terminal
- [pynput](https://pynput.readthedocs.io/en/latest/#) pour la gestion du clavier

## Notes

Par défaut, le projet bloque tout autre input clavier, même lorsque la fenetre n'est pas active afin d'éviter que l'utilisateur tape dans le terminal par erreur.
Pour changer ce comportement il suffit de modifier la variable `BLOQUER_INPUTS` dans `Global.py` et de relancer le projet.
