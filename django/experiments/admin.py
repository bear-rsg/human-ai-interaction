from django.contrib import admin
from . import models


LIST_PER_PAGE = 100

# Actions

admin.site.disable_action('delete_selected')


def duplicate_experiments(modeladmin, request, queryset):
    # Copies the content of the public transcription text to the parent letter
    for experiment in queryset:
        models.Experiment.objects.create(
            name=f'{experiment.name} (copy)',
            modality=experiment.modality,
            description=experiment.description,
            instructions=experiment.instructions,
            ai_model=experiment.ai_model,
            initial_prompt_for_ai_responder=experiment.initial_prompt_for_ai_responder,
            survey_url=experiment.survey_url,
            is_published=experiment.is_published,
            admin_notes=experiment.admin_notes
        )


duplicate_experiments.short_description = "Duplicate selected experiments"


@admin.register(models.AiModelProvider)
class AiModelProviderAdminView(admin.ModelAdmin):
    """
    Customise the admin interface for AiModelProvider model
    """

    list_display = ('id',
                    'name',
                    'api_key',
                    'datetime_created',
                    'datetime_updated')
    search_fields = ('name', 'admin_notes')
    readonly_fields = ('datetime_created', 'datetime_updated')
    list_per_page = LIST_PER_PAGE


@admin.register(models.AiModel)
class AiModelAdminView(admin.ModelAdmin):
    """
    Customise the admin interface for AiModel model
    """

    list_display = ('id',
                    'name',
                    'ai_model_provider',
                    'datetime_created',
                    'datetime_updated')
    search_fields = ('name', 'admin_notes')
    readonly_fields = ('datetime_created', 'datetime_updated')
    list_per_page = LIST_PER_PAGE


@admin.register(models.Modality)
class ModalityAdminView(admin.ModelAdmin):
    """
    Customise the admin interface for Modality model
    """

    list_display = ('id',
                    'name',
                    'datetime_created',
                    'datetime_updated')
    search_fields = ('name', 'admin_notes')
    readonly_fields = ('datetime_created', 'datetime_updated')
    list_per_page = LIST_PER_PAGE


@admin.register(models.Experiment)
class ExperimentAdminView(admin.ModelAdmin):
    """
    Customise the admin interface for Experiment model
    """

    list_display = ('id',
                    'name',
                    'description',
                    'modality',
                    'ai_model',
                    'is_published',
                    'datetime_created',
                    'datetime_updated')
    list_select_related = ('modality',)
    list_filter = ('modality', 'is_published')
    search_fields = ('name', 'description', 'instructions', 'admin_notes')
    readonly_fields = ('datetime_created', 'datetime_updated')
    actions = (duplicate_experiments,)
    list_per_page = LIST_PER_PAGE


@admin.register(models.ExperimentInstance)
class ExperimentInstanceAdminView(admin.ModelAdmin):
    """
    Customise the admin interface for ExperimentInstance model
    """

    list_display = ('id',
                    'experiment',
                    'originator',
                    'responder',
                    'is_responder_ai',
                    'is_active',
                    'datetime_created',
                    'datetime_updated')
    list_select_related = ('experiment', 'originator', 'responder')
    list_filter = ('experiment',)
    search_fields = ('admin_notes',)
    readonly_fields = ('datetime_created', 'datetime_updated')
    list_per_page = LIST_PER_PAGE

    def is_active(self, instance):
        return instance.is_active

    is_active.boolean = True


@admin.register(models.ExperimentInstanceMessage)
class ExperimentInstanceMessageAdminView(admin.ModelAdmin):
    """
    Customise the admin interface for ExperimentInstanceMessage model
    """

    list_display = ('id',
                    'experiment_instance',
                    'sender',
                    'is_sender_ai',
                    'text',
                    'datetime_created',
                    'datetime_updated')
    list_select_related = ('experiment_instance', 'sender',)
    search_fields = ('text',)
    readonly_fields = ('datetime_created', 'datetime_updated')
    list_per_page = LIST_PER_PAGE
