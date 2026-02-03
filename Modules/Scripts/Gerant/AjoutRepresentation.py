import Global
import Modules.Interface as UI

import re

from rich.console import Group
from rich.markdown import Markdown
from rich.text import Text

import datetime


def annulation():
    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Annulation",
        message="Ajout de la représentation [red]annulé[/red]. \n\nAppuyez sur Entrée pour continuer.",
    )


def main():
    CURSEUR = Global.CONNEXION.cursor()

    requete = "SELECT id, libelle FROM spectacle"
    CURSEUR.execute(requete)
    spectacles = CURSEUR.fetchall()

    options = []
    for spectacle in spectacles:
        options.append(
            {
                "nom": spectacle[1],
                "id": spectacle[0],
            }
        )

    spectacle = UI.afficherMenu(
        titre="Sélectionnez un spectacle pour ajouter une représentation",
        afficherLesDescriptions=False,
        sortieAvecEchap=True,
        options=options,
    )

    if spectacle is None:
        annulation()
        CURSEUR.close()
        return

    texteInput = """[bold]Ajoutez les informations de la nouvelle représentation :[/bold]\n
    [bold]Date (JJ/MM/AAAA):[/bold] __INPUT__
    [bold]Heure (HH:MM):[/bold] __INPUT__"""

    def validerRepresentation(date, heure):
        regexDate = r"^\d{2}/\d{2}/\d{4}$"
        regexHeure = r"^\d{2}:\d{2}$"
        if not re.fullmatch(regexDate, date):
            return "Le format de la date est invalide. Utilisez le format JJ/MM/AAAA."
        if not re.fullmatch(regexHeure, heure):
            return "Le format de l'heure est invalide. Utilisez le format HH:MM."

        try:
            datetime.datetime.strptime(date, "%d/%m/%Y")
        except ValueError:
            return "La date fournie n'est pas valide."
        return True

    date, heure = UI.inputTexte(
        ecranAffichage="gauche",
        titre="Ajout d'une nouvelle représentation",
        message=texteInput,
        sortieAvecEchap=True,
        functionDeValidation=validerRepresentation,
    )

    if date is None:
        annulation()
        CURSEUR.close()
        return

    requete = """
    INSERT INTO representation (id_spectacle, date, heure)
    VALUES (?, ?, ?)
    """

    date = f"{date[6:10]}-{date[3:5]}-{date[0:2]}"  # Convertir en AAAA-MM-JJ
    CURSEUR.execute(requete, (spectacle["id"], date, heure))
    Global.CONNEXION.commit()

    # Ajout de places/catégories
    UI.mettreAJourPanelDroit(
        Group(
            Markdown("# Création d'une représentation"),
            f"Représentation pour le spectacle [bold]{spectacle['nom']}[/bold] le [bold]{UI.formatDateSQLToFR(date)}[/bold] à [bold]{heure}[/bold].",
        )
    )
    categories = ""
    continuer = True

    def validation(cat, nbPlaces, prixUnitaire):
        if len(cat.strip()) == 0:
            return "La catégorie ne peut pas être vide."

        if not nbPlaces.isdigit() or int(nbPlaces) <= 0:
            return "Le nombre de places doit être un entier positif."

        if not prixUnitaire.replace(".", "", 1).isdigit() or float(prixUnitaire) <= 0:
            return "Le prix unitaire doit être un nombre positif."

        return True

    idRepresentation = CURSEUR.lastrowid

    while continuer == True:
        message = """[bold]Ajout the places pour la représentation[/bold]\n"""
        message += """Appuyez sur [bold red]Echap[/bold red] pour finir l'ajout des places.\n\n"""
        message += """[bold]Catégorie :[/bold] __INPUT__\n"""
        message += """[bold]Nombre de places :[/bold] __INPUT__\n"""
        message += """[bold]Prix unitaire:[/bold] __INPUT__ €\n"""
        cat, nbPlaces, prixUnitaire = UI.inputTexte(
            ecranAffichage="gauche",
            titre="Ajout de places pour la représentation",
            message=message,
            sortieAvecEchap=True,
            functionDeValidation=validation,
        )
        if cat is None:
            continuer = False
            break

        categories += f"- Catégorie [bold]{cat}[/bold] : [bold]{nbPlaces}[/bold] places à [bold]{prixUnitaire} €[/bold] chacune.\n"

        UI.mettreAJourPanelDroit(
            Group(
                Markdown("# Création d'une représentation"),
                f"Représentation pour le spectacle [bold]{spectacle['nom']}[/bold] le [bold]{UI.formatDateSQLToFR(date)}[/bold] à [bold]{heure}[/bold].",
                categories,
            )
        )

        requetePlaces = """
        INSERT INTO place (id_representation, type_place, prix, nb_places) VALUES (?, ?, ?, ?)
        """
        CURSEUR.execute(requetePlaces, (idRepresentation, cat, prixUnitaire, nbPlaces))

    Global.CONNEXION.commit()
    message = f"[green]La représentation pour le spectacle [bold]{spectacle['nom']}[/bold] le [bold]{UI.formatDateSQLToFR(date)}[/bold] à [bold]{heure}[/bold] a été ajoutée avec succès.\n\n[/green]"
    message += "Les places suivantes ont été créées :\n"
    message += categories
    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Représentation ajoutée",
        message=message,
    )

    CURSEUR.close()
