# -*- coding: utf-8 -*-
"""
tab_saisie.py
=============
Onglet Saisie de l'application TransacSave.

Responsabilités :
    - Présenter le formulaire de saisie d'une transaction
    - Gérer la sélection du type (Dépôt / Transfert)
    - Gérer la sélection du réseau (MTN / Orange / Camtel)
    - Valider les champs en temps réel (numéro, montant)
    - Appeler add_transaction() pour enregistrer dans le CSV
    - Afficher le retour visuel (succès / erreur)
    - Réinitialiser partiellement le formulaire après enregistrement

Modifications v2 :
    - Suppression du header interne (géré globalement dans main.py)
    - on_enter() reste inchangé fonctionnellement mais est maintenant
      appelé depuis main.py/_on_tab_switch()

Dépendances core :
    - core.utils        → get_today_date(), get_current_time()
    - core.file_manager → file_exists_today(), get_today_filepath()
    - core.transaction  → add_transaction()

Auteur : Nous
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.clock import Clock

from core.utils import get_today_date, get_current_time
from core.file_manager import file_exists_today, get_today_filepath
from core.transaction import add_transaction


# ─────────────────────────────────────────────────────────────
# CONSTANTES DE STYLE (thème nuit)
# ─────────────────────────────────────────────────────────────
COULEUR_CARD       = (0.110, 0.125, 0.188, 1)
COULEUR_ACCENT     = (0.000, 0.898, 0.627, 1)   # #00E5A0 — vert dépôt
COULEUR_TRANSFERT  = (1.000, 0.420, 0.208, 1)   # #FF6B35 — orange transfert
COULEUR_TEXTE      = (0.910, 0.925, 0.957, 1)
COULEUR_MUTED      = (0.420, 0.447, 0.502, 1)
COULEUR_DANGER     = (1.000, 0.302, 0.427, 1)   # #FF4D6D
COULEUR_MTN        = (1.000, 0.800, 0.000, 1)   # #FFCC00 — jaune MTN
COULEUR_ORANGE_NET = (1.000, 0.478, 0.000, 1)   # #FF7A00 — orange Orange
COULEUR_CAMTEL     = (0.290, 0.565, 0.886, 1)   # #4A90E2 — bleu Camtel


class OngletSaisie(BoxLayout):
    """
    Widget principal de l'onglet Saisie.

    Le formulaire est logé dans un ScrollView pour s'adapter
    aux petits écrans.

    Attributs :
        type_selectionne   (str)       : "Depot" ou "Transfert"
        reseau_selectionne (str)       : "MTN", "Orange" ou "Camtel"
        btn_depot          (Button)    : sélecteur type Dépôt
        btn_transfert      (Button)    : sélecteur type Transfert
        btn_mtn            (Button)    : chip réseau MTN
        btn_orange         (Button)    : chip réseau Orange
        btn_camtel         (Button)    : chip réseau Camtel
        input_numero       (TextInput) : champ numéro
        input_nom          (TextInput) : champ nom
        input_montant      (TextInput) : champ montant
        lbl_hint_numero    (Label)     : retour validation numéro
        lbl_hint_montant   (Label)     : retour validation montant
        lbl_heure          (Label)     : affichage heure automatique
        lbl_feedback       (Label)     : message succès/erreur
        btn_enregistrer    (Button)    : bouton enregistrement
        bloc_avert         (BoxLayout) : avertissement fichier absent
        lbl_section_nom    (Label)     : label dynamique champ Nom
    """

    def __init__(self, **kwargs):
        """
        Initialise le layout et construit le formulaire.
        Sélections par défaut : type = Dépôt, réseau = MTN.
        """
        super().__init__(orientation="vertical", **kwargs)

        self.type_selectionne   = "Depot"
        self.reseau_selectionne = "MTN"

        # ScrollView pour les petits écrans
        scroll = ScrollView(do_scroll_x=False)
        self.conteneur_form = BoxLayout(
            orientation="vertical",
            padding=dp(14),
            spacing=dp(10),
            size_hint_y=None
        )
        self.conteneur_form.bind(
            minimum_height=self.conteneur_form.setter("height")
        )

        # Construction du formulaire
        self._construire_bloc_avertissement()
        self._construire_selecteur_type()
        self._construire_selecteur_reseau()
        self._construire_champ_numero()
        self._construire_champ_nom()
        self._construire_champ_montant()
        self._construire_champ_heure()
        self._construire_bouton_enregistrer()
        self._construire_label_feedback()

        scroll.add_widget(self.conteneur_form)
        self.add_widget(scroll)

    # ─────────────────────────────────────────────────────────
    # CONSTRUCTION DES BLOCS UI
    # ─────────────────────────────────────────────────────────

    def _construire_bloc_avertissement(self):
        """
        Crée un bandeau d'avertissement affiché quand le fichier
        du jour n'existe pas.

        Masqué (opacity=0) par défaut.
        Rendu visible dans on_enter() si le fichier est absent.
        Le bouton Enregistrer est simultanément désactivé.
        """
        self.bloc_avert = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            padding=[dp(10), dp(0)],
            spacing=dp(8),
            opacity=0
        )

        with self.bloc_avert.canvas.before:
            Color(1.000, 0.302, 0.427, 0.10)
            rect = RoundedRectangle(
                pos=self.bloc_avert.pos,
                size=self.bloc_avert.size,
                radius=[dp(8)]
            )
        self.bloc_avert.bind(
            pos=lambda o, v: setattr(rect, "pos", v),
            size=lambda o, v: setattr(rect, "size", v)
        )

        lbl = Label(
            text="⚠  Aucun fichier du jour — créez-en un depuis l'onglet Accueil",
            font_size=dp(10),
            color=COULEUR_DANGER,
            halign="left",
            valign="middle"
        )
        lbl.bind(size=lbl.setter("text_size"))

        self.bloc_avert.add_widget(lbl)
        self.conteneur_form.add_widget(self.bloc_avert)

    def _construire_selecteur_type(self):
        """
        Crée la section "TYPE DE TRANSACTION" avec deux boutons :
            - Dépôt    → vert   quand actif
            - Transfert → orange quand actif

        Sélection par défaut : Dépôt.
        """
        self.conteneur_form.add_widget(
            self._creer_label_section("TYPE DE TRANSACTION")
        )

        ligne = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8)
        )

        self.btn_depot = Button(
            text="⬇  Dépôt",
            background_normal="",
            font_size=dp(13),
            bold=True,
            on_press=self._selectionner_depot
        )
        self.btn_transfert = Button(
            text="↗  Transfert",
            background_normal="",
            font_size=dp(13),
            bold=True,
            on_press=self._selectionner_transfert
        )

        ligne.add_widget(self.btn_depot)
        ligne.add_widget(self.btn_transfert)
        self.conteneur_form.add_widget(ligne)

        # Style initial : Dépôt actif
        self._appliquer_style_type()

    def _construire_selecteur_reseau(self):
        """
        Crée la section "RÉSEAU" avec trois chips colorées :
            - MTN    → jaune  (#FFCC00)
            - Orange → orange (#FF7A00)
            - Camtel → bleu   (#4A90E2)

        Sélection par défaut : MTN.
        """
        self.conteneur_form.add_widget(
            self._creer_label_section("RÉSEAU")
        )

        ligne = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(6)
        )

        self.btn_mtn    = Button(
            text="MTN",    background_normal="", bold=True,
            font_size=dp(12),
            on_press=lambda x: self._selectionner_reseau("MTN")
        )
        self.btn_orange = Button(
            text="Orange", background_normal="", bold=True,
            font_size=dp(12),
            on_press=lambda x: self._selectionner_reseau("Orange")
        )
        self.btn_camtel = Button(
            text="Camtel", background_normal="", bold=True,
            font_size=dp(12),
            on_press=lambda x: self._selectionner_reseau("Camtel")
        )

        ligne.add_widget(self.btn_mtn)
        ligne.add_widget(self.btn_orange)
        ligne.add_widget(self.btn_camtel)
        self.conteneur_form.add_widget(ligne)

        # Style initial : MTN actif
        self._appliquer_style_reseau()

    def _construire_champ_numero(self):
        """
        Crée le champ numéro de téléphone.

        - Clavier numérique (input_type="number")
        - Validation en temps réel via format_phone_number()
        - Message de retour affiché dans lbl_hint_numero
        """
        self.conteneur_form.add_widget(
            self._creer_label_section("NUMÉRO  *")
        )

        self.input_numero = TextInput(
            hint_text="Ex : 697124538",
            multiline=False,
            input_type="number",
            size_hint_y=None,
            height=dp(44),
            background_color=COULEUR_CARD,
            foreground_color=COULEUR_TEXTE,
            hint_text_color=COULEUR_MUTED,
            cursor_color=COULEUR_ACCENT,
            font_size=dp(14)
        )
        self.input_numero.bind(text=self._valider_numero_temps_reel)

        self.lbl_hint_numero = Label(
            text="", font_size=dp(10),
            size_hint_y=None, height=dp(14), halign="left"
        )
        self.lbl_hint_numero.bind(size=self.lbl_hint_numero.setter("text_size"))

        self.conteneur_form.add_widget(self.input_numero)
        self.conteneur_form.add_widget(self.lbl_hint_numero)

    def _construire_champ_nom(self):
        """
        Crée le champ nom du client.

        Le label de section change dynamiquement :
            - "NOM DU CLIENT  *"          si type = Dépôt (obligatoire)
            - "NOM DU CLIENT  (optionnel)" si type = Transfert
        """
        self.lbl_section_nom = self._creer_label_section("NOM DU CLIENT  *")
        self.conteneur_form.add_widget(self.lbl_section_nom)

        self.input_nom = TextInput(
            hint_text="Ex : Jean-Paul Mbarga",
            multiline=False,
            size_hint_y=None,
            height=dp(44),
            background_color=COULEUR_CARD,
            foreground_color=COULEUR_TEXTE,
            hint_text_color=COULEUR_MUTED,
            cursor_color=COULEUR_ACCENT,
            font_size=dp(14)
        )
        self.conteneur_form.add_widget(self.input_nom)

    def _construire_champ_montant(self):
        """
        Crée le champ montant en FCFA.

        - Clavier numérique
        - Validation en temps réel : 100 ≤ montant ≤ 1 000 000
        - Message de retour dans lbl_hint_montant
        """
        self.conteneur_form.add_widget(
            self._creer_label_section("MONTANT (FCFA)  *")
        )

        self.input_montant = TextInput(
            hint_text="Ex : 75000",
            multiline=False,
            input_type="number",
            size_hint_y=None,
            height=dp(44),
            background_color=COULEUR_CARD,
            foreground_color=COULEUR_TEXTE,
            hint_text_color=COULEUR_MUTED,
            cursor_color=COULEUR_ACCENT,
            font_size=dp(14)
        )
        self.input_montant.bind(text=self._valider_montant_temps_reel)

        self.lbl_hint_montant = Label(
            text="", font_size=dp(10),
            size_hint_y=None, height=dp(14), halign="left"
        )
        self.lbl_hint_montant.bind(
            size=self.lbl_hint_montant.setter("text_size")
        )

        self.conteneur_form.add_widget(self.input_montant)
        self.conteneur_form.add_widget(self.lbl_hint_montant)

    def _construire_champ_heure(self):
        """
        Crée le champ heure en lecture seule.

        L'heure est automatiquement renseignée par get_current_time()
        lors de l'appui sur "Enregistrer". Ce champ est informatif.
        """
        self.conteneur_form.add_widget(
            self._creer_label_section("HEURE  (automatique)")
        )

        self.lbl_heure = Label(
            text=get_current_time(),
            font_size=dp(13),
            color=COULEUR_MUTED,
            size_hint_y=None,
            height=dp(44),
            halign="left",
            valign="middle"
        )
        self.lbl_heure.bind(size=self.lbl_heure.setter("text_size"))
        self.conteneur_form.add_widget(self.lbl_heure)

    def _construire_bouton_enregistrer(self):
        """
        Crée le bouton principal d'enregistrement.

        On_press → _action_enregistrer() :
            1. Vérifie le fichier du jour
            2. Collecte les champs
            3. Appelle add_transaction()
            4. Affiche le feedback
            5. Réinitialise partiellement le formulaire si succès
        """
        self.btn_enregistrer = Button(
            text="Enregistrer la transaction",
            size_hint_y=None,
            height=dp(52),
            background_normal="",
            background_color=COULEUR_ACCENT,
            color=(0.051, 0.059, 0.078, 1),
            bold=True,
            font_size=dp(14),
            on_press=self._action_enregistrer
        )
        self.conteneur_form.add_widget(self.btn_enregistrer)

    def _construire_label_feedback(self):
        """
        Crée le label de retour affiché sous le bouton.

        Vide par défaut.
        Vert (succès) ou rouge (erreur) après un enregistrement.
        Effacé automatiquement après 3 secondes via Clock.
        """
        self.lbl_feedback = Label(
            text="",
            font_size=dp(12),
            size_hint_y=None,
            height=dp(30),
            halign="center",
            valign="middle"
        )
        self.lbl_feedback.bind(size=self.lbl_feedback.setter("text_size"))
        self.conteneur_form.add_widget(self.lbl_feedback)

    # ─────────────────────────────────────────────────────────
    # SÉLECTION TYPE
    # ─────────────────────────────────────────────────────────

    def _selectionner_depot(self, instance):
        """
        Active le type "Dépôt".
            - Bouton Dépôt → vert actif
            - Bouton Transfert → grisé
            - Label Nom → obligatoire (*)

        Args :
            instance : Button source (Kivy, non utilisé)
        """
        self.type_selectionne     = "Depot"
        self.lbl_section_nom.text = "NOM DU CLIENT  *"
        self._appliquer_style_type()

    def _selectionner_transfert(self, instance):
        """
        Active le type "Transfert".
            - Bouton Transfert → orange actif
            - Bouton Dépôt → grisé
            - Label Nom → optionnel

        Args :
            instance : Button source (Kivy, non utilisé)
        """
        self.type_selectionne     = "Transfert"
        self.lbl_section_nom.text = "NOM DU CLIENT  (optionnel)"
        self._appliquer_style_type()

    def _appliquer_style_type(self):
        """
        Met à jour les couleurs des boutons Dépôt / Transfert
        selon self.type_selectionne.

        Actif   → fond semi-transparent coloré + texte coloré
        Inactif → fond CARD + texte MUTED
        """
        if self.type_selectionne == "Depot":
            self.btn_depot.background_color    = (*COULEUR_ACCENT[:3], 0.15)
            self.btn_depot.color               = COULEUR_ACCENT
            self.btn_transfert.background_color = COULEUR_CARD
            self.btn_transfert.color            = COULEUR_MUTED
        else:
            self.btn_transfert.background_color = (*COULEUR_TRANSFERT[:3], 0.15)
            self.btn_transfert.color            = COULEUR_TRANSFERT
            self.btn_depot.background_color     = COULEUR_CARD
            self.btn_depot.color                = COULEUR_MUTED

    # ─────────────────────────────────────────────────────────
    # SÉLECTION RÉSEAU
    # ─────────────────────────────────────────────────────────

    def _selectionner_reseau(self, reseau: str):
        """
        Enregistre le réseau sélectionné et met à jour les chips.

        Args :
            reseau (str) : "MTN", "Orange" ou "Camtel"
        """
        self.reseau_selectionne = reseau
        self._appliquer_style_reseau()

    def _appliquer_style_reseau(self):
        """
        Applique la couleur propre à chaque réseau sur le chip actif.
        Les chips inactifs retournent au style CARD / MUTED.

        Mapping couleurs :
            MTN    → COULEUR_MTN    (jaune)
            Orange → COULEUR_ORANGE_NET (orange)
            Camtel → COULEUR_CAMTEL (bleu)
        """
        configs = {
            "MTN":    (self.btn_mtn,    COULEUR_MTN),
            "Orange": (self.btn_orange, COULEUR_ORANGE_NET),
            "Camtel": (self.btn_camtel, COULEUR_CAMTEL),
        }
        for nom, (btn, couleur) in configs.items():
            if nom == self.reseau_selectionne:
                btn.background_color = (*couleur[:3], 0.15)
                btn.color            = couleur
            else:
                btn.background_color = COULEUR_CARD
                btn.color            = COULEUR_MUTED

    # ─────────────────────────────────────────────────────────
    # VALIDATION EN TEMPS RÉEL
    # ─────────────────────────────────────────────────────────

    def _valider_numero_temps_reel(self, instance, valeur):
        """
        Callback déclenché à chaque frappe dans input_numero.
        Appelle format_phone_number() et met à jour lbl_hint_numero.

        Vert si valide (9 chiffres), rouge sinon, vide si champ vide.

        Args :
            instance : TextInput source (Kivy)
            valeur   (str) : valeur courante du champ
        """
        from core.utils import format_phone_number

        if not valeur.strip():
            self.lbl_hint_numero.text = ""
            return

        valide, message = format_phone_number(valeur.strip())
        if valide:
            self.lbl_hint_numero.text  = "✓ Format valide — 9 chiffres"
            self.lbl_hint_numero.color = COULEUR_ACCENT
        else:
            self.lbl_hint_numero.text  = f"✗ {message}"
            self.lbl_hint_numero.color = COULEUR_DANGER

    def _valider_montant_temps_reel(self, instance, valeur):
        """
        Callback déclenché à chaque frappe dans input_montant.
        Appelle format_amount() et met à jour lbl_hint_montant.

        Vert si valide (100–1 000 000), rouge sinon, vide si vide.

        Args :
            instance : TextInput source (Kivy)
            valeur   (str) : valeur courante du champ
        """
        from core.utils import format_amount

        if not valeur.strip():
            self.lbl_hint_montant.text = ""
            return

        valide, message = format_amount(valeur.strip())
        if valide:
            self.lbl_hint_montant.text  = "✓ Montant entre 100 et 1 000 000"
            self.lbl_hint_montant.color = COULEUR_ACCENT
        else:
            self.lbl_hint_montant.text  = f"✗ {message}"
            self.lbl_hint_montant.color = COULEUR_DANGER

    # ─────────────────────────────────────────────────────────
    # ACTION PRINCIPALE
    # ─────────────────────────────────────────────────────────

    def _action_enregistrer(self, instance):
        """
        Callback du bouton "Enregistrer la transaction".

        Étapes :
            1. Vérifie l'existence du fichier du jour
            2. Collecte les valeurs des champs
            3. Construit le dict data pour add_transaction()
            4. Appelle add_transaction(filepath, data)
            5. Affiche le feedback (vert / rouge)
            6. Réinitialise partiellement si succès

        Conservés après succès : type, réseau
        Effacés après succès   : numéro, nom, montant

        Args :
            instance : Button source (Kivy, non utilisé)
        """
        date     = get_today_date()
        filepath = get_today_filepath(date)

        # Étape 1 — Vérification fichier
        existe, _ = file_exists_today(date)
        if not existe:
            self._afficher_feedback(
                "Aucun fichier du jour. Créez-en un depuis l'onglet Accueil.",
                succes=False
            )
            return

        # Étape 2 — Collecte
        numero  = self.input_numero.text.strip()
        nom     = self.input_nom.text.strip()
        montant = self.input_montant.text.strip()

        # Étape 3 — Construction du dict
        # "heure" est laissé vide ici ; add_transaction() l'injecte
        # automatiquement via get_current_time()
        data = {
            "type":    self.type_selectionne,
            "reseau":  self.reseau_selectionne,
            "numero":  numero,
            "nom":     nom,
            "montant": montant,
            "heure":   ""
        }

        # Étape 4 — Appel backend
        valide, message = add_transaction(filepath, data)

        # Étapes 5 et 6
        if valide:
            self._afficher_feedback(f"✓ {message}", succes=True)
            self._reinitialiser_formulaire()
        else:
            self._afficher_feedback(f"✗ {message}", succes=False)

    # ─────────────────────────────────────────────────────────
    # RÉINITIALISATION ET FEEDBACK
    # ─────────────────────────────────────────────────────────

    def _reinitialiser_formulaire(self):
        """
        Efface les champs de saisie après un enregistrement réussi.

        Effacés  : Numéro, Nom, Montant, messages de validation
        Conservés : Type de transaction, Réseau
        """
        self.input_numero.text     = ""
        self.input_nom.text        = ""
        self.input_montant.text    = ""
        self.lbl_hint_numero.text  = ""
        self.lbl_hint_montant.text = ""
        # Actualiser l'heure affichée pour la prochaine saisie
        self.lbl_heure.text = get_current_time()

    def _afficher_feedback(self, message: str, succes: bool):
        """
        Affiche un message sous le bouton Enregistrer.
        Disparaît automatiquement après 3 secondes.

        Args :
            message (str)  : texte à afficher
            succes  (bool) : True → vert, False → rouge
        """
        self.lbl_feedback.text  = message
        self.lbl_feedback.color = COULEUR_ACCENT if succes else COULEUR_DANGER
        Clock.schedule_once(lambda dt: self._effacer_feedback(), 3)

    def _effacer_feedback(self):
        """Efface le message de feedback. Appelée par Clock après 3s."""
        self.lbl_feedback.text = ""

    # ─────────────────────────────────────────────────────────
    # CYCLE DE VIE
    # ─────────────────────────────────────────────────────────

    def on_enter(self):
        """
        Appelée depuis main.py/_on_tab_switch() à chaque arrivée
        sur l'onglet Saisie.

        Vérifie l'existence du fichier du jour :
            - Présent → masque l'avertissement, active le bouton
            - Absent  → affiche l'avertissement, bloque le bouton
        """
        date = get_today_date()
        existe, _ = file_exists_today(date)

        if existe:
            self.bloc_avert.opacity          = 0
            self.btn_enregistrer.disabled    = False
            self.btn_enregistrer.background_color = COULEUR_ACCENT
            self.lbl_heure.text = get_current_time()
        else:
            self.bloc_avert.opacity          = 1
            self.btn_enregistrer.disabled    = True
            self.btn_enregistrer.background_color = COULEUR_CARD

    # ─────────────────────────────────────────────────────────
    # UTILITAIRES PRIVÉS
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _creer_label_section(texte: str) -> Label:
        """
        Crée un label de titre de section stylisé.

        Args :
            texte (str) : texte du label (ex. "NUMÉRO  *")

        Returns :
            Label : label stylisé (10dp, MUTED, majuscules).
        """
        lbl = Label(
            text=texte,
            font_size=dp(10),
            color=COULEUR_MUTED,
            size_hint_y=None,
            height=dp(16),
            halign="left",
            valign="bottom"
        )
        lbl.bind(size=lbl.setter("text_size"))
        return lbl
