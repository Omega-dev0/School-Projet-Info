from Global import INTERFACE, LIVE, CONSOLE
from pynput import keyboard
from rich.console import Group
from rich.live import Live
from rich.table import Table
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.console import Console
import time
from typing import Union
import os
import pathlib

import Global


def majusculeCaractere(caractere: str, majEnfoncee: bool, altEnfoncee: bool) -> str:
    """
     Transforme un caractère selon l'état des touches Majuscule et Alt.
    Cette fonction prend un caractère et retourne sa version modifiée en fonction de l'appui sur les touches Majuscule (majEnfoncee) et Alt (altEnfoncee), en tenant compte des caractères spéciaux du clavier AZERTY français.
    Paramètres :
        caractere (str) : Le caractère à transformer.
        majEnfoncee (bool) : Indique si la touche Majuscule est enfoncée.
        altEnfoncee (bool) : Indique si la touche Alt est enfoncée.
    Retourne :
         str : Le caractère transformé selon les touches enfoncées.
    """
    caracteresSpeciaux = [
        ("&", "1"),
        ("é", "2", "~"),
        ('"', "3", "#"),
        ("'", "4", "{"),
        ("(", "5", "["),
        ("-", "6", "|"),
        ("è", "7", "`"),
        ("_", "8", "\\"),
        ("ç", "9", "^"),
        ("à", "0", "@"),
        (")", "°", "]"),
        ("=", "+", "}"),
        ("$", "£", "€"),
        ("ù", "%"),
        ("*", "µ"),
        (",", "?"),
        (";", "."),
        (":", "/"),
        ("!", "§"),
        ("<", ">"),
    ]

    for speciaux in caracteresSpeciaux:
        if caractere == speciaux[0]:
            if majEnfoncee:
                return speciaux[1] if len(speciaux) > 1 else speciaux[0]
            elif len(speciaux) >= 3 and altEnfoncee:
                return speciaux[2]
            else:
                return speciaux[0]

    if majEnfoncee:
        return caractere.upper()
    return caractere.lower()


def enleverFormattage(content: str) -> str:
    """
    Supprime le formatage du texte si il y en a pour uniformiser les inputs

    Args:
        content (str): Le texte formaté à traiter.

    Returns:
        str: Le texte sans formatage (texte brut).
    """
    return Text.from_markup(content).plain


def elementTexteVersString(elementTexte: Union[str, Text]) -> str:
    """
    Convertit un élément de texte en chaîne de caractères pour uniformiser les affichages.

    Cette fonction prend en entrée soit une chaîne de caractères (`str`), soit un objet `Text`.
    Si l'entrée est un objet `Text`, elle retourne son attribut `plain`. Sinon, elle retourne la chaîne telle quelle.

    Paramètres:
        elementTexte (Union[str, Text]): L'élément de texte à convertir.

    Retourne:
        str: La représentation sous forme de chaîne de caractères de l'élément de texte.
    """
    return elementTexte.plain if isinstance(elementTexte, Text) else elementTexte


def mettreAJourPanelGauche(contenuNouveau):
    """
    Met à jour le panneau gauche de l'interface avec un nouveau contenu.

    Paramètres:
        contenuNouveau (str): Le nouveau contenu à afficher dans le panneau gauche.
    """
    INTERFACE["gauche"].update(Panel(contenuNouveau, border_style="bold green"))
    LIVE.refresh()


def mettreAJourPanelDroit(contenuNouveau):
    """
    Met à jour le panneau droit de l'interface avec un nouveau contenu.

    Paramètres:
        contenuNouveau (str): Le nouveau contenu à afficher dans le panneau droit.
    """
    INTERFACE["droite"].update(Panel(contenuNouveau, border_style="bold red"))
    LIVE.refresh()


def afficherMenu(
    options,
    titre="Menu",
    afficherLesDescriptions=True,
    separateurs={},
    sortieAvecEchap=True,
    boucle=True,
    ecranAffichage="gauche",
    afficherAideNavigation=False,
):
    """
    Affiche un menu interactif dans la console permettant à l'utilisateur de sélectionner une option à l'aide du clavier.

    Paramètres:
        options : list[dict]
            Liste des options à afficher dans le menu. Chaque option doit être un dictionnaire contenant au minimum la clé "nom" et éventuellement "description".
        titre : str, optionnel
            Titre affiché en haut du menu (par défaut "Menu").
        afficherLesDescriptions : bool, optionnel
            Si True, affiche la description de l'option sélectionnée (par défaut True).
        separateurs : dict, optionnel
            Dictionnaire associant des indices d'options à des séparateurs à afficher avant l'option correspondante.
        sortieAvecEchap : bool, optionnel
            Si True, permet de quitter le menu avec la touche Échap (par défaut True).
        boucle : bool, optionnel
            Si True, la navigation dans le menu boucle de la dernière à la première option et inversement (par défaut True).
        ecranAffichage : str, optionnel
            Détermine où afficher le menu ("gauche" ou "droite", par défaut "gauche").
        afficherAideNavigation : bool, optionnel
            Si True, affiche un texte d'aide à la navigation (par défaut False).

    Retourne:
        dict ou None
            Le dictionnaire de l'option sélectionnée, ou None si l'utilisateur quitte le menu avec Échap.
    """
    indexCurseur, optionSelectionnee, selectionFaite = 0, None, False

    hauteurConsole = CONSOLE.size.height
    itemsParPage = hauteurConsole - 8  # Réserver de l'espace pour le titre et les bordures

    def miseAJourInterface():
        elementTitre, elementOptions, page = (
            Markdown(f"# {titre}"),
            [],
            indexCurseur // itemsParPage,
        )
        debutIndex = page * itemsParPage

        if len(options) > itemsParPage:
            elementOptions.append(
                f"[dim]Page {page + 1} / {(len(options) - 1) // itemsParPage + 1}[/dim]"
            )
        if debutIndex > 0:
            elementOptions.append("[dim]...[/dim]")

        for index, option in enumerate(
            options[debutIndex : debutIndex + itemsParPage], start=debutIndex
        ):
            if separateurs.get(index):
                elementOptions.append(separateurs[index])
            if index == indexCurseur:
                nom = option["nom"]
                elementOptions.append("[bold yellow]• >[/bold yellow][bold] " + nom + "[/bold]")
                if afficherLesDescriptions and "description" in option:
                    mettreAJourPanelDroit(
                        Group(
                            Markdown(f"# {enleverFormattage(option['nom'])}"),
                            "",
                            option["description"],
                            (Global.TEXTES["aideNavigationMenu"] if afficherAideNavigation else ""),
                        )
                    )
            else:
                elementOptions.append("• " + option["nom"])

        if debutIndex + itemsParPage < len(options):
            elementOptions.append(f"[dim]...[/dim]")

        if ecranAffichage == "gauche":
            mettreAJourPanelGauche(Group(elementTitre, "", *elementOptions))
        else:
            mettreAJourPanelDroit(Group(elementTitre, "", *elementOptions))

    def toucheDeclenchee(touche):
        nonlocal indexCurseur, selectionFaite, optionSelectionnee
        if touche == keyboard.Key.up:
            indexCurseur = (indexCurseur - 1) % len(options) if boucle else max(0, indexCurseur - 1)
            miseAJourInterface()
        elif touche == keyboard.Key.down:
            indexCurseur = (
                (indexCurseur + 1) % len(options)
                if boucle
                else min(len(options) - 1, indexCurseur + 1)
            )
            miseAJourInterface()
        elif touche == keyboard.Key.enter:
            optionSelectionnee, selectionFaite = options[indexCurseur], True
        elif touche == keyboard.Key.esc and sortieAvecEchap:
            optionSelectionnee, selectionFaite = None, True

    connexionClavier = keyboard.Listener(on_press=toucheDeclenchee, suppress=Global.BLOQUER_INPUTS)
    connexionClavier.start()
    miseAJourInterface()

    while not selectionFaite:
        time.sleep(0.1)

    connexionClavier.stop()
    return optionSelectionnee


def attendreAppuiEntree(
    ecranAffichage="droite",
    titre="Continuer",
    message="Appuyez sur [bold]entrée[/bold] pour continuer...",
):
    """
    Affiche un message et attend l'appui sur une touche pour continuer.

    Cette fonction affiche un contenu avec un titre et un message sur l'écran spécifié,
    puis reste en attente jusqu'à ce que l'utilisateur appuie sur la touche Entrée ou Échap.

    Paramètres:
        ecranAffichage (str, optional): Position d'affichage du contenu ("gauche" ou "droite", par défaut "droite").
        titre (str, optional): Titre à afficher en haut du message (par défaut "Continuer").
        message (str, optional): Message à afficher au-dessous du titre (par défaut "Appuyez sur [bold]entrée[/bold] pour continuer...").

    Retourne:
        bool: False si l'utilisateur appuie sur Entrée, True si l'utilisateur appuie sur Échap.
    """
    annulee = None

    def toucheDeclenchee(touche):
        nonlocal annulee
        if touche == keyboard.Key.enter:
            annulee = False
        elif touche == keyboard.Key.esc:
            annulee = True

    connexionClavier = keyboard.Listener(on_press=toucheDeclenchee, suppress=Global.BLOQUER_INPUTS)
    connexionClavier.start()

    contenu = Group(Markdown(f"# {elementTexteVersString(titre)}"), "", message)
    (
        mettreAJourPanelGauche(contenu)
        if ecranAffichage == "gauche"
        else mettreAJourPanelDroit(contenu)
    )

    while annulee is None:
        time.sleep(0.1)

    connexionClavier.stop()
    return annulee


def inputTexte(
    ecranAffichage="gauche",
    titre="Entrée de texte",
    message="Veuillez entrer du texte : __INPUT__",
    valeurParDefaut=[],
    sortieAvecEchap=True,
    functionDeValidation=None,
):
    """
    Affiche une interface interactive pour l'entrée de texte utilisateur avec support clavier.

    Permet à l'utilisateur de saisir un ou plusieurs champs de texte via le clavier,
    avec navigation entre les champs, curseur positionnable, et validation personnalisée.

    Paramètres:
        ecranAffichage (str, optional): Position d'affichage du panneau ("gauche" ou "droite") (par défaut "gauche").
        titre (str, optional): Titre de la boîte de dialogue. (par défaut "Entrée de texte").
        message (str, optional): Message affiché avec placeholders "__INPUT__" pour chaque champ. (par défaut "Veuillez entrer du texte : __INPUT__").
        valeurParDefaut (list, optional): Liste des valeurs par défaut pour chaque champ. (par défaut []).
        sortieAvecEchap (bool, optional): Permet l'annulation avec la touche Échap. (par défaut True).
        functionDeValidation (callable, optional): Fonction de validation appelée avec les réponses.
            Doit retourner True si valide, sinon un message d'erreur.
            Défaut à None.

    Retourne:
        list: Liste des réponses saisies, ou liste de None si annulée avec Échap.
    """
    nombreChamps, reponses, termine = message.count("__INPUT__"), [], False
    annulee = False
    for i in range(nombreChamps):
        reponses.append(valeurParDefaut[i] if valeurParDefaut and len(valeurParDefaut) > i else "")
    valeurParDefaut = reponses.copy()

    positionDuCurseur, erreurPrecedente, indexReponseSelectionnee = (
        len(valeurParDefaut[0]) if valeurParDefaut else 0,
        "",
        0,
    )

    def miseAJourInterface():
        nonlocal reponses, positionDuCurseur, erreurPrecedente
        reponseStr = (
            reponses[indexReponseSelectionnee]
            if reponses[indexReponseSelectionnee] is not None
            else ""
        )
        reponseAffichee = reponseStr[:positionDuCurseur] + "|" + reponseStr[positionDuCurseur:]
        messageModifie = message

        for i in range(len(reponses)):
            r = (
                reponseAffichee
                if i == indexReponseSelectionnee
                else (reponses[i] if reponses[i] is not None else "")
            )
            messageModifie = messageModifie.replace("__INPUT__", r, 1)

        contenu = Group(
            Markdown(f"# {elementTexteVersString(titre)}"),
            "",
            messageModifie,
            f"[red]{erreurPrecedente}[/red]" if erreurPrecedente else "",
        )
        (
            mettreAJourPanelGauche(contenu)
            if ecranAffichage == "gauche"
            else mettreAJourPanelDroit(contenu)
        )

    majEnfoncee, altEnfoncee = False, False

    def toucheDeclenchee(touche):
        nonlocal reponses, termine, positionDuCurseur, majEnfoncee, altEnfoncee, indexReponseSelectionnee, annulee
        if touche == keyboard.Key.enter:
            termine = True
        elif touche == keyboard.Key.esc:
            if sortieAvecEchap:
                reponses, termine, annulee = (
                    [None for _ in reponses],
                    True,
                    True,
                )
        elif touche == keyboard.Key.backspace:
            if positionDuCurseur > 0:
                reponses[indexReponseSelectionnee] = (
                    reponses[indexReponseSelectionnee][: positionDuCurseur - 1]
                    + reponses[indexReponseSelectionnee][positionDuCurseur:]
                )
                positionDuCurseur -= 1
            miseAJourInterface()
        elif touche == keyboard.Key.space:
            reponses[indexReponseSelectionnee] = (
                reponses[indexReponseSelectionnee][:positionDuCurseur]
                + " "
                + reponses[indexReponseSelectionnee][positionDuCurseur:]
            )
            positionDuCurseur += 1
            miseAJourInterface()
        elif touche == keyboard.Key.delete:
            if positionDuCurseur < len(reponses[indexReponseSelectionnee]):
                reponses[indexReponseSelectionnee] = (
                    reponses[indexReponseSelectionnee][:positionDuCurseur]
                    + reponses[indexReponseSelectionnee][positionDuCurseur + 1 :]
                )
            miseAJourInterface()
        elif touche == keyboard.Key.left:
            positionDuCurseur = max(0, positionDuCurseur - 1)
            miseAJourInterface()
        elif touche == keyboard.Key.right:
            positionDuCurseur = min(len(reponses[indexReponseSelectionnee]), positionDuCurseur + 1)
            miseAJourInterface()
        elif touche in [keyboard.Key.shift, keyboard.Key.shift_r]:
            majEnfoncee = True
        elif touche == keyboard.Key.alt_gr:
            altEnfoncee = True
        elif touche == keyboard.Key.caps_lock:
            majEnfoncee = not majEnfoncee
        elif touche == keyboard.Key.up:
            NouveauIndexReponseSelectionnee = max(0, indexReponseSelectionnee - 1)
            if NouveauIndexReponseSelectionnee != indexReponseSelectionnee:
                indexReponseSelectionnee = NouveauIndexReponseSelectionnee
                positionDuCurseur = len(reponses[indexReponseSelectionnee])
                miseAJourInterface()
        elif touche == keyboard.Key.down:
            NouveauIndexReponseSelectionnee = min(len(reponses) - 1, indexReponseSelectionnee + 1)
            if NouveauIndexReponseSelectionnee != indexReponseSelectionnee:
                indexReponseSelectionnee = NouveauIndexReponseSelectionnee
                positionDuCurseur = len(reponses[indexReponseSelectionnee])
                miseAJourInterface()
        elif touche == keyboard.Key.num_lock:
            pass  # Ignorer cette touche pour éviter des problèmes sur certains claviers
        else:
            try:
                caractere = majusculeCaractere(touche.char, majEnfoncee, altEnfoncee)
                reponses[indexReponseSelectionnee] = (
                    reponses[indexReponseSelectionnee][:positionDuCurseur]
                    + caractere
                    + reponses[indexReponseSelectionnee][positionDuCurseur:]
                )
                positionDuCurseur += 1
                miseAJourInterface()
            except AttributeError:
                pass

    def toucheRelachee(touche):
        nonlocal majEnfoncee, altEnfoncee
        if touche in [keyboard.Key.shift, keyboard.Key.shift_r]:
            majEnfoncee = False
        elif touche in [keyboard.Key.alt, keyboard.Key.alt_r]:
            altEnfoncee = False

    miseAJourInterface()
    connexionClavier = keyboard.Listener(
        on_press=toucheDeclenchee, on_release=toucheRelachee, suppress=Global.BLOQUER_INPUTS
    )
    connexionClavier.start()

    while True:
        if termine:
            if annulee == True:
                if sortieAvecEchap == True:
                    break
            elif functionDeValidation is not None:
                resultatValidation = functionDeValidation(*reponses)
                if resultatValidation is True:
                    break
                else:
                    erreurPrecedente, termine = (
                        resultatValidation,
                        False,
                    )
                    miseAJourInterface()
            else:
                break
        time.sleep(0.1)

    connexionClavier.stop()
    return reponses


def inputFichier(
    ecranAffichage="gauche",
    titre="Sélection de fichier",
    cheminDeBase="./Data/",
    sortieAvecEchap=True,
    formatsAcceptes=["*"],
):
    """
    Affiche une interface interactive pour la sélection de fichiers via le clavier.

    Permet à l'utilisateur de naviguer dans le système de fichiers et de sélectionner un fichier,
    avec support clavier.

    Paramètres:
        ecranAffichage (str, optional): Position d'affichage du panneau ("gauche" ou "droite") (par défaut "gauche").
        titre (str, optional): Titre de la boîte de dialogue. (par défaut "Sélection de fichier").
        cheminDeBase (str, optional): Chemin de départ pour la navigation. (par défaut "./Data/").
        sortieAvecEchap (bool, optional): Permet l'annulation avec la touche Échap. (par défaut True).
        formatsAcceptes (list, optional): Liste des extensions de fichiers acceptées (par défaut ["*"] pour tous les formats).

    Retourne:
        str ou None: Chemin complet du fichier sélectionné, ou None si annulé avec Échap.
    """
    cheminActuel = pathlib.Path(cheminDeBase).resolve()

    while True:
        listeOptions = []
        if cheminActuel.parent != cheminActuel:
            listeOptions.append({"nom": "⤷ .."})

        for element in sorted(cheminActuel.iterdir()):
            if element.is_dir():
                listeOptions.append({"nom": f"[blue]{element.name}/[/blue]", "type": "dossier"})
        for element in sorted(cheminActuel.iterdir()):
            if element.is_file() and (
                "*" in formatsAcceptes or any(element.name.endswith(ext) for ext in formatsAcceptes)
            ):
                listeOptions.append({"nom": f"{element.name}", "type": "fichier"})

        optionChoisie = afficherMenu(
            listeOptions,
            titre=f"{elementTexteVersString(titre)} - {str(cheminActuel)}",
            afficherLesDescriptions=False,
            sortieAvecEchap=sortieAvecEchap,
            boucle=False,
            ecranAffichage=ecranAffichage,
        )
        if optionChoisie is None:
            return None

        nomOption, typeOption = optionChoisie["nom"], optionChoisie.get("type")
        nomOption = enleverFormattage(nomOption).rstrip(
            "/"
        )  # Enlever le formattage et le slash final pour les dossiers
        if nomOption == "⤷ ..":
            cheminActuel = cheminActuel.parent
        elif typeOption == "dossier":
            cheminActuel = cheminActuel / nomOption
        elif typeOption == "fichier":
            return str(cheminActuel / nomOption)


def formatDateSQLToFR(dateSQL: str) -> str:
    """
    Convertit une date au format SQL (AAAA-MM-JJ) en format français (JJ/MM/AAAA).

    Paramètres:
        dateSQL (str): La date au format SQL (AAAA-MM-JJ).

    Retourne:
        str: La date au format français (JJ/MM/AAAA).
    """
    dateParties = dateSQL.split("-")
    if len(dateParties) != 3:
        return dateSQL
    return f"{dateParties[2]}/{dateParties[1]}/{dateParties[0]}"
