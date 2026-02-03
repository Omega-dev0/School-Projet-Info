from Global import CONNEXION
import Modules.Interface as UI

import datetime


def main():

    CURSEUR = CONNEXION.cursor()

    requete = """SELECT spectacle.id, spectacle.libelle, spectacle.site_web, COUNT(representation.id)
    FROM spectacle 
    JOIN representation ON spectacle.id = representation.id_spectacle 
    GROUP BY spectacle.id, spectacle.libelle, spectacle.site_web 
    ORDER BY spectacle.libelle;"""
    CURSEUR.execute(requete)
    spectacles = CURSEUR.fetchall()

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
    while spectacle is not None:
        spectacle = UI.afficherMenu(
            titre="Liste des Spectacles",
            afficherLesDescriptions=True,
            sortieAvecEchap=True,
            options=options,
            afficherAideNavigation=True,
        )

        if spectacle is not None:

            requete = """SELECT representation.id, representation.date, representation.heure, place.type_place, place.prix, place.nb_places 
            FROM representation, place 
            WHERE id_spectacle = ? AND place.id_representation = representation.id 
            ORDER BY representation.date, representation.heure, place.type_place"""
            CURSEUR.execute(requete, (spectacle["id"],))
            representations = CURSEUR.fetchall()

            optionsRepresentation = []
            idRepresentation = None
            desc = ""
            date, heure = "", ""
            for place in representations:
                if idRepresentation != place[0]:
                    if desc != "":
                        dateRepresentation = datetime.datetime.strptime(date, "%Y-%m-%d")
                        if datetime.datetime.now() > dateRepresentation:
                            optionsRepresentation.append(
                                {
                                    "nom": f"[dim]Représentation le {UI.formatDateSQLToFR(date)} à {heure}[/dim]",
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
                desc += f"- Catégorie: {place[3]}, Prix: {place[4]}€, Nombre de places disponibles: {place[5]}\n"
            if desc != "":
                optionsRepresentation.append(
                    {
                        "nom": f"Représentation le {UI.formatDateSQLToFR(date)} à {heure}",
                        "description": desc,
                        "idRepresentation": idRepresentation,
                    }
                )

            if len(optionsRepresentation) == 0:
                texte = f"Aucune représentation n'est programmée pour le spectacle [bold]{spectacle['nom']}[/bold]."
                UI.attendreAppuiEntree(
                    titre=spectacle["nom"],
                    message=texte,
                    ecranAffichage="gauche",
                )
            else:
                UI.afficherMenu(
                    titre=f"Représentations pour le spectacle {spectacle['nom']}",
                    afficherLesDescriptions=True,
                    sortieAvecEchap=True,
                    options=optionsRepresentation,
                    afficherAideNavigation=True,
                    ecranAffichage="gauche",
                )

    CURSEUR.close()
