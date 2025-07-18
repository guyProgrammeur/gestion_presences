from pyexpat.errors import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.conf import settings

from .models import Agent, Bureau, Direction, Presence, Institution, Division
from .forms import RapportForm

import datetime
from weasyprint import HTML, CSS

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
    division_id = request.GET.get('division', '')
    bureau_id = request.GET.get('bureau', '')

    agents_query = Agent.objects.all()

    if q_nom:
        agents_query = agents_query.filter(Q(nom__icontains=q_nom) | Q(postnom__icontains=q_nom)| Q(prenom__icontains=q_nom))

    if division_id:
        agents_query = agents_query.filter(bureau__division_id=division_id)

    if bureau_id:
        agents_query = agents_query.filter(bureau_id=bureau_id)
    
    divisions = Division.objects.all()
    bureaux = Bureau.objects.select_related('division').all()
    agents_query = agents_query.order_by('bureau__division__ordre', 'nom', 'postnom', 'prenom')

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

    # Préparation du contexte pour le template
    return render(request, 'presence/gestion_presences.html', {
        'page_obj': page_obj,
        'presences_map': presences_map,
        'date_selectionnee': date_selectionnee,
        'q_nom': q_nom,
        'division_id': division_id,
        'bureau_id': bureau_id,
        'divisions': divisions,
        'bureaux': bureaux
    })


@login_required
def liste_agents(request):
    search_query = request.GET.get('search', '')
    bureau_id = request.GET.get('bureau')
    division_id = request.GET.get('division')
    
    agents = Agent.objects.select_related('bureau', 'division', 'direction').order_by('bureau__division__ordre','nom', 'postnom','prenom')

    if search_query:
        agents = agents.filter(
            Q(nom__icontains=search_query) |
            Q(postnom__icontains=search_query) |
            Q(prenom__icontains=search_query) |
            Q(matricule__icontains=search_query)
        )

    if bureau_id and bureau_id != 'all':
        agents = agents.filter(bureau_id=bureau_id)
    
    if division_id and division_id != 'all':
        agents = agents.filter(division_id=division_id)

    paginator = Paginator(agents, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'divisions': Division.objects.all(),
        'bureaux': Bureau.objects.select_related('division').all(),
        'selected_bureau': bureau_id,
        'selected_division': division_id,
        'search_query': search_query,
    }
    return render(request, 'presence/liste_agents.html', context)



from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone

@csrf_exempt  # facultatif si tu passes bien le token CSRF dans fetch
def update_presence_ajax(request):
    if request.method == 'POST':
        try:
            date_str = request.POST.get('date')
            if date_str:
                date_selectionnee = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                date_selectionnee = timezone.now().date()

            agent_id = request.POST.get('agent_id')
            statut = request.POST.get('statut')
            agent = Agent.objects.get(id=agent_id)
            print(agent, date_selectionnee, statut)
            Presence.objects.update_or_create(
                agent=agent,
                date=date_selectionnee,
                defaults={'statut': statut, 'enregistre_par': request.user}
            )

            # Optionnel : renvoyer HTML mis à jour ou juste un statut
            return JsonResponse({'success': True, 'statut': statut})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

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
            #logo_path = f"file:///{logo_abspath}"
            logo_path = "file:///app/media/institution/logo.png"
            # agents = Agent.objects.select_related('bureau__division').prefetch_related('presence_set') \
            # .order_by('bureau__division__ordre', 'nom', 'postnom', 'prenom')

            #agents = Agent.objects.select_related('bureau__division').prefetch_related('presence_set').order_by('bureau__division__ordre', 'nom', 'postnom', 'prenom')

            #jours_qs = Presence.objects.filter(date__year=annee, date__month=mois).order_by('date','agent__bureau__division__ordre')
            jours_qs = Presence.objects.select_related(
                'agent__bureau__division'
            ).filter(
                date__year=annee,
                date__month=mois
            ).order_by('date', 'agent__bureau__division__ordre')

            #jours_qs = Presence.objects.filter(date__year=annee, date__month=mois).order_by('date','agent__bureau__division__ordre')
            jours_ouvrables = sorted(set(p.date.day for p in jours_qs))
            #lignes = []
            # On suppose qu'il n'y a qu'une direction principale
            direction = Direction.objects.first()
            lignes = []
            numero = 1

            # Chef de direction
            if direction and direction.chef:
                agent = direction.chef
                presences = agent.presence_set.filter(date__year=annee, date__month=mois)
                presence_map = {p.date.day: p.statut for p in presences}

                jours_qs = Presence.objects.filter(date__year=annee, date__month=mois).order_by('date')
                jours_ouvrables = sorted(set(p.date.day for p in jours_qs))
                lignes.append({
                    'numero': numero,
                    'nom': agent.nom_complet,
                    'matricule': agent.matricule,
                    'grade': agent.grade,
                    'sexe': agent.sexe,
                    'departement': direction.abrege,
                    'jours': [presence_map.get(j, '-') for j in jours_ouvrables],
                    'jours_ouvrables': len(jours_ouvrables),
                    'np': list(presence_map.values()).count('P'),
                    'na': list(presence_map.values()).count('A'),
                    'remarque': 'D-CS',
                })
                numero += 1

            # Pour chaque division
            for division in direction.divisions.all().order_by('ordre'):
                # Chef de division
                if division.chef and division.chef != direction.chef:
                    agent = division.chef
                    presences = agent.presence_set.filter(date__year=annee, date__month=mois)
                    presence_map = {p.date.day: p.statut for p in presences}
                    lignes.append({
                        'numero': numero,
                        'nom': agent.nom_complet,
                        'matricule': agent.matricule,
                        'grade': agent.grade,
                        'sexe': agent.sexe,
                        'departement': division.abrege,
                        'jours': [presence_map.get(j, '-') for j in jours_ouvrables],
                        'jours_ouvrables': len(jours_ouvrables),
                        'np': list(presence_map.values()).count('P'),
                        'na': list(presence_map.values()).count('A'),
                        'remarque': 'CD',
                    })
                    numero += 1
                # Pour chaque bureau de la division
                for bureau in division.bureaux.all() :
                    # Chef de bureau
                    if bureau.chef and bureau.chef != direction.chef:
                        agent = bureau.chef
                        presences = agent.presence_set.filter(date__year=annee, date__month=mois)
                        presence_map = {p.date.day: p.statut for p in presences}
                        lignes.append({
                            'numero': numero,
                            'nom': agent.nom_complet,
                            'matricule': agent.matricule,
                            'grade': agent.grade,
                            'sexe': agent.sexe,
                            'departement': f"{division.abrege}/{bureau.abrege}",
                            'jours': [presence_map.get(j, '-') for j in jours_ouvrables],
                            'jours_ouvrables': len(jours_ouvrables),
                            'np': list(presence_map.values()).count('P'),
                            'na': list(presence_map.values()).count('A'),
                            'remarque': 'CB',
                        })
                        numero += 1

                    # Membres du bureau (hors chef)
                    #membres_bureau = bureau.agents.exclude(id=bureau.chef.id if bureau.chef else None)
                    membres_bureau = bureau.agents.exclude(id=bureau.chef.id) if bureau.chef else bureau.agents.all()
                    for agent in membres_bureau:
                        presences = agent.presence_set.filter(date__year=annee, date__month=mois)
                        presence_map = {p.date.day: p.statut for p in presences}
                        lignes.append({
                            'numero': numero,
                            'nom': agent.nom_complet,
                            'matricule': agent.matricule,
                            'grade': agent.grade,
                            'sexe': agent.sexe,
                            'departement': f"{division.abrege}/{bureau.abrege}",
                            'jours': [presence_map.get(j, '-') for j in jours_ouvrables],
                            'jours_ouvrables': len(jours_ouvrables),
                            'np': list(presence_map.values()).count('P'),
                            'na': list(presence_map.values()).count('A'),
                            'remarque': '',
                        })
                        numero += 1

                    # for i, agent in enumerate(agents, start=1):
                    #     presences = agent.presence_set.filter(date__year=annee, date__month=mois)
                    #     presence_map = {p.date.day: p.statut for p in presences}
                    #     lignes.append({
                    #         'numero': i,
                    #         'nom': agent.nom_complet,
                    #         'matricule': agent.matricule,
                    #         'grade': agent.grade,
                    #         'sexe': agent.sexe,
                    #         'departement': agent.rattachement_abrege,
                    #         'jours': [presence_map.get(j, '-') for j in jours_ouvrables],
                    #         'jours_ouvrables': len(jours_ouvrables),
                    #         'np': list(presence_map.values()).count('P'),
                    #         'na': list(presence_map.values()).count('A'),
                    #         'remarque': '',
                    #     })
                    
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


@login_required
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
    #logo_path = f"file:///{logo_abspath}"
    logo_path = "file:///app/media/institution/logo.png"
    #agents = Agent.objects.all().prefetch_related('presence_set')
    agents = Agent.objects.select_related(
        'bureau__division__direction'
    ).prefetch_related(
        'presence_set'
    ).order_by(
        'bureau__division__ordre',        # ou direction__ordre si nécessaire
        'nom', 'postnom', 'prenom'
    )

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


import os

def generer_pdf_rapport_paysage(mois, annee):
    institution = Institution.objects.first()
    #logo_abspath = institution.logo.path.replace('\\', '/') if institution and institution.logo else ""
    #logo_path = f"file:///{logo_abspath}" if logo_abspath else "" <img src="{% static 'images/logo.png' %}" alt="Logo">
    #logo_path = os.path.join(settings.MEDIA_ROOT, 'institution/logo.png')
    logo_path = "file:///app/media/institution/logo.png"
    mois = int(mois)
    annee = int(annee)

    # On suppose qu'il n'y a qu'une direction principale
    direction = Direction.objects.first()
    lignes = []
    numero = 1

    # Chef de direction
    if direction and direction.chef:
        agent = direction.chef
        presences = agent.presence_set.filter(date__year=annee, date__month=mois)
        presence_map = {p.date.day: p.statut for p in presences}

        jours_qs = Presence.objects.filter(date__year=annee, date__month=mois).order_by('date')
        jours_ouvrables = sorted(set(p.date.day for p in jours_qs))
        lignes.append({
            'numero': numero,
            'nom': agent.nom_complet,
            'matricule': agent.matricule,
            'grade': agent.grade,
            'sexe': agent.sexe,
            'departement': direction.abrege,
            'jours': [presence_map.get(j, '-') for j in jours_ouvrables],
            'jours_ouvrables': len(jours_ouvrables),
            'np': list(presence_map.values()).count('P'),
            'na': list(presence_map.values()).count('A'),
            'remarque': 'D-CS',
        })
        numero += 1

    # Pour chaque division
    for division in direction.divisions.all().order_by('ordre'):
        # Chef de division
        if division.chef and division.chef != direction.chef:
            agent = division.chef
            presences = agent.presence_set.filter(date__year=annee, date__month=mois)
            presence_map = {p.date.day: p.statut for p in presences}
            lignes.append({
                'numero': numero,
                'nom': agent.nom_complet,
                'matricule': agent.matricule,
                'grade': agent.grade,
                'sexe': agent.sexe,
                'departement': division.abrege,
                'jours': [presence_map.get(j, '-') for j in jours_ouvrables],
                'jours_ouvrables': len(jours_ouvrables),
                'np': list(presence_map.values()).count('P'),
                'na': list(presence_map.values()).count('A'),
                'remarque': 'CD',
            })
            numero += 1

        # Pour chaque bureau de la division
        for bureau in division.bureaux.all() :
            # Chef de bureau
            if bureau.chef and bureau.chef != direction.chef:
                agent = bureau.chef
                presences = agent.presence_set.filter(date__year=annee, date__month=mois)
                presence_map = {p.date.day: p.statut for p in presences}
                lignes.append({
                    'numero': numero,
                    'nom': agent.nom_complet,
                    'matricule': agent.matricule,
                    'grade': agent.grade,
                    'sexe': agent.sexe,
                    'departement': f"{division.abrege}/{bureau.abrege}",
                    'jours': [presence_map.get(j, '-') for j in jours_ouvrables],
                    'jours_ouvrables': len(jours_ouvrables),
                    'np': list(presence_map.values()).count('P'),
                    'na': list(presence_map.values()).count('A'),
                    'remarque': 'CB',
                })
                numero += 1

            # Membres du bureau (hors chef)
            #membres_bureau = bureau.agents.exclude(id=bureau.chef.id if bureau.chef else None)
            membres_bureau = bureau.agents.exclude(id=bureau.chef.id) if bureau.chef else bureau.agents.all()
            for agent in membres_bureau:
                presences = agent.presence_set.filter(date__year=annee, date__month=mois)
                presence_map = {p.date.day: p.statut for p in presences}
                lignes.append({
                    'numero': numero,
                    'nom': agent.nom_complet,
                    'matricule': agent.matricule,
                    'grade': agent.grade,
                    'sexe': agent.sexe,
                    'departement': f"{division.abrege}/{bureau.abrege}",
                    'jours': [presence_map.get(j, '-') for j in jours_ouvrables],
                    'jours_ouvrables': len(jours_ouvrables),
                    'np': list(presence_map.values()).count('P'),
                    'na': list(presence_map.values()).count('A'),
                    'remarque': '',
                })
                numero += 1

        # Membres de la division sans bureau (hors chef)
        # membres_division = division.agents_sans_bureau.exclude(id=division.chef.id if division.chef else None)
        # for agent in membres_division:
            # presences = agent.presence_set.filter(date__year=annee, date__month=mois)
            # presence_map = {p.date.day: p.statut for p in presences}
            # lignes.append({
            #     'numero': numero,
            #     'nom': agent.nom_complet,
            #     'matricule': agent.matricule,
            #     'grade': agent.grade,
            #     'sexe': agent.sexe,
            #     'departement': division.abrege,
            #     'jours': [presence_map.get(j, '-') for j in jours_ouvrables],
            #     'jours_ouvrables': len(jours_ouvrables),
            #     'np': list(presence_map.values()).count('P'),
            #     'na': list(presence_map.values()).count('A'),
            #     'remarque': '',
            # })
            # numero += 1

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
    html = HTML(string=html_string, base_url=settings.MEDIA_ROOT)
    pdf = html.write_pdf(stylesheets=[css])

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_presences_paysage_{mois}_{annee}.pdf"'
    return response




from django.shortcuts import get_object_or_404
from datetime import datetime

@login_required
def details_agent(request, agent_id):
    agent = get_object_or_404(Agent.objects.select_related('bureau__division'), pk=agent_id)

    date_query = request.GET.get('date', '')
    presences_qs = Presence.objects.filter(agent=agent).order_by('-date')

    # Filtrage par date (si au format valide YYYY-MM-DD)
    if date_query:
        try:
            date_obj = datetime.strptime(date_query, '%Y-%m-%d').date()
            presences_qs = presences_qs.filter(date=date_obj)
        except ValueError:
            messages.warning(request, "Date invalide. Format attendu : AAAA-MM-JJ")

    # Pagination
    paginator = Paginator(presences_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'agent': agent,
        'page_obj': page_obj,
        'total_presence': presences_qs.filter(statut='P').count(),
        'total_absence': presences_qs.filter(statut='A').count(),
        'total_retard': presences_qs.filter(statut='R').count(),
        'date_query': date_query,
    }
    return render(request, 'presence/details_agents.html', context)
