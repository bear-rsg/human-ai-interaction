from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.exceptions import PermissionDenied, BadRequest, ObjectDoesNotExist
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.core.mail import send_mail
from openai import OpenAI
from google import genai
from datetime import datetime
from . import models
import time
import io
import csv


# Reusable values and functions


# Establish the AI client
ai_client = genai.Client(api_key=settings.EXPERIMENTS_AI_API_KEYS['GOOGLE'])


def get_experiment_instance(pk, user):
    """
    Returns an ExperimentInstance object, if exists.
    Checks the user has permissions to access this object.
    """

    # Get ExperimentIntance object by provided pk
    try:
        experiment_instance = models.ExperimentInstance.objects.get(id=pk)
    except ObjectDoesNotExist:
        raise BadRequest('No matching ExperimentInstance object found')
    # Block access if user is a participant and not associated with this ExperimentInstance
    if user.is_participant and user != experiment_instance.participant:
        raise PermissionDenied()
    return experiment_instance


def get_experiment_instances_all():
    """
    Gets all ExperimentInstance objects, including performance improvements
    """

    return models.ExperimentInstance.objects.all().select_related(
        'participant',
        'host',
        'experiment'
    ).prefetch_related('experimentinstancemessages')


def get_experiment_instances_active_all(experiment_instances):
    """
    Filters the passed queryset of ExperimentInstance objects,
    only including ones where is_active dynamic property is True.
    Returns as a list of objects, not a queryset.
    """

    return [e for e in experiment_instances if e.is_active]


def get_experiment_instances_active_currentuser(experiment_instances, user):
    """
    Filters the passed queryset of ExperimentInstance objects,
    only including ones where is_active dynamic property is True and current user is the participant.
    Returns as a list of objects, not a queryset.
    """

    return [e for e in experiment_instances if e.is_active and e.participant == user]


def create_message_dict_for_client(message, user=None):
    """
    Take an ExperimentInstanceMessage object and create a dictionary
    containing only the data needed for the client
    """

    return {
        'id': message.id,
        'text': message.text.replace('\n', '<br>'),  # allow for linebreaks on page
        'datetime': message.datetime_created_clean,
        'time': message.time_created_clean,
        'sender_or_receiver': message.sender_or_receiver(user),
        'is_sender_participant': message.is_sender_participant
    }


# Views


@login_required
def experiment_index(request):
    """
    Functional view for displaying the 'index' page for experiments,
    which allows the user to create a new ExperimentInstance object
    or browse a history of existing ExperimentInstances objects relevant to them.
    """

    context = {}

    # Build initial querysets
    experiments_all = models.Experiment.objects.all().select_related('modality')
    experiment_instances_history = get_experiment_instances_all()
    # Get active (all and for those where current user is the participant)
    experiment_instances_active_all = get_experiment_instances_active_all(experiment_instances_history)
    experiment_instances_active_currentuser = get_experiment_instances_active_currentuser(experiment_instances_active_all, request.user)
    # Limit data in querysets if user is a participant
    if request.user.is_participant:
        # Participants can only view active experiments
        experiments_all = experiments_all.filter(is_published=True)
        # Participants can only view their own history
        experiment_instances_history = experiment_instances_history.filter(participant=request.user)
    # Add additional data for admins
    elif request.user.is_admin:
        context.update({
            'experiment_instances_active_host_none': [e for e in experiment_instances_active_all if not e.is_host_determined],
            'experiment_instances_active_host_currentuser': [e for e in experiment_instances_active_all if e.host == request.user]
        })

    # Get a count of all before search and show limits are applied
    experiment_instances_history_countall = experiment_instances_history.count()

    # Perform search
    search = request.GET.get('search', None)
    if search:
        experiment_instances_history = experiment_instances_history.filter(
            Q(experiment__name__icontains=search) |
            Q(experiment__description__icontains=search) |
            Q(experiment__instructions__icontains=search) |

            Q(participant__first_name__icontains=search) |
            Q(participant__last_name__icontains=search) |
            Q(participant__email__icontains=search) |

            Q(host__first_name__icontains=search) |
            Q(host__last_name__icontains=search) |
            Q(host__email__icontains=search)
        )
    experiment_instances_history = experiment_instances_history.distinct()  # avoids duplicates

    # Limit number of results to show
    show = request.GET.get('show', None)
    show_limit = None
    if show not in [None, 'all']:
        show_limit = int(show)
    elif show is None:
        show_limit = 25  # default
    if show_limit:
        experiment_instances_history = experiment_instances_history[:show_limit]

    # Add data to context and return it with the template
    context.update({
        'experiments_all': experiments_all.distinct(),
        'experiment_instances_warning_toomanyactive_allusers': settings.EXPERIMENT_INSTANCES_ACTIVE_MAX < len(experiment_instances_active_all),
        'experiment_instances_warning_toomanyactive_currentuser': len(experiment_instances_active_currentuser),
        'experiment_instances_history': experiment_instances_history,
        'experiment_instances_history_count': experiment_instances_history.count(),
        'experiment_instances_history_countall': experiment_instances_history_countall
    })
    return render(request, 'experiments/index.html', context)


@login_required
def experiment_instance_create(request):
    """
    Functional view that creates a new ExperimentInstance object
    and redirects the user to the detail page for this object.
    If it cannot be created (e.g. too many active ExperimentInstance objects)
    then it will redirect user back to the experiment index page.
    """

    # Checks for warnings (e.g. too many active ExperimentInstance objects) and redirect to index if any warning found
    experiment_instances_active_all = get_experiment_instances_active_all(get_experiment_instances_all())
    experiment_instances_active_currentuser = get_experiment_instances_active_currentuser(experiment_instances_active_all, request.user)
    experiment_instances_warning_toomanyactive_allusers = settings.EXPERIMENT_INSTANCES_ACTIVE_MAX < len(experiment_instances_active_all)
    experiment_instances_warning_toomanyactive_currentuser = len(experiment_instances_active_currentuser)
    if experiment_instances_warning_toomanyactive_allusers or experiment_instances_warning_toomanyactive_currentuser:
        return redirect(reverse('experiments:index'))

    # Get an Experiment object using the experiment_id from the POST request
    try:
        experiment_id = int(request.POST.get('experiment_id', None))
        if experiment_id is None:
            raise BadRequest('No valid experiment_id provided')
        experiment = models.Experiment.objects.get(id=experiment_id)
    except (TypeError, ValueError):
        raise BadRequest('No valid experiment_id provided')
    except ObjectDoesNotExist:
        raise BadRequest('No matching Experiment object found for provided experiment_id')

    # Create a new ExperimentInstance object
    experiment_instance = models.ExperimentInstance.objects.create(
        experiment=experiment,
        participant=request.user,
    )

    experiment_instance_url = reverse('experiments:experimentinstance-detail', kwargs={'pk': experiment_instance.id})

    # Email admins to alert them, so they can set a host if needed
    try:
        send_mail(
            'Human-AI Interaction: New Experiment Instance Started',
            f"A new experiment instance has started and requires a host:\n\nUser: {request.user}\nExperiment: {experiment}\nLink: {request.build_absolute_uri(experiment_instance_url)}\n\nIf a host hasn't been manually selected after {settings.WAIT_FOR_HOST_TO_BE_DETERMINED_MINUTES} minutes, the AI host will be automatically set.",
            settings.DEFAULT_FROM_EMAIL,
            settings.NOTIFICATION_EMAIL,
            fail_silently=False
        )
    except Exception:
        print("Failed to send email")

    # Redirect user to the detail view of the newly created ExperimentInstance
    return redirect(experiment_instance_url)


@login_required
def experiment_instance_detail(request, pk):
    """
    Functional view that returns a suitable template with required data
    for an ExperimentInstance object
    """

    experiment_instance = get_experiment_instance(pk, request.user)
    context = {
        'experiment_instance': experiment_instance,
        'is_experiment_instance_active': experiment_instance.is_active,
        'is_experiment_instance_host_determined': experiment_instance.is_host_determined,
        'user_role_in_experiment_instance': experiment_instance.user_role(request.user)
    }
    return render(request, 'experiments/textchat.html', context)


@login_required
def experiment_instance_sethost(request, pk):
    """
    Functional view that sets the ExperimentInstance host,
    either as current user or AI. Returns a success/fail data via JSON.
    """

    success = False
    experiment_instance = get_experiment_instance(pk, request.user)
    host_type = request.POST.get('host_type', None)
    # If user is admin, a valid host_type provided, user isn't the participant, and host is not yet determined
    if request.user.is_admin and host_type in ['human', 'ai'] and request.user != experiment_instance.participant and not experiment_instance.is_host_determined:
        experiment_instance.host = request.user if host_type == 'human' else None
        experiment_instance.is_host_ai = host_type == 'ai'
        experiment_instance.save()
        success = True
    # Return data as JSON
    return JsonResponse({'success': success}, safe=False)


@login_required
def experiment_instance_completed(request, pk):
    """
    Functional view that marks the ExperimentInstance as completed and
    returns a suitable template with required data
    """

    # Mark experiment as ended by user
    experiment_instance = get_experiment_instance(pk, request.user)
    experiment_instance.is_ended_by_user = True
    experiment_instance.save()
    # Return user to template
    context = {'experiment_instance': experiment_instance}
    return render(request, 'experiments/completed.html', context)


@login_required
def experiment_instance_feedback(request, pk):
    """
    Functional view that stores feedback from a participant of an ExperimentInstance
    and redirects the user to the experiments index page
    """

    text = request.POST.get('text', None)
    if text:
        experiment_instance = get_experiment_instance(pk, request.user)
        models.ExperimentInstanceParticipantFeedback.objects.create(
            experiment_instance=experiment_instance,
            participant=request.user,
            text=text
        )

    # Redirect user to the detail view of the newly created ExperimentInstance
    return redirect(reverse('experiments:index'))


@login_required
def experiment_instance_message_list(request, pk):
    """
    Functional view that returns a list of ExperimentInstanceMessage objects
    belonging to the ExperimentInstance object as JSON
    """

    experiment_instance = get_experiment_instance(pk, request.user)

    # Automatically set the host
    if experiment_instance.is_wait_for_host_to_be_determined_expired:
        experiment_instance.is_host_ai = True
        experiment_instance.save()

    # Get all messages for experiment instance
    messages = experiment_instance.experimentinstancemessages.all().order_by('datetime_created')
    # If 'latest_message_id' parameter provided, only show messages since this
    latest_message_id = request.GET.get('latest_message_id', None)
    if latest_message_id:
        latest_message = models.ExperimentInstanceMessage.objects.get(id=latest_message_id)
        messages = messages.filter(datetime_created__gt=latest_message.datetime_created)
    # Build a list of new messages, where each message is a dict containing only required data
    messages = [create_message_dict_for_client(m, request.user) for m in messages]
    # Return data as JSON
    return JsonResponse(
        {
            'messages': messages,
            'is_host_determined': experiment_instance.is_host_determined,
            'is_host_ai': experiment_instance.is_host_ai,
        }, safe=False
    )


@login_required
def experiment_instance_message_new_user(request, pk):
    """
    Functional view that creates a new ExperimentInstanceMessage object
    belonging to an ExperimentInstance object and returns as JSON.
    The new object was generated by a user (e.g. a participant or an admin).
    """

    # Get all messages for experiment instance
    experiment_instance = get_experiment_instance(pk, request.user)
    # Ensure the experiment instance is active
    if not experiment_instance.is_active:
        return JsonResponse({'experiment_instance_active': False}, safe=False)
    # Get the required message_text data
    message_text = request.POST.get('message_text', None)
    if not message_text:
        raise BadRequest('Missing required parameter: message_text')
    # Create a new ExperimentInstanceMessage object
    experiment_instance_message = models.ExperimentInstanceMessage.objects.create(
        experiment_instance=experiment_instance,
        sender=request.user,
        text=message_text
    )
    # Create the message dictionary
    message = create_message_dict_for_client(experiment_instance_message, request.user)
    # Return data as JSON
    return JsonResponse({'message': message, 'experiment_instance_active': True}, safe=False)


@login_required
def experiment_instance_message_new_ai(request, pk):
    """
    Functional view that creates a new ExperimentInstanceMessage object
    belonging to an ExperimentInstance object and returns success/fail as JSON.
    The message text new object was generated by an AI/LLM.
    """

    # Get all messages for experiment instance
    experiment_instance = get_experiment_instance(pk, request.user)

    #OpenAI TODO - finish or delete
    # openai_client = OpenAI(api_key=settings.EXPERIMENTS_AI_API_KEYS['OPENAI'])
    # response = openai_client.responses.create(
    #     model="gpt-4o",
    #     instructions="You are a coding assistant that talks like a pirate.",
    #     input="How do I check if a Python object is an instance of a class?",
    # )
    # response_text = response.output_text

    # Google
    try:

        # Build conversation history (using past messages from user and model)
        conversation_history = []
        # Add initial instruction for the experiment
        conversation_history.append(experiment_instance.experiment.initial_prompt_for_ai_host)
        # Add al messages of this experiment instance
        for message in experiment_instance.experimentinstancemessages.all():
            conversation_history.append({
                'role': 'model' if message.is_sender_ai else 'user',
                'parts': [{'text': message.text}]
            })

        # Get response text from LLM
        response = ai_client.models.generate_content(
            model="gemini-2.0-flash",
            config=genai.types.GenerateContentConfig(
                # system_instruction="We are playing a game. You must guess a random number between 1 and 100. You must not talk about anything else. You must keep your answer brief. You must only say a random whole number between 1 and 100.",
                max_output_tokens=500,
                temperature=0.1
            ),
            contents=conversation_history  # experiment_instance.experimentinstancemessages.last().text
        )
        response_text = response.text.strip()

        # Wait for a suitable length to mimic how long it could take a human to type the response text
        delay_seconds = len(response_text) / 10
        print(f'\nDelay AI response by: {delay_seconds} seconds\n')
        time.sleep(delay_seconds)

        try:
            # Create a new ExperimentInstanceMessage object with the response text
            models.ExperimentInstanceMessage.objects.create(
                experiment_instance=experiment_instance,
                sender=None,
                is_sender_ai=True,
                text=response_text
            )
            success = True
        except Exception:
            success = False

    except genai.errors.ServerError as e:
        success = False
        # Email admins to alert them, so they can set a host if needed
        try:
            send_mail(
                'Human-AI Interaction: Error using AI API',
                f"An error has occurred when trying to use an external AI API:\n\nError message: {e}\n\nPlease contact the software developer if you believe this is a problem.",
                settings.DEFAULT_FROM_EMAIL,
                settings.NOTIFICATION_EMAIL,
                fail_silently=False
            )
        except Exception:
            print("Failed to send email")

    # Return data as JSON
    return JsonResponse({'success': success}, safe=False)


@login_required
def experiment_instance_exportdata(request):
    """
    Functional view that exports data from multiple ExperimentInstance objects
    into a CSV file, which is then returned to be downloaded by the user
    """

    # Define the content (column titles and data) to write to file
    column_titles = [["Experiment Instance", "Message", "Sender", "Sent time", "Text"]]
    experiment_instance_id = request.GET.get('experiment_instance_id', None)
    data = models.ExperimentInstanceMessage.objects.all().select_related('experiment_instance', 'sender')
    # If experiment instance id provided, only include data for this ExperimentInstance object
    if experiment_instance_id:
        data = data.filter(experiment_instance_id=experiment_instance_id)
    if request.user.is_participant:
        data = data.filter(experiment_instance__participant=request.user)
    data = [[d.experiment_instance_id, d.id, d.sender_role, d.datetime_created_clean, d.text.strip()] for d in data]

    # Create an in-memory text buffer (StringIO for CSV writer)
    csv_buffer = io.StringIO()
    # Create a CSV writer object
    csv_writer = csv.writer(csv_buffer)
    # Write data to the CSV buffer
    csv_writer.writerows(column_titles + data)
    csv_file_content = csv_buffer.getvalue()
    csv_buffer.close()

    # Create and return the file as response
    response = HttpResponse(csv_file_content, content_type='text/csv')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    response['Content-Disposition'] = f'attachment; filename="exported_list_data_{timestamp}.csv"'
    return response
