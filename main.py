# coding = utf-8

import Modules.Interface as UI
import Global

from rich.console import Group
from rich.markdown import Markdown
from rich.text import Text

from Modules.Scripts.Client.AfficherPieces import main as afficherPieces
from Modules.Scripts.Demo import main as demonstration
from Modules.Scripts.Client.AcheterPlace import main as acheterPlace
from Modules.Scripts.Client.AnnulerReservation import main as annulerReservation
from Modules.Scripts.Client.ModifierReservartion import main as modifierReservation
from Modules.Scripts.Client.VoirReservations import main as voirReservations
from Modules.Scripts.Client.ModificationCompteClient import main as modifierCompteClient

from Modules.Scripts.Gerant.AjoutSpectacle import main as ajoutSpectacle
from Modules.Scripts.Gerant.AjoutRepresentation import main as ajoutRepresentation
from Modules.Scripts.Gerant.SupprimerRepresentation import main as supprimerRepresentation
from Modules.Scripts.Gerant.ModifierRepresentation import main as modifierRepresentation
from Modules.Scripts.Gerant.TableauDeBord import main as tableauDeBord
from Modules.Scripts.Gerant.ImporterRepresentation import main as importerRepresentation
from Modules.Scripts.Gerant.ImporterReservation import main as importerReservation

import re


def main():

    CURSEUR = Global.CONNEXION.cursor()

    requete = """SELECT id,nom,prenom,email FROM client ORDER BY nom, prenom"""
    CURSEUR.execute(requete)
    clients = CURSEUR.fetchall()

    options = []
    for client in clients:
        options.append(
            {
                "nom": f"{client[1]} {client[2]} ([dim]{client[3]}[/dim])",
                "id": client[0],
                "client": {
                    "id": client[0],
                    "nom": client[1],
                    "prenom": client[2],
                    "email": client[3],
                },
            }
        )
    options.append(
        {
            "nom": "[blue]Créer un nouveau client[/blue]",
            "id": "NEW",
        }
    )
    UI.mettreAJourPanelDroit(
        Group(
            Markdown("# Disclaimer"),
            "",
            Text(
                "Ceci est une méthode peu pratique (et encore moins sécurisée mais ce n'est pas le sujet de ce projet) pour simuler une connexion client. Sélectionnez votre nom dans le menu de gauche pour continuer."
            ),
            Global.TEXTES["aideNavigationMenu"],
        )
    )

    while True:
        clientChoisi = UI.afficherMenu(
            titre="Sélectionnez votre client",
            afficherLesDescriptions=False,
            sortieAvecEchap=True,
            options=options,
        )
        if clientChoisi is None:
            Global.exit()  # L'utilisateur a appuyé sur Échap, impossible de continuer, on quitte le programme

        if clientChoisi["id"] == "NEW":
            # Création d'un nouveau client
            texte = """[bold]Veuillez entrer les informations du nouveau client :[/bold]\n\n
            [bold]Nom:[/bold] __INPUT__
            [bold]Prénom:[/bold] __INPUT__
            
            [bold]Email:[/bold] __INPUT__
            """

            def validationInfoClients(nom, prenom, email):
                if len(nom) < 1 or len(prenom) < 1:
                    return "Le nom et le prénom ne doivent pas être vides."
                regexExpression = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"  # Simple regex pour valider une adresse email | (W3C/WHATWG)/RFC 5322
                if not re.fullmatch(
                    regexExpression,
                    email,
                ):
                    return "L'adresse email n'est pas valide."
                return True

            nom, prenom, email = UI.inputTexte(
                ecranAffichage="gauche",
                titre="Création d'un nouveau client",
                message=texte,
                sortieAvecEchap=True,
                functionDeValidation=validationInfoClients,
            )

            if nom is None:
                continue  # L'utilisateur a appuyé sur Échap, on revient au menu de sélection du client

            # Insertion du nouveau client dans la base de données
            requeteInsertion = "INSERT INTO client (nom, prenom, email) VALUES (?,?,?)"
            CURSEUR.execute(requeteInsertion, (nom, prenom, email))
            Global.CONNEXION.commit()

            # Récupération de l'ID du nouveau client sans une autre requete (De stack overflow)
            idNouveauClient = CURSEUR.lastrowid
            Global.client = {
                "id": idNouveauClient,
                "nom": nom,
                "prenom": prenom,
                "email": email,
            }
            break  # Nouveau client créé, on peut sortir de la boucle
        else:
            Global.client = clientChoisi["client"]
            break  # Un client existant a été choisi

    options = [
        {
            "nom": "Modifier mes informations personnelles",
            "description": "Mettre à jour les informations de votre compte client.",
            "fonction": modifierCompteClient,
        },
        {
            "nom": "Se renseigner sur les spectacles",
            "description": "Consulter les informations sur les spectacles disponibles.",
            "fonction": afficherPieces,
        },
        {
            "nom": "Acheter une place",
            "description": "Procéder à l'achat de places pour un spectacle.",
            "fonction": acheterPlace,
        },
        {
            "nom": "Voir mes réservations",
            "description": "Consulter les réservations existantes.",
            "fonction": voirReservations,
        },
        {
            "nom": "Modifier une réservation",
            "description": "Modifier une réservation existante.",
            "fonction": modifierReservation,
        },
        {
            "nom": "Annuler une réservation",
            "description": "Annuler une réservation existante.",
            "fonction": annulerReservation,
        },
        {
            "nom": "Importer une réservation",
            "description": "Espace gérant : Importe une réservation depuis un fichier texte.",
            "fonction": importerReservation,
        },
        {
            "nom": "Ajouter un spectacle",
            "description": "Espace gérant : Ajouter un nouveau spectacle.",
            "fonction": ajoutSpectacle,
        },
        {
            "nom": "Démonstration",
            "description": "Démo pour Enora",
            "fonction": demonstration,
        },
        {
            "nom": "Ajouter une représentation",
            "description": "Espace gérant : Ajouter une nouvelle représentation.",
            "fonction": ajoutRepresentation,
        },
        {
            "nom": "Supprimer une représentation",
            "description": "Espace gérant : Supprimer une représentation existante.",
            "fonction": supprimerRepresentation,
        },
        {
            "nom": "Modifier une représentation",
            "description": "Modifier une représentation existante.",
            "fonction": modifierRepresentation,
        },
        {
            "nom": "Importer une représentation",
            "description": "Espace gérant : Importe une représentation depuis un fichier texte.",
            "fonction": importerRepresentation,
        },
        {
            "nom": "Tableau de bord",
            "description": "Espace gérant : Voir les statistiques du théâtre.",
            "fonction": tableauDeBord,
        },
    ]
    separateurs = {
        2: "[plum3]⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯ Réservations ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[/plum3]",
        6: "[blue]⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯ Espace gérant ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[/blue]",
    }
    choix = ""
    while choix is not None:
        choix = UI.afficherMenu(
            titre="Menu Principal",
            afficherLesDescriptions=True,
            sortieAvecEchap=True,
            options=options,
            separateurs=separateurs,
            afficherAideNavigation=True,
        )
        if choix is not None:
            choix["fonction"]()

    CURSEUR.close()
    Global.exit()


if __name__ == "__main__":
    main()
