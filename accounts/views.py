from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseRedirect

def custom_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Bienvenue, {user.username}!")
            return redirect('presence:dashboard')
        else:
            messages.error(request, "Identifiants invalides. Veuillez réessayer.")
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def custom_logout_view(request):
    logout(request)
    messages.info(request, "Vous avez été déconnecté avec succès.")
    return HttpResponseRedirect(reverse_lazy('accounts:login'))

@login_required
def profile_view(request):
    context = {
        'user': request.user,
        'last_login': request.user.last_login,
    }
    return render(request, 'accounts/profile.html', context)

# Alias pour compatibilité avec l'ancien nom
profil_utilisateur = profile_view
