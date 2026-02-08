# ╔═════════════════════════════════════════════════════════════════════════════════════╗
# ║                   Modification des informations du compte client                    ║
# ║                                                                                     ║
# ║  Ce module permet au client de modifier les informations de son compte.             ║
# ║  Il affiche les informations actuelles, permet de les modifier, puis met à jour     ║
# ║  la base de données avec les nouvelles informations.                                ║
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
        ecranAffichage="gauche",
        titre="Annulation",
        message="Procédure [red]annulée[/red]. \n\nAppuyez sur Entrée pour continuer.",
    )


def main():

    # Texte affiché dans l'écran de saisie des informations du client,
    # avec des espaces réservés __INPUT__ pour indiquer où les champs de saisie seront placés
    texteInput = """[bold]Modifiez vos informations ci-dessous :[/bold]\n
    [bold]Nom:[/bold] __INPUT__
    [bold]Prénom:[/bold] __INPUT__
    [bold]Email:[/bold] __INPUT__"""
    # On récupère les informations actuelles du client pour les afficher comme valeurs par défaut dans les champs de saisie
    # à paartir de l'objet Global.client, qui a été initialisé lors de la sélection du client dans main.py
    valeurParDefaut = [
        Global.client["nom"],
        Global.client["prenom"],
        Global.client["email"],
    ]

    # Fonction de validation des informations saisies par le client, utilisée pour valider les champs de saisie dans UI.inputTexte
    def validerModification(nom, prenom, email):

        # Référence obligatoire
        # https://www.kalzumeus.com/2010/06/17/falsehoods-programmers-believe-about-names/
        if len(nom) < 0:
            return "Le nom ne doit pas être vide."

        if len(prenom) < 0:
            return "Le prénom ne doit pas être vide."

        # Simple regex pour valider une adresse email | (W3C/WHATWG)/RFC 5322
        regexExpression = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.fullmatch(
            regexExpression,
            email,
        ):
            return "L'adresse email n'est pas valide."
        return True

    # On affiche l'écran de saisie des informations du client, avec les valeurs actuelles comme valeurs par défaut,
    # et on valide les informations saisies avec la fonction de validation définie ci-dessus
    nom, prenom, email = UI.inputTexte(
        ecranAffichage="gauche",
        titre="Modification des informations du compte",
        message=texteInput,
        valeurParDefaut=valeurParDefaut,
        sortieAvecEchap=True,
        functionDeValidation=validerModification,
    )
    # Si l'utilisateur appuie sur Échap, la fonction inputTexte retourne [None, None, None]
    # On affiche alors un message d'annulation et on quitte le processus de modification des informations du compte
    if nom is None:
        annulation()
        return

    # Mise à jour des informations du client dans la base de données avec les nouvelles informations saisies
    CURSEUR = Global.CONNEXION.cursor()
    requete = """
    UPDATE client
    SET nom = ?, prenom = ?, email = ?
    WHERE id = ?
    """
    CURSEUR.execute(requete, (nom, prenom, email, Global.client["id"]))
    Global.CONNEXION.commit()

    # Message de confirmation de la modification des informations du compte
    UI.attendreAppuiEntree(
        ecranAffichage="gauche",
        titre="Succès",
        message="Vos informations ont été [green]modifiées avec succès[/green]. \n\nAppuyez sur Entrée pour continuer.",
    )

    # Mise à jour de l'objet Global.client avec les nouvelles informations saisies,
    # pour que les autres modules aient accès aux informations à jour du client
    Global.client["nom"] = nom
    Global.client["prenom"] = prenom
    Global.client["email"] = email

    CURSEUR.close()
