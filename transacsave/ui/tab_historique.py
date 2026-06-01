# -*- coding: utf-8 -*-
"""
tab_historique.py
=================
Onglet Historique de l'application TransacSave.

Responsabilités :
    - Lister tous les fichiers CSV disponibles dans data/
    - Permettre la sélection d'un fichier par date
    - Afficher les transactions dans un tableau scrollable
    - Proposer une recherche filtrée par champ (Nom, Numéro, Type, Réseau)
    - Afficher les totaux dynamiques selon le filtre actif

Modifications v2 :
    - Suppression du header interne (géré globalement dans main.py)
    - Correction du chargement initial : on_enter() est maintenant
      appelé depuis main.py/_on_tab_switch(), ce qui garantit que
      les données se chargent à chaque sélection de l'onglet.

Dépendances core :
    - core.utils        → get_today_date()
    - core.file_manager → get_all_files(), get_today_filepath(), open_file()
    - core.transaction  → search_transactions(), calculate_totals()

Auteur : Nous
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
from kivy.clock import Clock

from core.utils import get_today_date
from core.file_manager import get_all_files, get_today_filepath, open_file
from core.transaction import search_transactions


# ─────────────────────────────────────────────────────────────
# CONSTANTES DE STYLE (thème nuit)
# ─────────────────────────────────────────────────────────────
COULEUR_CARD       = (0.110, 0.125, 0.188, 1)
COULEUR_ACCENT     = (0.000, 0.898, 0.627, 1)   # #00E5A0 — vert dépôts
COULEUR_TRANSFERT  = (1.000, 0.420, 0.208, 1)   # #FF6B35 — orange transferts
COULEUR_TEXTE      = (0.910, 0.925, 0.957, 1)
COULEUR_MUTED      = (0.420, 0.447, 0.502, 1)
COULEUR_DANGER     = (1.000, 0.302, 0.427, 1)
COULEUR_LIGNE_PAIR = (0.110, 0.125, 0.188, 0.4)  # fond alterné du tableau

# Définition des colonnes du tableau : (titre, size_hint_x)
COLONNES_TABLEAU = [
    ("Type",    0.14),
    ("Réseau",  0.14),
    ("Numéro",  0.26),   # Remplace "Nom" — le nom reste accessible au tap
    ("Montant", 0.22),
    ("Heure",   0.24),
]


class OngletHistorique(BoxLayout):
    """
    Widget principal de l'onglet Historique.

    Structure :
        BoxLayout vertical
        ├── Sélecteur fichier  (Spinner)
        ├── Barre de recherche (TextInput + Spinner + boutons)
        ├── Tableau scrollable (en-tête fixe + GridLayout)
        └── Pied de page       (totaux dépôts / transferts / global)

    Attributs :
        fichier_actif        (str)       : nom du CSV en cours d'affichage
        transactions_actives (list)      : transactions chargées en mémoire
        spinner_fichiers     (Spinner)   : sélecteur de fichier
        input_recherche      (TextInput) : champ de recherche
        spinner_champ        (Spinner)   : sélecteur du champ cible
        grille_tableau       (GridLayout): conteneur des lignes
        lbl_depot_total      (Label)     : total dépôts
        lbl_transfert_total  (Label)     : total transferts
        lbl_global_total     (Label)     : total global
    """

    def __init__(self, **kwargs):
        """
        Initialise le layout et construit l'interface.
        Les données sont chargées dans on_enter(), pas ici,
        car aucun fichier n'est forcément disponible au démarrage.
        """
        super().__init__(
            orientation="vertical",
            padding=dp(14),
            spacing=dp(10),
            **kwargs
        )

        # État interne — initialisé à vide
        self.fichier_actif        = ""
        self.transactions_actives = []

        self._construire_selecteur_fichier()
        self._construire_barre_recherche()
        self._construire_tableau()
        self._construire_banniere_nom()
        self._construire_pied_de_page()

    # ─────────────────────────────────────────────────────────
    # CONSTRUCTION DES BLOCS UI
    # ─────────────────────────────────────────────────────────

    def _construire_selecteur_fichier(self):
        """
        Crée le bloc de sélection du fichier CSV.

        Utilise un Spinner Kivy alimenté par get_all_files()
        lors de chaque appel de on_enter().

        Le fichier du jour est présélectionné par défaut.
        Un changement déclenche _on_fichier_change().
        """
        conteneur = self._creer_carte(height=dp(58))

        lbl_titre = Label(
            text="FICHIER CONSULTÉ",
            font_size=dp(9), color=COULEUR_MUTED,
            size_hint_y=None, height=dp(14), halign="left"
        )
        lbl_titre.bind(size=lbl_titre.setter("text_size"))

        self.spinner_fichiers = Spinner(
            text="Chargement...",
            values=[],
            size_hint_y=None,
            height=dp(34),
            background_normal="",
            background_color=COULEUR_CARD,
            color=COULEUR_ACCENT,
            font_size=dp(12),
            bold=True
        )
        self.spinner_fichiers.bind(text=self._on_fichier_change)

        conteneur.add_widget(lbl_titre)
        conteneur.add_widget(self.spinner_fichiers)
        self.add_widget(conteneur)

    def _construire_barre_recherche(self):
        """
        Crée la barre de recherche :
            - TextInput  : requête de recherche
            - Spinner    : champ cible (Nom / Numero / Type / Reseau)
            - Btn Chercher : déclenche _action_rechercher()
            - Btn ✕       : réinitialise via _action_reset_recherche()

        La recherche est manuelle (bouton) pour éviter des
        lectures fichier excessives à chaque frappe.
        """
        ligne = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(6)
        )

        self.input_recherche = TextInput(
            hint_text="Rechercher...",
            multiline=False,
            size_hint_x=0.45,
            size_hint_y=None,
            height=dp(40),
            background_color=COULEUR_CARD,
            foreground_color=COULEUR_TEXTE,
            hint_text_color=COULEUR_MUTED,
            cursor_color=COULEUR_ACCENT,
            font_size=dp(12)
        )

        # Les valeurs du Spinner correspondent aux clés de CHAMPS
        # dans search_transactions() — via la table de correspondance
        # dans _action_rechercher()
        self.spinner_champ = Spinner(
            text="Nom",
            values=["Nom", "Numero", "Type", "Reseau"],
            size_hint_x=0.22,
            size_hint_y=None,
            height=dp(40),
            background_normal="",
            background_color=COULEUR_CARD,
            color=COULEUR_MUTED,
            font_size=dp(11)
        )

        btn_chercher = Button(
            text="Chercher",
            size_hint_x=0.20,
            size_hint_y=None,
            height=dp(40),
            background_normal="",
            background_color=COULEUR_ACCENT,
            color=(0.051, 0.059, 0.078, 1),
            bold=True,
            font_size=dp(11),
            on_press=self._action_rechercher
        )

        btn_reset = Button(
            text="✕",
            size_hint_x=0.13,
            size_hint_y=None,
            height=dp(40),
            background_normal="",
            background_color=COULEUR_CARD,
            color=COULEUR_MUTED,
            bold=True,
            font_size=dp(14),
            on_press=self._action_reset_recherche
        )

        ligne.add_widget(self.input_recherche)
        ligne.add_widget(self.spinner_champ)
        ligne.add_widget(btn_chercher)
        ligne.add_widget(btn_reset)
        self.add_widget(ligne)

    def _construire_tableau(self):
        """
        Crée la zone centrale : en-tête fixe + ScrollView.

        Structure :
            BoxLayout vertical
            ├── GridLayout  (en-tête — 1 ligne, hauteur fixe)
            └── ScrollView
                 └── GridLayout (corps — N lignes dynamiques)

        L'en-tête reste visible pendant le défilement.
        """
        conteneur_tableau = BoxLayout(orientation="vertical", spacing=0)

        # ── En-tête fixe ──
        entete = GridLayout(
            cols=len(COLONNES_TABLEAU),
            size_hint_y=None,
            height=dp(28)
        )

        with entete.canvas.before:
            Color(*COULEUR_CARD)
            self._rect_entete = Rectangle(pos=entete.pos, size=entete.size)
        entete.bind(
            pos=lambda o, v: setattr(self._rect_entete, "pos", v),
            size=lambda o, v: setattr(self._rect_entete, "size", v)
        )

        for texte_col, taille in COLONNES_TABLEAU:
            lbl = Label(
                text=texte_col.upper(),
                font_size=dp(9),
                color=COULEUR_MUTED,
                size_hint_x=taille,
                halign="left",
                valign="middle"
            )
            lbl.bind(size=lbl.setter("text_size"))
            entete.add_widget(lbl)

        # ── Corps scrollable ──
        scroll = ScrollView(do_scroll_x=False)

        # La grille est vidée et reconstruite à chaque chargement
        # ou filtrage via _remplir_tableau()
        self.grille_tableau = GridLayout(
            cols=len(COLONNES_TABLEAU),
            size_hint_y=None,
            spacing=[0, 1]
        )
        self.grille_tableau.bind(
            minimum_height=self.grille_tableau.setter("height")
        )

        scroll.add_widget(self.grille_tableau)
        conteneur_tableau.add_widget(entete)
        conteneur_tableau.add_widget(scroll)
        self.add_widget(conteneur_tableau)

    def _construire_banniere_nom(self):
        """
        Crée une bannière discrète affichée entre le tableau et le pied
        de page, destinée à révéler le nom du client quand l'utilisateur
        tape sur une ligne du tableau.

        Masquée (opacity=0) par défaut.
        Rendue visible 3 secondes par _afficher_nom(), puis effacée
        automatiquement via Clock.schedule_once().
        """
        self.banniere_nom = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(34),
            padding=[dp(12), dp(0)],
            spacing=dp(8),
            opacity=0    # masquée par défaut
        )

        # Fond discret — légèrement coloré accent
        from kivy.graphics import Color, RoundedRectangle
        with self.banniere_nom.canvas.before:
            Color(*COULEUR_ACCENT[:3], 0.10)
            rect = RoundedRectangle(
                pos=self.banniere_nom.pos,
                size=self.banniere_nom.size,
                radius=[dp(8)]
            )
        self.banniere_nom.bind(
            pos=lambda o, v: setattr(rect, "pos", v),
            size=lambda o, v: setattr(rect, "size", v)
        )

        # Icône fixe
        lbl_ico = Label(
            text="👤",
            font_size=dp(13),
            size_hint=(None, 1),
            width=dp(22)
        )

        # Texte du nom — mis à jour dans _afficher_nom()
        self.lbl_nom_banniere = Label(
            text="",
            font_size=dp(12),
            color=COULEUR_ACCENT,
            halign="left",
            valign="middle"
        )
        self.lbl_nom_banniere.bind(
            size=self.lbl_nom_banniere.setter("text_size")
        )

        self.banniere_nom.add_widget(lbl_ico)
        self.banniere_nom.add_widget(self.lbl_nom_banniere)
        self.add_widget(self.banniere_nom)

    def _afficher_nom(self, nom: str):
        """
        Affiche le nom du client dans la bannière pendant 3 secondes.

        Appelée depuis le callback on_press de chaque btn_numero
        dans _ajouter_ligne_tableau().

        Args :
            nom (str) : nom du client à afficher
        """
        # Annuler un éventuel timer précédent pour éviter les chevauchements
        if hasattr(self, "_timer_nom") and self._timer_nom:
            self._timer_nom.cancel()

        self.lbl_nom_banniere.text = f"Client : {nom}" if nom else "Nom non renseigné"
        self.banniere_nom.opacity  = 1

        # Masquer automatiquement après 3 secondes
        self._timer_nom = Clock.schedule_once(
            lambda dt: self._masquer_banniere_nom(), 3
        )

    def _masquer_banniere_nom(self):
        """Masque la bannière nom. Appelée par Clock après 3 secondes."""
        self.banniere_nom.opacity     = 0
        self.lbl_nom_banniere.text    = ""
        self._timer_nom               = None

    def _construire_pied_de_page(self):
        """
        Crée le pied de page avec les totaux en 3 colonnes :
            Dépôts (vert) | Transferts (orange) | Total (blanc)

        Recalculés dans _mettre_a_jour_totaux() après chaque
        chargement ou filtrage.
        """
        pied = self._creer_carte(height=dp(52))
        grille = GridLayout(cols=3)

        # ── Dépôts ──
        col_d = BoxLayout(orientation="vertical")
        lbl_t_d = Label(
            text="DÉPÔTS", font_size=dp(9), color=COULEUR_MUTED,
            size_hint_y=None, height=dp(14), halign="center"
        )
        lbl_t_d.bind(size=lbl_t_d.setter("text_size"))
        self.lbl_depot_total = Label(
            text="— F", font_size=dp(13), bold=True,
            color=COULEUR_ACCENT, halign="center"
        )
        self.lbl_depot_total.bind(
            size=self.lbl_depot_total.setter("text_size")
        )
        col_d.add_widget(lbl_t_d)
        col_d.add_widget(self.lbl_depot_total)

        # ── Transferts ──
        col_t = BoxLayout(orientation="vertical")
        lbl_t_t = Label(
            text="TRANSFERTS", font_size=dp(9), color=COULEUR_MUTED,
            size_hint_y=None, height=dp(14), halign="center"
        )
        lbl_t_t.bind(size=lbl_t_t.setter("text_size"))
        self.lbl_transfert_total = Label(
            text="— F", font_size=dp(13), bold=True,
            color=COULEUR_TRANSFERT, halign="center"
        )
        self.lbl_transfert_total.bind(
            size=self.lbl_transfert_total.setter("text_size")
        )
        col_t.add_widget(lbl_t_t)
        col_t.add_widget(self.lbl_transfert_total)

        # ── Total global ──
        col_g = BoxLayout(orientation="vertical")
        lbl_t_g = Label(
            text="TOTAL", font_size=dp(9), color=COULEUR_MUTED,
            size_hint_y=None, height=dp(14), halign="center"
        )
        lbl_t_g.bind(size=lbl_t_g.setter("text_size"))
        self.lbl_global_total = Label(
            text="—", font_size=dp(13), bold=True,
            color=COULEUR_TEXTE, halign="center"
        )
        self.lbl_global_total.bind(
            size=self.lbl_global_total.setter("text_size")
        )
        col_g.add_widget(lbl_t_g)
        col_g.add_widget(self.lbl_global_total)

        grille.add_widget(col_d)
        grille.add_widget(col_t)
        grille.add_widget(col_g)
        pied.add_widget(grille)
        self.add_widget(pied)

    # ─────────────────────────────────────────────────────────
    # CHARGEMENT ET AFFICHAGE DES DONNÉES
    # ─────────────────────────────────────────────────────────

    def _charger_fichiers_disponibles(self):
        """
        Récupère la liste des CSV via get_all_files() et alimente
        le Spinner. Trie par ordre décroissant (le plus récent en tête).

        Présélectionne le fichier du jour si disponible,
        sinon le fichier le plus récent.
        """
        valide, fichiers = get_all_files()

        if not valide:
            self.spinner_fichiers.values = []
            self.spinner_fichiers.text   = "Aucun fichier disponible"
            return

        fichiers_tries = sorted(fichiers, reverse=True)
        self.spinner_fichiers.values = fichiers_tries

        fichier_jour = get_today_date() + ".csv"
        if fichier_jour in fichiers_tries:
            self.spinner_fichiers.text = fichier_jour
        else:
            self.spinner_fichiers.text = fichiers_tries[0]

    def _charger_transactions(self, nom_fichier: str):
        """
        Charge les transactions d'un fichier CSV via open_file()
        et met à jour le tableau et les totaux.

        Args :
            nom_fichier (str) : nom du fichier (ex: "2026-05-21.csv")
                               Le chemin "data/" est ajouté ici.
        """
        import os
        filepath = os.path.join("data", nom_fichier)

        valide, donnees = open_file(filepath)

        if not valide:
            # Fichier vide ou illisible
            self.transactions_actives = []
            self._remplir_tableau([])
            self._mettre_a_jour_totaux([])
            return

        self.fichier_actif        = nom_fichier
        self.transactions_actives = donnees

        self._remplir_tableau(donnees)
        self._mettre_a_jour_totaux(donnees)

    def _remplir_tableau(self, transactions: list):
        """
        Reconstruit la grille du tableau à partir d'une liste
        de transactions.

        Vide la grille, puis ajoute une ligne par transaction.
        Lignes paires : fond COULEUR_LIGNE_PAIR (effet zebra).
        Liste vide    : affiche "Aucune transaction".

        Args :
            transactions (list) : liste de dicts avec les clés
                                  type, reseau, numero, nom, montant, heure
        """
        self.grille_tableau.clear_widgets()

        if not transactions:
            # Message centré, pleine largeur (cols=1 temporairement)
            lbl_vide = Label(
                text="Aucune transaction à afficher",
                font_size=dp(12),
                color=COULEUR_MUTED,
                size_hint_y=None,
                height=dp(40)
            )
            self.grille_tableau.cols = 1
            self.grille_tableau.add_widget(lbl_vide)
            self.grille_tableau.cols = len(COLONNES_TABLEAU)
            return

        for index, tx in enumerate(transactions):
            self._ajouter_ligne_tableau(tx, index)

    def _ajouter_ligne_tableau(self, tx: dict, index: int):
        """
        Ajoute une ligne de transaction dans la grille.

        Colonnes :
            1. Type    → badge DÉP (vert) ou TRF (orange)
            2. Réseau  → texte
            3. Nom     → tronqué à 12 caractères
            4. Montant → formaté, couleur selon type
            5. Heure   → HH:MM (secondes masquées)

        Effet zebra : fond COULEUR_LIGNE_PAIR sur les lignes paires.

        Args :
            tx    (dict) : données de la transaction
            index (int)  : index 0-based pour l'alternance des couleurs
        """
        h = dp(32)
        fond = COULEUR_LIGNE_PAIR if index % 2 == 0 else (0, 0, 0, 0)

        est_depot    = tx["type"] == "Depot"
        texte_badge  = "DÉP" if est_depot else "TRF"
        couleur_type = COULEUR_ACCENT if est_depot else COULEUR_TRANSFERT

        # ── Colonne 1 : Type ──
        lbl_type = Label(
            text=texte_badge, font_size=dp(9), bold=True,
            color=couleur_type,
            size_hint=(COLONNES_TABLEAU[0][1], None), height=h,
            halign="left", valign="middle"
        )
        lbl_type.bind(size=lbl_type.setter("text_size"))
        self._appliquer_fond(lbl_type, fond)

        # ── Colonne 2 : Réseau ──
        lbl_reseau = Label(
            text=tx["reseau"], font_size=dp(10), color=COULEUR_TEXTE,
            size_hint=(COLONNES_TABLEAU[1][1], None), height=h,
            halign="left", valign="middle"
        )
        lbl_reseau.bind(size=lbl_reseau.setter("text_size"))
        self._appliquer_fond(lbl_reseau, fond)

        # ── Colonne 3 : Numéro ──
        # Bouton transparent pour capturer le tap et afficher le nom
        # dans la bannière info via _afficher_nom().
        btn_numero = Button(
            text=tx["numero"],
            font_size=dp(10),
            color=COULEUR_TEXTE,
            background_normal="",
            background_color=(0, 0, 0, 0),
            size_hint=(COLONNES_TABLEAU[2][1], None),
            height=h,
            halign="left",
            valign="middle",
            on_press=lambda inst, nom=tx["nom"]: self._afficher_nom(nom)
        )
        btn_numero.bind(size=btn_numero.setter("text_size"))
        self._appliquer_fond(btn_numero, fond)

        # ── Colonne 4 : Montant ──
        lbl_montant = Label(
            text=self._formater_montant(tx["montant"]),
            font_size=dp(10), bold=True, color=couleur_type,
            size_hint=(COLONNES_TABLEAU[3][1], None), height=h,
            halign="right", valign="middle"
        )
        lbl_montant.bind(size=lbl_montant.setter("text_size"))
        self._appliquer_fond(lbl_montant, fond)

        # ── Colonne 5 : Heure (HH:MM uniquement) ──
        heure = tx["heure"][:5] if len(tx["heure"]) >= 5 else tx["heure"]
        lbl_heure = Label(
            text=heure, font_size=dp(10), color=COULEUR_MUTED,
            size_hint=(COLONNES_TABLEAU[4][1], None), height=h,
            halign="left", valign="middle"
        )
        lbl_heure.bind(size=lbl_heure.setter("text_size"))
        self._appliquer_fond(lbl_heure, fond)

        # Ajout des 5 cellules dans la grille (ordre = ordre des colonnes)
        self.grille_tableau.add_widget(lbl_type)
        self.grille_tableau.add_widget(lbl_reseau)
        self.grille_tableau.add_widget(btn_numero)
        self.grille_tableau.add_widget(lbl_montant)
        self.grille_tableau.add_widget(lbl_heure)

    def _mettre_a_jour_totaux(self, transactions: list):
        """
        Calcule et affiche les totaux dépôts / transferts / global
        à partir de la liste en mémoire.

        Opère sur la liste transmise (peut être filtrée) sans
        relire le fichier, pour que les totaux reflètent le filtre actif.

        Args :
            transactions (list) : liste de dicts de transactions
        """
        depot_total = transfert_total = 0

        for tx in transactions:
            if tx["type"] == "Depot":
                depot_total += tx["montant"]
            elif tx["type"] == "Transfert":
                transfert_total += tx["montant"]

        global_total = depot_total + transfert_total

        self.lbl_depot_total.text     = self._formater_montant(depot_total)     + " F"
        self.lbl_transfert_total.text = self._formater_montant(transfert_total) + " F"
        self.lbl_global_total.text    = self._formater_montant(global_total)

    # ─────────────────────────────────────────────────────────
    # ACTIONS UTILISATEUR
    # ─────────────────────────────────────────────────────────

    def _on_fichier_change(self, spinner, valeur):
        """
        Callback déclenché lors d'un changement de fichier dans le Spinner.

        Ignore les valeurs de placeholder.
        Réinitialise la recherche et charge le nouveau fichier.

        Args :
            spinner : Spinner source (Kivy)
            valeur  (str) : nom du fichier sélectionné
        """
        if valeur in ("Chargement...", "Aucun fichier disponible"):
            return

        self.input_recherche.text = ""
        self._charger_transactions(valeur)

    def _action_rechercher(self, instance):
        """
        Callback du bouton "Chercher".

        Convertit le label du Spinner en clé CSV interne,
        puis appelle search_transactions() sur le fichier actif.

        Table de correspondance :
            "Nom"    → "nom"
            "Numero" → "numero"
            "Type"   → "type"
            "Reseau" → "reseau"

        Args :
            instance : Button source (Kivy, non utilisé)
        """
        query = self.input_recherche.text.strip()

        if not query:
            # Requête vide → afficher tout sans filtre
            self._remplir_tableau(self.transactions_actives)
            self._mettre_a_jour_totaux(self.transactions_actives)
            return

        correspondance = {
            "Nom":     "nom",
            "Numero":  "numero",
            "Type":    "type",
            "Reseau":  "reseau"
        }
        champ = correspondance.get(self.spinner_champ.text, "nom")

        import os
        filepath = os.path.join("data", self.fichier_actif)
        valide, resultats = search_transactions(filepath, query, champ)

        if valide:
            self._remplir_tableau(resultats)
            self._mettre_a_jour_totaux(resultats)
        else:
            # Aucun résultat trouvé
            self._remplir_tableau([])
            self._mettre_a_jour_totaux([])

    def _action_reset_recherche(self, instance):
        """
        Callback du bouton "✕".

        Efface la recherche et affiche toutes les transactions
        du fichier actif sans filtre.

        Args :
            instance : Button source (Kivy, non utilisé)
        """
        self.input_recherche.text = ""
        self._remplir_tableau(self.transactions_actives)
        self._mettre_a_jour_totaux(self.transactions_actives)

    # ─────────────────────────────────────────────────────────
    # CYCLE DE VIE
    # ─────────────────────────────────────────────────────────

    def on_enter(self):
        """
        Appelée depuis main.py/_on_tab_switch() à chaque sélection
        de l'onglet Historique.

        Actions :
            1. Recharge la liste des fichiers disponibles
               (un nouveau fichier a pu être créé depuis l'Accueil)
            2. Recharge les transactions du fichier affiché
               (de nouvelles transactions ont pu être ajoutées)
        """
        self._charger_fichiers_disponibles()

        fichier_courant = self.spinner_fichiers.text
        if fichier_courant not in ("Chargement...", "Aucun fichier disponible"):
            self._charger_transactions(fichier_courant)

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
            BoxLayout : conteneur stylisé.
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
    def _appliquer_fond(widget, couleur: tuple):
        """
        Applique une couleur de fond à un widget via canvas.before.
        Utilisé pour l'effet zebra sur les lignes du tableau.

        Args :
            widget  : widget Kivy cible
            couleur (tuple) : couleur RGBA
        """
        with widget.canvas.before:
            Color(*couleur)
            rect = Rectangle(pos=widget.pos, size=widget.size)
        widget.bind(
            pos=lambda o, v: setattr(rect, "pos", v),
            size=lambda o, v: setattr(rect, "size", v)
        )

    @staticmethod
    def _formater_montant(montant: int) -> str:
        """
        Formate un entier avec séparateurs de milliers.

        Exemple : 395000 → "395 000"

        Args :
            montant (int) : montant brut.

        Returns :
            str : montant formaté.
        """
        return f"{montant:,}".replace(",", " ")
