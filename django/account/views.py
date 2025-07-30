from django.views.generic import (TemplateView, CreateView)
from django.urls import reverse_lazy
from django.shortcuts import render
from django.contrib.auth import login
from django.contrib.auth.views import (PasswordChangeView, PasswordResetView, PasswordResetConfirmView)
from django.contrib.auth.decorators import login_required
from account import forms


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
    success_url = reverse_lazy('experiments:index')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Log the user in (self.object is the user object that was created)
        if not self.request.user.is_authenticated:
            login(self.request, self.object)
        return response


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


@login_required
def withdraw_from_study(request):
    """
    Functional view that sets the 'withdrawn' value of the current user to True
    and renders the withdraw confirmation template.
    """

    user = request.user
    user.withdrawn_from_study = True
    user.is_active = False
    user.save()

    return render(request, 'account/withdraw.html')
