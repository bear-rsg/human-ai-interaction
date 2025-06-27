from django.contrib import admin
from . import models


LIST_PER_PAGE = 100


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
                    'is_published',
                    'datetime_created',
                    'datetime_updated')
    list_select_related = ('modality',)
    list_filter = ('modality', 'is_published')
    search_fields = ('name', 'description', 'instructions', 'admin_notes')
    readonly_fields = ('datetime_created', 'datetime_updated')
    list_per_page = LIST_PER_PAGE


@admin.register(models.ExperimentInstance)
class ExperimentInstanceAdminView(admin.ModelAdmin):
    """
    Customise the admin interface for ExperimentInstance model
    """

    list_display = ('id',
                    'experiment',
                    'participant',
                    'host',
                    'is_host_ai',
                    'is_active',
                    'datetime_created',
                    'datetime_updated')
    list_select_related = ('experiment', 'participant', 'host')
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


@admin.register(models.ExperimentInstanceParticipantFeedback)
class ExperimentInstanceParticipantFeedbackAdminView(admin.ModelAdmin):
    """
    Customise the admin interface for ExperimentInstanceParticipantFeedback model
    """

    list_display = ('id',
                    'experiment_instance',
                    'participant',
                    'text',
                    'datetime_created',
                    'datetime_updated')
    list_select_related = ('experiment_instance', 'participant',)
    search_fields = ('text',)
    readonly_fields = ('datetime_created', 'datetime_updated')
    list_per_page = LIST_PER_PAGE
