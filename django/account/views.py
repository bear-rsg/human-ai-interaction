from django.views.generic import (TemplateView, CreateView, UpdateView)
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (PasswordChangeView, PasswordResetView, PasswordResetConfirmView)
from account import (forms, models)


class AccountTemplateView(TemplateView):
    """
    Class-based view to show the account template
    """

    template_name = 'account/account.html'


class UserCreateView(CreateView):
    """
    Class-based view to show the account create template
    """

    template_name = 'account/create.html'
    form_class = forms.PublicUserCreationForm
    success_url = reverse_lazy('account:create-success')


class UserCreateSuccessTemplateView(TemplateView):
    """
    Class-based view to show the account create success template
    """

    template_name = 'account/create-success.html'


class PasswordChangeView(PasswordChangeView):
    """
    Class-based view to show the password change template
    """

    form_class = forms.PublicPasswordChangeForm
    template_name = 'registration/change-password.html'
    success_url = reverse_lazy('account:change-password-success')


class PasswordChangeSuccessTemplateView(TemplateView):
    """
    Class-based view to show the password change success template
    """

    template_name = 'registration/change-password-success.html'


class PasswordResetRequestView(PasswordResetView):
    """
    Class-based view to show the password reset request template
    """

    template_name = 'registration/reset-password-request.html'
    email_template_name = 'registration/reset-password-request-email.txt'
    subject_template_name = 'registration/reset-password-request-subject.txt'
    success_url = reverse_lazy('account:reset-password-request-success')


class PasswordResetRequestSuccessTemplateView(TemplateView):
    """
    Class-based view to show the password reset request success template
    """

    template_name = 'registration/reset-password-request-success.html'


class PasswordResetChangeView(PasswordResetConfirmView):
    """
    Class-based view to show the password reset change template
    """

    template_name = 'registration/reset-password-change.html'
    success_url = reverse_lazy('account:reset-password-change-success')


class PasswordResetChangeSuccessTemplateView(TemplateView):
    """
    Class-based view to show the password reset change success template
    """

    template_name = 'registration/reset-password-change-success.html'
