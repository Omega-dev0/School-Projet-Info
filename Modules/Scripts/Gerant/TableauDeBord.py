import Global
import Modules.Interface as UI
import datetime

from rich.table import Table
from rich.console import Group
from rich.markdown import Markdown


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
    contenu = ""
    if len(ventesParSpectacle) == 0:
        contenu += "\nAucune vente enregistrée.\n"
        UI.mettreAJourPanelDroit(
            Group(
                Markdown("# Ventes"),
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
            table,
        )
        UI.mettreAJourPanelDroit(group)

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
            dateRep = datetime.datetime.strptime(
                f"{representation[1]} {representation[2]}", "%Y-%m-%d %H:%M"
            )
            delta = dateRep - dateNow
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
            contenu += f"\n- [bold]{representation[3]}[/bold] le [green]{UI.formatDateSQLToFR(representation[1])}[/green] à [green]{representation[2]}[/green] | Dans: {tempsRestant}"

    UI.attendreAppuiEntree(
        titre="Tableau de bord",
        message=contenu,
        ecranAffichage="gauche",
    )
