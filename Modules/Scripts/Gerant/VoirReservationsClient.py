# ╔═════════════════════════════════════════════════════════════════════════════════════╗
# ║                   Suppression d'un spectacle                                        ║
# ║                                                                                     ║
# ║  Ce module permet au gérant de supprimer un spectacle de la base de données.        ║
# ║  Il permet de sélectionner un spectacle et de le supprimer définitivement,          ║
# ║  ainsi que toutes les données associées (représentations, places et réservations).  ║
# ║                                                                                     ║
# ║                                                                                     ║
# ╚═════════════════════════════════════════════════════════════════════════════════════╝

# ――――――――――――――――――――――――― IMPORTATION DES MODULES ――――――――――――――――――――――――――

import Global
import Modules.Interface as UI

# ――――――――――――――――――――――――― FONCTIONS ――――――――――――――――――――――――――――――――


def main():

    CURSEUR = Global.CONNEXION.cursor()

    # On récupère la liste des clients avec le nombre de réservations associées, avec pour chacun d'eux son id, son nom, son prénom et son email
    requete = """
    SELECT client.id, client.nom, client.prenom, client.email, COUNT(distinct representation.id)
    FROM client, reservation, place, representation
    WHERE client.id = reservation.id_client
    AND reservation.id_place = place.id
    AND place.id_representation = representation.id
    GROUP BY client.id
    ORDER BY client.nom, client.prenom
    """
    clientsEtReservations = CURSEUR.execute(requete).fetchall()

    # Construction de la liste des options du menu de sélection du client pour voir ses réservations,
    # avec pour chacun d'eux son nom, son prénom, son email, le nombre de réservations associées,
    # et son id pour pouvoir récupérer ses réservations dans la base de données
    options = []
    for client in clientsEtReservations:
        options.append(
            {
                "nom": f"{client[1]} {client[2]} [dim]({client[3]}) - {client[4]} réservation{'s' if client[4] > 1 else ''}[/dim]",
                "idClient": client[0],
                "email": client[3],
                "prenom": client[2],
                "nomFamille": client[1],
            }
        )
    clientSelectionne = UI.afficherMenu(
        titre="Sélectionnez un client pour voir ses réservations",
        afficherLesDescriptions=False,
        sortieAvecEchap=True,
        options=options,
    )
    if clientSelectionne is None:
        return

    # On récupère la liste des réservations du client
    requete = """
    SELECT reservation.id, reservation.nb_places, place.type_place, place.prix, representation.date, representation.heure, spectacle.libelle, place.id, representation.id
    FROM reservation, place, representation, spectacle
    WHERE reservation.id_client = ? 
    AND reservation.id_place = place.id 
    AND place.id_representation = representation.id 
    AND representation.id_spectacle = spectacle.id
    ORDER BY representation.date, representation.heure
    """
    reservations = CURSEUR.execute(requete, (clientSelectionne["idClient"],)).fetchall()

    options = []
    representationEnCours = None
    description = ""
    nom = ""
    date = ""
    heure = ""
    categories = []

    # On itere sur les réservations, pour l'instant les différentes catégories sont séparées, on les regroupe par représentation
    for reservation in reservations:

        # On regarde si on est sur une nouvelle représentation, si oui on ajoute la réservation en cours à la liste des options
        if representationEnCours != reservation[8]:
            # La premiere fois, ce sera une reservation vide, on ne veut pas l'ajouter
            if description != "":
                options.append(
                    {
                        "nom": nom,
                        "description": description,
                        "idRepresentation": representationEnCours,
                        "categories": categories,
                        "heure": heure,
                        "date": date,
                    }
                )

            representationEnCours = reservation[8]  # On change de représentation en cours
            categories = []  # On réinitialise les catégories pour la nouvelle représentation
            nom = f"{reservation[6]} - {UI.formatDateSQLToFR(reservation[4])} {reservation[5]}"
            date = reservation[4]
            heure = reservation[5]

            # Texte de départ pour la description de la réservation, on ajoutera les différentes catégories de places réservées ensuite
            description = f"""Réservation pour le spectacle [bold]{reservation[6]}[/bold] le [bold]{UI.formatDateSQLToFR(reservation[4])}[/bold] à [bold]{reservation[5]}[/bold].\n\n"""

        # Si le nombre de places réservées est supérieur à 0, on ajoute la catégorie à la description de la réservation, sinon on l'ignore (ça peut arriver si une réservation a été modifiée pour annuler certaines places)
        if reservation[1] > 0:
            description += f"""Place{"s" if reservation[1] > 1 else ""} de type [bold]{reservation[2]}[/bold], {reservation[1]} place{"" if reservation[1] == 1 else "s"} réservée{"" if reservation[1] == 1 else "s"} au prix unitaire de [bold]{reservation[3]}€[/bold].\n"""

        # On en profite pour ajouter la catégorie à une liste de catégories, qui nous servira plus tard pour afficher les détails de la réservation
        categories.append(
            {
                "type_place": reservation[2],
                "nb_places": reservation[1],
                "id_place": reservation[7],
            }
        )

    # A la fin de boucle, on ajoute la dernière réservation en cours à la liste des options
    if description != "":
        options.append(
            {
                "nom": nom,
                "description": description,
                "idRepresentation": representationEnCours,
                "categories": categories,
                "heure": heure,
                "date": date,
            }
        )

    reservationChoisie = UI.afficherMenu(
        titre=f"Réservation{"s" if len(options) > 1 else ""} de {clientSelectionne['prenom']} {clientSelectionne['nomFamille']}",
        afficherLesDescriptions=True,
        sortieAvecEchap=True,
        options=options,
        afficherAideNavigation=False,
    )

    # On affiche un faux billet de réservation avec les détails de la réservation choisie,
    # et un QR code factice
    texte = ""
    if reservationChoisie is not None:
        texte += "[bold]RÉSERVATION[/bold]\n\n"
        texte += f"NOM: {clientSelectionne['nomFamille']} {clientSelectionne['prenom']}\n"
        texte += f"SPECTACLE: {reservationChoisie['nom']}\n\n"
        texte += (
            f"DATE ET HEURE: {UI.formatDateSQLToFR(reservationChoisie['date'])} à {reservationChoisie['heure']}\n\n"
        )
        texte += "\n"
        if reservationChoisie["categories"]:
            for categorie in reservationChoisie["categories"]:  # type: ignore
                texte += f"x {categorie['nb_places']} - Place cat {categorie['type_place']}\n"
        QRCode = [
            "┌────────────────────────┐",
            "│████████      ████████  │",
            "│██      ██    ██      ██│",
            "│██████████    ██████████│",
            "│      ████      ████    │",
            "│████    ████      ████  │",
            "│██████████████    ████  │",
            "│██    ██      ████████  │",
            "│████    ██████      ██  │",
            "│████████    ██████████  │",
            "│██      ████    ██      │",
            "│██████████      ██████  │",
            "│██    ██████    ██████  │",
            "└────────────────────────┘",
        ]
        texte += "\n".join(QRCode)
        message = UI.attendreAppuiEntree(
            titre="Détails de la réservation",
            message=texte,
            ecranAffichage="gauche",
        )
