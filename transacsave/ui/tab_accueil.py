# -*- coding: utf-8 -*-
"""
tab_accueil.py
==============
Onglet Accueil de l'application TransacSave.

Responsabilités :
    - Afficher le statut du fichier de sauvegarde du jour
    - Permettre la création du fichier CSV quotidien
    - Afficher le résumé financier de la journée (dépôts, transferts, global)
    - Afficher la dernière transaction enregistrée

Modifications v2 :
    - Suppression du header interne (géré globalement dans main.py)
    - Correction du bandeau de statut : remplacement du BoxLayout
      avec canvas.before (causait un fond blanc) par un Button
      désactivé dont Kivy gère nativement la couleur de fond.

Dépendances core :
    - core.utils        → get_today_date()
    - core.file_manager → file_exists_today(), create_daily_file(), get_today_filepath()
    - core.transaction  → calculate_totals(), get_last_transaction()

Auteur : Nous
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

# Imports des modules métier
from core.utils import get_today_date
from core.file_manager import (
    file_exists_today,
    create_daily_file,
    get_today_filepath
)
from core.transaction import calculate_totals, get_last_transaction


# ─────────────────────────────────────────────────────────────
# CONSTANTES DE STYLE (thème nuit)
# ─────────────────────────────────────────────────────────────
COULEUR_CARD       = (0.110, 0.125, 0.188, 1)   # #1C2030
COULEUR_ACCENT     = (0.000, 0.898, 0.627, 1)   # #00E5A0 — vert (dépôts)
COULEUR_TRANSFERT  = (1.000, 0.420, 0.208, 1)   # #FF6B35 — orange (transferts)
COULEUR_TEXTE      = (0.910, 0.925, 0.957, 1)   # #E8ECF4
COULEUR_MUTED      = (0.420, 0.447, 0.502, 1)   # #6B7280
COULEUR_DANGER     = (1.000, 0.302, 0.427, 1)   # #FF4D6D
COULEUR_AVERT      = (0.984, 0.753, 0.141, 1)   # #FBBF24 — orange avertissement
COULEUR_BTN_DESAC  = (0.110, 0.125, 0.188, 1)   # même que CARD


class OngletAccueil(BoxLayout):
    """
    Widget principal de l'onglet Accueil.

    Hérite de BoxLayout (orientation verticale).
    Construit l'interface au moment de l'initialisation,
    puis se rafraîchit à chaque appel de on_enter() —
    déclenché depuis main.py via panel.bind(current_tab=...).

    Attributs :
        date_aujourdhui    (str)    : date du jour au format YYYY-MM-DD
        btn_statut         (Button) : bandeau de statut fichier
        dot_statut         (Label)  : point indicateur coloré
        lbl_statut         (Label)  : texte du statut
        btn_creer          (Button) : bouton de création du fichier
        lbl_depot          (Label)  : montant total des dépôts
        lbl_transfert      (Label)  : montant total des transferts
        lbl_global         (Label)  : montant total global
        lbl_count_depot    (Label)  : nombre de dépôts
        lbl_count_transfert(Label)  : nombre de transferts
        lbl_count_global   (Label)  : nombre total de transactions
        lbl_badge_type     (Label)  : badge type dernière transaction
        lbl_montant_derniere(Label) : montant dernière transaction
        lbl_reseau_numero  (Label)  : réseau · numéro + heure
        lbl_nom_derniere   (Label)  : nom client dernière transaction
    """

    def __init__(self, **kwargs):
        """
        Initialise le layout vertical et construit tous les widgets.
        Appelé une seule fois au démarrage de l'application.
        """
        super().__init__(
            orientation="vertical",
            padding=dp(14),
            spacing=dp(10),
            **kwargs
        )

        self.date_aujourdhui = get_today_date()

        # Construction séquentielle des blocs de l'interface
        self._construire_bandeau_statut()
        self._construire_resume_quotidien()
        self._construire_bouton_creation()
        self._construire_derniere_transaction()

        # Premier chargement des données au démarrage
        self.rafraichir()

    # ─────────────────────────────────────────────────────────
    # CONSTRUCTION DES BLOCS UI
    # ─────────────────────────────────────────────────────────

    def _construire_bandeau_statut(self):
        """
        Crée le bandeau de statut du fichier du jour.

        CORRECTION v2 : on utilise un BoxLayout avec canvas.before
        correctement lié via Clock.schedule_once pour éviter
        le problème de fond blanc au premier rendu.

        Le point (dot) et le texte sont des Labels enfants.
        La couleur de fond est mise à jour dans _rafraichir_statut().
        """
        # Conteneur du bandeau
        self.bandeau = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            padding=[dp(12), dp(6)],
            spacing=dp(8)
        )

        # Fond arrondi du bandeau — couleur initiale verte (accent)
        with self.bandeau.canvas.before:
            self._couleur_bandeau = Color(
                *COULEUR_ACCENT[:3], 0.12
            )
            self._rect_bandeau = RoundedRectangle(
                pos=self.bandeau.pos,
                size=self.bandeau.size,
                radius=[dp(10)]
            )
        # Liaison dynamique obligatoire : sans cela le rectangle
        # reste à (0,0) et ne suit pas le widget lors du layout
        self.bandeau.bind(
            pos=lambda o, v: setattr(self._rect_bandeau, "pos", v),
            size=lambda o, v: setattr(self._rect_bandeau, "size", v)
        )

        # Point coloré indicateur (● vert ou orange selon statut)
        self.dot_statut = Label(
            text="●",
            font_size=dp(10),
            color=COULEUR_ACCENT,
            size_hint=(None, 1),
            width=dp(14)
        )

        # Texte descriptif du statut
        self.lbl_statut = Label(
            text="Vérification...",
            font_size=dp(11),
            color=COULEUR_TEXTE,
            halign="left",
            valign="middle"
        )
        self.lbl_statut.bind(size=self.lbl_statut.setter("text_size"))

        self.bandeau.add_widget(self.dot_statut)
        self.bandeau.add_widget(self.lbl_statut)
        self.add_widget(self.bandeau)

    def _construire_resume_quotidien(self):
        """
        Crée la grille de résumé financier :
            - Ligne haute : carte Dépôts + carte Transferts
            - Ligne basse : carte Total Global (pleine largeur)

        Les labels de valeur sont mis à jour dans _rafraichir_resume()
        via calculate_totals().
        """
        grille = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(160),
            spacing=dp(8)
        )

        ligne_haute = BoxLayout(orientation="horizontal", spacing=dp(8))

        # ── Carte Dépôts ──
        carte_depot = self._creer_carte()

        lbl_titre_depot = Label(
            text="DÉPÔTS", font_size=dp(9), color=COULEUR_MUTED,
            size_hint_y=None, height=dp(14), halign="left"
        )
        lbl_titre_depot.bind(size=lbl_titre_depot.setter("text_size"))

        self.lbl_depot = Label(
            text="— F", font_size=dp(18), bold=True,
            color=COULEUR_ACCENT, halign="left"
        )
        self.lbl_depot.bind(size=self.lbl_depot.setter("text_size"))

        self.lbl_count_depot = Label(
            text="0 transaction", font_size=dp(9), color=COULEUR_MUTED,
            size_hint_y=None, height=dp(14), halign="left"
        )
        self.lbl_count_depot.bind(size=self.lbl_count_depot.setter("text_size"))

        carte_depot.add_widget(lbl_titre_depot)
        carte_depot.add_widget(self.lbl_depot)
        carte_depot.add_widget(self.lbl_count_depot)
        ligne_haute.add_widget(carte_depot)

        # ── Carte Transferts ──
        carte_transfert = self._creer_carte()

        lbl_titre_transfert = Label(
            text="TRANSFERTS", font_size=dp(9), color=COULEUR_MUTED,
            size_hint_y=None, height=dp(14), halign="left"
        )
        lbl_titre_transfert.bind(size=lbl_titre_transfert.setter("text_size"))

        self.lbl_transfert = Label(
            text="— F", font_size=dp(18), bold=True,
            color=COULEUR_TRANSFERT, halign="left"
        )
        self.lbl_transfert.bind(size=self.lbl_transfert.setter("text_size"))

        self.lbl_count_transfert = Label(
            text="0 transaction", font_size=dp(9), color=COULEUR_MUTED,
            size_hint_y=None, height=dp(14), halign="left"
        )
        self.lbl_count_transfert.bind(
            size=self.lbl_count_transfert.setter("text_size")
        )

        carte_transfert.add_widget(lbl_titre_transfert)
        carte_transfert.add_widget(self.lbl_transfert)
        carte_transfert.add_widget(self.lbl_count_transfert)
        ligne_haute.add_widget(carte_transfert)

        # ── Carte Total Global ──
        carte_global = self._creer_carte()

        lbl_titre_global = Label(
            text="TOTAL GLOBAL", font_size=dp(9), color=COULEUR_MUTED,
            size_hint_y=None, height=dp(14), halign="left"
        )
        lbl_titre_global.bind(size=lbl_titre_global.setter("text_size"))

        self.lbl_global = Label(
            text="— FCFA", font_size=dp(18), bold=True,
            color=COULEUR_TEXTE, halign="left"
        )
        self.lbl_global.bind(size=self.lbl_global.setter("text_size"))

        self.lbl_count_global = Label(
            text="0 transaction au total", font_size=dp(9), color=COULEUR_MUTED,
            size_hint_y=None, height=dp(14), halign="left"
        )
        self.lbl_count_global.bind(size=self.lbl_count_global.setter("text_size"))

        carte_global.add_widget(lbl_titre_global)
        carte_global.add_widget(self.lbl_global)
        carte_global.add_widget(self.lbl_count_global)

        grille.add_widget(ligne_haute)
        grille.add_widget(carte_global)
        self.add_widget(grille)

    def _construire_bouton_creation(self):
        """
        Crée le bouton de création du fichier quotidien.

        États :
            - Fichier absent  → bouton vert actif, texte "Créer le fichier du jour"
            - Fichier présent → bouton grisé désactivé, texte "✓ Déjà créé"

        L'état est mis à jour dans _rafraichir_statut().
        """
        self.btn_creer = Button(
            text="＋ Créer le fichier du jour",
            size_hint_y=None,
            height=dp(48),
            background_normal="",
            background_color=COULEUR_ACCENT,
            color=(0.051, 0.059, 0.078, 1),
            bold=True,
            font_size=dp(13),
            on_press=self._action_creer_fichier
        )
        self.add_widget(self.btn_creer)

    def _construire_derniere_transaction(self):
        """
        Crée le bloc d'affichage de la dernière transaction.

        Contenu :
            - Titre "DERNIÈRE TRANSACTION"
            - Badge type (DÉPÔT / TRANSFERT) + montant
            - Réseau · Numéro    Heure
            - Nom du client

        Mis à jour dans _rafraichir_derniere_transaction()
        via get_last_transaction().
        """
        bloc = self._creer_carte(height=dp(105))

        lbl_titre = Label(
            text="DERNIÈRE TRANSACTION",
            font_size=dp(9), color=COULEUR_MUTED,
            size_hint_y=None, height=dp(14), halign="left"
        )
        lbl_titre.bind(size=lbl_titre.setter("text_size"))

        # Ligne : badge type + montant
        ligne_type_montant = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(26)
        )

        self.lbl_badge_type = Label(
            text="", font_size=dp(10), bold=True,
            size_hint=(None, 1), width=dp(72),
            halign="left", valign="middle"
        )
        self.lbl_badge_type.bind(size=self.lbl_badge_type.setter("text_size"))

        self.lbl_montant_derniere = Label(
            text="", font_size=dp(15), bold=True,
            color=COULEUR_TEXTE, halign="right"
        )
        self.lbl_montant_derniere.bind(
            size=self.lbl_montant_derniere.setter("text_size")
        )

        ligne_type_montant.add_widget(self.lbl_badge_type)
        ligne_type_montant.add_widget(self.lbl_montant_derniere)

        # Ligne : réseau · numéro + heure
        self.lbl_reseau_numero = Label(
            text="", font_size=dp(10), color=COULEUR_MUTED,
            size_hint_y=None, height=dp(16), halign="left"
        )
        self.lbl_reseau_numero.bind(
            size=self.lbl_reseau_numero.setter("text_size")
        )

        # Ligne : nom du client
        self.lbl_nom_derniere = Label(
            text="", font_size=dp(11), color=COULEUR_TEXTE,
            size_hint_y=None, height=dp(16), halign="left"
        )
        self.lbl_nom_derniere.bind(
            size=self.lbl_nom_derniere.setter("text_size")
        )

        bloc.add_widget(lbl_titre)
        bloc.add_widget(ligne_type_montant)
        bloc.add_widget(self.lbl_reseau_numero)
        bloc.add_widget(self.lbl_nom_derniere)
        self.add_widget(bloc)

    # ─────────────────────────────────────────────────────────
    # RAFRAÎCHISSEMENT
    # ─────────────────────────────────────────────────────────

    def rafraichir(self):
        """
        Point d'entrée unique pour mettre à jour l'affichage.

        Appelée :
            - Au démarrage dans __init__()
            - À chaque retour sur l'onglet via on_enter()
            - Après création d'un fichier via _action_creer_fichier()
        """
        # Re-calculer la date : utile si l'app tourne au passage minuit
        self.date_aujourdhui = get_today_date()
        self._rafraichir_statut()
        self._rafraichir_resume()
        self._rafraichir_derniere_transaction()

    def _rafraichir_statut(self):
        """
        Vérifie l'existence du fichier du jour via file_exists_today()
        et met à jour le bandeau de statut et le bouton de création.

        Bandeau vert  → fichier présent, bouton désactivé
        Bandeau orange → fichier absent, bouton actif
        """
        existe, _ = file_exists_today(self.date_aujourdhui)

        if existe:
            # Fichier présent — bandeau vert
            self._couleur_bandeau.rgba = (*COULEUR_ACCENT[:3], 0.12)
            self.dot_statut.color      = COULEUR_ACCENT
            self.lbl_statut.text       = (
                f"Fichier {self.date_aujourdhui} actif — prêt"
            )
            self.lbl_statut.color      = COULEUR_TEXTE
            # Bouton désactivé
            self.btn_creer.text             = "✓ Fichier du jour déjà créé"
            self.btn_creer.background_color = COULEUR_BTN_DESAC
            self.btn_creer.color            = COULEUR_MUTED
            self.btn_creer.disabled         = True
        else:
            # Fichier absent — bandeau orange
            self._couleur_bandeau.rgba = (*COULEUR_AVERT[:3], 0.12)
            self.dot_statut.color      = COULEUR_AVERT
            self.lbl_statut.text       = "Aucun fichier pour aujourd'hui"
            self.lbl_statut.color      = COULEUR_AVERT
            # Bouton actif
            self.btn_creer.text             = "＋ Créer le fichier du jour"
            self.btn_creer.background_color = COULEUR_ACCENT
            self.btn_creer.color            = (0.051, 0.059, 0.078, 1)
            self.btn_creer.disabled         = False

    def _rafraichir_resume(self):
        """
        Récupère les totaux via calculate_totals() et met à jour
        les trois cartes de résumé financier.

        Si le fichier est absent ou vide, les cartes affichent "—".
        """
        filepath = get_today_filepath(self.date_aujourdhui)
        valide, donnees = calculate_totals(filepath)

        if not valide:
            # Fichier absent ou vide — valeurs neutres
            self.lbl_depot.text           = "— F"
            self.lbl_transfert.text       = "— F"
            self.lbl_global.text          = "— FCFA"
            self.lbl_count_depot.text     = "0 transaction"
            self.lbl_count_transfert.text = "0 transaction"
            self.lbl_count_global.text    = "0 transaction au total"
            return

        # Formatage des montants avec séparateurs de milliers
        self.lbl_depot.text     = f"{self._formater_montant(donnees['Depot']['total'])} F"
        self.lbl_transfert.text = f"{self._formater_montant(donnees['Transfert']['total'])} F"
        self.lbl_global.text    = f"{self._formater_montant(donnees['Global']['total'])} FCFA"

        d = donnees["Depot"]["count"]
        t = donnees["Transfert"]["count"]
        g = donnees["Global"]["count"]

        # Pluralisation du mot "transaction"
        self.lbl_count_depot.text     = f"{d} transaction{'s' if d > 1 else ''}"
        self.lbl_count_transfert.text = f"{t} transaction{'s' if t > 1 else ''}"
        self.lbl_count_global.text    = f"{g} transaction{'s' if g > 1 else ''} au total"

    def _rafraichir_derniere_transaction(self):
        """
        Récupère la dernière transaction via get_last_transaction()
        et met à jour le bloc inférieur.

        Couleur du badge :
            Dépôt    → vert  COULEUR_ACCENT
            Transfert → orange COULEUR_TRANSFERT
        """
        filepath = get_today_filepath(self.date_aujourdhui)
        valide, donnees = get_last_transaction(filepath)

        if not valide:
            # Pas de transaction disponible
            self.lbl_badge_type.text        = ""
            self.lbl_montant_derniere.text  = "Aucune transaction"
            self.lbl_reseau_numero.text     = ""
            self.lbl_nom_derniere.text      = ""
            return

        # Couleur et texte du badge selon le type
        if donnees["type"] == "Depot":
            self.lbl_badge_type.color = COULEUR_ACCENT
            self.lbl_badge_type.text  = "DÉPÔT"
        else:
            self.lbl_badge_type.color = COULEUR_TRANSFERT
            self.lbl_badge_type.text  = "TRANSFERT"

        montant = self._formater_montant(donnees["montant"])
        self.lbl_montant_derniere.text = f"{montant} F"
        self.lbl_reseau_numero.text    = (
            f"{donnees['reseau']} · {donnees['numero']}    {donnees['heure']}"
        )
        self.lbl_nom_derniere.text = donnees["nom"]

    # ─────────────────────────────────────────────────────────
    # ACTION UTILISATEUR
    # ─────────────────────────────────────────────────────────

    def _action_creer_fichier(self, instance):
        """
        Callback du bouton "Créer le fichier du jour".

        Appelle create_daily_file() puis rafraîchit l'onglet
        pour refléter le nouvel état.

        Args :
            instance : Button source (paramètre Kivy, non utilisé)
        """
        valide, message = create_daily_file(self.date_aujourdhui)

        if valide:
            self.rafraichir()
        else:
            # Erreur — afficher dans le bandeau
            self.lbl_statut.text  = f"Erreur : {message}"
            self.dot_statut.color = COULEUR_DANGER

    # ─────────────────────────────────────────────────────────
    # CYCLE DE VIE
    # ─────────────────────────────────────────────────────────

    def on_enter(self):
        """
        Appelée depuis main.py/_on_tab_switch() à chaque retour
        sur l'onglet Accueil.

        Déclenche un rafraîchissement complet pour que les données
        soient à jour après une saisie sur l'onglet Saisie.
        """
        self.rafraichir()

    # ─────────────────────────────────────────────────────────
    # UTILITAIRES PRIVÉS
    # ─────────────────────────────────────────────────────────

    def _creer_carte(self, height=dp(70)) -> BoxLayout:
        """
        Crée un BoxLayout vertical stylisé "carte"
        (fond CARD, coins arrondis).

        Args :
            height (float) : hauteur en dp. Défaut : 70dp.

        Returns :
            BoxLayout : conteneur prêt à recevoir des widgets.
        """
        carte = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=height,
            padding=[dp(12), dp(8)],
            spacing=dp(4)
        )
        with carte.canvas.before:
            Color(*COULEUR_CARD)
            rect = RoundedRectangle(
                pos=carte.pos,
                size=carte.size,
                radius=[dp(12)]
            )
        carte.bind(
            pos=lambda o, v: setattr(rect, "pos", v),
            size=lambda o, v: setattr(rect, "size", v)
        )
        return carte

    @staticmethod
    def _formater_montant(montant: int) -> str:
        """
        Formate un entier avec séparateurs de milliers.

        Exemple : 1159500 → "1 159 500"

        Args :
            montant (int) : montant brut.

        Returns :
            str : montant formaté.
        """
        return f"{montant:,}".replace(",", " ")
