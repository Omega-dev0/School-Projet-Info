# ╔═════════════════════════════════════════════════════════════════════════════════════╗
# ║                   Annulation de réservation                                         ║
# ║                                                                                     ║
# ║  Ce module permet au client d'annuler une réservation existante.                    ║
# ║  Il affiche la liste des réservations du client, lui permet de sélectionner celle   ║
# ║  qu'il souhaite annuler, puis supprime la réservation de la base de données         ║
# ║  et met à jour le nombre de places disponibles.                                     ║
# ║                                                                                     ║
# ╚═════════════════════════════════════════════════════════════════════════════════════╝

# ――――――――――――――――――――――――― IMPORTATION DES MODULES ――――――――――――――――――――――――――

import Global
import Modules.Interface as UI

from rich.console import Group
from rich.markdown import Markdown
from rich.text import Text

# ――――――――――――――――――――――――― FONCTIONS ――――――――――――――――――――――――――


# Fonction d'affichage de l'écran de confirmation d'annulation, utilisée à plusieurs endroits
def annulation():
    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Annulation",
        message="Réservation [red]annulée[/red]. \n\nAppuyez sur Entrée pour continuer.",
    )


def main():

    CURSEUR = Global.CONNEXION.cursor()

    # On récupère la liste des réservations du client, avec pour chacune d'elle le nombre de places réservées, le type de place,
    # le prix unitaire, la date et l'heure de la représentation, le nom du spectacle
    # et l'id de la place associée à la réservation (pour pouvoir mettre à jour le nombre de places disponibles lors de l'annulation)
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

    # Construction de la liste des options du menu d'annulation,
    # avec pour chacune d'elle une description détaillée de la réservation
    options = []
    for reservation in reservations:

        """
        Descrition affichée à droite dans le menu
        Format:
        Réservation pour le spectacle <nom du spectacle> le <date> à <heure>.
        Place(s) de type <type de place>, <nombre de places> réservée(s) au prix unitaire de <prix>€.
        Total de la réservation : <prix total>€.
        Reservation faite le <date de la réservation>.
        """
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

    # Si le client n'a aucune réservation, on affiche un message l'indiquant
    if len(options) == 0:
        UI.attendreAppuiEntree(
            ecranAffichage="gauche",
            titre="Aucune réservation",
            message="Vous n'avez aucune réservation à annuler. \n\nAppuyez sur Entrée pour continuer.",
        )
        return

    # Affichage du menu de sélection de la réservation à annuler,
    # avec pour chacune d'elle une description détaillée de la réservation
    reservationChoisie = UI.afficherMenu(
        titre="Sélectionnez une réservation à annuler",
        afficherLesDescriptions=True,
        sortieAvecEchap=True,
        options=options,
        afficherAideNavigation=True,
    )

    # Si l'utilisateur appuie sur Échap, on affiche un message d'annulation et on quitte le processus
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

    # Message de confirmation d'annulation de la réservation
    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Annulation réussie",
        message="La réservation a été [green]annulée avec succès[/green]. \n\nAppuyez sur Entrée pour continuer.",
    )

    CURSEUR.close()
    return
