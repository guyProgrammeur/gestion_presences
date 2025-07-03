from django import forms
from .models import Presence
from django.utils import timezone

class PresenceForm(forms.ModelForm):
    class Meta:
        model = Presence
        fields = ['agent', 'date', 'heure_arrivee', 'heure_depart', 'statut', 'type_travail', 'remarques']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'heure_arrivee': forms.TimeInput(attrs={'type': 'time'}),
            'heure_depart': forms.TimeInput(attrs={'type': 'time'}),
        }


from django import forms
import datetime

class RapportForm(forms.Form):
    mois = forms.ChoiceField(
        choices=[(i, datetime.date(1900, i, 1).strftime('%B').capitalize()) for i in range(1, 13)],
        label='Mois'
    )
    annee = forms.ChoiceField(
        choices=[(y, y) for y in range(2020, datetime.date.today().year + 1)],
        label='Année'
    )

# class RapportForm(forms.Form):
#     mois = forms.ChoiceField(choices=[(i, i) for i in range(1, 13)])
#     annee = forms.IntegerField(min_value=2000, max_value=2100)
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         aujourd_hui = timezone.now().date()
#         self.fields['mois'].initial = aujourd_hui.month
#         self.fields['annee'].initial = aujourd_hui.year