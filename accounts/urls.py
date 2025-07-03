from django.urls import path
from .views import custom_login_view, custom_logout_view, profile_view, profil_utilisateur

app_name = 'accounts'
urlpatterns = [
    path('login/', custom_login_view, name='login'),
    path('logout/', custom_logout_view, name='logout'),
    path('profil/', profile_view, name='profil'),  # Version fonction
    # OU
    # path('profil/', profil_utilisateur, name='profil'),  # Alias si tu préfères
]