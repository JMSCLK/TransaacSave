# -*- coding: utf-8 -*-
"""
Created on Wed May 20 23:11:04 2026

file_manager.py
======
Logique métier (ajout, validation)
Création/lecture des fichiers CSV

@author: Nous
"""

import csv
import os

def file_exists_today(date: str):
    #construire le chemin du fichier "data/2026-05-08.csv"
    #valider si ce  chemin existe "return(True, "fichier exite") ou (False, "fichier inexixtant")
    filepath = os.path.join("data", date + ".csv")
    
    if os.path.exists(filepath):
        return (True, "Fichier Existant")
    else:
        return (False,"Fichier introuvable")
    
    

def get_today_filepath(date: str):
    #Retourne le chemin complet du fichier du jour
    return(os.path.join("data", date + ".csv"))



def create_daily_file(date: str):
    """Cree le fichier du jour"""
    #Retourner Vrai ou Faux
    
    #verifier si le fichier existe via file_exists_today()
    existe, _ = file_exists_today(date)
    if existe:
        return(False, "Fichier du jour deja existant")
    
    #verifier si le dossier "data/" existe
    os.makedirs("data", exist_ok=True)
    
    try:
        #Creer le fichier et ecrire l'en tete
        filepath = get_today_filepath(date)
        with open(filepath, 'w', newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["type", "reseau", "numero", "nom", "montant", "heure"])
    except Exception as e:
        return (False, "Erreur lors de la creation du fichier")
    
    return(True, "Fichier cree avec succes")



def get_all_files():
    """lister tout les fichiers csv disponible du repertoire data/""" 
    #retourner Vrai ou Faux
    
    #valider si le dossier "data/" existe
    valide = os.path.exists("data")
    if not valide :
        return(False, "Dossier introuvable")

    #Lister ,tout les fichiers du dossier
    fichiers = [f for f in os.listdir("data") if f.endswith(".csv")]
    
    #verifier si la liste est vide
    if len(fichiers)==0:
        return(False, "Aucun fichiers disponible")
    
    return(True, fichiers)



def open_file(filepath: str):
    
    #verifier si le fichier existe
    #lire toutes les lignes
    try:
        with open(filepath, "r", encoding="utf-8") as file :
            lines = list(csv.reader(file))
            lines = lines[1:]
    except Exception as e :
        return (False, "Fichier introuvable ou Erreur de lecture")
    
    #si fichier vide retourner "aucune transaction"   
    if len(lines)==0 :
        return(False, "Aucune transaction")
    
    #Convertir chaque ligne en dictionnaire
    transaction = []
    for line in lines:
        transaction.append({
            "type": line[0],
            "reseau": line[1],
            "numero": line[2],
            "nom": line[3],
            "montant": int(line[4]),
            "heure": line[5]
            })
        
    return(True, transaction) #Retourner Vrai ou Faux
    
