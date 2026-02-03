import Global
import Modules.Interface as UI

import re


def annulation():
    UI.attendreAppuiEntree(
        titre="Opération annulée",
        message="L'ajout du spectacle a été annulé.",
        ecranAffichage="gauche",
    )


def main():
    texteInput = """[bold]Veuillez entrer les informations du spectacle à ajouter :[/bold]\n\n
    [bold]Nom du spectacle :[/bold] __INPUT__
    [bold]Site web du spectacle :[/bold] __INPUT__
    """

    def validation(nom, siteWeb):
        if len(nom.strip()) == 0:
            return "Le nom du spectacle ne peut pas être vide."
        if len(siteWeb.strip()) == 0:
            return "Le site web du spectacle ne peut pas être vide."
        if not re.match(r"^https?://", siteWeb):
            return "Le site web doit commencer par http:// ou https://"
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
