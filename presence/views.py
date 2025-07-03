from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.conf import settings

from .models import Agent, Presence, Institution, DivisionEtBureau
from .forms import RapportForm

import datetime
from weasyprint import HTML, CSS

@login_required
@login_required
def dashboard(request):
    aujourd_hui = timezone.now().date()
    mois_courant = aujourd_hui.month
    annee_courante = aujourd_hui.year
    nombreAgents = Agent.objects.count()
    stats = Presence.stats_mois(mois_courant, annee_courante)
    presences_auj = []
    presences_qs = Presence.objects.filter(date=aujourd_hui).select_related('agent')
    for presence in presences_qs:
        agent = presence.agent
        presences_mois = agent.presence_set.filter(date__year=annee_courante, date__month=mois_courant)
        total_presence = presences_mois.filter(statut='P').count()
        total_absence = presences_mois.filter(statut='A').count()
        presences_auj.append({
            'presence': presence,
            'agent': agent,
            'total_presence': total_presence,
            'total_absence': total_absence,
        })
    context = {
        'institution': Institution.objects.first(),
        'stats': stats,
        'nombreAgents': nombreAgents,
        'presences_auj': presences_auj,
        'aujourd_hui': aujourd_hui,
    }
    return render(request, 'presence/dashboard.html', context)


@login_required
def gestion_presences(request):
    date_str = request.GET.get('date')
    if date_str:
        try:
            date_selectionnee = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            date_selectionnee = timezone.now().date()
    else:
        date_selectionnee = timezone.now().date()

    if request.method == 'POST':
        agent_id = request.POST.get('agent_id')
        statut = request.POST.get('statut')
        agent = Agent.objects.get(id=agent_id)
        Presence.objects.update_or_create(
            agent=agent,
            date=date_selectionnee,
            defaults={'statut': statut, 'enregistre_par': request.user}
        )
        return redirect(f"{request.path}?date={date_selectionnee}")

    # Filtres
    q_nom = request.GET.get('q', '')
    departement_id = request.GET.get('departement', '')

    agents_query = Agent.objects.all()

    if q_nom:
        agents_query = agents_query.filter(
            Q(nom__icontains=q_nom) | Q(postnom__icontains=q_nom)
        )

    if departement_id:
        agents_query = agents_query.filter(Division_Bureau_id=departement_id)

    agents_query = agents_query.order_by('nom', 'postnom')

    paginator = Paginator(agents_query, 20)  # 20 agents par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    presences = Presence.objects.filter(date=date_selectionnee)
    presences_map = {p.agent_id: p for p in presences}

    # Enregistrement automatique des absences
    for agent in page_obj.object_list:
        if agent.id not in presences_map:
            p = Presence.objects.create(
                agent=agent,
                date=date_selectionnee,
                statut='A',
                enregistre_par=request.user
            )
            presences_map[agent.id] = p

    departements = DivisionEtBureau.objects.all()

    return render(request, 'presence/gestion_presences.html', {
        'page_obj': page_obj,
        'presences_map': presences_map,
        'date_selectionnee': date_selectionnee,
        'q_nom': q_nom,
        'departement_id': departement_id,
        'departements': departements
    })



def liste_agents(request):
    # Récupérer les paramètres de recherche et filtre
    search_query = request.GET.get('search', '')
    departement_id = request.GET.get('departement', None)
    
    # Construire la queryset de base
    agents = Agent.objects.select_related('Division_Bureau').order_by('nom', 'postnom')
    
    # Appliquer les filtres
    if search_query:
        agents = agents.filter(
            Q(nom__icontains=search_query) | 
            Q(postnom__icontains=search_query) |
            Q(matricule__icontains=search_query)
        )
    
    if departement_id and departement_id != 'all':
        agents = agents.filter(Division_Bureau_id=departement_id)
    
    # Pagination - 10 agents par page
    paginator = Paginator(agents, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Contexte pour le template
    context = {
        'page_obj': page_obj,
        'departements': DivisionEtBureau.objects.all(),
        'selected_departement': departement_id,
        'search_query': search_query,
    }
    
    return render(request, 'presence/liste_agents.html', context)

@login_required
def generer_rapport(request):
    if request.method == 'POST':
        form = RapportForm(request.POST)
        if form.is_valid():
            mois = form.cleaned_data['mois']
            annee = form.cleaned_data['annee']
            # Logique de génération du rapport PDF
            return generer_pdf_rapport(mois, annee)
    else:
        form = RapportForm()
    
    return render(request, 'presence/generer_rapport.html', {'form': form})


#from .utils import generer_pdf_rapport_paysage  # si tu mets la fonction ailleurs


@login_required
def rapport_paysage_view(request):
    if request.method == 'POST':
        form = RapportForm(request.POST)
        if form.is_valid():
            mois = form.cleaned_data['mois']
            annee = form.cleaned_data['annee']
            return generer_pdf_rapport_paysage(mois, annee)
    else:
        form = RapportForm()

    return render(request, 'presence/generer_rapport.html', {
        'form': form,
        'mode': 'paysage'
    })


@login_required
def rapport_paysage_apercu(request):
    if request.method == 'POST':
        form = RapportForm(request.POST)
        if form.is_valid():
            mois = form.cleaned_data['mois']
            annee = form.cleaned_data['annee']
            mois = int(mois)
            annee = int(annee)
            # Génère le même contexte que pour le PDF paysage
            institution = Institution.objects.first()
            logo_abspath = institution.logo.path.replace('\\', '/')
            logo_path = f"file:///{logo_abspath}"
            agents = Agent.objects.all().prefetch_related('presence_set')
            jours_qs = Presence.objects.filter(date__year=annee, date__month=mois).order_by('date')
            jours_ouvrables = sorted(set(p.date.day for p in jours_qs))
            lignes = []
            for i, agent in enumerate(agents, start=1):
                presences = agent.presence_set.filter(date__year=annee, date__month=mois)
                presence_map = {p.date.day: p.statut for p in presences}
                lignes.append({
                    'numero': i,
                    'nom': agent.nom_complet,
                    'matricule': agent.matricule,
                    'grade': agent.grade,
                    'sexe': agent.sexe,
                    'departement': agent.Division_Bureau.nom,
                    'jours': [presence_map.get(j, '-') for j in jours_ouvrables],
                    'jours_ouvrables': len(jours_ouvrables),
                    'np': list(presence_map.values()).count('P'),
                    'na': list(presence_map.values()).count('A'),
                    'remarque': '',
                })
            context = {
                'institution': institution,
                'logo_path': logo_path,
                'mois': mois,
                'annee': annee,
                'mois_nom': [
                    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
                ][mois - 1],
                'lignes': lignes,
                'jours_ouvrables': jours_ouvrables,
                'premiere_page': True,
                'apercu': True,  # Pour adapter le template si besoin
            }
            return render(request, 'presence/partials/_rapport_paysage.html', context)
    # Si GET ou formulaire invalide, retour au formulaire
    return redirect('presence:generer_rapport')


def api_presence(request):
    if request.method == 'POST':
        agent_id = request.POST.get('agent_id')
        date_str = request.POST.get('date')
        
        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            agent = Agent.objects.get(pk=agent_id)
            
            presence, created = Presence.objects.get_or_create(
                agent=agent,
                date=date,
                defaults={
                    'statut': 'P',
                    'enregistre_par': request.user
                }
            )
            
            return JsonResponse({
                'success': True,
                'presence_id': presence.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


def generer_pdf_rapport(mois, annee):
    mois = int(mois)
    annee = int(annee)


    # Récupération des données
    institution = Institution.objects.first()
    logo_abspath = institution.logo.path.replace('\\', '/')
    logo_path = f"file:///{logo_abspath}"
    agents = Agent.objects.all().prefetch_related('presence_set')

    # Préparation des données pour le template
    donnees_agents = []
    for agent in agents:
        presences_mois = agent.presence_set.filter(
            date__year=annee,
            date__month=mois
        )

        donnees_agents.append({
            'agent': agent,
            'presences': presences_mois.filter(statut='P').count(),
            'absences': presences_mois.filter(statut='A').count(),
            'retards': presences_mois.filter(statut='R').count(),
        })

    # Contexte pour le template
    context = {
        'institution': institution,
        'mois': mois,
        'annee': annee,
        'logo_path': logo_path,
        'agents': donnees_agents,
        'mois_nom': [
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ][mois-1],
        'date_generation': timezone.now().strftime("%d/%m/%Y %H:%M"),
        'premiere_page': True,  # Pour le rendu du template
    }

    # Rendu du template HTML
    html_string = render_to_string('presence/partials/_rapport_pdf.html', context)

    # Configuration PDF sans FontConfiguration
    css = CSS(
        string='''
        @page {
            size: A4;
            margin: 1.5cm;
            @top-left {
                content: element(header);
            }
            @bottom-center {
                content: "Page " counter(page) " sur " counter(pages);
                font-size: 9pt;
            }
        }
        body {
            font-family: 'Roboto', sans-serif;
            line-height: 1.5;
        }
        '''
    )

    # Génération du PDF
    html = HTML(string=html_string, base_url=settings.BASE_DIR)
    pdf = html.write_pdf(stylesheets=[css])

    # Réponse HTTP
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_presences_{mois}_{annee}.pdf"'
    return response



def generer_pdf_rapport_paysage(mois, annee):
    institution = Institution.objects.first()
    #logo_path = f"file://{institution.logo.path}" if institution and institution.logo else ""
    
    logo_abspath = institution.logo.path.replace('\\', '/')
    logo_path = f"file:///{logo_abspath}"
    mois = int(mois)
    annee = int(annee)

    institution = Institution.objects.first()
    agents = Agent.objects.all().prefetch_related('presence_set')

    jours_qs = Presence.objects.filter(date__year=annee, date__month=mois).order_by('date')
    jours_ouvrables = sorted(set(p.date.day for p in jours_qs))

    lignes = []
    for i, agent in enumerate(agents, start=1):
        presences = agent.presence_set.filter(date__year=annee, date__month=mois)
        presence_map = {p.date.day: p.statut for p in presences}

        lignes.append({
            'numero': i,
            'nom': agent.nom_complet,
            'matricule': agent.matricule,
            'grade': agent.grade,
            'sexe': agent.sexe,
            'departement': agent.Division_Bureau.nom,
            'jours': [presence_map.get(j, '-') for j in jours_ouvrables],
            'jours_ouvrables': len(jours_ouvrables),
            'np': list(presence_map.values()).count('P'),
            'na': list(presence_map.values()).count('A'),
            'remarque': '',
        })

    context = {
        'institution': institution,
        'logo_path': logo_path,
        'mois': mois,
        'annee': annee,
        'mois_nom': [
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ][mois - 1],
        'lignes': lignes,
        'jours_ouvrables': jours_ouvrables,
        'premiere_page': True,
    }

    html_string = render_to_string('presence/partials/_rapport_paysage.html', context)
    css = CSS(string='''@page { size: A4 landscape; margin: 1.5cm; }
                        @page:last { @bottom-center { content: "Page " counter(page) " sur " counter(pages); font-size: 9pt; } }
                        body { font-family: "DejaVu Sans", sans-serif; font-size: 10pt; }''')
    #print(html_string)
    html = HTML(string=html_string, base_url=settings.MEDIA_ROOT)

    #print(html)
    pdf = html.write_pdf(stylesheets=[css])

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_presences_paysage_{mois}_{annee}.pdf"'
    return response

from django.core.paginator import Paginator

@login_required
def details_agent(request, agent_id):
    agent = Agent.objects.select_related('Division_Bureau').get(pk=agent_id)
    # Recherche par date
    date_query = request.GET.get('date', '')
    presences_qs = Presence.objects.filter(agent=agent).order_by('-date')
    if date_query:
        try:
            presences_qs = presences_qs.filter(date=date_query)
        except:
            pass  # ignore si la date n'est pas valide

    # Pagination
    paginator = Paginator(presences_qs, 10)  # 10 présences par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_presence = presences_qs.filter(statut='P').count()
    total_absence = presences_qs.filter(statut='A').count()
    return render(request, 'presence/details_agents.html', {
        'agent': agent,
        'page_obj': page_obj,
        'total_presence': total_presence,
        'total_absence': total_absence,
        'date_query': date_query,
    })