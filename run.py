"""
Normalement, le correcteur a un environement avec pip/uv installé.
Dans ce cas, il peut utiliser: uv pip install -r requirements.txt ou pip install -r requirements.txt et lancer main.py directement.

Cependant, si ce n'est pas le cas, j'ai sauvegardé toutes les dépendances dans le dossier 'lib'.
Dans ce cas il faut lancer run.py qui ajoute 'lib' au path avant d'importer main.py.
"""


import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from main import main
if __name__ == "__main__":
    main()