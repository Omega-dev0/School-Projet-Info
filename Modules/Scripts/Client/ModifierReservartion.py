import Global
import Modules.Interface as UI


def annulation():
    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Annulation",
        message="Procédure [red]annulée[/red]. \n\nAppuyez sur Entrée pour continuer.",
    )


def main():
    CURSEUR = Global.CONNEXION.cursor()

    requete = """
    SELECT reservation.id, reservation.nb_places, place.type_place, place.prix, representation.date, representation.heure, spectacle.libelle, place.id, representation.id
    FROM reservation, place, representation, spectacle
    WHERE reservation.id_client = ? 
    AND reservation.id_place = place.id 
    AND place.id_representation = representation.id 
    AND representation.id_spectacle = spectacle.id
    ORDER BY representation.date, representation.heure
    """

    reservations = CURSEUR.execute(requete, (Global.client["id"],)).fetchall()

    options = []
    representationEnCours = None
    description = ""
    nom = ""
    categories = []
    for reservation in reservations:
        if representationEnCours != reservation[8]:

            if description != "":
                options.append(
                    {
                        "nom": nom,
                        "description": description,
                        "idRepresentation": representationEnCours,
                        "categories": categories,
                    }
                )

            representationEnCours = reservation[8]
            categories = []
            nom = f"{reservation[6]} - {UI.formatDateSQLToFR(reservation[4])} {reservation[5]}"
            description = f"""Réservation pour le spectacle [bold]{reservation[6]}[/bold] le [bold]{UI.formatDateSQLToFR(reservation[4])}[/bold] à [bold]{reservation[5]}[/bold].\n\n"""

        if reservation[1] > 0:
            description += f"""Place{"s" if reservation[1] > 1 else ""} de type [bold]{reservation[2]}[/bold], {reservation[1]} place{"" if reservation[1] == 1 else "s"} réservée{"" if reservation[1] == 1 else "s"} au prix unitaire de [bold]{reservation[3]}€[/bold].\n\n"""
        categories.append(
            {
                "type_place": reservation[2],
                "nb_places": reservation[1],
                "id_place": reservation[7],
            }
        )

    if description != "":
        options.append(
            {
                "nom": nom,
                "description": description,
                "idRepresentation": representationEnCours,
                "categories": categories,
            }
        )

    if len(options) == 0:
        UI.attendreAppuiEntree(
            ecranAffichage="gauche",
            titre="Aucune réservation",
            message="Vous n'avez aucune réservation à modifier. \n\nAppuyez sur Entrée pour continuer.",
        )
        return

    reservationChoisie = UI.afficherMenu(
        titre="Sélectionnez une réservation à modifier",
        afficherLesDescriptions=True,
        sortieAvecEchap=True,
        options=options,
        afficherAideNavigation=True,
    )

    if reservationChoisie is None:
        annulation()
        CURSEUR.close()
        return

    texteInput = f"""[bold]Modification de la réservation pour le spectacle {reservationChoisie['nom']}[/bold]\n\n"""

    inoutValues = []
    for categorie in reservationChoisie["categories"]:
        if categorie["nb_places"] == 0:
            continue  # On ne propose pas de modifier les catégories avec 0 place réservée
        inoutValues.append(str(categorie["nb_places"]))
        texteInput += f"""Catégorie [bold]{categorie['type_place']}[/bold] - Nombre de places réservées: __INPUT__ [dim](réservées {categorie['nb_places']})[/dim]\n\n"""

    def validerModification(*args):
        for valeur in args:
            if not valeur.isdigit() or int(valeur) < 0:
                return "Le nombre de places doit être un entier positif ou nul."

        for i in range(len(args)):
            nouveauNombrePlaces = int(args[i])
            ancientNombrePlaces = reservationChoisie["categories"][i]["nb_places"]
            if nouveauNombrePlaces > ancientNombrePlaces:
                requete = """
                SELECT nb_places FROM place
                WHERE id_representation = ? AND type_place = ?
                """
                nombrePlacesDisponible = CURSEUR.execute(
                    requete,
                    (
                        reservationChoisie["idRepresentation"],
                        reservationChoisie["categories"][i]["type_place"],
                    ),
                ).fetchone()[0]

                if nouveauNombrePlaces - ancientNombrePlaces > nombrePlacesDisponible:
                    return f"Il n'y a pas assez de places disponibles pour la catégorie {reservationChoisie['categories'][i]['type_place']}. (Disponibles: {nombrePlacesDisponible}, Demandées en plus: {nouveauNombrePlaces - ancientNombrePlaces})"
        return True

    nouvellesValeurs = UI.inputTexte(
        ecranAffichage="gauche",
        titre="Modification de la réservation",
        message=texteInput,
        sortieAvecEchap=True,
        valeurParDefaut=inoutValues,
        functionDeValidation=validerModification,
    )

    if nouvellesValeurs[0] is None:
        annulation()
        CURSEUR.close()
        return

    for i in range(len(nouvellesValeurs)):
        # Mise a jour de la réservation
        nouveauNombrePlaces = int(nouvellesValeurs[i])

        requeteMajReservation = """
        UPDATE reservation
        SET nb_places = ?
        WHERE id_place = ? AND id_client = ?
        """
        CURSEUR.execute(
            requeteMajReservation,
            (
                nouveauNombrePlaces,
                reservationChoisie["categories"][i]["id_place"],
                Global.client["id"],
            ),
        )

        requeteMajPlacesDisponibles = """
        UPDATE place
        SET nb_places = nb_places + ?
        WHERE id_representation = ? AND type_place = ?
        """
        ancientNombrePlaces = reservationChoisie["categories"][i]["nb_places"]
        difference = (
            ancientNombrePlaces - nouveauNombrePlaces
        )  # Si positif, on libère des places, si négatif on en réserve plus
        CURSEUR.execute(
            requeteMajPlacesDisponibles,
            (
                difference,
                reservationChoisie["idRepresentation"],
                reservationChoisie["categories"][i]["type_place"],
            ),
        )
    Global.CONNEXION.commit()
    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Modification réussie",
        message="La réservation a été modifiée avec succès. \n\nAppuyez sur Entrée pour continuer.",
    )
    CURSEUR.close()
