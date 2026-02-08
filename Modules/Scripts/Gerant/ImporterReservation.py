# ╔═════════════════════════════════════════════════════════════════════════════════════╗
# ║                   Importation de réservations                                       ║
# ║                                                                                     ║
# ║  Ce module permet au gérant d'importer des réservations depuis un fichier texte.    ║
# ║  Il lit le fichier, valide les données, puis les enregistre dans la base de données.║
# ║                                                                                     ║
# ║  Format du fichier (.txt):                                                          ║
# ║  email <email_client>                                                               ║
# ║  prenom <prenom_client>                                                             ║
# ║  nom <nom_client>                                                                   ║
# ║  nom_spectacle <nom_spectacle>                                                      ║
# ║  date <YYYY-MM-DD>                                                                  ║
# ║  heure <HH:MM>                                                                      ║
# ║  type_place <type_place>                                                            ║
# ║  prix <prix>                                                                        ║
# ║  nb_places <nb_places>                                                              ║
# ║  date_reservation <YYYY-MM-DD>                                                      ║
# ║                                                                                     ║
# ╚═════════════════════════════════════════════════════════════════════════════════════╝

# ――――――――――――――――――――――――― IMPORTATION DES MODULES ――――――――――――――――――――――――――


import Global
import Modules.Interface as UI


# ――――――――――――――――――――――――― FONCTIONS ――――――――――――――――――――――――――――――――――


# Fonction d'affichage de l'écran de confirmation d'annulation, utilisée à plusieurs endroits
def annulation():
    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Annulation",
        message="Importation [red]annulée[/red]. \n\nAppuyez sur Entrée pour continuer.",
    )


def main():
    CURSEUR = Global.CONNEXION.cursor()

    # On demande au gérant de sélectionner le fichier texte à importer, avec comme chemin de base le dossier ./Files/
    # et en filtrant les fichiers pour n'afficher que les .txt
    cheminFichier = UI.inputFichier(
        titre="Importer des réservation",
        cheminDeBase="./Files/",
        formatsAcceptes=[".txt"],
        sortieAvecEchap=True,
    )
    # Si le gérant appuie sur Échap au lieu de sélectionner un fichier, on annule l'importation et on retourne au menu précédent
    if cheminFichier is None:
        annulation()
        CURSEUR.close()
        return

    # L'ouverture peut échouer pour différentes raisons,
    # mieux vaut gérer les exceptions pour éviter de planter le programme et afficher un message d'erreur clair au gérant
    try:
        """
        Format:
        email <email_client>
        prenom <prenom_client>
        nom <nom_client>
        nom_spectacle <nom_spectacle>
        date <YYYY-MM-DD>
        heure <HH:MM>
        type_place <type_place>
        prix <prix>
        nb_places <nb_places>
        date_reservation <YYYY-MM-DD>
        """

        # Le fichier reste ouvert et sera fermé a la fin du bloc même en cas d'erreur grâce à l'utilisation de with
        with open(cheminFichier, "r", encoding="utf-8") as fichier:
            texte = fichier.read()
            texte = texte.replace("\t", " ")  # Remplacer les tabulations par des espaces pour uniformiser
            lignes = [
                ligne.strip() for ligne in texte.split("\n") if ligne.strip() != ""
            ]  # Nettoyer les lignes vides et les espaces superflus en fin de ligne
            emailClient = lignes[0].split(" ", 1)[1].strip()
            prenomClient = lignes[1].split(" ", 1)[1].strip()
            nomClient = lignes[2].split(" ", 1)[1].strip()

            nomSpectacle = lignes[3].split(" ", 1)[1].strip()
            date = lignes[4].split(" ", 1)[1].strip()
            heure = lignes[5].split(" ", 1)[1].strip()

            typePlace = lignes[6].split(" ", 1)[1].strip()
            prix = float(lignes[7].split(" ", 1)[1].strip())
            nbPlaces = int(lignes[8].split(" ", 1)[1].strip())
            dateReservation = lignes[9].split(" ", 1)[1].strip()

            # avant de gérer le client, vérifions que la réservation est possible
            requete = """SELECT representation.id
            FROM spectacle, representation
            WHERE spectacle.id = representation.id_spectacle
            AND spectacle.libelle = ?
            AND representation.date = ?
            AND representation.heure = ?"""
            CURSEUR.execute(requete, (nomSpectacle, date, heure))
            rep = CURSEUR.fetchone()

            if rep is None:
                UI.attendreAppuiEntree(
                    ecranAffichage="gauche",
                    titre="Représentation Inconnue",
                    message=f"[red]La représentation pour le spectacle '{nomSpectacle}' le {date} à {heure} n'existe pas dans la base de données.[/red]\n\nAppuyez sur Entrée pour continuer.",
                )
                CURSEUR.close()
                return

            # Verification des informations de places
            idRepresentation = rep[0]
            requete = """SELECT nb_places, prix, id
            FROM place
            WHERE id_representation = ?
            AND type_place = ?"""
            CURSEUR.execute(requete, (idRepresentation, typePlace))
            placeInfo = CURSEUR.fetchone()

            if placeInfo is None:
                UI.attendreAppuiEntree(
                    ecranAffichage="gauche",
                    titre="Type de Place Inconnu",
                    message=f"[red]Le type de place '{typePlace}' n'existe pas pour la représentation du spectacle '{nomSpectacle}' le {date} à {heure}.[/red]\n\nAppuyez sur Entrée pour continuer.",
                )
                CURSEUR.close()
                return

            if prix != placeInfo[1]:
                UI.attendreAppuiEntree(
                    ecranAffichage="gauche",
                    titre="Prix Incohérent",
                    message=f"[red]Le prix indiqué ({prix}€) ne correspond pas au prix en base de données ({placeInfo[1]}€) pour le type de place '{typePlace}'.[/red]\n\nAppuyez sur Entrée pour continuer.",
                )
                CURSEUR.close()
                return

            if nbPlaces > placeInfo[0]:
                UI.attendreAppuiEntree(
                    ecranAffichage="gauche",
                    titre="Nombre de Places Insuffisant",
                    message=f"[red]Le nombre de places disponibles ({placeInfo[0]}) est insuffisant pour la réservation de {nbPlaces} places du type '{typePlace}'.[/red]\n{nomSpectacle} le {date} à {heure}\n\nAppuyez sur Entrée pour continuer.",
                )
                CURSEUR.close()
                return

            # Gestion du client
            requete = """SELECT id,nom,prenom FROM client WHERE email = ?"""
            CURSEUR.execute(requete, (emailClient,))
            clientChoisi = CURSEUR.fetchone()

            if clientChoisi is None:
                annule = UI.attendreAppuiEntree(
                    ecranAffichage="gauche",
                    titre="Client Inconnu",
                    message=f"[yellow]Le client avec l'email '{emailClient}' n'existe pas dans la base de données. Il sera donc crée avec les informations fournies dans le fichier.[/yellow]\n\nAppuyez sur Entrée pour continuer ou Échap pour annuler.",
                )
                if annule:
                    annulation()
                    CURSEUR.close()
                    return

                if nomClient == "" or prenomClient == "" or emailClient == "":
                    UI.attendreAppuiEntree(
                        ecranAffichage="gauche",
                        titre="Informations Incomplètes",
                        message="[red]Les informations du client sont incomplètes dans le fichier. Le client ne peut pas être créé.[/red]\n\nAppuyez sur Entrée pour continuer.",
                    )
                    CURSEUR.close()
                    return

                # Insertion du nouveau client dans la base de données
                requeteInsertion = "INSERT INTO client (nom, prenom, email) VALUES (?,?,?)"
                CURSEUR.execute(requeteInsertion, (nomClient, prenomClient, emailClient))
                Global.CONNEXION.commit()
                idClient = CURSEUR.lastrowid
            else:
                idClient = clientChoisi[0]
                if nomClient != clientChoisi[1] or prenomClient != clientChoisi[2]:
                    UI.attendreAppuiEntree(
                        ecranAffichage="gauche",
                        titre="Incohérence des Informations du Client",
                        message=f"[red]Un client avec l'email '{emailClient}' existe déjà, mais les informations fournies dans le fichier ne correspondent pas à celles en base de données\n {clientChoisi[1]} {clientChoisi[2]} /  {nomClient} {prenomClient}.[/red]\n\nAppuyez sur Entrée pour continuer.",
                    )
                    CURSEUR.close()
                    return

            # Insertion de la réservation
            requeteInsertion = (
                """INSERT INTO reservation (id_client, id_place, nb_places, date_reservation) VALUES (?, ?, ?, ?)"""
            )
            CURSEUR.execute(
                requeteInsertion,
                (idClient, placeInfo[2], nbPlaces, dateReservation),
            )

            # Mise à jour du nombre de places disponibles
            requeteMiseAJour = """UPDATE place SET nb_places = nb_places - ? WHERE id = ?"""
            CURSEUR.execute(requeteMiseAJour, (nbPlaces, placeInfo[2]))
            Global.CONNEXION.commit()

            UI.attendreAppuiEntree(
                ecranAffichage="gauche",
                titre="Importation Réussie",
                message=f"[green]La réservation a été importée avec succès.[/green]\n\nClient: [bold]{prenomClient} {nomClient}[/bold]\nSpectacle: [bold]{nomSpectacle}[/bold]\nDate: [bold]{date}[/bold]\nHeure: [bold]{heure}[/bold]\nType de Place: [bold]{typePlace}[/bold]\nNombre de Places: [bold]{nbPlaces}[/bold]\nDate de Réservation: [bold]{dateReservation}[/bold]\n\nAppuyez sur Entrée pour continuer.",
            )

    except Exception as e:
        UI.attendreAppuiEntree(
            ecranAffichage="gauche",
            titre="Erreur d'Importation",
            message=f"[red]Une erreur est survenue lors de l'importation :[/red]\n{str(e)}\n\nAppuyez sur Entrée pour continuer.",
        )
    finally:
        CURSEUR.close()
