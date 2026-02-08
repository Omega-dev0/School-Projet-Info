"""
Ce module contient sert à partager des éléments globaux à touts les scripts sans avoir à les passer en paramètres à chaque fois.
Ceci est un bon design car python genere un contexte d'execution isolé à chaque execution et un seul utilisateur peut utiliser
le programme à la fois, donc on peut se permettre d'avoir des éléments globaux sans risquer de conflits entre utilisateurs ou entre différentes exécutions du programme.
"""

# ――――――――――――――――――――――――― IMPORTATION DES MODULES ――――――――――――――――――――――――――

from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console

import sqlite3

import Modules.Interface as UI

import sys

# ――――――――――――――――――――――――― FONCTIONS ――――――――――――――――――――――――――


def interfacePrincipale():
    """ "
    Genere l'interface principale du programme, qui est un layout divisé en deux parties, une partie gauche et une partie droite.
    """
    contenu = Layout()
    contenu.split_row(Layout(name="gauche", ratio=10), Layout(name="droite", ratio=7))

    gauche = Panel("En attente de données...", border_style="bold green")
    contenu["gauche"].update(gauche)
    droite = Panel("En attente de données...", border_style="bold red")
    contenu["droite"].update(droite)

    return contenu


# Fonction de sortie du programme, utilisée à plusieurs endroits pour éviter les redondances et faciliter les modifications futures
def exit():

    UI.mettreAJourPanelDroit("")
    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Fermeture de l'application",
        message="[red]Vous avez choisi de quitter l'application.[/red] \n\nAppuyez sur Entrée pour continuer",
    )

    # Nettoyage de rich
    LIVE.stop()
    CONSOLE.clear()

    # Fermeture de la connexion à la base de données
    CONNEXION.close()

    # Fermeture du programme
    sys.exit(0)


def estGerant(idClient):
    """ "
    Fonction qui vérifie si un client est un gérant ou non, en fonction de son id.
    Les ids des clients gérants sont définis dans la variable COMPTES_GERANT.
    """
    return str(idClient) in COMPTES_GERANT


# ――――――――――――――――――――――――― VARIABLES ――――――――――――――――――――――――――
# comptes désignés pour être des gérants, utilisés pour différencier les options du menu principal destinées au gérant de celles destinées au client, et pour restreindre l'accès à certaines fonctionnalités aux seuls gérants.
COMPTES_GERANT = ["6", "7"]


# Pour pynput, si True, touts les inputs sont bloqués hors du programme.
BLOQUER_INPUTS = True

# Initialisation de rich
CONSOLE = Console()
INTERFACE = interfacePrincipale()
LIVE = Live(INTERFACE, console=CONSOLE, auto_refresh=False, transient=False)
LIVE.start(refresh=True)

# Connextion à la base de donnée, unique pour tout le programme
# Sera fermée par main à la fin
CONNEXION = sqlite3.connect("./Data/spectacles.sqlite", check_same_thread=False)

# Textes réutilisés dans plusieurs scripts, pour éviter les redondances et faciliter les modifications futures
TEXTES = {
    "aideNavigationMenu": "\n\n[gray]Utilisez [↑]/[↓] pour naviguer, Entrée pour sélectionner, Échap pour revenir en arrière.[/gray]",
}

# Varaible globale pour stocker le client connecté, utilisée dans plusieurs scripts pour éviter de devoir passer le client en paramètre à chaque fois, ce qui serait fastidieux et rendrait le code moins lisible.
# Sera initialisée lors de la sélection du client dans main.py et utilisée dans les scripts du client pour afficher les réservations, les achats, etc...
global client
