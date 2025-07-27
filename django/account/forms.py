from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django import forms
from .models import User, UserRole
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3


class PublicUserCreationForm(UserCreationForm):
    """
    Form to specify fields in the user creation form on the public website
    Role is ommitted as this will be set in the view, as users shouldn't choose their own role
    It's used in views.py
    """

    # Account Create Code (prevents unwanted people from creating account)
    participant_account_create_code = forms.CharField(
        label='Account creation code',
        help_text="The code provided by the project team, which is required to create an account. Please contact us to request a code if you don't have one."
    )

    # Google ReCaptcha v3
    captcha = ReCaptchaField(widget=ReCaptchaV3, label='')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""  # removes : from label, e.g. Email: becomes Email
        self.fields['password1'].help_text = "Your password:<br>- can't be too similar to your other personal information.<br>- must contain at least 8 characters.<br>- can't be a commonly used password.<br>- can't be entirely numeric."
        self.fields['username'].help_text = "This should be your Prolific username. If you don't have a Prolific account, please provide a custom username that does NOT include any personally identifiable information (e.g. does not include your name, email address, etc). Make a note of this username, as you'll need it to login."

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('participant_account_create_code', 'username')

    def clean_participant_account_create_code(self):
        """
        Ensure that the participant_account_create_code matches the code defined in the settings
        """
        cleaned_data = self.clean()
        participant_account_create_code = cleaned_data.get('participant_account_create_code')
        # If code is valid, set new user as a 'participant' and set username (otherwise throw error)
        if participant_account_create_code == settings.PARTICIPANT_ACCOUNT_CREATE_CODE:
            self.instance.role = UserRole.objects.get(name='participant')
            return participant_account_create_code
        else:
            self.add_error(
                'participant_account_create_code',
                "The participant account creation code is not valid"
            )


class PublicPasswordChangeForm(PasswordChangeForm):
    """
    Form to specify fields in the password change form, which is accessible through the public website
    It's used in views.py
    """

    # Hide password, as template gives a direct link to it styled more appropriately
    password = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""  # removes : from label, e.g. Email: becomes Email
        self.fields['new_password1'].help_text = "Your password:<br>- can't be too similar to your other personal information.<br>- must contain at least 8 characters.<br>- can't be a commonly used password.<br>- cant be entirely numeric."

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email',)
