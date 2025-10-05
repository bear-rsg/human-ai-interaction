from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.exceptions import PermissionDenied, BadRequest, ObjectDoesNotExist
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from openai import OpenAI, AzureOpenAI
from google import genai
from datetime import datetime
from . import models
import io
import csv
import random


# Reusable values and functions


# Define the AI Clients dict
# Note, there must be corresponding AiModelProvider objects in the database
# for each of the ai services listed below, e.g. Google, OpenAI, etc.
try:
    ai_clients = {}
    for ai_model_provider_obj in models.AiModelProvider.objects.all():
        api_key = ai_model_provider_obj.api_key
        ai_model_provider = ai_model_provider_obj.name.upper()
        # Build ai client for each approved ai service
        ai_client = None
        if ai_model_provider == 'OPENAI':
            ai_client = OpenAI(api_key=api_key)
        elif ai_model_provider == 'GOOGLE':
            ai_client = genai.Client(api_key=api_key)
        elif ai_model_provider == 'UOB_AZURE_OPENAI':
            ai_client = AzureOpenAI(
                api_version=ai_model_provider_obj.api_version,
                azure_endpoint=ai_model_provider_obj.api_endpoint,
                api_key=api_key
            )
        # If ai client has been defined, add it to dict of ai clients
        if ai_client:
            ai_clients[ai_model_provider] = ai_client
except Exception:
    pass  # expected to fail sometimes, e.g. if AiModelProvider model not yet added to db


def get_ai_response_google(experiment_instance, ai_model):
    """
    Provide conversation data to Google-based AI model and return the response text
    """

    # Build conversation history (using past messages from user and model)
    conversation_history = []
    # Add initial system instruction for the experiment
    conversation_history.append(experiment_instance.experiment.initial_prompt_for_ai_responder)
    # Add all messages of this experiment instance
    for message in experiment_instance.experimentinstancemessages.all():
        conversation_history.append({
            'role': 'model' if message.is_sender_ai else 'user',
            'parts': [{'text': message.text}]
        })

    try:
        response = ai_clients['GOOGLE'].models.generate_content(
            model=ai_model,  # e.g. "gemini-2.0-flash"
            config=genai.types.GenerateContentConfig(
                max_output_tokens=500,
                temperature=0.1
            ),
            contents=conversation_history
        )
        return response.text.strip()

    except genai.errors.ServerError as e:
        print(e)


def get_ai_response_openai(experiment_instance, ai_model, ai_client_name):
    """
    Provide conversation data to OpenAI-based AI model and return the response text
    """

    # Build conversation history (using past messages from user and model)
    conversation_history = []
    experiment_instance.experiment.initial_prompt_for_ai_responder
    # Add initial system instruction for the experiment
    conversation_history.append({
        'role': 'system',
        'content': experiment_instance.experiment.initial_prompt_for_ai_responder
    })
    # Add all messages of this experiment instance
    for message in experiment_instance.experimentinstancemessages.all():
        conversation_history.append({
            'role': 'assistant' if message.is_sender_ai else 'user',
            'content': message.text
        })

    try:
        response = ai_clients[ai_client_name].chat.completions.create(
            model=ai_model,  # e.g. "gpt-4o"
            messages=conversation_history
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(e)


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
    if user.is_participant and user not in [experiment_instance.originator, experiment_instance.responder]:
        raise PermissionDenied()
    return experiment_instance


def get_experiment_instances_all():
    """
    Gets all ExperimentInstance objects, including performance improvements
    """

    return models.ExperimentInstance.objects.all().select_related(
        'originator',
        'responder',
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
    only including ones where is_active property is True and current user is the originator or responder.
    Returns as a list of objects, not a queryset.
    """

    return [e for e in experiment_instances if e.is_active and user in [e.originator, e.responder]]


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
        'is_sender_originator': message.is_sender_originator,
        'is_sender_ai': message.is_sender_ai
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
    # Get active (all and for those where current user is the originator)
    experiment_instances_active_all = get_experiment_instances_active_all(experiment_instances_history)
    experiment_instances_active_currentuser = get_experiment_instances_active_currentuser(experiment_instances_active_all, request.user)
    # Limit data in querysets if user is a participant
    if request.user.is_participant:
        # Participants can only view published experiments
        experiments_all = experiments_all.filter(is_published=True)
        # Participants can only view their own history
        experiment_instances_history = experiment_instances_history.filter(Q(originator=request.user) | Q(responder=request.user))
    # Add additional data for admins
    elif request.user.is_admin:
        context.update({
            'experiment_instances_active_responder_none': [e for e in experiment_instances_active_all if not e.is_responder_determined],
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

            Q(originator__first_name__icontains=search) |
            Q(originator__last_name__icontains=search) |
            Q(originator__email__icontains=search) |

            Q(responder__first_name__icontains=search) |
            Q(responder__last_name__icontains=search) |
            Q(responder__email__icontains=search)
        )
    experiment_instances_history = experiment_instances_history.distinct()  # avoids duplicates

    # Participants can only see active instances
    if request.user.is_participant:
        experiment_instances_history = [e for e in experiment_instances_history if e.is_active]

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
        'experiment_instances_history_count': len(experiment_instances_history),
        'experiment_instances_history_countall': experiment_instances_history_countall
    })
    return render(request, 'experiments/index.html', context)


@login_required
def experiment_instance_create_or_join(request):
    """
    Functional view that either:
    - creates a new ExperimentInstance object
    - joins the user to an existing ExperimentInstance object, if one is available

    It then redirects the user to the detail page for this ExperimentInstance object
    (or back to the experiment index page if the object can't be created)
    """

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

    # The experiment_instance will be either the joined or newly created ExperimentInstance object
    create_experiment_instance = True

    # If there are existing active experiments, consider joining one
    experiment_instances_active_all = get_experiment_instances_active_all(get_experiment_instances_all())
    if not experiment.is_responder_type_ai and experiment_instances_active_all:

        # Checks for warnings (e.g. too many active ExperimentInstance objects) and redirect to index if any warning found
        experiment_instances_active_currentuser = get_experiment_instances_active_currentuser(experiment_instances_active_all, request.user)
        experiment_instances_warning_toomanyactive_allusers = settings.EXPERIMENT_INSTANCES_ACTIVE_MAX < len(experiment_instances_active_all)
        experiment_instances_warning_toomanyactive_currentuser = len(experiment_instances_active_currentuser)
        if experiment_instances_warning_toomanyactive_allusers or experiment_instances_warning_toomanyactive_currentuser:
            return redirect(reverse('experiments:index'))

        # If there are any existing ExperimentInstance objects without a Responder
        # either set current user or AI as the Responder
        experiment_instances_active_awaitingresponder = [e for e in experiment_instances_active_all if not e.is_responder_determined]
        if len(experiment_instances_active_awaitingresponder):
            # Set the current user as the responder for the experiment instance
            experiment_instance = experiment_instances_active_awaitingresponder[0]
            experiment_instance.responder = request.user
            experiment_instance.is_responder_ai = False
            experiment_instance.save()
            # User has joined this experiment instance, so no need to create one
            create_experiment_instance = False

    # Create a new ExperimentInstance object (if one hasn't already been joined)
    if create_experiment_instance:
        experiment_instance = models.ExperimentInstance.objects.create(
            experiment=experiment,
            originator=request.user,
        )
        # Set responder to be AI if the experiment responder type is AI (or random and system decides)
        if experiment.is_responder_type_ai or (experiment.is_responder_type_random and random.random() <= settings.PROBABILITY_RESPONDER_IS_AI):
            experiment_instance.is_responder_ai = True
            experiment_instance.save()

    # Redirect user to the detail view of the created/joined ExperimentInstance
    return redirect(reverse('experiments:experimentinstance-detail', kwargs={'pk': experiment_instance.id}))


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
        'is_experiment_instance_responder_determined': experiment_instance.is_responder_determined,
        'user_position_in_experiment_instance': experiment_instance.user_position_in_experiment_instance(request.user),
        'wait_to_request_response_seconds': experiment_instance.wait_to_request_response_seconds
    }
    return render(request, 'experiments/textchat.html', context)


@login_required
def experiment_instance_setresponder(request, pk):
    """
    Functional view that sets the ExperimentInstance responder,
    either as current user or AI. Returns a success/fail data via JSON.
    """

    success = False
    experiment_instance = get_experiment_instance(pk, request.user)
    responder_type = request.POST.get('responder_type', None)
    # If user is admin, a valid responder_type provided, user isn't the originator, and responder is not yet determined
    if request.user.is_admin and responder_type in ['human', 'ai'] and request.user != experiment_instance.originator and not experiment_instance.is_responder_determined:
        experiment_instance.responder = request.user if responder_type == 'human' else None
        experiment_instance.is_responder_ai = responder_type == 'ai'
        experiment_instance.save()
        success = True
    # Return data as JSON
    return JsonResponse({'success': success}, safe=False)


@login_required
def experiment_instance_survey(request, pk):
    """
    Functional view that marks the ExperimentInstance as completed and
    returns a template that includes the experiment survey
    """

    # Mark experiment as ended by user
    experiment_instance = get_experiment_instance(pk, request.user)
    experiment_instance.is_ended_by_user = True
    experiment_instance.save()
    # Return user to template
    context = {'experiment_instance': experiment_instance}
    return render(request, 'experiments/survey.html', context)


@login_required
def experiment_instance_message_list(request, pk):
    """
    Functional view that returns a list of ExperimentInstanceMessage objects
    belonging to the ExperimentInstance object as JSON
    """

    experiment_instance = get_experiment_instance(pk, request.user)

    # Automatically set the responder
    if experiment_instance.is_wait_for_responder_to_be_determined_expired:
        experiment_instance.is_responder_ai = True
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

    # Send a delay for the latest message to client to simulate human typing,
    # if AI is sender (but user doesn't know if sender is AI or human)
    delay_latest_message_seconds = 0
    if settings.USE_ARTIFICIAL_DELAYS and not experiment_instance.is_responder_type_ai and messages and len(messages) == 1 and messages[0]['is_sender_ai']:
        # Average human types 3-4 chars per second so divide chars by 4 (source: Google Gemini)
        delay_latest_message_seconds = len(messages[0]['text']) / 4

    # Return data as JSON
    return JsonResponse(
        {
            'messages': messages,
            'is_responder_determined': experiment_instance.is_responder_determined,
            'is_responder_ai': experiment_instance.is_responder_ai,
            'timer': experiment_instance.timer,
            'delay_latest_message_seconds': delay_latest_message_seconds
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

    # Build response text (using the appropriate AI model provider for this experiment instance)
    response_text = None
    ai_model_provider = experiment_instance.experiment.ai_model.ai_model_provider.name.upper()
    ai_model = experiment_instance.experiment.ai_model.name
    if ai_model_provider == 'GOOGLE':
        response_text = get_ai_response_google(experiment_instance, ai_model)
    elif ai_model_provider == 'OPENAI':
        response_text = get_ai_response_openai(experiment_instance, ai_model, ai_model_provider)
    elif ai_model_provider == 'UOB_AZURE_OPENAI':
        response_text = get_ai_response_openai(experiment_instance, ai_model, ai_model_provider)

    # Create a new ExperimentInstanceMessage object with the response text
    success = False
    if response_text:
        models.ExperimentInstanceMessage.objects.create(
            experiment_instance=experiment_instance,
            sender=None,
            is_sender_ai=True,
            text=response_text
        )
        success = True

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
        data = data.filter(Q(experiment_instance__originator=request.user) | Q(experiment_instance__responder=request.user))
    data = [[d.experiment_instance_id, d.id, d.sender_position, d.datetime_created_clean, d.text.strip()] for d in data]

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
