# ╔═════════════════════════════════════════════════════════════════════════════════════╗
# ║                   Importation de représentations                                    ║
# ║                                                                                     ║
# ║  Ce module permet au gérant d'importer des représentations depuis un fichier texte. ║
# ║  Il lit le fichier, valide les données, puis les enregistre dans la base de données.║
# ║                                                                                     ║
# ║  Format du fichier (.txt):                                                          ║
# ║  nom_spectacle <nom_du_spectacle>                                                   ║
# ║  site_web <url_du_site>                                                             ║
# ║  date <YYYY-MM-DD>                                                                  ║
# ║  heure <HH:MM>                                                                      ║
# ║  <type_place> <prix> <nb_places>                                                    ║
# ║  [<type_place> <prix> <nb_places>]  (répéter pour chaque catégorie)                 ║
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
        titre="Importer des Représentations",
        cheminDeBase="./Files/",
        formatsAcceptes=[".txt"],
        sortieAvecEchap=True,
    )
    if cheminFichier is None:
        annulation()
        CURSEUR.close()
        return

    # L'ouverture peut échouer pour différentes raisons,
    # mieux vaut gérer les exceptions pour éviter de planter le programme et afficher un message d'er
    try:
        """
        Format:
        nom_spectacle <nom_spectacle>
        site_web <site_web>
        date <YYYY-MM-DD>
        heure <HH:MM>
        type_place prix   nb_places
        [<cat>  <prix> <nb_places>]

        Commentaire: Le format de fichier fourni n'est pas très bon...
        Il utilise de façon variable des espaces et des tabulations pour séparer les champs.
        Il y a même parfois des espaces après les textes de façon aléatoire.
        Et a un format ligne par ligne puis bloc. Il serait préférable d'utiliser un format CSV ou JSON.
        Ou si l'on veut rester sur un format éditable par l'humain, YAML ou TOML seraient plus adaptés.

        Cette implémentation sera donc peut robuste pour les txt
        """
        with open(cheminFichier, "r", encoding="utf-8") as fichier:
            texte = fichier.read()
            texte = texte.replace("\t", " ")  # Remplacer les tabulations par des espaces pour uniformiser
            lignes = [
                ligne.strip() for ligne in texte.split("\n") if ligne.strip() != ""
            ]  # Nettoyer les lignes vides et les espaces superflus en fin de ligne
            nomSpectacle = (
                lignes[0].split(" ", 1)[1].strip()
            )  # On strip au cas ou le délémiteur serait multiple espaces pour une raison inconnue
            siteWeb = lignes[1].split(" ", 1)[1].strip()
            date = lignes[2].split(" ", 1)[1].strip()
            heure = lignes[3].split(" ", 1)[1].strip()
            places = []
            for ligne in lignes[5:]:
                parties = ligne.split(" ")
                parties = [partie for partie in parties if partie != ""]
                typePlace = parties[0].strip()
                prix = float(parties[1].strip())
                nbPlaces = int(parties[2].strip())
                places.append((typePlace, prix, nbPlaces))

            # On vérifie si le spectacle existe déjà
            CURSEUR.execute(
                "SELECT id FROM spectacle WHERE libelle = ? AND site_web = ?",
                (nomSpectacle, siteWeb),
            )
            idSpectacle = CURSEUR.fetchone()

            if idSpectacle is None:
                annule = UI.attendreAppuiEntree(
                    ecranAffichage="gauche",
                    titre="Spectacle Inconnu",
                    message=f"[yellow]Le spectacle '{nomSpectacle}' n'existe pas dans la base de données. Il sera donc crée.[/yellow]\n\nAppuyez sur Entrée pour continuer ou Échap pour annuler.",
                )
                if annule:
                    annulation()
                    CURSEUR.close()
                    return
                # Insertion du nouveau spectacle
                CURSEUR.execute(
                    "INSERT INTO spectacle (libelle, site_web) VALUES (?, ?)",
                    (nomSpectacle, siteWeb),
                )
                idSpectacle = CURSEUR.lastrowid
            else:
                idSpectacle = idSpectacle[0]

            # Vérification si la représentation existe déjà
            CURSEUR.execute(
                "SELECT id FROM representation WHERE id_spectacle = ? AND date = ? AND heure = ?",
                (idSpectacle, date, heure),
            )
            idRepresentation = CURSEUR.fetchone()
            if idRepresentation is not None:
                raise Exception(
                    f"La représentation du spectacle '{nomSpectacle}' le {date} à {heure} existe déjà dans la base de données."
                )

            # Insertion de la représentation
            CURSEUR.execute(
                "INSERT INTO representation (id_spectacle, date, heure) VALUES (?, ?, ?)",
                (idSpectacle, date, heure),
            )

            idRepresentation = CURSEUR.lastrowid

            # Insertion des places
            for typePlace, prix, nbPlaces in places:
                CURSEUR.execute(
                    "INSERT INTO place (id_representation, type_place, prix, nb_places) VALUES (?, ?, ?, ?)",
                    (idRepresentation, typePlace, prix, nbPlaces),
                )

        Global.CONNEXION.commit()
        infosRepresentation = (
            f"Spectacle: [bold]{nomSpectacle}[/bold]\nDate: [bold]{date}[/bold]\nHeure: [bold]{heure}[/bold]\nPlaces:\n"
        )
        for typePlace, prix, nbPlaces in places:
            infosRepresentation += f"- Catégorie: [bold]{typePlace}[/bold], Prix: [bold]{prix}€[/bold], Nombre de places: [bold]{nbPlaces}[/bold]\n"

        UI.attendreAppuiEntree(
            ecranAffichage="gauche",
            titre="Importation Réussie",
            message=f"[green]La représentation a été importée avec succès.[/green]\n\n{infosRepresentation}\n\nAppuyez sur Entrée pour continuer.",
        )
    except Exception as e:
        UI.attendreAppuiEntree(
            ecranAffichage="gauche",
            titre="Erreur d'Importation",
            message=f"[red]Une erreur est survenue lors de l'importation :[/red]\n{str(e)}\n\nAppuyez sur Entrée pour continuer.",
        )
    finally:
        CURSEUR.close()
