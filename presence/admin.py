from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Institution, Direction, Division, Bureau,
    Agent, Presence,JourOuvrable, JourFerie
)



@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'adresse')  # Removed 'telephone'
    search_fields = ('nom', 'adresse')
    ordering = ('nom',)

@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'abrege', 'chef')
    search_fields = ('nom', 'abrege','chef__nom', 'chef__postnom')
    ordering = ('nom',)
    def direction_nom(self, obj):
        return obj.nom if obj else ''
    direction_nom.admin_order_field = 'nom'  # Allows sorting by direction name
    direction_nom.short_description = 'Direction'

@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'abrege', 'direction', 'chef')
    list_filter = ('direction',)
    search_fields = ('nom', 'abrege','direction__nom', 'chef__nom')
    ordering = ('direction', 'nom')
    def division_nom(self, obj):
        return obj.nom if obj else ''
    division_nom.admin_order_field = 'nom'  # Allows sorting by division name
    division_nom.short_description = 'Division'

@admin.register(Bureau)
class BureauAdmin(admin.ModelAdmin):
    list_display = ('nom', 'abrege', 'division', 'chef')
    list_filter = ('division', 'division__direction')
    ordering = ('nom',)
    search_fields = ('nom', 'division__nom', 'direction__nom', 'chef__nom')

    ordering = ('direction', 'division', 'nom')
    def bureau_nom(self, obj):
        return obj.nom if obj else ''
    bureau_nom.admin_order_field = 'nom'  # Allows sorting by bureau name
    bureau_nom.short_description = 'Bureau'
    


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = (
        'matricule', 'nom_complet', 'grade', 'sexe',
        'bureau', 'division', 'direction',
        'photo_preview'
    )
    list_filter = ('grade', 'sexe', 'bureau__nom', 'division__nom', 'direction__nom')
    search_fields = ('nom', 'postnom', 'prenom', 'matricule')
    readonly_fields = ('photo_preview',)
    ordering = ('nom', 'postnom')

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="70" />', obj.photo.url)
        return "Aucune photo"
    photo_preview.short_description = 'Aperçu'
    def affichage_rattachement(self, obj):
        return obj.rattachement_complet
    affichage_rattachement.short_description = 'Affectation'
@admin.register(Presence)

class PresenceAdmin(admin.ModelAdmin):
    list_display = ('agent', 'date', 'statut', 'type_travail', 'heure_arrivee', 'heure_depart')
    list_filter = ('statut', 'type_travail', 'date', 'agent__bureau')
    search_fields = ('agent__nom', 'agent__postnom', 'agent__matricule', 'agent__bureau__nom')
    date_hierarchy = 'date'
    ordering = ('-date',)
    list_select_related = ('agent',)
    raw_id_fields = ('agent',)

    actions = ['marquer_present']

    def marquer_present(self, request, queryset):
        updated = queryset.update(statut='Présent')
        self.message_user(request, f"{updated} présences marquées comme Présent.")
    marquer_present.short_description = "Marquer comme Présent"

@admin.register(JourOuvrable)
class JourOuvrableAdmin(admin.ModelAdmin):
    list_display = ("jour", "est_ouvrable")
    list_editable = ("est_ouvrable",)

@admin.register(JourFerie)
class JourFerieAdmin(admin.ModelAdmin):
    list_display = ("date", "description")
    search_fields = ("description",)
    list_filter = ("date",)


# Si tu veux garder l'enregistrement direct :
# admin.site.register(Institution, InstitutionAdmin)
# admin.site.register(Agent, AgentAdmin)
# admin.site.register(Presence, PresenceAdmin)