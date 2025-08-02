from datetime import datetime, timezone
from django.db import models
from django.db.models import Q, Count
from django.conf import settings
from django.contrib.auth.models import User

class Institution(models.Model):
    nom = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='institution/')
    adresse = models.TextField()
    contact = models.CharField(max_length=100)

    def __str__(self):
        return self.nom
    class Meta:
        verbose_name = "INSTITUTION"
        verbose_name_plural = "INSTITUTIONS"
    
class Direction(models.Model):
    nom = models.CharField(max_length=100)
    abrege = models.CharField(max_length=20)
    chef = models.ForeignKey('Agent', null=True, blank=True, on_delete=models.SET_NULL, related_name='direction_dirigee')

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "DIRECTION"
        verbose_name_plural = "DIRECTIONS"

class Division(models.Model):
    nom = models.CharField(max_length=100)
    abrege = models.CharField(max_length=20)
    direction = models.ForeignKey(Direction, on_delete=models.CASCADE, related_name='divisions')
    chef = models.ForeignKey('Agent', null=True, blank=True, on_delete=models.SET_NULL, related_name='division_dirigee')
    ordre = models.PositiveIntegerField(default=0, help_text="Ordre d'affichage de la division")
    def __str__(self):
        return self.nom
    class Meta:
        verbose_name = "DIVISION"
        verbose_name_plural = "DIVISIONS"

class Bureau(models.Model):
    nom = models.CharField(max_length=100)
    abrege = models.CharField(max_length=20)
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='bureaux')
    direction = models.ForeignKey(Direction, null=True, blank=True, on_delete=models.SET_NULL, related_name='bureaux_directs')
    chef = models.ForeignKey('Agent', null=True, blank=True, on_delete=models.SET_NULL, related_name='bureau_dirigee')

    def __str__(self):
        return self.nom
    
    class Meta:
        verbose_name = "BUREAU"
        verbose_name_plural = "BUREAUX"

# class DivisionEtBureau(models.Model):
#     nom = models.CharField(max_length=100)
#     #code = models.CharField(max_length=10)

#     def __str__(self):
#         return f"Divisions / Bureaux: {self.nom}"


class Agent(models.Model):
    SEXE_CHOIX = [('M', 'Masculin'), ('F', 'Féminin')]

    matricule = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=100)
    postnom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    grade = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOIX)
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='agent_profile')

    bureau = models.ForeignKey(Bureau, null=True, blank=True, on_delete=models.PROTECT, related_name='agents')
    division = models.ForeignKey(Division, null=True, blank=True, on_delete=models.PROTECT, related_name='agents_sans_bureau')
    direction = models.ForeignKey(Direction, null=True, blank=True, on_delete=models.PROTECT, related_name='agents_sans_division')

    photo = models.ImageField(upload_to='agents/', null=True, blank=True)
    heure_arrivee_attendue = models.TimeField(default='08:00')
    heure_depart_attendue = models.TimeField(default='16:00')

    class Meta:
        ordering = ['nom', 'postnom', 'prenom']

    def __str__(self):
        return f"{self.nom} {self.postnom} {self.prenom}"

    @property
    def nom_complet(self):
        return f"{self.nom} {self.postnom} {self.prenom}"

    def presence_mois(self, mois=None, annee=None):
        aujourd_hui = timezone.now().date()
        mois = mois or aujourd_hui.month
        annee = annee or aujourd_hui.year
        return Presence.objects.filter(agent=self, date__year=annee, date__month=mois, statut='P').count()

    def absences_mois(self, mois=None, annee=None):
        aujourd_hui = timezone.now().date()
        mois = mois or aujourd_hui.month
        annee = annee or aujourd_hui.year
        return Presence.objects.filter(agent=self, date__year=annee, date__month=mois, statut='A').count()
    @property
    def rattachement_complet(self):
        if self.bureau and self.bureau.division:
            return f"{self.bureau.division.nom} / {self.bureau.nom}"
        elif self.division:
            return f"{self.division.nom}"
        elif self.direction:
            return f"{self.direction.nom}"
        return "Aucun rattachement"
    
    @property
    def rattachement_abrege(self):
        if self.bureau and self.bureau.division:
            return f"{self.bureau.division.abrege}/{self.bureau.abrege}"
        elif self.division:
            return self.division.abrege
        elif self.direction:
            return self.direction.abrege
        return "-"

    class Meta:
        verbose_name = "AGENT"
        verbose_name_plural = "AGENTS"

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
        permissions = [
            ("can_manage_presence", "Peut gérer les présences"),
            ("can_export_rapport", "Peut exporter les rapports"),
            ("can_view_own_presence", "Peut voir ses propres présences"),
        ]
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
    class Meta:
        verbose_name = "PRESENCE"
        verbose_name_plural = "PRESENCES"


# Modèle pour configurer les jours ouvrables
class JourOuvrable(models.Model):
    JOUR_CHOICES = [
        (0, "Lundi"),
        (1, "Mardi"),
        (2, "Mercredi"),
        (3, "Jeudi"),
        (4, "Vendredi"),
        (5, "Samedi"),
        (6, "Dimanche"),
    ]
    jour = models.IntegerField(choices=JOUR_CHOICES, unique=True)
    est_ouvrable = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_jour_display()} - {'Ouvrable' if self.est_ouvrable else 'Non ouvrable'}"

# Modèle pour enregistrer les jours fériés spécifiques
class JourFerie(models.Model):
    date = models.DateField(unique=True)
    description = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.date} - {self.description}"