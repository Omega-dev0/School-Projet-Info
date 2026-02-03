import Global
import Modules.Interface as UI


def annulation():
    UI.attendreAppuiEntree(
        titre="Opération annulée",
        message="[red]La suppression de la représentation a été annulée.[/red]\n\nAppuyez sur Entrée pour continuer.",
        ecranAffichage="gauche",
    )


def main():
    CURSEUR = Global.CONNEXION.cursor()
    requete = """SELECT representation.id, representation.date, representation.heure, spectacle.libelle
    FROM representation, spectacle
    WHERE representation.id_spectacle = spectacle.id
    ORDER BY spectacle.libelle, representation.date, representation.heure
    """

    representations = CURSEUR.execute(requete).fetchall()

    options = []
    separateurs = {}

    spectacleCourant = None
    for representation in representations:
        if spectacleCourant != representation[3]:
            spectacleCourant = representation[3]
            separateurs[len(options)] = f"[bold tan]{spectacleCourant}[/bold tan]"

        options.append(
            {
                "nom": f"Représentation le {UI.formatDateSQLToFR(representation[1])} à {representation[2]}",
                "idRepresentation": representation[0],
                "date": representation[1],
                "heure": representation[2],
            }
        )

    representationSelectionnee = UI.afficherMenu(
        titre="Sélectionnez la représentation à supprimer",
        options=options,
        afficherLesDescriptions=False,
        sortieAvecEchap=True,
        separateurs=separateurs,
    )

    if representationSelectionnee is None:
        annulation()
        CURSEUR.close()
        return

    annulee = UI.attendreAppuiEntree(
        titre="Confirmer la suppression",
        message=f"Êtes-vous sûr de vouloir supprimer la représentation du {UI.formatDateSQLToFR(representationSelectionnee['date'])} à {representationSelectionnee['heure']} ? Cette action est irréversible.\n\nAppuyez sur [green]Entrée[/green] pour confirmer ou sur [red]Échap[/red] pour annuler.",
        ecranAffichage="gauche",
    )
    if annulee:
        annulation()
        CURSEUR.close()
        return

    requeteSuppressionRepresentation = "DELETE FROM representation WHERE id = ?"
    CURSEUR.execute(
        requeteSuppressionRepresentation,
        (representationSelectionnee["idRepresentation"],),
    )

    requeteSupressionReservation = """DELETE FROM reservation
    WHERE id_place IN (
        SELECT id FROM place WHERE id_representation = ?
    )"""
    CURSEUR.execute(
        requeteSupressionReservation,
        (representationSelectionnee["idRepresentation"],),
    )

    requeteSuppressionPlaces = "DELETE FROM place WHERE id_representation = ?"
    CURSEUR.execute(
        requeteSuppressionPlaces,
        (representationSelectionnee["idRepresentation"],),
    )

    Global.CONNEXION.commit()
    UI.attendreAppuiEntree(
        titre="Suppression réussie",
        message="[green]La représentation a été supprimée avec succès.[/green]\n\nAppuyez sur Entrée pour continuer.",
        ecranAffichage="gauche",
    )
    CURSEUR.close()
