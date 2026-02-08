# coding = utf-8

# ――――――――――――――――――――――――― IMPORTATION DES MODULES ――――――――――――――――――――――――――

# Modules personnels
import Modules.Interface as UI
import Global

# Rich
from rich.console import Group
from rich.markdown import Markdown
from rich.text import Text

# On pourrait importer de façon dynamique et créer le menu principale de façon dynamique aussi?
# Mais on reste simple

# Scripts client
from Modules.Scripts.Client.AfficherPieces import main as afficherPieces
from Modules.Scripts.Client.AcheterPlace import main as acheterPlace
from Modules.Scripts.Client.AnnulerReservation import main as annulerReservation
from Modules.Scripts.Client.ModifierReservartion import main as modifierReservation
from Modules.Scripts.Client.VoirReservations import main as voirReservations
from Modules.Scripts.Client.ModificationCompteClient import main as modifierCompteClient

# Scripts gérant
from Modules.Scripts.Gerant.AjoutSpectacle import main as ajoutSpectacle
from Modules.Scripts.Gerant.AjoutRepresentation import main as ajoutRepresentation
from Modules.Scripts.Gerant.SupprimerRepresentation import main as supprimerRepresentation
from Modules.Scripts.Gerant.ModifierRepresentation import main as modifierRepresentation
from Modules.Scripts.Gerant.TableauDeBord import main as tableauDeBord
from Modules.Scripts.Gerant.ImporterRepresentation import main as importerRepresentation
from Modules.Scripts.Gerant.ImporterReservation import main as importerReservation
from Modules.Scripts.Gerant.SupprimerSpectacle import main as supprimerSpectacle
from Modules.Scripts.Gerant.VoirReservationsClient import main as voirReservationsClient

# Pour la manipulation d'expression regex
import re

# ――――――――――――――――――――――――― FONCTIONS ――――――――――――――――――――――――――


def main():

    CURSEUR = Global.CONNEXION.cursor()

    # On obtient la liste des clients enregistrés
    requete = """SELECT id,nom,prenom,email FROM client ORDER BY nom, prenom"""
    CURSEUR.execute(requete)
    clients = CURSEUR.fetchall()

    # Création des options du menu
    options = []
    for client in clients:
        estGerant = Global.estGerant(client[0])
        options.append(
            {
                "nom": f"{client[1]} {client[2]} ([dim]{client[3]}[/dim]) {"[blue]Gérant[/blue]" if estGerant else ""} ",
                "id": client[0],
                "client": {
                    "id": client[0],
                    "nom": client[1],
                    "prenom": client[2],
                    "email": client[3],
                    "gerant": estGerant,
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

    # ------- Processus de sélection du client/création d'un nouveau client -------
    while True:
        clientChoisi = UI.afficherMenu(
            titre="Sélectionnez votre client",
            afficherLesDescriptions=False,
            sortieAvecEchap=True,
            options=options,
        )
        if clientChoisi is None:
            Global.exit()  # L'utilisateur a appuyé sur Échap, impossible de continuer, on quitte le programme

        if clientChoisi["id"] == "NEW":  # type: ignore
            # Création d'un nouveau client
            # __INPUT__ désigne les champs de saisie
            texte = """[bold]Veuillez entrer les informations du nouveau client :[/bold]\n\n
            [bold]Nom:[/bold] __INPUT__
            [bold]Prénom:[/bold] __INPUT__
            
            [bold]Email:[/bold] __INPUT__
            """

            # Fonction permettant de valider l'input
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
                # Si l'utilisateur a appuyé sur Échap, la fonction inputTexte retourne [None, None, None]
                # L'utilisateur a appuyé sur Échap, on revient au menu de sélection du client
                continue

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
                "gerant": False,
            }
            break  # Nouveau client créé, on peut sortir de la boucle
        else:
            Global.client = clientChoisi["client"]  # type: ignore
            break  # Un client existant a été choisi

    CURSEUR.close()  # Plus besoin d'interagir avec la base de données dans ce script, on peut fermer le curseur

    # ------- Menu principal -------
    # Options du menu principal
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
            "gerantOnly": True,
        },
        {
            "nom": "Ajouter un spectacle",
            "description": "Espace gérant : Ajouter un nouveau spectacle.",
            "fonction": ajoutSpectacle,
            "gerantOnly": True,
        },
        {
            "nom": "Supprimer un spectacle",
            "description": "Espace gérant : Supprimer un spectacle existant.",
            "fonction": supprimerSpectacle,
            "gerantOnly": True,
        },
        {
            "nom": "Ajouter une représentation",
            "description": "Espace gérant : Ajouter une nouvelle représentation.",
            "fonction": ajoutRepresentation,
            "gerantOnly": True,
        },
        {
            "nom": "Supprimer une représentation",
            "description": "Espace gérant : Supprimer une représentation existante.",
            "fonction": supprimerRepresentation,
            "gerantOnly": True,
        },
        {
            "nom": "Modifier une représentation",
            "description": "Modifier une représentation existante.",
            "fonction": modifierRepresentation,
            "gerantOnly": True,
        },
        {
            "nom": "Importer une représentation",
            "description": "Espace gérant : Importe une représentation depuis un fichier texte.",
            "fonction": importerRepresentation,
            "gerantOnly": True,
        },
        {
            "nom": "Tableau de bord",
            "description": "Espace gérant : Voir les statistiques du théâtre.",
            "fonction": tableauDeBord,
            "gerantOnly": True,
        },
        {
            "nom": "Voir les réservations d'un client",
            "description": "Espace gérant : Voir les réservations d'un client sélectionné.",
            "fonction": voirReservationsClient,
            "gerantOnly": True,
        },
    ]
    # Séparateurs pour différencier les options destinées au client et celles destinées au gérant
    separateurs = {
        2: "[plum3]⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯ Réservations ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[/plum3]",
        6: "[blue]⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯ Espace gérant ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[/blue]",
    }
    choix = ""

    optionsFiltrees = []
    for option in options:
        if "gerantOnly" in option and option["gerantOnly"] and not Global.client["gerant"]:
            continue  # Si l'option est réservée aux gérants et que le client n'est pas un gérant, on n'ajoute pas l'option à la liste des options à afficher
        optionsFiltrees.append(option)
    options = optionsFiltrees

    # Boucle du menu principal, qui continue tant que l'utilisateur ne choisit pas de sortir (en appuyant sur Échap dans le menu)
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
            try:
                choix["fonction"]()  # Appel de la fonction associée à l'option choisie
            except Exception as e:
                UI.attendreAppuiEntree(
                    titre="Erreur",
                    message=f"[red]Une erreur est survenue lors de l'exécution de cette option :[/red]\n{str(e)}\n\nAppuyez sur Entrée pour continuer.",
                    ecranAffichage="gauche",
                )

    Global.exit()


# ――――――――――――――――――――――――― EXECUTION ――――――――――――――――――――――――――

if __name__ == "__main__":
    main()
