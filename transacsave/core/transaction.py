# -*- coding: utf-8 -*-
"""
Created on Fri May 15 17:35:14 2026

transaction.py
======
Logique métier (ajout, validation)

@author: Nous
"""

import csv
from core.utils import get_current_time, format_amount, format_phone_number


def validate_fields (type_transaction: str, fields: dict): 
    #retourner (True, " ") ou (False, "message")
     
    net = ["MTN", "Orange", "Camtel"]
    Transaction = ["Depot", "Transfert"]
    
    #verifier le type de transaction
    if type_transaction not in Transaction:
        return (False, "Type de Transaction invalide")
    
    #verifier le reseau
    if fields["reseau"] not in net:
        return (False, "Reseau invalide!!!")
    
    #valider le format du numero de telephone (format_phone_number)            
    valide, message = format_phone_number(fields["numero"])
    if not valide:
        return (False, message)

    
    #verifier si nom vide en cas de transfert
    if type_transaction == "Depot":
        if fields["nom"].strip() == "":
            return(False, "Nom obligatoire pour un depot")


    #valider montant via format_amount()
    valide, message= format_amount(fields["montant"])
    if not valide:
        return (False, message)
    
    return (True, " ")
     
   
    
def add_transaction(filepath: str, data: dict):
    #retourner (True, "Transaction enregistrée")
    
    #appeler validate_fields
    valide, message = validate_fields(data["type"], data)
    if not valide:
        return (False, message)
    
    #ajouter l'heure via get_current_time
    data["heure"] = get_current_time()
    
    #ouvrir le fichier en mode append 'a'
    #Ecrire la ligne CSV
    
    try:
        with open(filepath, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                data["type"],
                data["reseau"],
                data["numero"],
                data["nom"],
                data["montant"],
                data["heure"]
                ])
    except Exception as e:
        return(False, "Erreur lors de l'ecriture du fichier")
    
    return(True, "Transaction enregistrée")

    
    
def get_last_transaction(filepath):
    
    #verifier si le fichier existe
    #lire toutes les lignes
    try:
        with open(filepath, "r", encoding="utf-8") as file :
            lines = list(csv.reader(file))
            lines = lines[1:]
    except FileNotFoundError :
        return (False, "Fichier introuvable")
    
   
    #si fichier vide retourner "aucune transaction"   
    if len(lines)==0 :
        return(False, "Aucune transaction")
    
    
    #retourner la derniere ligne sous forme de dictionnaire
    last_line = lines[-1]
    transaction ={
        "type": last_line[0],
        "reseau": last_line[1],
        "numero": last_line[2],
        "nom": last_line[3],
        "montant": int(last_line[4]),
        "heure": last_line[5]
        }
    
    return(True, transaction)

    
    
def search_transactions(filepath: str, query: str, field: str):
    #verifier si le fichier existe
    try:
        with open(filepath, "r", encoding="utf-8") as file :
            lines = list(csv.reader(file))
    except FileNotFoundError :
        return (False, "Fichier introuvable")
        
    if len(lines)==0 :
        return(False, "Aucune transaction")
    
    #filtrer les lignes qui corresponde à Query
    CHAMPS = {
        "type": 0,
        "reseau": 1,
        "numero": 2,
        "nom": 3,
        "montant": 4,
        "heure": 5
        }
    
    #Recuper l'index du champ recherché
    index = CHAMPS[field]
    
    #Filtrer et construire la liste des résultats
    results = []
    for line in lines:
        if query.lower() in line[index].lower():
            results.append({
                "type": line[0],
                "reseau": line[1],
                "numero": line[2],
                "nom": line[3],
                "montant": int(line[4]),
                "heure": line[5]
                })
    
    #verifier si on a trouvé quelque chose
    if len(results)==0 :
        return(False, "aucun resultat trouvé")
    
    return(True, results)

    

def calculate_totals(filepath):
    
    try:
        with open(filepath, "r", encoding="utf-8") as file :
            lines = list(csv.reader(file))
            lines = lines[1:]
    except FileNotFoundError :
        return (False, "Fichier introuvable")
        
    if len(lines)==0 :
        return(False, "Aucune transaction")
    
    depot_total = 0
    depot_count = 0
    transfert_total = 0
    transfert_count = 0
    for line in lines:
        if line[0] == "Depot" :
            depot_total += int(line[4])
            depot_count += 1
        elif line[0] == "Transfert" :
            transfert_total += int(line[4])
            transfert_count += 1
            
    #construction du dictionnaire de retour
    Depot = {
        "total": depot_total, 
        "count": depot_count}
    Transfert = {
        "total": transfert_total,
        "count": transfert_count}
    dict_return = {
        "Depot": {"total": depot_total, "count": depot_count}, 
        "Transfert": {"total": transfert_total, "count": transfert_count}, 
        "Global": {"total": Depot["total"]+Transfert["total"], "count": Depot["count"]+Transfert["count"]}
    }
    
    return (True, dict_return)
    
    
     