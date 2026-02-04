import Global
import Modules.Interface as UI

import re
import datetime

from rich.console import Group
from rich.markdown import Markdown
from rich.text import Text


def annulation():
    UI.attendreAppuiEntree(
        titre="Opération annulée",
        message="[red]La modification de la représentation a été annulée.[/red]\n\nAppuyez sur Entrée pour continuer.",
        ecranAffichage="gauche",
    )


def main():
    CURSEUR = Global.CONNEXION.cursor()
    requete = """SELECT representation.id, representation.date, representation.heure, spectacle.libelle
    FROM representation, spectacle
    WHERE representation.id_spectacle = spectacle.id
    AND representation.date >= DATE('now')
    ORDER BY spectacle.libelle, representation.date, representation.heure
    """

    representations = CURSEUR.execute(requete).fetchall()

    options = []
    separateurs = {}

    spectacleCourant = None
    for representation in representations:
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

    representationSelectionnee = UI.afficherMenu(
        titre="Sélectionnez la représentation à modifier",
        options=options,
        afficherLesDescriptions=False,
        sortieAvecEchap=True,
        separateurs=separateurs,
    )

    if representationSelectionnee is None:
        annulation()
        CURSEUR.close()
        return

    requeteInfosAdditionnelles = """SELECT type_place, prix, nb_places 
    FROM place 
    WHERE id_representation = ?"""
    infosCategories = CURSEUR.execute(
        requeteInfosAdditionnelles, (representationSelectionnee["idRepresentation"],)
    ).fetchall()

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
        if action is None:
            break

        if action["action"] == "modifier_info":
            message = f"""Modification de la représentation:\n\n  [bold]Date de représentation (JJ/MM/AAAA):[/bold] __INPUT__\n   [bold]Heure de représentation (HH:MM):[/bold] __INPUT__
            """

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

            requete = """UPDATE representation
            SET date = ?, heure = ?
            WHERE id = ?"""
            dateSPlit = date.split("/")
            dateSQL = f"{dateSPlit[2]}-{dateSPlit[1]}-{dateSPlit[0]}"
            CURSEUR.execute(
                requete, (dateSQL, heure, representationSelectionnee["idRepresentation"])
            )
            representationSelectionnee["date"] = dateSQL
            representationSelectionnee["heure"] = heure
            Global.CONNEXION.commit()
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
            UI.attendreAppuiEntree(
                titre="Modification réussie",
                message="[green]Les informations de la représentation ont été modifiées avec succès.[/green]\n\nAppuyez sur Entrée pour continuer.",
                ecranAffichage="gauche",
            )

        elif action["action"] == "modifier_categories":
            placesRepresentation = CURSEUR.execute(
                """SELECT place.id, place.type_place, place.prix, place.nb_places, COUNT(reservation.id)
                FROM place
                LEFT JOIN reservation ON place.id = reservation.id_place
                WHERE place.id_representation = ?
                GROUP BY place.id;""",
                (representationSelectionnee["idRepresentation"],),
            ).fetchall()
            print(placesRepresentation)
            if len(placesRepresentation) == 0 or placesRepresentation[0][0] is None:
                UI.attendreAppuiEntree(
                    titre="Aucune catégorie de place",
                    message="[red]Il n'y a pas de catégories de places à modifier pour cette représentation.[/red]\n\nAppuyez sur Entrée pour continuer.",
                    ecranAffichage="gauche",
                )
                continue

            message = f"""[bold salmon1]Modifications des places[/bold salmon1]"""

            valeursParDefaut = []
            for place in placesRepresentation:
                message += f"\n[bold]Catégorie: __INPUT__[/bold]:\n  - Prix: __INPUT__ €\n  - Nombre de places disponibles: __INPUT__ [dim] {place[4] + place[3]} Places dans la catégorie au total[/dim]"
                valeursParDefaut.append(place[1])  # type_place
                valeursParDefaut.append(str(place[2]))  # prix
                valeursParDefaut.append(str(place[3]))  # nb_places

            def validationCategories(*args):
                for i in range(0, len(args), 3):
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
            CURSEUR.connection.commit()

        elif action["action"] == "ajouter_categories":
            message = f"""Ajout de nouvelles catégories de places pour la représentation:
            
            [bold]Catégorie :[/bold] [blue]__INPUT__[/blue]
            [bold]Nombre de places :[/bold] [blue]__INPUT__[/blue]
            [bold]Prix unitaire:[/bold] [blue]__INPUT__[/blue] €
            """

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

            requetePlaces = """
            INSERT INTO place (id_representation, type_place, prix, nb_places) VALUES (?, ?, ?, ?)
            """
            infosCategories.append((cat, float(prixUnitaire), int(nbPlaces)))
            CURSEUR.execute(
                requetePlaces,
                (
                    representationSelectionnee["idRepresentation"],
                    cat,
                    prixUnitaire,
                    nbPlaces,
                ),
            )
            Global.CONNEXION.commit()
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
            UI.attendreAppuiEntree(
                titre="Ajout réussi",
                message="[green]La nouvelle catégorie de places a été ajoutée avec succès.[/green]\n\nAppuyez sur Entrée pour continuer.",
                ecranAffichage="gauche",
            )

        elif action["action"] == "supprimer_categories":
            # On utilise une jointure qui n'est pas sur place car on ne sait pas si des réservations existent
            placesRepresentation = CURSEUR.execute(
                """SELECT place.id, place.type_place, place.prix, place.nb_places, COUNT(reservation.id)
                FROM place
                LEFT JOIN reservation ON place.id = reservation.id_place
                WHERE place.id_representation = ?
                GROUP BY place.id;""",
                (representationSelectionnee["idRepresentation"],),
            ).fetchall()
            if len(placesRepresentation) == 0 or placesRepresentation[0][0] is None:
                UI.attendreAppuiEntree(
                    titre="Aucune catégorie de place",
                    message="[red]Il n'y a pas de catégories de places à supprimer pour cette représentation.[/red]\n\nAppuyez sur Entrée pour continuer.",
                    ecranAffichage="gauche",
                )
                continue
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

            nbReservations = placeASupprimer["nombre_reservations"]
            if nbReservations > 0:
                UI.attendreAppuiEntree(
                    titre="Attention",
                    message=f"[red]Il y a {nbReservations} réservation{'s' if nbReservations > 1 else ''} associée{'s' if nbReservations > 1 else ''} à cette catégorie de place, si vous la supprimez, ces réservations seront également supprimées.[/red]\n\nAppuyez sur Entrée pour supprimer quand même. \n Appuyez sur Échap pour annuler.",
                    ecranAffichage="gauche",
                )
                continue

            # Supression des reservations associées à cette catégorie de place
            CURSEUR.execute(
                "DELETE FROM reservation WHERE id_place = ?", (placeASupprimer["id_place"],)
            )

            # Suppression de la catégorie de place
            CURSEUR.execute("DELETE FROM place WHERE id = ?", (placeASupprimer["id_place"],))

            Global.CONNEXION.commit()
            infosCategories = [
                info
                for info in infosCategories
                if info[0] != placeASupprimer["nom"].split(",")[0].replace("Catégorie: ", "")
            ]
            UI.mettreAJourPanelDroit(
                UI.Group(
                    Markdown(f"# Informations sur la représentation"),
                    ""
                    f"""\n\n[bold]Spectacle:[/bold] {spectacleCourant}
[bold]Date:[/bold] {UI.formatDateSQLToFR(representationSelectionnee["date"])}
[bold]Heure:[/bold] {representationSelectionnee["heure"]}

[bold]Catégories de places:[/bold]
{''.join([f'- Catégorie: [bold]{info[0]}[/bold], Prix: [bold]{info[1]}€[/bold], Nombre de places: [bold]{info[2]}[/bold]\n' for info in infosCategories])}
""",
                )
            )

    CURSEUR.close()
