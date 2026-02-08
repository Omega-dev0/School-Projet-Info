# ╔═════════════════════════════════════════════════════════════════════════════════════╗
# ║                   Modification des réservations du client                           ║
# ║                                                                                     ║
# ║  Ce module permet au client de modifier les réservations de son compte.             ║
# ║  Il affiche les informations actuelles, permet de les modifier, puis met à jour     ║
# ║  la base de données avec les nouvelles informations.                                ║
# ║                                                                                     ║
# ║                                                                                     ║
# ╚═════════════════════════════════════════════════════════════════════════════════════╝

# ――――――――――――――――――――――――― IMPORTATION DES MODULES ――――――――――――――――――――――――――


import Global
import Modules.Interface as UI


# ――――――――――――――――――――――――― FONCTIONS ――――――――――――――――――――――――――――――――


# Fonction d'affichage de l'écran de confirmation d'annulation, utilisée à plusieurs endroits
def annulation():
    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Annulation",
        message="Procédure [red]annulée[/red]. \n\nAppuyez sur Entrée pour continuer.",
    )


def main():
    CURSEUR = Global.CONNEXION.cursor()

    # ------ Choix de la réservation à modifier ------

    # On récupère les informations des réservations du client, avec pour chacune d'elle le nombre de places réservées, le type de place,
    # le prix unitaire, la date et l'heure de la représentation, le nom du spectacle et
    # l'id de la place associée à la réservation (pour pouvoir mettre à jour le nombre de places disponibles lors de la modification)
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

    # Construction de la liste des options du menu de modification,
    # avec pour chacune d'elle une description détaillée de la réservation
    # et une liste des catégories de places réservées pour cette réservation (pour pouvoir les modifier ensuite)
    # On doit regrouper les réservations par représentation, car une réservation peut comporter plusieurs catégories de places réservées,
    # qui sont séparées dans la base de données
    options = []
    representationEnCours = None
    description = ""
    nom = ""
    categories = []
    for reservation in reservations:

        # Si on est sur une nouvelle représentation, on ajoute la réservation en cours à la liste des options,
        # et on réinitialise les variables de construction de la réservation
        if representationEnCours != reservation[8]:

            if description != "":  # La première fois, ce sera une réservation vide, on ne veut pas l'ajouter
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

        # On ajoute la catégorie de place réservée à la description de la réservation, et à la liste des catégories de la réservation
        if reservation[1] > 0:
            description += f"""Place{"s" if reservation[1] > 1 else ""} de type [bold]{reservation[2]}[/bold], {reservation[1]} place{"" if reservation[1] == 1 else "s"} réservée{"" if reservation[1] == 1 else "s"} au prix unitaire de [bold]{reservation[3]}€[/bold].\n\n"""

        # Au passage on crée une liste des catégories pour une réservation,
        # qui nous servira plus tard pour afficher les différentes catégories de la réservation dans l'écran de modification,
        # et pour savoir quelles catégories modifier dans la base de données lors de la validation de la modification
        categories.append(
            {
                "type_place": reservation[2],
                "nb_places": reservation[1],
                "id_place": reservation[7],
            }
        )

    # Après la boucle, on ajoute la dernière réservation en cours à la liste des options
    if description != "":
        options.append(
            {
                "nom": nom,
                "description": description,
                "idRepresentation": representationEnCours,
                "categories": categories,
            }
        )

    # Si le client n'a aucune réservation, on affiche un message l'indiquant et on quitte le processus de modification des réservations
    if len(options) == 0:
        UI.attendreAppuiEntree(
            ecranAffichage="gauche",
            titre="Aucune réservation",
            message="[red]Vous n'avez aucune réservation à modifier.[/red] \n\nAppuyez sur Entrée pour continuer.",
        )
        return

    # Affichage du menu de sélection de la réservation à modifier,
    # avec pour chacune d'elle une description détaillée de la réservation et des catégories de places
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

    # ------ Modification de la réservation ------
    """
    On affiche un écran de saisie pour modifier le nombre de places réservées pour chaque catégorie de place de la réservation choisie,
    dans le format:
    
    Modification de la réservation pour le spectacle <nom du spectacle>
    Catégorie <type de place 1> - Nombre de places réservées: __INPUT__ (réservées <nombre de places actuellement réservées>)
    Catégorie <type de place 2> - Nombre de places réservées: __INPUT__ (réservées <nombre de places actuellement réservées>)
    ...
    """
    texteInput = f"""[bold]Modification de la réservation pour le spectacle {reservationChoisie['nom']}[/bold]\n\n"""

    # Grace a la liste de catégories de la réservation, on construit le texte de l'écran de saisie
    # et la liste des valeurs par défaut pour les champs de saisie
    valeursParDefaut = []
    for categorie in reservationChoisie["categories"]:  # type: ignore
        if categorie["nb_places"] == 0:
            continue  # On ne propose pas de modifier les catégories avec 0 place réservée
        valeursParDefaut.append(str(categorie["nb_places"]))
        texteInput += f"""Catégorie [bold]{categorie['type_place']}[/bold] - Nombre de places réservées: __INPUT__ [dim](réservées {categorie['nb_places']})[/dim]\n\n"""

    # Fonction de validation des informations saisies par le client, utilisée pour valider les champs de saisie dans UI.inputTexte
    # On ne connait pas à l'avance le nombre de catégories de places de la réservation, donc on utilise *args pour récupérer les valeurs saisies
    # sous forme de liste
    def validerModification(*args):

        # On vérifie que les valeurs saisies sont des entiers positifs ou nuls
        for valeur in args:
            if not valeur.isdigit() or int(valeur) < 0:
                return "Le nombre de places doit être un entier positif ou nul."

        # On vérifie que le nombre de places demandées pour chaque catégorie ne dépasse pas le nombre de places disponibles pour cette catégorie,
        # en prenant en compte le nombre de places déjà réservées pour cette catégorie dans la réservation
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
                # On utilise fetchone() car il ne peut y avoir qu'une seule ligne correspondant à une catégorie de place pour une représentation
                # Donc pas besoin de continuer la recherche

                if nouveauNombrePlaces - ancientNombrePlaces > nombrePlacesDisponible:
                    return f"Il n'y a pas assez de places disponibles pour la catégorie {reservationChoisie['categories'][i]['type_place']}. (Disponibles: {nombrePlacesDisponible}, Demandées en plus: {nouveauNombrePlaces - ancientNombrePlaces})"
        return True

    # Nouvelles valeurs saisies par le client pour le nombre de places réservées pour chaque catégorie de place de la réservation,
    # Sous forme de tuple, dans le même ordre que les catégories de la réservation
    nouvellesValeurs = UI.inputTexte(
        ecranAffichage="gauche",
        titre="Modification de la réservation",
        message=texteInput,
        sortieAvecEchap=True,
        valeurParDefaut=valeursParDefaut,
        functionDeValidation=validerModification,
    )

    # Si l'utilisateur appuie sur Échap, la fonction inputTexte retourne un tuple de None, on considère que c'est une annulation de la modification,
    # on affiche un message d'annulation et on quitte le processus de modification des réservations
    if nouvellesValeurs[0] is None:
        annulation()
        CURSEUR.close()
        return

    # Dans la DB, on a une ligne par catégorie de place réservée pour une réservation, avec le nombre de places réservées pour cette catégorie,
    # Donc pour mettre à jour la réservation avec les nouvelles valeurs saisies par le client,
    # on doit faire une mise à jour pour chaque catégorie de place de la réservation,
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
        message="[green]La réservation a été modifiée avec succès.[/green] \n\nAppuyez sur Entrée pour continuer.",
    )
    CURSEUR.close()
