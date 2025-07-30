from django.db import models
from account.models import User
from ckeditor.fields import RichTextField
from django.utils.timezone import now
from django.urls import reverse
from django.conf import settings
import datetime
import textwrap


class AiModelProvider(models.Model):
    """
    The organisation that provides AI models, e.g. Google, OpenAI
    """

    related_name = 'aimodelproviders'

    name = models.CharField(max_length=200)
    api_key = models.TextField(blank=True, null=True, verbose_name='API key')

    datetime_created = models.DateTimeField(auto_now_add=True, verbose_name='created')
    datetime_updated = models.DateTimeField(auto_now=True, verbose_name='updated')

    admin_notes = models.TextField(blank=True, null=True, help_text="Optional. Only visible to admins in this dashboard.")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'AI Model Provider'
        verbose_name_plural = 'AI Model Providers'
        ordering = ('name', 'id')


class AiModel(models.Model):
    """
    The specific AI model offered by an AI service used within an experiment, e.g. Google's gemini-2.0-flash
    """

    related_name = 'aimodels'

    name = models.CharField(max_length=200)
    ai_model_provider = models.ForeignKey(AiModelProvider, related_name=related_name, on_delete=models.PROTECT, verbose_name='AI model provider')

    datetime_created = models.DateTimeField(auto_now_add=True, verbose_name='created')
    datetime_updated = models.DateTimeField(auto_now=True, verbose_name='updated')

    admin_notes = models.TextField(blank=True, null=True, help_text="Optional. Only visible to admins in this dashboard.")

    def __str__(self):
        return f'{self.ai_model_provider.name} - {self.name}'

    class Meta:
        verbose_name = 'AI Model'
        verbose_name_plural = 'AI Models'
        ordering = ('ai_model_provider', 'name', 'id')


class Modality(models.Model):
    """
    The type of modality/media used within an experiment. E.g. text, audio, video, etc.
    """

    related_name = 'modalities'

    name = models.CharField(max_length=200)
    icon = models.CharField(max_length=200, blank=True, null=True)

    datetime_created = models.DateTimeField(auto_now_add=True, verbose_name='created')
    datetime_updated = models.DateTimeField(auto_now=True, verbose_name='updated')

    admin_notes = models.TextField(blank=True, null=True, help_text="Optional. Only visible to admins in this dashboard.")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'modalities'
        ordering = ('name', 'id')


class ResponderType(models.Model):
    """
    The type of responder used by default for an experiment. E.g. AI, Human, system decides randomly
    """

    related_name = 'respondertypes'

    name = models.CharField(max_length=200)

    datetime_created = models.DateTimeField(auto_now_add=True, verbose_name='created')
    datetime_updated = models.DateTimeField(auto_now=True, verbose_name='updated')

    admin_notes = models.TextField(blank=True, null=True, help_text="Optional. Only visible to admins in this dashboard.")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name', 'id')


class Experiment(models.Model):
    """
    A type of activity that users complete, with a clearly defined set of instructions to follow
    """

    related_name = 'experiments'

    name = models.CharField(max_length=255)
    description = models.TextField(
        blank=True, null=True,
        help_text="A brief description of this experiment aimed at participants"
    )
    instructions = RichTextField(
        blank=True, null=True,
        help_text="Detailed instructions to participants to complete this experiment"
    )
    modality = models.ForeignKey(Modality, related_name=related_name, on_delete=models.PROTECT)
    originator_speaks_first = models.BooleanField(
        default=True,
        help_text="If checked, the <em>originator</em> (the participant who first creates the chat) must send the first message. If unchecked, the <em>responder</em> (the AI or the 2nd participant to join the chat) must speak first"
    )
    responder_type = models.ForeignKey(
        ResponderType,
        related_name=related_name,
        on_delete=models.PROTECT,
        help_text='Whether the responder in this experiment will always be AI, always be human, or system randomly decides'
    )
    ai_model = models.ForeignKey(AiModel, related_name=related_name, on_delete=models.PROTECT, verbose_name='AI model')
    initial_prompt_for_ai_responder = models.TextField(
        blank=True, null=True,
        help_text="Provide the initial prompt to send to the AI responder to explain how they should behave in this experiment"
    )
    survey_url = models.URLField(help_text="Provide a URL for the associated survey, e.g. Qualtrics. This will be embeded in the website and completed by participants following each experiment instance.")
    is_published = models.BooleanField(default=True)

    datetime_created = models.DateTimeField(auto_now_add=True, verbose_name='created')
    datetime_updated = models.DateTimeField(auto_now=True, verbose_name='updated')

    admin_notes = models.TextField(blank=True, null=True, help_text="Optional. Only visible to admins in this dashboard.")

    @property
    def speaks_first(self):
        """ Return the name of the role that speaks first in the chat (originator or responder) """
        return 'originator' if self.originator_speaks_first else 'responder'

    @property
    def speaks_second(self):
        """ Return the name of the role that speaks second in the chat (originator or responder) """
        return 'responder' if self.originator_speaks_first else 'originator'

    @property
    def is_responder_type_ai(self):
        """ Return True if the responder type of this experiment is always AI else return False"""
        return self.responder_type and self.responder_type.name == 'AI'

    @property
    def is_responder_type_random(self):
        """ Return True if the responder type of this experiment is random else return False"""
        return self.responder_type and self.responder_type.name == 'Random (Human or AI)'

    @property
    def description_brief(self):
        return textwrap.shorten(self.description, width=200, placeholder="...")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name', 'id')


class ExperimentInstance(models.Model):
    """
    An instance of a user completing an Experiment
    """

    related_name = 'experimentinstances'

    experiment = models.ForeignKey(Experiment, related_name=related_name, on_delete=models.PROTECT)
    originator = models.ForeignKey(User, related_name=f'{related_name}_originator', on_delete=models.PROTECT)
    responder = models.ForeignKey(User, related_name=f'{related_name}_responder', blank=True, null=True, on_delete=models.PROTECT)
    is_responder_ai = models.BooleanField(blank=True, null=True)
    is_ended_by_user = models.BooleanField(default=False)

    datetime_created = models.DateTimeField(auto_now_add=True, verbose_name='created')
    datetime_updated = models.DateTimeField(auto_now=True, verbose_name='updated')

    admin_notes = models.TextField(blank=True, null=True, help_text="Optional. Only visible to admins in this dashboard.")

    def user_position_in_experiment_instance(self, current_user):
        """ The position of the current user in this experiment instance, e.g. originator, responder, or no_position """
        if current_user == self.originator:
            return 'originator'
        elif current_user == self.responder:
            return 'responder'
        else:
            return 'no_position'

    @property
    def is_responder_type_ai(self):
        """ Return True if the responder type of this experiment is always AI else return False"""
        return self.experiment.is_responder_type_ai

    @property
    def is_responder_determined(self):
        """ Return True if the responder has been determined (as a user or AI) else return False """
        return True if self.is_responder_ai or self.responder else False

    @property
    def is_wait_for_responder_to_be_determined_expired(self):
        return not self.is_responder_determined and self.datetime_created <= now() - datetime.timedelta(minutes=settings.WAIT_FOR_RESPONDER_TO_BE_DETERMINED_MINUTES)

    @property
    def responder_name(self):
        if self.is_responder_ai:
            return 'AI'
        elif self.responder:
            return self.responder.name
        elif not self.is_responder_determined:
            return '-'

    @property
    def wait_to_request_response_seconds(self):
        """ How long to delay on the client when waiting for response, to simulate waiting for a reply """
        if settings.USE_ARTIFICIAL_DELAYS and not self.is_responder_type_ai:
            return settings.WAIT_TO_REQUEST_RESPONSE_SECONDS * 1000
        else:
            return 0

    @property
    def is_active(self):
        # Inactive if user has manually ended the experiment
        if self.is_ended_by_user:
            return False
        # Inactive if the first message was created more than the allowed time
        first_message = self.experimentinstancemessages.first()
        if first_message:
            if first_message.datetime_created <= now() - datetime.timedelta(minutes=settings.EXPERIMENT_INSTANCE_INACTIVE_AFTER_MINUTES_SINCE_FIRST_MESSAGE):
                return False
        # Inactive if there are no messages and the instance was created over 30 minutes ago
        elif self.datetime_created <= now() - datetime.timedelta(minutes=settings.EXPERIMENT_INSTANCE_INACTIVE_AFTER_MINUTES_SINCE_SINCE_CREATED):
            return False
        return True

    @property
    def is_active_html(self):
        if self.is_active:
            return '<span class="active-status active">Active</span>'
        else:
            return '<span class="active-status completed">Completed</span>'

    @property
    def count_messages(self):
        return self.experimentinstancemessages.count()

    @property
    def datetime_started(self):
        if self.count_messages > 0:
            return self.experimentinstancemessages.first().datetime_created

    @property
    def timer(self):
        first_message = self.experimentinstancemessages.first()
        timer_in_seconds = settings.EXPERIMENT_INSTANCE_INACTIVE_AFTER_MINUTES_SINCE_FIRST_MESSAGE * 60
        if first_message:
            return max(
                0,
                timer_in_seconds - int((now() - self.datetime_started).total_seconds())
            )
        else:
            return timer_in_seconds

    def get_absolute_url(self):
        return reverse('experiments:experimentinstance-detail', kwargs={'pk': str(self.id)})

    def __str__(self):
        return f'#{self.id} --- {self.experiment.name} --- Originator: {self.originator} --- Responder: {self.responder_name}'

    def save(self, *args, **kwargs):
        # Ensure there can't be a user assigned to the responder if an AI is already marked as responder
        if self.is_responder_ai:
            self.responder = None
        # Ensure the originator cannot also be the responder
        if self.originator == self.responder:
            self.responder = None
        super().save(*args, **kwargs)

    class Meta:
        ordering = ('-datetime_created', '-id')


class ExperimentInstanceMessage(models.Model):
    """
    A message sent by a originator or responder within an ExperimentInstance
    """

    related_name = 'experimentinstancemessages'

    experiment_instance = models.ForeignKey(ExperimentInstance, related_name=related_name, on_delete=models.PROTECT)
    sender = models.ForeignKey(User, related_name=f'{related_name}_sender', blank=True, null=True, on_delete=models.PROTECT)
    is_sender_ai = models.BooleanField(default=False)
    text = models.TextField()

    datetime_created = models.DateTimeField(auto_now_add=True, verbose_name='created')
    datetime_updated = models.DateTimeField(auto_now=True, verbose_name='updated')

    admin_notes = models.TextField(blank=True, null=True, help_text="Optional. Only visible to admins in this dashboard.")

    def sender_or_receiver(self, current_user=None):
        """ Whether the current user is the sender or receiver of this message """
        return 'sender' if current_user and current_user == self.sender else 'receiver'

    @property
    def is_sender_originator(self):
        """ Whether the sender of the message is the originator in the experiment instance """
        return self.sender == self.experiment_instance.originator

    @property
    def sender_position(self):
        """ Whether the sender of the message is the originator in the experiment instance """
        return 'originator' if self.is_sender_originator else 'responder'

    @property
    def time_created_clean(self):
        """ A human readable time of when the message was created """
        return self.datetime_created.strftime(("%H:%M"))

    @property
    def datetime_created_clean(self):
        """ A human readable datetime of when the message was created """
        return self.datetime_created.strftime(("%Y-%m-%d %H:%M:%S"))

    def __str__(self):
        return f'#{self.id}'

    class Meta:
        ordering = ('datetime_created', 'id')
