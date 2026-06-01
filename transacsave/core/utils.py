# -*- coding: utf-8 -*-
"""
Created on Sat May  9 22:28:12 2026

utils.py
======
Fonctions utilitaires (date, heure...)

@author: Nous
"""

import datetime

def get_today_date():
    """ #retourne la date du jour formatée en str format YYYY-MM-DD"""
    maintenant = datetime.datetime.now()
    today_date = maintenant.strftime("%Y-%m-%d")
    return today_date


def get_current_time():
    """#retourne l'heure actuelle formatee"""
    actuel = datetime.datetime.now()
    current_time = actuel.strftime("%H:%M:%S")
    return current_time
    
def format_amount(amount):
    """#valide et formate le montant saisi
    #retourne le montant propre"""
    
    amount_clean = str(amount).replace(" ", "")
    
    if amount_clean == "" :
        return (False, "Le montant est vide")
    
    try:
        amount_clean = int(float(amount_clean))
    except ValueError:
        return (False, "Valeur invalide, entrez un nombre")
    
    if amount_clean<100 or amount_clean>1000000:
        return (False, "Montant entre 100 et 1000000")
    
    
    return (True, amount_clean)
    
    
def format_phone_number(number: str):
    #valide le format du numero
    #retourne le numero formaté ou erreur
    
    number = str(number).replace(" ", "")
        
        
    if number == "":
        return (False, "Numero vide")
     
    if len(number)!=9 or not number.isdigit():
        return (False, "Format invalide: 09 chiffres")

    
    return (True, number)
        
    
    
    
    