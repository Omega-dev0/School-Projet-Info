# ╔═════════════════════════════════════════════════════════════════════════════════════╗
# ║                   Modification de représentations                                   ║
# ║                                                                                     ║
# ║  Ce module permet au gérant de modifier les représentations de spectacles.          ║
# ║  Il permet de modifier la date et l'heure d'une représentation, ainsi que de        ║
# ║  gérer les catégories de places (ajouter, modifier, supprimer).                     ║
# ║                                                                                     ║
# ║  Fonctionnalités:                                                                   ║
# ║  - Sélectionner une représentation à modifier                                       ║
# ║  - Modifier la date et l'heure de la représentation                                 ║
# ║  - Modifier les catégories de places existantes                                     ║
# ║  - Ajouter de nouvelles catégories de places                                        ║
# ║  - Supprimer des catégories de places                                               ║
# ║                                                                                     ║
# ╚═════════════════════════════════════════════════════════════════════════════════════╝

# ――――――――――――――――――――――――― IMPORTATION DES MODULES ――――――――――――――――――――――――――

import Global
import Modules.Interface as UI

import re
import datetime

from rich.console import Group
from rich.markdown import Markdown
from rich.text import Text

# ――――――――――――――――――――――――― FONCTIONS ――――――――――――――――――――――――――――――――――


# Fonction d'affichage de l'écran de confirmation d'annulation, utilisée à plusieurs endroits
def annulation():
    UI.attendreAppuiEntree(
        titre="Opération annulée",
        message="[red]La modification de la représentation a été annulée.[/red]\n\nAppuyez sur Entrée pour continuer.",
        ecranAffichage="gauche",
    )


# Fonction d'affichage du récap des informations de la représentation sélectionnée à droite,
# utilisée après chaque modification pour mettre à jour l'affichage
def affichageRecap(representationSelectionnee, spectacleCourant, infosCategories):
    UI.mettreAJourPanelDroit(
        UI.Group(
            Markdown(f"# Informations sur la représentation"),
            f"""\n\n[bold]Spectacle:[/bold] {spectacleCourant}
[bold]Date:[/bold] {UI.formatDateSQLToFR(representationSelectionnee["date"])}
[bold]Heure:[/bold] {representationSelectionnee["heure"]}

[bold]Catégories de places:[/bold]
{''.join([f'- Catégorie: [bold]{info[0]}[/bold], Prix: [bold]{info[1]}€[/bold], Nombre de places: [bold]{info[2]}[/bold]\n' for info in infosCategories])}
""",
        )
    )


def main():

    CURSEUR = Global.CONNEXION.cursor()

    # On récupère la liste des représentations à modifier, avec pour chacune d'elle le nom du spectacle,
    # la date et l'heure de la représentation
    requete = """SELECT representation.id, representation.date, representation.heure, spectacle.libelle
    FROM representation, spectacle
    WHERE representation.id_spectacle = spectacle.id
    AND representation.date >= DATE('now')
    ORDER BY spectacle.libelle, representation.date, representation.heure
    """
    representations = CURSEUR.execute(requete).fetchall()

    # Construction de la liste des options du menu de sélection de la représentation à modifier,
    # On ajoute également des séparateurs pour regrouper les représentations par spectacle et faciliter la navigation dans le menu
    options = []
    separateurs = {}
    spectacleCourant = None
    for representation in representations:
        # Si c'est un nouveau spectacle par rapport à la représentation précédente,
        # on ajoute un séparateur dans le menu avec le nom du spectacle
        if spectacleCourant != representation[3]:
            spectacleCourant = representation[3]
            separateurs[len(options)] = f"[bold tan]{spectacleCourant}[/bold tan]"

        options.append(
            {
                "nom": f"Représentation le {UI.formatDateSQLToFR(representation[1])} à {representation[2]}",
                "idRepresentation": representation[0],
                "date": representation[1],
                "heure": representation[2],
            }
        )
    # Affichage du menu de sélection de la représentation à modifier, avec les options construites précédemment
    # et les séparateurs pour regrouper par spectacle
    representationSelectionnee = UI.afficherMenu(
        titre="Sélectionnez la représentation à modifier",
        options=options,
        afficherLesDescriptions=False,
        sortieAvecEchap=True,
        separateurs=separateurs,
    )
    # Si l'utilisateur appuie sur Échap au lieu de sélectionner une représentation,
    # on annule l'opération
    if representationSelectionnee is None:
        annulation()
        CURSEUR.close()
        return

    # On récupère les informations additionnelles de la représentation sélectionnée,
    # à savoir les différentes catégories de places disponibles pour cette représentation,
    requeteInfosAdditionnelles = """SELECT type_place, prix, nb_places 
    FROM place 
    WHERE id_representation = ?"""
    infosCategories = CURSEUR.execute(
        requeteInfosAdditionnelles, (representationSelectionnee["idRepresentation"],)
    ).fetchall()

    # On affiche un récap des informations de la représentation sélectionnée à droite,
    # avec le nom du spectacle, la date et l'heure de la représentation,
    affichageRecap(representationSelectionnee, spectacleCourant, infosCategories)

    # Sous menu de sélection de l'action à effectuer sur la représentation sélectionnée,
    # Actions disponibles:
    # - Modifier les informations de la représentation (date et heure)
    # - Modifier les catégories de places existantes (prix, nombre de places disponibles)
    # - Ajouter de nouvelles catégories de places
    # - Supprimer des catégories de places
    while True:
        action = UI.afficherMenu(
            titre="Sélectionnez l'action à effectuer",
            options=[
                {
                    "nom": "Modifier les informations de la représentation",
                    "action": "modifier_info",
                },
                {
                    "nom": "Modifier les catégories de places existantes",
                    "action": "modifier_categories",
                },
                {"nom": "Ajouter des catégories de places", "action": "ajouter_categories"},
                {"nom": "Supprimer des catégories de places", "action": "supprimer_categories"},
            ],
            afficherLesDescriptions=False,
            sortieAvecEchap=True,
        )
        # Si l'utilisateur appuie sur Échap au lieu de sélectionner une action,
        if action is None:
            break

        # -------- MODIFIER LES INFORMATIONS DE LA REPRÉSENTATION --------
        if action["action"] == "modifier_info":
            # Message d'invite pour la saisie des nouvelles informations de la représentation,
            # __INPUT_ indique les champs de saisie, qui seront remplacés par des champs de saisie dans l'interface
            message = f"""Modification de la représentation:\n\n  [bold]Date de représentation (JJ/MM/AAAA):[/bold] __INPUT__\n   [bold]Heure de représentation (HH:MM):[/bold] __INPUT__
            """

            # Fonction de validation des nouvelles informations de la représentation,
            # qui vérifie que la date et l'heure sont au bon format et que la date est valide
            def validationInfos(date, heure):
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
                titre="Modifier les informations de la représentation",
                message=message,
                valeurParDefaut=[
                    UI.formatDateSQLToFR(representationSelectionnee["date"]),
                    representationSelectionnee["heure"],
                ],
                sortieAvecEchap=True,
                functionDeValidation=validationInfos,
            )
            if date is None:
                UI.attendreAppuiEntree(
                    titre="Opération annulée",
                    message="[red]La modification des informations de la représentation a été annulée.[/red]\n\nAppuyez sur Entrée pour continuer.",
                    ecranAffichage="gauche",
                )
                continue

            # Mise à jour des informations de la représentation dans la base de données,
            requete = """UPDATE representation
            SET date = ?, heure = ?
            WHERE id = ?"""
            dateSPlit = date.split("/")
            dateSQL = (
                f"{dateSPlit[2]}-{dateSPlit[1]}-{dateSPlit[0]}"  # Conversion de la date au format SQL (AAAA-MM-JJ)
            )
            CURSEUR.execute(requete, (dateSQL, heure, representationSelectionnee["idRepresentation"]))

            # Mise à jour des informations de la représentation sélectionnée dans l'objet representationSelectionnee pour mettre à jour
            # l'affichage à droite avec les nouvelles informations,
            representationSelectionnee["date"] = dateSQL
            representationSelectionnee["heure"] = heure
            affichageRecap(representationSelectionnee, spectacleCourant, infosCategories)

            Global.CONNEXION.commit()

            UI.attendreAppuiEntree(
                titre="Modification réussie",
                message="[green]Les informations de la représentation ont été modifiées avec succès.[/green]\n\nAppuyez sur Entrée pour continuer.",
                ecranAffichage="gauche",
            )

        # -------- MODIFIER LES CATÉGORIES DE PLACES EXISTANTES --------
        elif action["action"] == "modifier_categories":

            # On récupère les catégories de places de la représentation sélectionnée,
            # avec pour chacune d'elle le type de place, le prix, le nombre de places disponibles
            # et le nombre de réservations associées à cette catégorie de place,
            placesRepresentation = CURSEUR.execute(
                """SELECT place.id, place.type_place, place.prix, place.nb_places, COUNT(reservation.id)
                FROM place
                LEFT JOIN reservation ON place.id = reservation.id_place
                WHERE place.id_representation = ?
                GROUP BY place.id;""",
                (representationSelectionnee["idRepresentation"],),
            ).fetchall()

            # Si aucune catégorie de place n'existe pour cette représentation,
            # on affiche un message d'erreur et on retourne au menu de sélection de l'action
            if len(placesRepresentation) == 0 or placesRepresentation[0][0] is None:
                UI.attendreAppuiEntree(
                    titre="Aucune catégorie de place",
                    message="[red]Il n'y a pas de catégories de places à modifier pour cette représentation.[/red]\n\nAppuyez sur Entrée pour continuer.",
                    ecranAffichage="gauche",
                )
                continue

            # On affiche un message d'invite pour la saisie des nouvelles informations des catégories de places,
            """
            Le message aura le format:
            Modification des places
            
            Catégorie: [type de place à saisir]: - Prix: [prix à saisir] € - Nombre de places disponibles: [nombre de places à saisir] (X Places dans la catégorie au total)
            Catégorie: [type de place à saisir]: - Prix: [prix à saisir] € - Nombre de places disponibles: [nombre de places à saisir] (X Places dans la catégorie au total)
            ...
            """
            message = f"""[bold salmon1]Modifications des places[/bold salmon1]"""
            valeursParDefaut = []
            for place in placesRepresentation:
                message += f"\n[bold]Catégorie: __INPUT__[/bold]:\n  - Prix: __INPUT__ €\n  - Nombre de places disponibles: __INPUT__ [dim] {place[4] + place[3]} Places dans la catégorie au total[/dim]"
                valeursParDefaut.append(place[1])  # type_place
                valeursParDefaut.append(str(place[2]))  # prix
                valeursParDefaut.append(str(place[3]))  # nb_places

            # Fonction de validation des nouvelles informations des catégories de places,
            # qui vérifie que le type de place n'est pas vide, que le prix est un nombre positif
            # et que le nombre de places disponibles est un entier positif

            # On ne connait pas le nombre de catégories de places à l'avance,
            # donc la fonction de validation doit pouvoir prendre un nombre variable d'arguments,
            # on utilise donc l'opérateur * pour prendre tous les arguments dans une liste et les traiter par groupe de 3 (type_place, prix, nb_places)
            def validationCategories(*args):
                for i in range(
                    0, len(args), 3
                ):  # On traite les arguments par groupe de 3 (type_place, prix, nb_places)
                    type_place = args[i]
                    prix = args[i + 1]
                    nb_places = args[i + 2]
                    if not type_place or len(type_place.strip()) == 0:
                        return "Le type de place ne peut pas être vide."
                    try:
                        prix_float = float(prix)
                        if prix_float < 0:
                            return "Le prix doit être un nombre positif."
                    except ValueError:
                        return "Le prix doit être un nombre valide."
                    try:
                        nb_places_int = int(nb_places)
                        if nb_places_int < 0:
                            return "Le nombre de places doit être un entier positif."
                    except ValueError:
                        return "Le nombre de places doit être un entier valide."
                return True

            nouvellesValeurs = UI.inputTexte(
                titre="Modifier les catégories de places",
                message=message,
                valeurParDefaut=valeursParDefaut,
                sortieAvecEchap=True,
                functionDeValidation=validationCategories,
            )
            if nouvellesValeurs[0] is None:
                UI.attendreAppuiEntree(
                    titre="Opération annulée",
                    message="[red]La modification des catégories de places a été annulée.[/red]\n\nAppuyez sur Entrée pour continuer.",
                    ecranAffichage="gauche",
                )
                continue

            # Pour chaque catégorie de place, on met à jour les informations dans la base de données avec les nouvelles valeurs saisies par le gérant,
            # on utilise l'id de la place pour identifier la catégorie de place à mettre à jour
            for i in range(0, len(nouvellesValeurs), 3):
                type_place = nouvellesValeurs[i]
                prix = float(nouvellesValeurs[i + 1])
                nb_places = int(nouvellesValeurs[i + 2])
                place_id = placesRepresentation[i // 3][0]
                infosCategories[i // 3] = (type_place, prix, nb_places)
                CURSEUR.execute(
                    "UPDATE place SET type_place = ?, prix = ?, nb_places = ? WHERE id = ?",
                    (type_place, prix, nb_places, place_id),
                )
            affichageRecap(representationSelectionnee, spectacleCourant, infosCategories)
            CURSEUR.connection.commit()

        # ------- AJOUTER DE NOUVELLES CATÉGORIES DE PLACES --------
        elif action["action"] == "ajouter_categories":
            # On propose d'ajouter une nouvelle catégorie.
            # Format du texte d'input:

            # Ajout de nouvelles catégories de places pour la représentation:
            # Catégorie: [type de place à saisir]
            # Nombre de places: [nombre de places à saisir]
            # Prix unitaire: [prix à saisir] €
            message = f"""Ajout de nouvelles catégories de places pour la représentation:
            
            [bold]Catégorie :[/bold] [blue]__INPUT__[/blue]
            [bold]Nombre de places :[/bold] [blue]__INPUT__[/blue]
            [bold]Prix unitaire:[/bold] [blue]__INPUT__[/blue] €
            """

            # Fonction de validation des informations de la nouvelle catégorie de place,
            # qui vérifie que le type de place n'est pas vide, que le prix est un nombre positif et que le nombre de places est un entier positif
            def validation(cat, nbPlaces, prixUnitaire):
                if len(cat.strip()) == 0:
                    return "La catégorie ne peut pas être vide."

                if not nbPlaces.isdigit() or int(nbPlaces) <= 0:
                    return "Le nombre de places doit être un entier positif."

                if not prixUnitaire.replace(".", "", 1).isdigit() or float(prixUnitaire) <= 0:
                    return "Le prix unitaire doit être un nombre positif."

                return True

            cat, nbPlaces, prixUnitaire = UI.inputTexte(
                ecranAffichage="gauche",
                titre="Ajout de catégories de places pour la représentation",
                message=message,
                sortieAvecEchap=True,
                functionDeValidation=validation,
            )
            if cat is None:
                UI.attendreAppuiEntree(
                    titre="Opération annulée",
                    message="[red]L'ajout de catégories de places a été annulé.[/red]\n\nAppuyez sur Entrée pour continuer.",
                    ecranAffichage="gauche",
                )
                continue

            # On ajoute la nouvelle catégorie de place dans la base de données en l'associant à la représentation sélectionnée,
            requetePlaces = """
            INSERT INTO place (id_representation, type_place, prix, nb_places) VALUES (?, ?, ?, ?)
            """
            # On ajoute la nouvelle catégorie à la liste des catégories pour mettre à jour l'affichage à droite
            infosCategories.append((cat, float(prixUnitaire), int(nbPlaces)))
            CURSEUR.execute(
                requetePlaces,
                (
                    representationSelectionnee["idRepresentation"],
                    cat,
                    float(prixUnitaire),
                    int(nbPlaces),
                ),
            )
            Global.CONNEXION.commit()
            affichageRecap(representationSelectionnee, spectacleCourant, infosCategories)
            UI.attendreAppuiEntree(
                titre="Ajout réussi",
                message="[green]La nouvelle catégorie de places a été ajoutée avec succès.[/green]\n\nAppuyez sur Entrée pour continuer.",
                ecranAffichage="gauche",
            )

        # ------- SUPPRIMER DES CATÉGORIES DE PLACES --------
        elif action["action"] == "supprimer_categories":
            # On récupère les catégories de places de la représentation sélectionnée,
            # avec pour chacune d'elle le type de place, le prix, le nombre de places
            # On utilise une jointure qui n'est pas sur place car on ne sait pas si des réservations existent
            # Une jointure avec WHERE sur place.id_representation ne fonctionnerait pas si aucune catégorie de place n'existe pour la représentation sélectionnée
            placesRepresentation = CURSEUR.execute(
                """SELECT place.id, place.type_place, place.prix, place.nb_places, COUNT(reservation.id)
                FROM place
                LEFT JOIN reservation ON place.id = reservation.id_place
                WHERE place.id_representation = ?
                GROUP BY place.id;""",
                (representationSelectionnee["idRepresentation"],),
            ).fetchall()

            # Si aucune catégorie de place n'existe pour cette représentation,
            # on affiche un message d'erreur et on retourne au menu de sélection de l'action
            if len(placesRepresentation) == 0 or placesRepresentation[0][0] is None:
                UI.attendreAppuiEntree(
                    titre="Aucune catégorie de place",
                    message="[red]Il n'y a pas de catégories de places à supprimer pour cette représentation.[/red]\n\nAppuyez sur Entrée pour continuer.",
                    ecranAffichage="gauche",
                )
                continue

            # Construction de la liste des options du menu de sélection de la catégorie de place à supprimer,
            options = []
            for place in placesRepresentation:
                options.append(
                    {
                        "nom": f"Catégorie: {place[1]}, Prix: {place[2]}€, Nombre de places disponibles: {place[3]}",
                        "id_place": place[0],
                        "nombre_reservations": place[4],
                    }
                )
            placeASupprimer = UI.afficherMenu(
                titre="Sélectionnez la catégorie de place à supprimer",
                options=options,
                afficherLesDescriptions=False,
                sortieAvecEchap=True,
            )
            if placeASupprimer is None:
                UI.attendreAppuiEntree(
                    titre="Opération annulée",
                    message="[red]La suppression de la catégorie de place a été annulée.[/red]\n\nAppuyez sur Entrée pour continuer.",
                    ecranAffichage="gauche",
                )
                continue

            # On vérifie s'il y a des réservations associées à cette catégorie de place, si c'est le cas,
            # on affiche un message d'avertissement pour confirmer la suppression,
            nbReservations = placeASupprimer["nombre_reservations"]
            if nbReservations > 0:
                UI.attendreAppuiEntree(
                    titre="Attention",
                    message=f"[red]Il y a {nbReservations} réservation{'s' if nbReservations > 1 else ''} associée{'s' if nbReservations > 1 else ''} à cette catégorie de place, si vous la supprimez, ces réservations seront également supprimées.[/red]\n\nAppuyez sur Entrée pour supprimer quand même. \n Appuyez sur Échap pour annuler.",
                    ecranAffichage="gauche",
                )
                continue

            # Supression des reservations associées à cette catégorie de place
            CURSEUR.execute("DELETE FROM reservation WHERE id_place = ?", (placeASupprimer["id_place"],))

            # Suppression de la catégorie de place
            CURSEUR.execute("DELETE FROM place WHERE id = ?", (placeASupprimer["id_place"],))

            Global.CONNEXION.commit()

            # Mise à jour de la liste des catégories de places pour mettre à jour l'affichage à droite,
            infosCategories = [
                info
                for info in infosCategories
                if info[0] != placeASupprimer["nom"].split(",")[0].replace("Catégorie: ", "")
            ]
            affichageRecap(representationSelectionnee, spectacleCourant, infosCategories)

    CURSEUR.close()
