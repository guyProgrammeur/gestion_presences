from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class SessionExpiryMiddleware:
    """
    Middleware pour détecter une redirection vers login avec ?next
    et marquer une session comme expirée si l'utilisateur n'est pas connecté.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Vérifie si la session est expirée
        if request.path == reverse('accounts:login'):
            if 'next' in request.GET and not request.user.is_authenticated:
                if not request.session.get('_has_expired_warning'):
                    request.session['_has_expired_warning'] = True

        
        
        #response = self.get_response(request)

        return response
def session_expired_redirect(request):
    """
    Redirige vers la page de connexion avec un message d'avertissement
    si la session a expiré.
    """
    messages.warning(request, "Votre session a expiré. Veuillez vous reconnecter.")
    return redirect('accounts:login')
def session_expired_middleware(get_response):
    """
    Middleware pour gérer les sessions expirées.
    Si la session a expiré, redirige vers la page de connexion avec un message.
    """
    def middleware(request):
        response = get_response(request)
        # Vérifie si la session a expiré
        if not request.user.is_authenticated and request.session.get('_has_expired_warning'):
            return session_expired_redirect(request)

        #response = get_response(request)
        return response

    return middleware