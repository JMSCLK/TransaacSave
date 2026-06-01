# -*- coding: utf-8 -*-
"""
main.py
=======
Point d'entrée de l'application TransacSave.

Modifications v2 :
    - Ajout d'un header global (nom de l'app + date du jour)
      fidèle à l'aperçu HTML, visible sur tous les onglets
    - Correction du rafraîchissement : on_enter() ne fonctionne
      pas avec TabbedPanel. On utilise panel.bind(current_tab=...)
      pour appeler manuellement on_enter() à chaque changement d'onglet.

Auteur : Nous
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

# Imports des onglets
from ui.tab_accueil    import OngletAccueil
from ui.tab_saisie     import OngletSaisie
from ui.tab_historique import OngletHistorique

# Imports utilitaires pour le header
from core.utils import get_today_date


# ─────────────────────────────────────────────────────────────
# CONSTANTES DE STYLE — header global
# ─────────────────────────────────────────────────────────────
COULEUR_SURFACE = (0.082, 0.094, 0.118, 1)   # #151820 — fond du header
COULEUR_BORDER  = (0.145, 0.165, 0.227, 1)   # #252A3A — séparateur bas header
COULEUR_ACCENT  = (0.000, 0.898, 0.627, 1)   # #00E5A0 — nom de l'app
COULEUR_MUTED   = (0.420, 0.447, 0.502, 1)   # #6B7280 — date du jour
COULEUR_CARD    = (0.110, 0.125, 0.188, 1)   # #1C2030 — fond badge date


class AppHeader(BoxLayout):
    """
    Header global affiché en permanence en haut de la fenêtre,
    indépendamment de l'onglet actif.

    Contenu (fidèle à l'aperçu HTML) :
        - Gauche : nom de l'application "TRANSACSAVE" en vert accent
        - Droite : badge avec la date du jour au format YYYY-MM-DD

    Ce widget est instancié une seule fois dans TransacSaveApp.build()
    et ne se rafraîchit pas (la date ne change pas en cours de session).
    """

    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            padding=[dp(14), dp(8)],
            spacing=dp(10),
            **kwargs
        )

        # ── Fond du header ──
        # Rectangle plein de la couleur SURFACE, avec un trait de séparation
        # en bas pour délimiter visuellement le header du contenu.
        with self.canvas.before:
            # Fond principal
            Color(*COULEUR_SURFACE)
            self._rect_bg = Rectangle(pos=self.pos, size=self.size)
            # Trait de séparation bas (1dp de hauteur, couleur border)
            Color(*COULEUR_BORDER)
            self._rect_border = Rectangle(
                pos=(self.x, self.y),
                size=(self.width, dp(1))
            )
        # Liaisons dynamiques : les rectangles suivent les redimensionnements
        self.bind(
            pos=self._maj_canvas,
            size=self._maj_canvas
        )

        # ── Nom de l'application (gauche) ──
        lbl_titre = Label(
            text="TRANSACSAVE",
            font_size=dp(15),
            bold=True,
            color=COULEUR_ACCENT,
            halign="left",
            valign="middle"
        )
        lbl_titre.bind(size=lbl_titre.setter("text_size"))

        # ── Badge date du jour (droite) ──
        # Affiche la date au format YYYY-MM-DD dans un badge arrondi
        badge_date = Label(
            text=get_today_date(),
            font_size=dp(11),
            color=COULEUR_MUTED,
            size_hint=(None, None),
            size=(dp(110), dp(28)),
            halign="center",
            valign="middle"
        )
        badge_date.bind(size=badge_date.setter("text_size"))

        # Fond du badge date
        with badge_date.canvas.before:
            Color(*COULEUR_CARD)
            from kivy.graphics import RoundedRectangle
            self._rect_badge = RoundedRectangle(
                pos=badge_date.pos,
                size=badge_date.size,
                radius=[dp(6)]
            )
        badge_date.bind(
            pos=lambda o, v: setattr(self._rect_badge, "pos", v),
            size=lambda o, v: setattr(self._rect_badge, "size", v)
        )

        self.add_widget(lbl_titre)
        self.add_widget(badge_date)

    def _maj_canvas(self, *args):
        """
        Met à jour la position et la taille des rectangles canvas
        lors d'un redimensionnement ou déplacement du widget.
        """
        self._rect_bg.pos  = self.pos
        self._rect_bg.size = self.size
        # Le trait de séparation est positionné tout en bas du header
        self._rect_border.pos  = (self.x, self.y)
        self._rect_border.size = (self.width, dp(1))


class TransacSaveApp(App):
    """
    Classe principale de l'application TransacSave.

    Structure de la fenêtre :
        BoxLayout vertical
        ├── AppHeader      (hauteur fixe dp(48)) — nom + date
        └── TabbedPanel    (occupe le reste)
             ├── Onglet Accueil
             ├── Onglet Saisie
             └── Onglet Historique

    Correction rafraîchissement :
        TabbedPanel ne déclenche pas on_enter() automatiquement.
        On utilise panel.bind(current_tab=_on_tab_switch) pour
        appeler manuellement on_enter() sur l'onglet actif.
    """

    def build(self):
        """
        Construit et retourne le widget racine de l'application.
        """
        # Taille de la fenêtre simulant un écran mobile
        Window.size = (400, 700)

        # ── Conteneur racine : header + panel ──
        racine = BoxLayout(orientation="vertical")

        # Fond global de la fenêtre
        with racine.canvas.before:
            Color(0.051, 0.059, 0.078, 1)   # #0D0F14 — fond page
            self._rect_racine = Rectangle(pos=racine.pos, size=racine.size)
        racine.bind(
            pos=lambda o, v: setattr(self._rect_racine, "pos", v),
            size=lambda o, v: setattr(self._rect_racine, "size", v)
        )

        # ── Header global ──
        header = AppHeader()
        racine.add_widget(header)

        # ── TabbedPanel ──
        panel = TabbedPanel(
            do_default_tab=False,
            tab_height=dp(40),          # hauteur des onglets
            tab_width=dp(120)           # largeur uniforme de chaque onglet
        )

        # ── Onglet Accueil ──
        # On conserve une référence à chaque widget d'onglet
        # pour pouvoir appeler on_enter() depuis _on_tab_switch()
        tab_accueil = TabbedPanelItem(text="Accueil")
        self.onglet_accueil = OngletAccueil()
        tab_accueil.add_widget(self.onglet_accueil)
        panel.add_widget(tab_accueil)

        # ── Onglet Saisie ──
        tab_saisie = TabbedPanelItem(text="Saisie")
        self.onglet_saisie = OngletSaisie()
        tab_saisie.add_widget(self.onglet_saisie)
        panel.add_widget(tab_saisie)

        # ── Onglet Historique ──
        tab_historique = TabbedPanelItem(text="Historique")
        self.onglet_historique = OngletHistorique()
        tab_historique.add_widget(self.onglet_historique)
        panel.add_widget(tab_historique)

        # ── Liaison du changement d'onglet ──
        # current_tab est la propriété Kivy qui change à chaque
        # sélection d'un nouvel onglet. On l'écoute pour déclencher
        # manuellement on_enter() sur le bon widget.
        panel.bind(current_tab=self._on_tab_switch)

        racine.add_widget(panel)
        return racine

    def _on_tab_switch(self, panel, tab_item):
        """
        Callback déclenché à chaque changement d'onglet actif.

        Récupère le widget contenu dans l'onglet sélectionné
        et appelle sa méthode on_enter() si elle existe.

        Cette méthode remplace le mécanisme on_enter() natif de
        ScreenManager qui ne fonctionne pas avec TabbedPanel.

        Args :
            panel    : TabbedPanel source (paramètre Kivy)
            tab_item : TabbedPanelItem qui vient de devenir actif
        """
        # tab_item.content retourne le widget enfant du TabbedPanelItem
        # (c'est-à-dire OngletAccueil, OngletSaisie ou OngletHistorique)
        contenu = tab_item.content

        # Appel conditionnel : on vérifie que la méthode existe
        # avant de l'appeler pour éviter une AttributeError
        if contenu is not None and hasattr(contenu, "on_enter"):
            contenu.on_enter()


if __name__ == "__main__":
    TransacSaveApp().run()
