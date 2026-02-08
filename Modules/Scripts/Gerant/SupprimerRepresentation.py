# ╔═════════════════════════════════════════════════════════════════════════════════════╗
# ║                   Suppression de représentations                                    ║
# ║                                                                                     ║
# ║  Ce module permet au gérant de supprimer les représentations de spectacles.         ║
# ║  Il permet de sélectionner une représentation et de la supprimer définitivement,    ║
# ║  ainsi que toutes les données associées (places et réservations).                   ║
# ║                                                                                     ║
# ║                                                                                     ║
# ╚═════════════════════════════════════════════════════════════════════════════════════╝

# ――――――――――――――――――――――――― IMPORTATION DES MODULES ――――――――――――――――――――――――――

import Global
import Modules.Interface as UI

# ――――――――――――――――――――――――― FONCTIONS ――――――――――――――――――――――――――――――――


# Fonction d'affichage de l'écran de confirmation d'annulation, utilisée à plusieurs endroits
def annulation():
    UI.attendreAppuiEntree(
        titre="Opération annulée",
        message="[red]La suppression de la représentation a été annulée.[/red]\n\nAppuyez sur Entrée pour continuer.",
        ecranAffichage="gauche",
    )


def main():

    CURSEUR = Global.CONNEXION.cursor()

    # On récupère la liste des représentations, avec pour chacune d'elle la date, l'heure, le nom du spectacle associé et son id
    requete = """SELECT representation.id, representation.date, representation.heure, spectacle.libelle
    FROM representation, spectacle
    WHERE representation.id_spectacle = spectacle.id
    ORDER BY spectacle.libelle, representation.date, representation.heure
    """
    representations = CURSEUR.execute(requete).fetchall()

    # Construction de la liste des options du menu de sélection de la représentation à supprimer,
    # avec pour chacune d'elle le nom du spectacle, la date et l'heure de la représentation, et son id pour pouvoir la supprimer de la base de données
    # On ajoute également des séparateurs pour regrouper les représentations par spectacle, en utilisant le nom du spectacle récupéré dans la requête SQL
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

    # Si aucune représentation n'est sélectionnée, on annule l'opération
    if representationSelectionnee is None:
        annulation()
        CURSEUR.close()
        return

    # Demande de confirmation
    annulee = UI.attendreAppuiEntree(
        titre="Confirmer la suppression",
        message=f"Êtes-vous sûr de vouloir supprimer la représentation du {UI.formatDateSQLToFR(representationSelectionnee['date'])} à {representationSelectionnee['heure']} ? Cette action est irréversible.\n\nAppuyez sur [green]Entrée[/green] pour confirmer ou sur [red]Échap[/red] pour annuler.",
        ecranAffichage="gauche",
    )
    if annulee:
        annulation()
        CURSEUR.close()
        return

    # Suppression de la représentation sélectionnée de la base de données, ainsi que de toutes les données associées (places et réservations)
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
