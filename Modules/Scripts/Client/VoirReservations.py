import Global
import Modules.Interface as UI


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

    reservationChoisie = UI.afficherMenu(
        titre=f"Vos réservation{"s" if len(options) > 1 else ""}",
        afficherLesDescriptions=True,
        sortieAvecEchap=True,
        options=options,
        afficherAideNavigation=False,
    )
    return
