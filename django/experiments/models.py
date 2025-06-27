from django.db import models
from account.models import User
from ckeditor.fields import RichTextField
from django.utils.timezone import now
from django.urls import reverse
from django.conf import settings
import datetime
import textwrap


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


class Experiment(models.Model):
    """
    A type of activity that participants complete, with a clearly defined set of instructions to follow
    """

    related_name = 'experiments'

    name = models.CharField(max_length=255)
    modality = models.ForeignKey(Modality, related_name=related_name, on_delete=models.PROTECT)
    description = models.TextField(
        blank=True, null=True,
        help_text="A brief description of this experiment aimed at participants"
    )
    instructions = RichTextField(
        blank=True, null=True,
        help_text="Detailed instructions to participants to complete this experiment"
    )
    initial_prompt_for_ai_host = models.TextField(
        blank=True, null=True,
        help_text="Provide the initial prompt to send to the AI host to explain how they should behave in this experiment"
    )
    is_published = models.BooleanField(default=True)

    datetime_created = models.DateTimeField(auto_now_add=True, verbose_name='created')
    datetime_updated = models.DateTimeField(auto_now=True, verbose_name='updated')

    admin_notes = models.TextField(blank=True, null=True, help_text="Optional. Only visible to admins in this dashboard.")

    @property
    def description_brief(self):
        return textwrap.shorten(self.description, width=200, placeholder="...")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name', 'id')


class ExperimentInstance(models.Model):
    """
    An instance of a participant completing an Experiment
    """

    related_name = 'experimentinstances'

    experiment = models.ForeignKey(Experiment, related_name=related_name, on_delete=models.PROTECT)
    participant = models.ForeignKey(User, related_name=f'{related_name}_participant', on_delete=models.PROTECT)
    host = models.ForeignKey(User, related_name=f'{related_name}_host', blank=True, null=True, on_delete=models.PROTECT)
    is_host_ai = models.BooleanField(blank=True, null=True)
    is_ended_by_user = models.BooleanField(default=False)

    datetime_created = models.DateTimeField(auto_now_add=True, verbose_name='created')
    datetime_updated = models.DateTimeField(auto_now=True, verbose_name='updated')

    admin_notes = models.TextField(blank=True, null=True, help_text="Optional. Only visible to admins in this dashboard.")

    def user_role(self, current_user):
        """ The role of the current user in this experiment instance, e.g. participant, host, or no_role """
        if current_user == self.participant:
            return 'participant'
        elif current_user == self.host:
            return 'host'
        else:
            return 'no_role'

    @property
    def is_host_determined(self):
        """ Return True if the host has been determined (as a user or AI) else return False """
        return True if self.is_host_ai or self.host else False

    @property
    def is_wait_for_host_to_be_determined_expired(self):
        """ Return True if the time allowed for admin to choose a host has expired and so now host must be AI """
        return not self.is_host_determined and self.datetime_created <= now() - datetime.timedelta(minutes=settings.WAIT_FOR_HOST_TO_BE_DETERMINED_MINUTES)

    @property
    def host_name(self):
        if self.is_host_ai:
            return 'AI'
        elif self.host:
            return self.host.name
        elif not self.is_host_determined:
            return '-'

    @property
    def is_active(self):
        # Inactive if user has manually ended the experiment
        if self.is_ended_by_user:
            return False
        # Inactive if the latest message was created over 30 minutes ago
        latest_message = self.experimentinstancemessages.last()
        if latest_message:
            if latest_message.datetime_created <= now() - datetime.timedelta(minutes=settings.EXPERIMENT_INSTANCE_INACTIVE_AFTER_MINUTES):
                return False
        # Inactive if there are no messages and the instance was created over 30 minutes ago
        elif self.datetime_created <= now() - datetime.timedelta(minutes=settings.EXPERIMENT_INSTANCE_INACTIVE_AFTER_MINUTES):
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

    def get_absolute_url(self):
        return reverse('experiments:experimentinstance-detail', kwargs={'pk': str(self.id)})

    def __str__(self):
        return f'#{self.id} --- {self.experiment.name} --- Participant: {self.participant} --- AI Host: {self.is_host_ai}'

    def save(self, *args, **kwargs):
        # Ensure there can't be a user assigned to the host if an AI is already marked as host
        if self.is_host_ai:
            self.host = None
        # Ensure the participant cannot also be the host
        if self.participant == self.host:
            self.host = None
        super().save(*args, **kwargs)

    class Meta:
        ordering = ('-datetime_created', '-id')


class ExperimentInstanceMessage(models.Model):
    """
    A message sent by a participant or host within an ExperimentInstance
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
    def is_sender_participant(self):
        """ Whether the sender of the message is the participant """
        return self.sender == self.experiment_instance.participant

    @property
    def sender_role(self):
        """ Whether the sender of the message is the participant """
        return 'participant' if self.is_sender_participant else 'host'

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


class ExperimentInstanceParticipantFeedback(models.Model):
    """
    A participant provides feedback after completing an Experiment
    """

    related_name = 'experimentinstanceparticipantfeedback'

    experiment_instance = models.ForeignKey(ExperimentInstance, related_name=related_name, on_delete=models.PROTECT)
    participant = models.ForeignKey(User, related_name=f'{related_name}_participant', on_delete=models.PROTECT)
    text = models.TextField()

    datetime_created = models.DateTimeField(auto_now_add=True, verbose_name='created')
    datetime_updated = models.DateTimeField(auto_now=True, verbose_name='updated')

    admin_notes = models.TextField(blank=True, null=True, help_text="Optional. Only visible to admins in this dashboard.")

    def __str__(self):
        return f'Feedback for "{self.experiment_instance.experiment.name}" from: {self.participant}'

    class Meta:
        ordering = ('-datetime_created', '-id')
        verbose_name_plural = 'experiment instance participant feedback'
