from django.urls import path
from . import views

app_name = 'presence'
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('agents/', views.liste_agents, name='liste_agents'),
    path('agents/<int:agent_id>/', views.details_agent, name='details_agent'),
    path('presences/', views.gestion_presences, name='gestion_presences'),
    path('rapport/', views.generer_rapport, name='generer_rapport'),
    path('rapport/paysage/', views.rapport_paysage_view, name='rapport_paysage'),
    path('api/presence/', views.api_presence, name='api_presence'),
    path('rapport/paysage/apercu/', views.rapport_paysage_apercu, name='rapport_paysage_apercu'),
]