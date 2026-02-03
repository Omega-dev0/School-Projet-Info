import Global
import Modules.Interface as UI


from rich.console import Group
from rich.markdown import Markdown
from rich.text import Text


# Fonction d'annulation de l'achat, réutilisée plusieurs fois
def annulation():
    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Annulation",
        message="Achat [red]annulée[/red]. \n\nAppuyez sur Entrée pour continuer.",
    )


def main():

    CURSEUR = Global.CONNEXION.cursor()

    requete = "SELECT id, libelle, site_web FROM spectacle"
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

    UI.mettreAJourPanelDroit(
        Group(
            Markdown(f"# Achat de places"),
            Text(
                "Sélectionnez un spectacle dans le menu de gauche pour commencer le processus d'achat de places."
            ),
            Global.TEXTES["aideNavigationMenu"],
        )
    )

    spectacle = UI.afficherMenu(
        titre="Liste des Spectacles",
        afficherLesDescriptions=False,
        sortieAvecEchap=True,
        options=options,
    )

    if spectacle is None:
        annulation()
        CURSEUR.close()
        return

    requete = """SELECT 
    representation.id, representation.date, representation.heure, place.type_place, place.prix, place.nb_places, place.id
    FROM representation, place 
    WHERE id_spectacle = ? 
    AND place.id_representation = representation.id 
    ORDER BY representation.date, representation.heure, place.type_place"""

    CURSEUR.execute(requete, (spectacle["id"],))
    representations = CURSEUR.fetchall()
    options = []
    idRepresentation = None
    places = {}
    for repEtPlace in representations:
        if idRepresentation != repEtPlace[0]:
            description = ""
            idRepresentation = repEtPlace[0]
            description += f"[bold]Places:[/bold]\n"
            description += f"- Type: {repEtPlace[3]}, Prix: {repEtPlace[4]}€, Nombre de places disponibles: {repEtPlace[5]}\n"
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
        else:
            options[-1][
                "description"
            ] += f"- Type: {repEtPlace[3]}, Prix: {repEtPlace[4]}€, Nombre de places disponibles: {repEtPlace[5]}\n"
            places[(idRepresentation, repEtPlace[3])] = {
                "nb_places": repEtPlace[5],
                "prix": repEtPlace[4],
                "id_place": repEtPlace[6],
            }
    representationChoisie = UI.afficherMenu(
        titre="Choisissez une représentation",
        afficherLesDescriptions=True,
        sortieAvecEchap=True,
        options=options,
    )

    if representationChoisie is None:
        annulation()
        CURSEUR.close()
        return

    texteInput = f"Entrez le nombre de places achetées pour la représentation du {representationChoisie['date']} à {representationChoisie['heure']}\n\n"
    for (idRep, typePlace), details in places.items():
        if idRep == representationChoisie["id_representation"]:
            texteInput += f"{typePlace} (disponibles: {details['nb_places']}): __INPUT__  ({details['prix']}€)\n"

    def validation(*placesInput):
        placesInput = list(placesInput)
        for i in range(len(placesInput)):
            if placesInput[i] == "":
                placesInput[i] = "0"  # On considère qu'une entrée vide signifie 0 place

        for nombrePlace in placesInput:
            if not nombrePlace.isdigit() or int(nombrePlace) < 0:
                return "Veuillez entrer un nombre valide de places (0 ou plus)."

        # Cette méthode fonctionne car l'ordre des places dans le texte d'entrée est le même que dans le dictionnaire places
        i = 0
        for (idRep, typePlace), details in places.items():
            if idRep == representationChoisie["id_representation"]:
                quantite = int(placesInput[i])
                if quantite > details["nb_places"]:
                    return f"Le nombre de places demandé pour le type '{typePlace}' dépasse le nombre de places disponibles ({details['nb_places']})."
                i += 1

        return True

    nombrePlaces = UI.inputTexte(
        ecranAffichage="gauche",
        titre="Achat de places",
        message=texteInput,
        sortieAvecEchap=True,
        functionDeValidation=validation,
    )

    if nombrePlaces[0] is None:
        annulation()
        CURSEUR.close()
        return

    UI.mettreAJourPanelDroit(
        Group(
            Markdown("# Confirmation d'achat"),
            "Appuyer sur Entrée pour [green]confirmer[/green] l'achat des places.\nAppuyer sur Échap pour [red]annuler[/red] l'achat.",
        )
    )
    total = "[bold]Récapitulatif de votre achat:[/bold]\n\n"
    total += f"Représentation le [bold]{representationChoisie['date']}[/bold] à [bold]{representationChoisie['heure']}[/bold]\n"
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
    echapAppuye = UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Confirmation",
        message=total,
    )
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
