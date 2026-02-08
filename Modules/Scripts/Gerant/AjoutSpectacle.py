# ╔═════════════════════════════════════════════════════════════════════════════════════╗
# ║                   Ajout d'un spectacle                                              ║
# ║                                                                                     ║
# ║  Ce module permet au gérant d'ajouter un nouveau spectacle.                         ║
# ║  Il demande les informations nécessaires, les valide, puis les enregistre dans la   ║
# ║  base de données.                                                                   ║
# ║                                                                                     ║
# ║                                                                                     ║
# ╚═════════════════════════════════════════════════════════════════════════════════════╝

# ――――――――――――――――――――――――― IMPORTATION DES MODULES ――――――――――――――――――――――――――


import Global
import Modules.Interface as UI

import re

# ――――――――――――――――――――――――― FONCTIONS ――――――――――――――――――――――――――――――――


# Fonction d'affichage de l'écran de confirmation d'annulation, utilisée à plusieurs endroits
def annulation():
    UI.attendreAppuiEntree(
        titre="Opération annulée",
        message="L'ajout du spectacle a été annulé.",
        ecranAffichage="gauche",
    )


def main():
    # __INPUT__ désigne les champs de saisie dans le texte affiché à l'écran
    texteInput = """[bold]Veuillez entrer les informations du spectacle à ajouter :[/bold]\n\n
    [bold]Nom du spectacle :[/bold] __INPUT__
    [bold]Site web du spectacle :[/bold] __INPUT__
    """

    # Fonction de validation des informations saisies par le gérant, utilisée pour valider les champs de saisie dans UI.inputTexte
    def validation(nom, siteWeb):
        if len(nom.strip()) == 0:
            return "Le nom du spectacle ne peut pas être vide."
        if len(siteWeb.strip()) == 0:
            return "Le site web du spectacle ne peut pas être vide."
        # Simple regex pour valider une URL (commençant par http:// ou https://, suivi d'un domaine valide, et éventuellement d'un chemin)
        if not re.match(r"^https?://[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(/.*)?$", siteWeb):
            return "Le site web doit commencer par http:// ou https:// et contenir un domaine valide."
        return True

    nom, siteWeb = UI.inputTexte(
        titre="Ajout d'un spectacle",
        message=texteInput,
        sortieAvecEchap=True,
        functionDeValidation=validation,
    )

    if nom is None:
        annulation()
        return

    # Mise à jour de la DB avec le nouveau spectacle
    CURSEUR = Global.CONNEXION.cursor()
    requeteInsertion = "INSERT INTO spectacle (libelle, site_web) VALUES (?, ?)"
    CURSEUR.execute(requeteInsertion, (nom.strip(), siteWeb.strip()))
    Global.CONNEXION.commit()

    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Spectacle ajouté",
        message=f"Le spectacle [bold]{nom}[/bold] a été ajouté avec [green]succès[/green].",
    )
    CURSEUR.close()
