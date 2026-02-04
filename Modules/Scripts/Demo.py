from Global import CONNEXION
import Modules.Interface as UI

from rich.console import Group
from rich.markdown import Markdown
from rich.text import Text


def annulation():
    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Annulation",
        message="Procédure [red]annulée[/red]. \n\nAppuyez sur Entrée pour continuer.",
    )


def main():
    # Afficher un message et attendre l'appui sur Entrée

    CURSEUR = CONNEXION.cursor()

    msg1 = """
    Ce que l'on peut faire en texte :
    Mettre de la [red]couleur rouge[/red], de la [green]couleur verte[/green],
    de la [blue]couleur bleue[/blue], ou encore [yellow]jaune[/yellow].
    On peut aussi mettre du [bold]gras[/bold], du [italic]italique[/italic], ou du [underline]souligné[/underline].
    On peut aussi combiner plusieurs styles, comme du [bold red]gras rouge[/bold red] ou du [italic blue]italique bleu[/italic blue].
    On peut aussi créer des [reverse]zones en inverse[/reverse].
    
    Appuyer sur [green]Entrée[/green] pour continuer...
    """

    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Démonstration des choses possibles",
        message=msg1,
    )

    msg2 = """
    On peut aussi demander à l'utilisateur de saisir du texte avec plusieurs options :
    
    [bold]Nom:[/bold] __INPUT__
    [bold]Prénom:[/bold] __INPUT__
    
    Et même avec une fonction de validation !
    """

    def validerNomPrenom(nom, prenom):
        if len(nom) < 2 or len(prenom) < 2:
            return "Le nom et le prénom doivent contenir au moins 2 caractères chacun."
        return True

    nom, prenom = UI.inputTexte(
        ecranAffichage="gauche",
        titre="Saisie de texte avec validation",
        message=msg2,
        sortieAvecEchap=True,  # Si l'utilisateur appuie sur Échap, la fonction retournera (None, None)
        functionDeValidation=validerNomPrenom,
    )
    if nom is None:  # L'utilisateur a appuyé sur Échap
        annulation()  # On lui affiche que la procédure est annulée
        return  # On revient au menu

    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Saisie réussie",
        message=f"Bonjour, [bold]{prenom} {nom}[/bold] ! \n\n On peut aussi afficher des menus avec des séparateurs \n\nAppuyez sur Entrée pour continuer.",
    )

    # On peut aussi afficher un menu avec des options
    options = [
        {
            "nom": "Option 1",
            "description": "Ceci est la description de l'option 1.",
        },
        {
            "nom": "Option 2",
            "description": "Ceci est la description de l'option 2.",
        },
        {
            "nom": "Option 3",
            "description": "Ceci est la description de l'option 3.",
        },
    ]
    separateurs = {2: "-- Séparateur entre l'option 2 et 3 --"}
    choix = UI.afficherMenu(
        titre="Menu de démonstration",
        afficherLesDescriptions=True,
        sortieAvecEchap=True,
        options=options,
        separateurs=separateurs,
    )
    if choix is None:  # L'utilisateur a appuyé sur Échap donc le choix est None
        annulation()
        return

    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Choix effectué",
        message=f"Vous avez choisi : [bold]{choix['nom']}[/bold]\n\n On peut aussi demander à l'utilisateur de choisir un fichier \n\nAppuyez sur Entrée pour continuer.",
    )

    cheminFichier = UI.inputFichier(
        ecranAffichage="gauche",
        titre="Sélection de fichier",
        cheminDeBase=".",  # Le dossier de base pour la sélection
        sortieAvecEchap=True,
        formatsAcceptes=[
            ".txt",
            ".md",
            ".py",
        ],  # On n'autorise que les fichiers .txt, .md et .py
    )
    if cheminFichier is None:  # L'utilisateur a appuyé sur Échap
        annulation()
        return

    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Fichier sélectionné",
        message=f"Vous avez sélectionné le fichier : [bold]{cheminFichier}[/bold]\n\nEnfin, on peut facilement afficher des données \n\n Appuyez sur Entrée pour continuer.",
    )

    enteteDonnees = ["ID", "Nom", "Âge"]
    donnees = [
        [1, "Alice", 30],
        [2, "Bob", 25],
        [3, "Charlie", 35],
        [4, prenom, 21],
    ]

    UI.mettreAJourPanelDroit(
        Group(
            Markdown("# Informations"),
            "",
            Text("Voici un exemple d'affichage de données en tableau :"),
        )
    )
    UI.afficherDonnee(
        ecranAffichage="gauche",
        titre="Affichage de données en tableau",
        entete=enteteDonnees,
        donnee=donnees,
        attendreAppui=True,
    )

    CURSEUR.close()
