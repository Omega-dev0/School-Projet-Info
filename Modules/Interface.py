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
            elif len(speciaux) >= 2 and altEnfoncee:
                return speciaux[2]
            else:
                return speciaux[0]

    if majEnfoncee:
        return caractere.upper()
    return caractere.lower()


def enleverFormattage(content: str) -> str:
    return Text.from_markup(content).plain


def elementTexteVersString(elementTexte: Union[str, Text]) -> str:
    return elementTexte.plain if isinstance(elementTexte, Text) else elementTexte


def mettreAJourPanelGauche(contenuNouveau):
    INTERFACE["gauche"].update(Panel(contenuNouveau, border_style="bold green"))
    LIVE.refresh()


def mettreAJourPanelDroit(contenuNouveau):
    INTERFACE["droite"].update(Panel(contenuNouveau, border_style="bold red"))
    LIVE.refresh()


def afficherMenu(
    options,
    titre="Menu",
    afficherLesDescriptions=True,
    separateurs={},
    sortieAvecEchap=True,
    itemsParPage=10,
    boucle=True,
    ecranAffichage="gauche",
    afficherAideNavigation=False,
):
    indexCurseur, optionSelectionnee, selectionFaite = 0, None, False
    tite = enleverFormattage(titre)

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
                            option["description"],
                            (Global.TEXTES["aideNavigationMenu"] if afficherAideNavigation else ""),
                        )
                    )
            else:
                elementOptions.append("• " + option["nom"])

        if debutIndex + itemsParPage < len(options):
            elementOptions.append(f"[dim]...[/dim]")

        if ecranAffichage == "gauche":
            mettreAJourPanelGauche(Group(elementTitre, *elementOptions))
        else:
            mettreAJourPanelDroit(Group(elementTitre, *elementOptions))

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
    annulee = None

    def toucheDeclenchee(touche):
        nonlocal annulee
        if touche == keyboard.Key.enter:
            annulee = False
        elif touche == keyboard.Key.esc:
            annulee = True

    connexionClavier = keyboard.Listener(on_press=toucheDeclenchee, suppress=Global.BLOQUER_INPUTS)
    connexionClavier.start()

    contenu = Group(Markdown(f"# {elementTexteVersString(titre)}"), message)
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
            itemsParPage=10,
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


def afficherDonnee(ecranAffichage="gauche", titre="", entete=[], donnee=[], attendreAppui=True):
    table = Table(show_header=len(entete) > 0, header_style="bold magenta")
    for col in entete:
        table.add_column(col)

    for ligne in donnee:
        table.add_row(*[str(cell) for cell in ligne])

    attenteTerminee = False

    def appuiTouche(touche):
        nonlocal attenteTerminee
        if touche == keyboard.Key.enter:
            attenteTerminee = True

    if attendreAppui:
        connexionClavier = keyboard.Listener(on_press=appuiTouche, suppress=Global.BLOQUER_INPUTS)
        connexionClavier.start()

    (
        mettreAJourPanelGauche(Group(Markdown(f"# {elementTexteVersString(titre)}"), table))
        if ecranAffichage == "gauche"
        else mettreAJourPanelDroit(Group(Markdown(f"# {elementTexteVersString(titre)}"), table))
    )

    if attendreAppui:
        while not attenteTerminee:
            time.sleep(0.1)
        connexionClavier.stop()


def formatDateSQLToFR(dateSQL: str) -> str:
    dateParties = dateSQL.split("-")
    if len(dateParties) != 3:
        return dateSQL
    return f"{dateParties[2]}/{dateParties[1]}/{dateParties[0]}"
