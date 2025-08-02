from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from presence.models import Presence, Agent

class Command(BaseCommand):
    help = "Initialise les groupes et permissions pour l'application de présence"

    def handle(self, *args, **kwargs):
        # Création des groupes
        admin_group, _ = Group.objects.get_or_create(name='Administrateur')
        agent_rh_group, _ = Group.objects.get_or_create(name='Agent RH')
        employe_group, _ = Group.objects.get_or_create(name='Employé')

        # Récupération des permissions
        presence_ct = ContentType.objects.get_for_model(Presence)
        agent_ct = ContentType.objects.get_for_model(Agent)

        # Permissions personnalisées
        manage_presence = Permission.objects.get(codename='can_manage_presence')
        export_rapport = Permission.objects.get(codename='can_export_rapport')
        view_own = Permission.objects.get(codename='can_view_own_presence')

        # Permissions standards
        all_presence_perms = Permission.objects.filter(content_type=presence_ct)
        all_agent_perms = Permission.objects.filter(content_type=agent_ct)

        # Attribution des permissions
        admin_group.permissions.set(list(all_presence_perms) + list(all_agent_perms))
        agent_rh_group.permissions.set([manage_presence, export_rapport])
        employe_group.permissions.set([view_own])

        self.stdout.write(self.style.SUCCESS("Groupes et permissions initialisés avec succès."))


""" Directement dans le shell :

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from presence.models import Presence

content_type = ContentType.objects.get_for_model(Presence)

Permission.objects.get_or_create(
    codename='can_manage_presence',
    name='Peut gérer les présences',
    content_type=content_type
)

Permission.objects.get_or_create(
    codename='can_export_rapport',
    name='Peut exporter les rapports',
    content_type=content_type
)

Permission.objects.get_or_create(
    codename='can_view_own_presence',
    name='Peut voir ses propres présences',
    content_type=content_type
)


In [1]: from django.contrib.auth.models import Permission

In [2]: from django.contrib.contenttypes.models import ContentType

In [3]: from presence.models import Presence

In [4]: 

In [4]: content_type = ContentType.objects.get_for_model(Presence)

In [5]: 

In [5]: Permission.objects.get_or_create(
   ...:     codename='can_manage_presence',
   ...:         name='Peut gérer les présences',
   ...:             content_type=content_type
   ...:             )
Out[5]: (<Permission: Presence | PRESENCE | Peut gérer les présences>, True)

In [6]: 

In [6]: Permission.objects.get_or_create(
   ...:     codename='can_export_rapport',
   ...:         name='Peut exporter les rapports',
   ...:             content_type=content_type
   ...:             )
Out[6]: (<Permission: Presence | PRESENCE | Peut exporter les rapports>, True)

In [7]: 

In [7]: Permission.objects.get_or_create(
   ...:     codename='can_view_own_presence',
   ...:         name='Peut voir ses propres présences',
   ...:             content_type=content_type
   ...:             )
Out[7]: (<Permission: Presence | PRESENCE | Peut voir ses propres présences>, True)"""