from django.contrib import admin
from django.utils.html import format_html
from .models import Institution,  DivisionEtBureau, Agent, Presence

@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'adresse')  # Removed 'telephone'
    search_fields = ('nom', 'adresse')
    ordering = ('nom',)

@admin.register(DivisionEtBureau)
class  DivisionEtBureauAdmin(admin.ModelAdmin):
    list_display = ('nom',)  # Use a method to display institution name
    list_filter = ('nom',)  # Use the correct field name if it exists
    search_fields = ('nom',)
    ordering = ('nom', )  # Use the correct field name if it exists

    def institution_nom(self, obj):
        return obj.institution.nom if obj.institution else ''
    institution_nom.admin_order_field = 'nom'  # Allows sorting by institution name
    institution_nom.short_description = 'Institution'
    @admin.register(Agent)
    class AgentAdmin(admin.ModelAdmin):
        list_display = ('matricule', 'nom_complet', 'Division_Bureau', 'grade', 'sexe', 'photo_preview')
        list_filter = ('Division_Bureau', 'grade', 'sexe')
        search_fields = ('nom', 'postnom', 'matricule', 'Division_Bureau__nom')
        readonly_fields = ('photo_preview',)
        ordering = ('Division_Bureau', 'nom')
        list_select_related = ('Division_Bureau',)
        # Retire raw_id_fields pour afficher un menu déroulant au lieu d'un champ de recherche
        # raw_id_fields = ('departement',)

        def photo_preview(self, obj):
            if obj.photo:
                return format_html('<img src="{}" width="100" />', obj.photo.url)
            return "Aucune photo"
        photo_preview.short_description = 'Aperçu'

@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ('agent', 'date', 'statut', 'type_travail', 'heure_arrivee', 'heure_depart')
    list_filter = ('statut', 'type_travail', 'date', 'agent__Division_Bureau')
    search_fields = ('agent__nom', 'agent__postnom', 'agent__matricule', 'agent__Division_Bureau__nom')
    date_hierarchy = 'date'
    ordering = ('-date',)
    list_select_related = ('agent',)
    raw_id_fields = ('agent',)

    actions = ['marquer_present']

    def marquer_present(self, request, queryset):
        updated = queryset.update(statut='Présent')
        self.message_user(request, f"{updated} présences marquées comme Présent.")
    marquer_present.short_description = "Marquer comme Présent"

# Si tu veux garder l'enregistrement direct :
# admin.site.register(Institution, InstitutionAdmin)
# admin.site.register(DivisionEtBureau, DivisionEtBureauAdmin)
# admin.site.register(Agent, AgentAdmin)
# admin.site.register(Presence, PresenceAdmin)