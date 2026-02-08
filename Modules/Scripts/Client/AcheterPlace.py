# ╔════════════════════════════════════════════════════════════════╗
# ║                     Achat de places                            ║
# ║                                                                ║
# ║ Propose à l'utilisateur de choisir un spectacle, puis une      ║
# ║ représentation, puis le nombre de places à acheter pour        ║
# ║ chaque catégorie de place disponible pour cette                ║
# ║ représentation, et enfin confirme l'achat avant de mettre      ║
# ║ à jour la base de données                                      ║
# ╚════════════════════════════════════════════════════════════════╝


# ――――――――――――――――――――――――― IMPORTATION DES MODULES ――――――――――――――――――――――――――
import Global
import Modules.Interface as UI


from rich.console import Group
from rich.markdown import Markdown
from rich.text import Text

# ――――――――――――――――――――――――― FONCTIONS ――――――――――――――――――――――――――


# Fonction d'annulation de l'achat, réutilisée plusieurs fois
def annulation():
    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Annulation",
        message="Achat [red]annulée[/red]. \n\nAppuyez sur Entrée pour continuer.",
    )


def main():

    CURSEUR = Global.CONNEXION.cursor()

    # On récupère la liste des spectacles avec au moins une représentation à venir, ainsi que le nombre de représentations à venir pour chaque spectacle
    requete = """SELECT spectacle.id, spectacle.libelle, spectacle.site_web, COUNT( distinct representation.id)
    FROM spectacle,representation 
    WHERE spectacle.id = representation.id_spectacle
    AND representation.date >= DATE('now')
    GROUP BY spectacle.id, spectacle.libelle, spectacle.site_web
    ORDER BY spectacle.libelle"""
    CURSEUR.execute(requete)
    spectacles = CURSEUR.fetchall()
    # Constution des options du menu des spectacles, avec le nom du spectacle et le nombre de représentations à venir entre parenthèses
    options = []
    for spectacle in spectacles:
        nom = f"{spectacle[1]} ([dim]{spectacle[3]} représentation disponibles[/dim])"
        options.append(
            {
                "nom": nom,
                "id": spectacle[0],
            }
        )

    UI.mettreAJourPanelDroit(
        Group(
            Markdown(f"# Achat de places"),
            "",
            Text("Sélectionnez un spectacle dans le menu de gauche pour commencer le processus d'achat de places."),
            Global.TEXTES["aideNavigationMenu"],
        )
    )

    if len(options) == 0:
        UI.attendreAppuiEntree(
            ecranAffichage="gauche",
            titre="Aucun spectacle disponible",
            message="[red]Il n'y a aucun spectacle avec une représentation à venir disponible pour le moment.[/red]\n\nAppuyez sur Entrée pour continuer.",
        )
        CURSEUR.close()
        return

    # On affiche le menu des spectacles et on récupère le spectacle choisi par l'utilisateur,
    # si l'utilisateur appuie sur Échap, on annule le processus d'achat et on retourne au menu principal
    spectacle = UI.afficherMenu(
        titre="Liste des Spectacles",
        afficherLesDescriptions=False,
        sortieAvecEchap=True,
        options=options,
    )

    # Si l'utilisateur appuie sur Échap
    if spectacle is None:
        annulation()
        CURSEUR.close()
        return

    # On récupère la liste des représentations à venir pour le spectacle choisi,
    # ainsi que les différentes catégories de places disponibles pour chaque représentation,
    # leur prix et le nombre de places disponibles
    requete = """SELECT 
    representation.id, representation.date, representation.heure, place.type_place, place.prix, place.nb_places, place.id
    FROM representation, place 
    WHERE id_spectacle = ? 
    AND representation.date >= DATE('now')
    AND place.id_representation = representation.id 
    ORDER BY representation.date, representation.heure, place.type_place"""
    CURSEUR.execute(requete, (spectacle["id"],))
    representations = CURSEUR.fetchall()

    # Construction des options du menu
    # On veut faire une option par représentation mais la requete donne une ligne par catégorie de place,
    # on doit donc regrouper les catégories de place par représentation pour construire les options du menu
    options = []
    idRepresentation = None
    places = {}
    for repEtPlace in representations:

        # On ajoute une options pour la représentation précédente avant de passer à la suivante, sauf pour la première itération
        if idRepresentation != repEtPlace[0]:
            description = ""
            idRepresentation = repEtPlace[0]
            description += f"[bold]Places:[/bold]\n"
            description += (
                f"- Type: {repEtPlace[3]}, Prix: {repEtPlace[4]}€, Nombre de places disponibles: {repEtPlace[5]}\n"
            )
            options.append(
                {
                    "nom": f"Représentation le {UI.formatDateSQLToFR(repEtPlace[1])} à {repEtPlace[2]}",
                    "description": description,
                    "id_representation": idRepresentation,
                    "date": repEtPlace[1],
                    "heure": repEtPlace[2],
                }
            )
            places[(idRepresentation, repEtPlace[3])] = {
                "nb_places": repEtPlace[5],
                "prix": repEtPlace[4],
                "id_place": repEtPlace[6],
            }

        # Si on est sur la même représentation que la ligne précédente, on ajoute simplement les informations de la catégorie
        # de place à la description de l'option en cours
        else:
            options[-1][
                "description"
            ] += f"- Type: {repEtPlace[3]}, Prix: {repEtPlace[4]}€, Nombre de places disponibles: {repEtPlace[5]}\n"
            places[(idRepresentation, repEtPlace[3])] = {
                "nb_places": repEtPlace[5],
                "prix": repEtPlace[4],
                "id_place": repEtPlace[6],
            }

    # On affiche le menu des représentations et on récupère la représentation choisie par l'utilisateur,
    # si l'utilisateur appuie sur Échap, on annule le processus d'achat et on retourne au menu principal
    representationChoisie = UI.afficherMenu(
        titre="Choisissez une représentation",
        afficherLesDescriptions=True,
        sortieAvecEchap=True,
        options=options,
    )

    # Si l'utilisateur appuie sur Échap
    if representationChoisie is None:
        annulation()
        CURSEUR.close()
        return

    """
    Pour la représentation choisie, on affiche un formulaire d'achat de places, avec un champ de saisie pour chaque catégorie de place disponible pour cette représentation,
    Le format sera:
    
    Entrez le nombre de places achetées pour la représentation du <date> à <heure>
    <type_place_1> (disponibles: <nb_places>): __INPUT__  (<prix>€)
    <type_place_2> (disponibles: <nb_places>): __INPUT__  (<prix>€)
    ...
    """
    texteInput = f"Entrez le nombre de places achetées pour la représentation du {representationChoisie['date']} à {representationChoisie['heure']}\n\n"
    for (idRep, typePlace), details in places.items():
        if idRep == representationChoisie["id_representation"]:
            texteInput += f"{typePlace} (disponibles: {details['nb_places']}): __INPUT__  ({details['prix']}€)\n"

    # On ne connait pas le nombre de categories
    # On utilise donc l'opérateur * pour unpack la liste des inputs dans la fonction de validation, qui les traitera comme des arguments séparés
    def validation(*placesInput):
        placesInput = list(placesInput)
        for i in range(len(placesInput)):
            if placesInput[i] == "":
                placesInput[i] = "0"  # On considère qu'une entrée vide signifie 0 place

        # ON vérifie que les entrées sont des nombres entiers positifs ou nuls
        for nombrePlace in placesInput:
            if not nombrePlace.isdigit() or int(nombrePlace) < 0:
                return "Veuillez entrer un nombre valide de places (0 ou plus)."

        # On vérifie que le nombre de places demandées pour chaque catégorie ne dépasse pas le nombre de places disponibles pour cette catégorie
        # Cette méthode fonctionne car l'ordre des places dans le texte d'entrée est le même que dans le dictionnaire places
        i = 0
        for (idRep, typePlace), details in places.items():
            if idRep == representationChoisie["id_representation"]:
                quantite = int(placesInput[i])
                if quantite > details["nb_places"]:
                    return f"Le nombre de places demandé pour le type '{typePlace}' dépasse le nombre de places disponibles ({details['nb_places']})."
                i += 1

        return True

    # On affiche le formulaire d'achat de places et on récupère le nombre de places à acheter pour chaque catégorie,
    # validé par la fonction de validation ci-dessus,
    nombrePlaces = UI.inputTexte(
        ecranAffichage="gauche",
        titre="Achat de places",
        message=texteInput,
        sortieAvecEchap=True,
        functionDeValidation=validation,
    )

    # Si l'utilisateur appuie sur Échap
    if nombrePlaces[0] is None:
        annulation()
        CURSEUR.close()
        return

    UI.mettreAJourPanelDroit(
        Group(
            Markdown("# Confirmation d'achat"),
            "",
            "Appuyer sur Entrée pour [green]confirmer[/green] l'achat des places.\nAppuyer sur Échap pour [red]annuler[/red] l'achat.",
        )
    )

    # On affiche un ecran de confirmation récapitulant les places achetées et le montant total,
    # et on demande à l'utilisateur de confirmer ou d'annuler l'achat,
    total = "[bold]Récapitulatif de votre achat:[/bold]\n\n"
    total += f"Représentation le [bold]{representationChoisie['date']}[/bold] à [bold]{representationChoisie['heure']}[/bold]\n"

    # Pour chaque catégorie de place achetée, on ajoute une ligne au récapitulatif
    montantTotal = 0
    i = 0
    for (idRep, typePlace), details in places.items():
        if idRep == representationChoisie["id_representation"]:
            quantite = int(nombrePlaces[i]) if nombrePlaces[i] != "" else 0
            if quantite > 0:
                sousTotal = quantite * details["prix"]
                total += f"- {quantite} x {typePlace} à {details['prix']}€ = {sousTotal}€\n"
                montantTotal += sousTotal
            i += 1

    total += f"\n[bold]Montant total: {montantTotal}€[/bold]"

    # Affichage de la confirmation
    echapAppuye = UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Confirmation",
        message=total,
    )

    # Si l'utilisateur appuie sur Échap, on annule l'achat et on retourne au menu principal
    if echapAppuye:
        annulation()
        CURSEUR.close()
        return

    # Mise à jour de la base de données
    i = 0
    for (idRep, typePlace), details in places.items():
        if idRep == representationChoisie["id_representation"]:
            quantite = int(nombrePlaces[i]) if nombrePlaces[i] != "" else 0
            id_client = Global.client["id"]
            idPlace = details["id_place"]
            if quantite > 0:

                # On insère une ligne dans la table reservations
                requeteInsertion = """INSERT INTO reservation (id_client, id_place, nb_places, date_reservation) VALUES (?, ?, ?, DATE('now'))"""
                CURSEUR.execute(requeteInsertion, (id_client, idPlace, quantite))

                # On met à jour le nombre de places disponibles
                requeteMiseAJour = """UPDATE place SET nb_places = nb_places - ? WHERE id = ?"""
                CURSEUR.execute(requeteMiseAJour, (quantite, idPlace))
            i += 1

    CURSEUR.connection.commit()
    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Achat réussi",
        message="[green]Votre achat a été enregistré avec succès ! \n\nAppuyez sur Entrée pour continuer.[/green]",
    )

    CURSEUR.close()
