import Global
import Modules.Interface as UI

from rich.console import Group
from rich.markdown import Markdown
from rich.text import Text


def annulation():
    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Annulation",
        message="Réservation [red]annulée[/red]. \n\nAppuyez sur Entrée pour continuer.",
    )


def main():

    CURSEUR = Global.CONNEXION.cursor()

    requete = """
    SELECT reservation.id, reservation.nb_places, place.type_place, place.prix, representation.date, representation.heure, spectacle.libelle, place.id
    FROM reservation, place, representation, spectacle
    WHERE reservation.id_client = ? 
    AND reservation.id_place = place.id 
    AND place.id_representation = representation.id 
    AND representation.id_spectacle = spectacle.id
    ORDER BY representation.date, representation.heure
    """

    reservations = CURSEUR.execute(requete, (Global.client["id"],)).fetchall()

    options = []
    for reservation in reservations:
        description = f"""Réservation pour le spectacle [bold]{reservation[6]}[/bold] le [bold]{UI.formatDateSQLToFR(reservation[4])}[/bold] à [bold]{reservation[5]}[/bold].\n\n
Place{"s" if reservation[1] > 1 else ""} de type [bold]{reservation[2]}[/bold], {reservation[1]} place{"" if reservation[1] == 1 else "s"} réservée{"" if reservation[1] == 1 else "s"} au prix unitaire de [bold]{reservation[3]}€[/bold].\n\n
        Total de la réservation : [bold]{reservation[1] * reservation[3]}€[/bold].\n\n
        Reservation faite le [bold]{UI.formatDateSQLToFR(reservation[4])}[/bold].
        """
        options.append(
            {
                "nom": f"{reservation[6]} - {UI.formatDateSQLToFR(reservation[4])} {reservation[5]} - Cat{reservation[2]}",
                "description": description,
                "id": reservation[0],
                "id_place": reservation[7],
                "nb_places": reservation[1],
            }
        )
    if len(options) == 0:
        UI.attendreAppuiEntree(
            ecranAffichage="gauche",
            titre="Aucune réservation",
            message="Vous n'avez aucune réservation à annuler. \n\nAppuyez sur Entrée pour continuer.",
        )
        return

    reservationChoisie = UI.afficherMenu(
        titre="Sélectionnez une réservation à annuler",
        afficherLesDescriptions=True,
        sortieAvecEchap=True,
        options=options,
        afficherAideNavigation=True,
    )

    if reservationChoisie is None:
        annulation()
        CURSEUR.close()
        return

    # On supprime la réservation choisie
    requeteSuppression = "DELETE FROM reservation WHERE id = ?"
    CURSEUR.execute(requeteSuppression, (reservationChoisie["id"],))

    # On met à jour le nombre de places disponibles pour la place associée
    requeteMiseAJourPlaces = """UPDATE place SET nb_places = nb_places + ? WHERE id = ?"""
    CURSEUR.execute(
        requeteMiseAJourPlaces,
        (reservationChoisie["nb_places"], reservationChoisie["id_place"]),
    )

    Global.CONNEXION.commit()
    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Annulation réussie",
        message="La réservation a été [green]annulée avec succès[/green]. \n\nAppuyez sur Entrée pour continuer.",
    )
    CURSEUR.close()
    return
