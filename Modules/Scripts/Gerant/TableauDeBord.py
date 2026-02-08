# ╔═════════════════════════════════════════════════════════════════════════════════════╗
# ║                      Tableau de Bord du Gérant                                      ║
# ║                                                                                     ║
# ║  Ce module affiche le tableau de bord du gérant avec :                             ║
# ║  - Les ventes par spectacle (nombre de places et chiffre d'affaires)               ║
# ║  - Les prochaines représentations à venir                                          ║
# ║                                                                                     ║
# ╚═════════════════════════════════════════════════════════════════════════════════════╝

# ――――――――――――――――――――――――― IMPORTATION DES MODULES ――――――――――――――――――――――――――

import Global
import Modules.Interface as UI
import datetime

from rich.table import Table
from rich.console import Group
from rich.markdown import Markdown

# ――――――――――――――――――――――――― FONCTIONS ――――――――――――――――――――――――――――――――


def main():
    CURSEUR = Global.CONNEXION.cursor()

    requeteVentes = """
        SELECT spectacle.libelle, SUM(reservation.nb_places), SUM(place.prix * reservation.nb_places)
        FROM reservation, place, representation, spectacle
        WHERE reservation.id_place = place.id
        AND place.id_representation = representation.id
        AND representation.id_spectacle = spectacle.id
        GROUP BY representation.id_spectacle
        ORDER BY SUM(place.prix * reservation.nb_places) DESC
    """
    ventesParSpectacle = CURSEUR.execute(requeteVentes).fetchall()

    # On affiche à droite les ventes par spectacle, avec pour chacun d'eux le nombre de places vendues et le chiffre d'affaires généré,
    # dans un tableau trié par chiffre d'affaires décroissant
    contenu = ""
    if len(ventesParSpectacle) == 0:
        contenu += "\nAucune vente enregistrée.\n"
        UI.mettreAJourPanelDroit(
            Group(
                Markdown("# Ventes"),
                "",
                contenu,
            )
        )
    else:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Spectacle", style="bold", width=30)
        table.add_column("Nombre de places vendues", justify="right")
        table.add_column("Chiffre d'affaires (€)", justify="right")
        for vente in ventesParSpectacle:
            table.add_row(
                vente[0],
                str(vente[1]),
                f"{vente[2]:.2f}",
            )
        contenu += "\n"
        group = Group(
            Markdown("# Ventes"),
            "",
            table,
        )
        UI.mettreAJourPanelDroit(group)

    # A gauche, on affiche les 5 prochaines représentations à venir, avec pour chacune d'elle le nom du spectacle, la date et l'heure de la représentation,
    # et le temps restant avant le début de la représentation, triées par date croissante
    prochainesRepresentation = CURSEUR.execute(
        """SELECT representation.id, representation.date, representation.heure, spectacle.libelle
        FROM representation,spectacle 
        WHERE representation.id_spectacle=spectacle.id
        AND date >= DATE('now')
        ORDER BY date, heure
        LIMIT 5""",
    ).fetchall()

    contenu = ""
    if len(prochainesRepresentation) == 0:
        contenu += "\nAucune représentation à venir.\n"
    else:
        contenu += "[bold underline]Prochaines Représentations:[/bold underline]\n"
        for representation in prochainesRepresentation:
            dateNow = datetime.datetime.now()
            dateRep = datetime.datetime.strptime(f"{representation[1]} {representation[2]}", "%Y-%m-%d %H:%M")
            delta = dateRep - dateNow

            # A partir du delta des deux dates, on construit une chaîne de caractères indiquant
            # le temps restant avant le début de la représentation, en affichant les jours, heures et minutes restants
            tempsRestant = ""
            if delta.days > 0:
                tempsRestant += f"{delta.days} jour{'s' if delta.days > 1 else ''} "
            heures = delta.seconds // 3600
            if heures > 0:
                tempsRestant += f"{heures} heure{'s' if heures > 1 else ''} "
            minutes = (delta.seconds % 3600) // 60
            if minutes > 0:
                if len(tempsRestant) > 0:
                    tempsRestant += "et "
                tempsRestant += f"{minutes} minute{'s' if minutes > 1 else ''} "

            contenu += f"\n\n- [bold]{representation[3]}[/bold] le [green]{UI.formatDateSQLToFR(representation[1])}[/green] à [green]{representation[2]}[/green] | Dans: {tempsRestant}"

    UI.attendreAppuiEntree(
        titre="Tableau de bord",
        message=contenu,
        ecranAffichage="gauche",
    )
