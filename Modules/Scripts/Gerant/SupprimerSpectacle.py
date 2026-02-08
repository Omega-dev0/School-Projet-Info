# ╔═════════════════════════════════════════════════════════════════════════════════════╗
# ║                   Suppression d'un spectacle                                        ║
# ║                                                                                     ║
# ║  Ce module permet au gérant de supprimer un spectacle de la base de données.        ║
# ║  Il permet de sélectionner un spectacle et de le supprimer définitivement,          ║
# ║  ainsi que toutes les données associées (représentations, places et réservations).  ║
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
        message="[red]La suppression du spectacle a été annulée.[/red]\n\nAppuyez sur Entrée pour continuer.",
        ecranAffichage="gauche",
    )


def main():

    CURSEUR = Global.CONNEXION.cursor()

    # On récupère la liste des représentations, avec pour chacune d'elle la date, l'heure, le nom du spectacle associé et son id
    requete = """
    SELECT spectacle.id, spectacle.libelle, COUNT(representation.id)
    FROM spectacle, representation
    WHERE spectacle.id = representation.id_spectacle
    GROUP BY spectacle.id
    ORDER BY spectacle.libelle
    """
    spectacles = CURSEUR.execute(requete).fetchall()

    # Construction de la liste des options du menu de sélection du spectacle à supprimer,
    # avec pour chacune d'elle le nom du spectacle, le nombre de représentations associées, et son id pour pouvoir la supprimer de la base de données
    options = []
    for spectacle in spectacles:
        options.append(
            {
                "nom": f"{spectacle[1]} [dim]({spectacle[2]} représentation{'s' if spectacle[2] > 1 else ''})[/dim]",
                "idSpectacle": spectacle[0],
                "libelle": spectacle[1],
            }
        )

    spectacleSelectionne = UI.afficherMenu(
        titre="Sélectionnez le spectacle à supprimer",
        afficherLesDescriptions=False,
        sortieAvecEchap=True,
        options=options,
    )

    if spectacleSelectionne is None:
        annulation()
        return

    # Confirmation de la suppression du spectacle, avec affichage du nom du spectacle sélectionné
    anulee = UI.attendreAppuiEntree(
        titre="Confirmation de la suppression",
        message=f"Êtes-vous sûr de vouloir supprimer le spectacle [bold red]{spectacleSelectionne['libelle']}[/bold red] et toutes ses représentations ?\n\nAppuyez sur Entrée pour confirmer, ou sur Échap pour annuler.",
        ecranAffichage="gauche",
    )

    if anulee:
        annulation()
        return

    # Supression des reservations associées aux représentations du spectacle sélectionné
    CURSEUR.execute(
        """DELETE 
        FROM reservation 
        WHERE id_place 
        IN (
            SELECT id 
            FROM place 
            WHERE id_representation 
            IN (
                SELECT id 
                FROM representation 
                WHERE id_spectacle = ?
                )
        )""",
        (spectacleSelectionne["idSpectacle"],),
    )

    # Supression des places associées aux représentations du spectacle sélectionné
    CURSEUR.execute(
        """DELETE 
        FROM place 
        WHERE id_representation 
        IN (
            SELECT id 
            FROM representation 
            WHERE id_spectacle = ?
            )
        """,
        (spectacleSelectionne["idSpectacle"],),
    )

    # Supression des représentations associées aux représentations du spectacle sélectionné
    CURSEUR.execute(
        """DELETE 
        FROM representation 
        WHERE id_spectacle = ?
        """,
        (spectacleSelectionne["idSpectacle"],),
    )

    # Suppression du spectacle sélectionné de la base de données, ainsi que toutes les représentations, places et réservations associées
    CURSEUR.execute(
        """DELETE 
        FROM spectacle 
        WHERE id = ?""",
        (spectacleSelectionne["idSpectacle"],),
    )

    Global.CONNEXION.commit()

    UI.attendreAppuiEntree(
        titre="Suppression réussie",
        message=f"[green]Le spectacle [bold]{spectacleSelectionne['libelle']}[/bold] et toutes ses représentations ont été supprimés avec succès.[/green]\n\nAppuyez sur Entrée pour continuer.",
        ecranAffichage="gauche",
    )

    CURSEUR.close()
