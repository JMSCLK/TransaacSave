# ================================================================
#         TRANSACSAVE — BUILDOZER SPEC
#         Fichier de configuration pour la compilation APK
#         Généré pour Google Colab + Buildozer
# ================================================================

[app]

# ── Identité de l'application ──
title                   = TransacSave
package.name            = transacsave
package.domain          = org.transacsave
version                 = 1.0

# ── Code source ──
source.dir              = .
source.include_exts     = py,png,jpg,jpeg,atlas,csv,json,txt
source.include_patterns = data/*

# ── Point d'entrée ──
# main.py doit être à la racine du projet
entrypoint              = main.py

# ── Icône de l'application ──
# Format requis : PNG, résolution 512x512 pixels minimum
# Nommé 'icon.png' à la racine du projet
icon.filename           = icon.png

# ── Orientation de l'écran ──
orientation             = portrait

# ── Plein écran ──
fullscreen              = 0

# ── Dépendances Python ──
# Uniquement les bibliothèques non incluses dans Python standard
# csv, json, os, datetime, pathlib → natifs, pas besoin de les lister
requirements            = python3,kivy==2.1.0

# ================================================================
#         CONFIGURATION ANDROID
# ================================================================

[buildozer]

# ── Niveau de log ──
# 0 = erreurs uniquement | 1 = info | 2 = debug complet
log_level               = 2

# ── Avertissement si exécuté en root ──
warn_on_root            = 1

[app:android]

# ── API Android ──
# android.api    : version cible (Android 13)
# android.minapi : version minimale supportée (Android 5.0)
android.api             = 33
android.minapi          = 21

# ── NDK ──
android.ndk             = 25b

# ── Architectures cibles ──
# arm64-v8a  : appareils modernes 64 bits
# armeabi-v7a : appareils anciens 32 bits
android.archs           = arm64-v8a, armeabi-v7a

# ── Permissions Android ──
# Nécessaires pour lire/écrire les fichiers CSV dans data/
android.permissions     = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# ── Acceptance automatique des licences SDK ──
android.accept_sdk_license = True

# ── Mode de build ──
# debug  : pour les tests (pas de signature requise)
# release : pour la distribution (signature requise)
android.build_type      = debug

# ── Gradle ──
android.gradle_dependencies =

# ================================================================
#         NOTES IMPORTANTES
# ================================================================
#
# ICÔNE :
#   - Fichier    : icon.png
#   - Emplacement: racine du projet (même niveau que main.py)
#   - Format     : PNG
#   - Résolution : 512 x 512 pixels minimum (recommandé)
#
# STRUCTURE PROJET ATTENDUE :
#   TransacSave/
#   ├── main.py
#   ├── buildozer.spec
#   ├── icon.png
#   ├── core/
#   │   ├── transaction.py
#   │   ├── file_manager.py
#   │   └── utils.py
#   ├── ui/
#   │   ├── tab_accueil.py
#   │   ├── tab_saisie.py
#   │   └── tab_historique.py
#   └── data/
#
# COMPILATION :
#   Commande : buildozer android debug
#   APK généré dans : bin/transacsave-1.0-debug.apk
#
# ================================================================
