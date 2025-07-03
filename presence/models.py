from datetime import datetime, timezone
from django.db import models
from django.db.models import Q, Count
from django.conf import settings

class Institution(models.Model):
    nom = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='institution/')
    adresse = models.TextField()
    contact = models.CharField(max_length=100)

    def __str__(self):
        return self.nom


class DivisionEtBureau(models.Model):
    nom = models.CharField(max_length=100)
    #code = models.CharField(max_length=10)

    def __str__(self):
        return f"Divisions / Bureaux: {self.nom}"


class Agent(models.Model):
    SEXE_CHOIX = [('M', 'Masculin'), ('F', 'Féminin')]

    matricule = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=100)
    postnom = models.CharField(max_length=100)
    grade = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOIX)
    # fonction = models.CharField(max_length=100, null=True, blank=True)
    Division_Bureau = models.ForeignKey(DivisionEtBureau, on_delete=models.PROTECT)
    photo = models.ImageField(upload_to='agents/', null=True, blank=True)
    heure_arrivee_attendue = models.TimeField(default='08:00')
    heure_depart_attendue = models.TimeField(default='16:00')

    class Meta:
        ordering = ['nom', 'postnom']

    def __str__(self):
        return f"{self.nom} {self.postnom}"
    def presence_mois(self, mois=None, annee=None):
        aujourd_hui = timezone.now().date()
        mois = mois or aujourd_hui.month
        annee = annee or aujourd_hui.year
        
        return Presence.objects.filter(
            agent=self,
            date__year=annee,
            date__month=mois,
            statut='P'
        ).count()
    
    def absences_mois(self, mois=None, annee=None):
        aujourd_hui = timezone.now().date()
        mois = mois or aujourd_hui.month
        annee = annee or aujourd_hui.year
        
        return Presence.objects.filter(
            agent=self,
            date__year=annee,
            date__month=mois,
            statut='A'
        ).count()
    @property
    def nom_complet(self):
        return f"{self.nom} {self.postnom}"


class Presence(models.Model):
    TYPE_TRAVAIL_CHOIX = [
        ('P', 'Présentiel'),
        ('D', 'Demi-journée'),
        ('T', 'Télétravail'),
    ]

    STATUT_CHOIX = [
        ('P', 'Présent'),
        ('A', 'Absent'),
        ('R', 'Retard'),
        ('F', 'Férié'),
    ]

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    date = models.DateField()
    heure_arrivee = models.TimeField(null=True, blank=True)
    heure_depart = models.TimeField(null=True, blank=True)
    statut = models.CharField(max_length=2, choices=STATUT_CHOIX)
    type_travail = models.CharField(max_length=1, choices=TYPE_TRAVAIL_CHOIX, default='P')
    justification = models.FileField(upload_to='justifications/', null=True, blank=True)
    remarques = models.TextField(blank=True)
    enregistre_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('agent', 'date')
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['agent', 'date']),
        ]

    def __str__(self):
        return f"{self.agent.nom_complet} - {self.date}"
    
    @property
    def duree_travail(self):
        if self.heure_arrivee and self.heure_depart:
            arrivee = datetime.datetime.combine(self.date, self.heure_arrivee)
            depart = datetime.datetime.combine(self.date, self.heure_depart)
            return depart - arrivee
        return None
    
    @classmethod
    @classmethod
    def stats_mois(cls, mois, annee):
        return cls.objects.filter(
            date__year=annee,
            date__month=mois
        ).aggregate(
            total=Count('id'),
            presents=Count('id', filter=Q(statut='P')),
            absents=Count('id', filter=Q(statut='A')),
            retards=Count('id', filter=Q(statut='R'))
        )