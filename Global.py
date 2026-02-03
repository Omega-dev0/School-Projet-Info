from rich.live import Live
from rich.table import Table
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.console import Console

import sqlite3

import Modules.Interface as UI

import sys


def interfacePrincipale():
    contenu = Layout()
    contenu.split_row(Layout(name="gauche", ratio=10), Layout(name="droite", ratio=7))

    gauche = Panel("En attente de données...", border_style="bold green")
    contenu["gauche"].update(gauche)
    droite = Panel("En attente de données...", border_style="bold red")
    contenu["droite"].update(droite)

    return contenu


BLOQUER_INPUTS = True

CONSOLE = Console()
INTERFACE = interfacePrincipale()
LIVE = Live(INTERFACE, console=CONSOLE, auto_refresh=False, transient=False)
LIVE.start(refresh=True)

CONNEXION = sqlite3.connect("./spectacles.sqlite", check_same_thread=False)

TEXTES = {
    "aideNavigationMenu": "\n\n[gray]Utilisez [↑]/[↓] pour naviguer, Entrée pour sélectionner, Échap pour revenir en arrière.[/gray]",
}


def exit():

    UI.mettreAJourPanelDroit("")
    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Fermeture de l'application",
        message="[red]Vous avez choisi de quitter l'application.[/red] \n\nAppuyez sur Entrée pour continuer",
    )

    LIVE.stop()
    CONNEXION.close()
    CONSOLE.clear()
    sys.exit(0)


global client
