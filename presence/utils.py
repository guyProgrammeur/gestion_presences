# Fonctions utilitaires
from datetime import date, timedelta
from .models import JourOuvrable, JourFerie

def est_jour_travail(jour: date):
    # Vérifie si la date est un jour férié
    if JourFerie.objects.filter(date=jour).exists():
        return False

    # Vérifie dans la configuration des jours ouvrables
    jour_semaine = jour.weekday()
    try:
        config = JourOuvrable.objects.get(jour=jour_semaine)
        return config.est_ouvrable
    except JourOuvrable.DoesNotExist:
        return False

def jours_travail_du_mois(annee: int, mois: int):
    jours_travail = []
    premier = date(annee, mois, 1)
    if mois == 12:
        dernier = date(annee + 1, 1, 1) - timedelta(days=1)
    else:
        dernier = date(annee, mois + 1, 1) - timedelta(days=1)

    jour_courant = premier
    while jour_courant <= dernier:
        if est_jour_travail(jour_courant):
            jours_travail.append(jour_courant)
        jour_courant += timedelta(days=1)

    return jours_travail