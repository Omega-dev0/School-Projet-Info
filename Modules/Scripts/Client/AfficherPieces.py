# ╔════════════════════════════════════════════════════════════════╗
# ║                    Affichage des pièces                        ║
# ║                                                                ║
# ║ Affiche les pieces disponibles ainsi que les representations   ║
# ║ pour ces pieces                                                ║
# ╚════════════════════════════════════════════════════════════════╝


# ――――――――――――――――――――――――― IMPORTATION DES MODULES ――――――――――――――――――――――――――
from Global import CONNEXION
import Modules.Interface as UI

import datetime


# ――――――――――――――――――――――――― FONCTION ――――――――――――――――――――――――――
def main():

    CURSEUR = CONNEXION.cursor()

    # On affiche la liste des pièces disponibles, avec pour chacune d'elle le nombre de représentations
    requete = """SELECT spectacle.id, spectacle.libelle, spectacle.site_web, COUNT(representation.id)
    FROM spectacle 
    JOIN representation ON spectacle.id = representation.id_spectacle 
    GROUP BY spectacle.id 
    ORDER BY spectacle.libelle;"""
    CURSEUR.execute(requete)
    spectacles = CURSEUR.fetchall()

    # Construction des la liste des items du menu
    options = []
    for spectacle in spectacles:
        options.append(
            {
                "nom": spectacle[1],
                "description": f"[bold]Site web[/bold]: {spectacle[2]}\n[bold]Nombre de représentations[/bold]: {spectacle[3]}",
                "id": spectacle[0],
            }
        )

    spectacle = ""
    # On utilise une boucle pour que l'utilisateur puisse consulter les différentes pièces et leurs représentations autant de fois qu'il le souhaite
    # sans avoir à relancer le programme, et pour pouvoir revenir à la liste des pièces après avoir consulté les représentations d'une pièce
    while spectacle is not None:
        spectacle = UI.afficherMenu(
            titre="Liste des Spectacles",
            afficherLesDescriptions=True,
            sortieAvecEchap=True,
            options=options,
            afficherAideNavigation=True,
        )

        if spectacle is not None:

            # On affiche les représentations de la pièce sélectionnée, avec pour chacune d'elle la date,
            # l'heure et les différentes catégories de places disponibles
            requete = """SELECT representation.id, representation.date, representation.heure, place.type_place, place.prix, place.nb_places 
            FROM representation, place 
            WHERE id_spectacle = ? AND place.id_representation = representation.id 
            ORDER BY representation.date, representation.heure, place.type_place"""
            CURSEUR.execute(requete, (spectacle["id"],))
            representations = CURSEUR.fetchall()

            # On construit la liste des items du menu des représentations, en regroupant les différentes catégories de places pour une même représentation
            optionsRepresentation = []
            idRepresentation = None
            desc = ""
            date, heure = "", ""
            for place in representations:

                # Si on change de représentation, on ajoute l'ancienne représentation à la liste des options du menu des représentations,
                # et on réinitialise la description pour la nouvelle représentation
                if idRepresentation != place[0]:
                    if desc != "":  # Evite de le faire pour la première itération

                        # Si la représentation est passée, on affiche son nom en grisé pour indiquer qu'elle n'est plus disponible, sinon on l'affiche normalement
                        dateRepresentation = datetime.datetime.strptime(date, "%Y-%m-%d")
                        print(dateRepresentation)
                        delta = dateRepresentation - datetime.datetime.now()
                        if delta < datetime.timedelta(0):
                            optionsRepresentation.append(
                                {
                                    "nom": f"[dim]Représentation le {UI.formatDateSQLToFR(date)} à {heure}[/dim]",  # dim --> grisé
                                    "description": desc,
                                    "idRepresentation": idRepresentation,
                                }
                            )
                        else:
                            optionsRepresentation.append(
                                {
                                    "nom": f"Représentation le {UI.formatDateSQLToFR(date)} à {heure}",
                                    "description": desc,
                                    "idRepresentation": idRepresentation,
                                }
                            )
                    idRepresentation = place[0]
                    date = place[1]
                    heure = place[2]
                    desc = ""
                    desc += f"\n\n[underline]Représentation le {UI.formatDateSQLToFR(place[1])} à {place[2]}[/underline]\n[bold]Places:[/bold]\n"

                # On ajoute la catégorie de place à la description de la représentation en cours
                desc += f"- Catégorie: {place[3]}, Prix: {place[4]}€, Nombre de places disponibles: {place[5]}\n"

            # Après la boucle, on ajoute la dernière représentation en cours à la liste des options du menu des représentations
            if desc != "":  # Evite de le faire si il n'y a aucune représentation pour la pièce sélectionnée
                dateRepresentation = datetime.datetime.strptime(date, "%Y-%m-%d")
                delta = dateRepresentation - datetime.datetime.now()
                if delta < datetime.timedelta(0):
                    optionsRepresentation.append(
                        {
                            "nom": f"[dim]Représentation le {UI.formatDateSQLToFR(date)} à {heure}[/dim]",  # dim --> grisé
                            "description": desc,
                            "idRepresentation": idRepresentation,
                        }
                    )
                else:
                    optionsRepresentation.append(
                        {
                            "nom": f"Représentation le {UI.formatDateSQLToFR(date)} à {heure}",
                            "description": desc,
                            "idRepresentation": idRepresentation,
                        }
                    )

            # Si il n'y a aucune représentation pour la pièce sélectionnée, on affiche un message l'indiquant, sinon on affiche le menu des représentations
            if len(optionsRepresentation) == 0:
                texte = f"Aucune représentation n'est programmée pour le spectacle [bold]{spectacle['nom']}[/bold]."
                UI.attendreAppuiEntree(
                    titre=spectacle["nom"],
                    message=texte,
                    ecranAffichage="gauche",
                )
            else:
                # On affiche les representations
                # On ne recupère pas la representation selectionnée.
                UI.afficherMenu(
                    titre=f"Représentations pour le spectacle {spectacle['nom']}",
                    afficherLesDescriptions=True,
                    sortieAvecEchap=True,
                    options=optionsRepresentation,
                    afficherAideNavigation=True,
                    ecranAffichage="gauche",
                )

    CURSEUR.close()
