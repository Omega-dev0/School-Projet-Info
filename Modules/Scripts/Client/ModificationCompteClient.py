import Global
import Modules.Interface as UI
import re


def annulation():
    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Annulation",
        message="Procédure [red]annulée[/red]. \n\nAppuyez sur Entrée pour continuer.",
    )


def main():

    texteInput = """[bold]Modifiez vos informations ci-dessous :[/bold]\n
    [bold]Nom:[/bold] __INPUT__
    [bold]Prénom:[/bold] __INPUT__
    [bold]Email:[/bold] __INPUT__"""

    valeurParDefaut = [
        Global.client["nom"],
        Global.client["prenom"],
        Global.client["email"],
    ]

    def validerModification(nom, prenom, email):
        if len(nom) < 2 or len(prenom) < 2:
            return "Le nom et le prénom doivent contenir au moins 2 caractères chacun."
        regexExpression = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"  # Simple regex pour valider une adresse email | (W3C/WHATWG)/RFC 5322
        if not re.fullmatch(
            regexExpression,
            email,
        ):
            return "L'adresse email n'est pas valide."
        return True

    nom, prenom, email = UI.inputTexte(
        ecranAffichage="gauche",
        titre="Modification des informations du compte",
        message=texteInput,
        valeurParDefaut=valeurParDefaut,
        sortieAvecEchap=True,
        functionDeValidation=validerModification,
    )
    if nom is None:
        annulation()
        return

    CURSEUR = Global.CONNEXION.cursor()
    requete = """
    UPDATE client
    SET nom = ?, prenom = ?, email = ?
    WHERE id = ?
    """
    CURSEUR.execute(requete, (nom, prenom, email, Global.client["id"]))
    Global.CONNEXION.commit()

    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Succès",
        message="Vos informations ont été [green]modifiées avec succès[/green]. \n\nAppuyez sur Entrée pour continuer.",
    )

    Global.client["nom"] = nom
    Global.client["prenom"] = prenom
    Global.client["email"] = email
    CURSEUR.close()
