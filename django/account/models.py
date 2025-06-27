from django.contrib.auth.models import AbstractUser, UserManager
from django.db.models.functions import Upper
from django.db import models
import logging

logger = logging.getLogger(__name__)


class UserRole(models.Model):
    """
    Role for each user, e.g. Admin, Participant
    """

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class CustomUserManager(UserManager):
    def get_by_natural_key(self, username):
        """
        Allow users to login with case-insensitive username

        E.g. both "My.Name@uni.ac.uk" and "my.name@uni.ac.uk" will allow users to login
        """
        return self.get(username__iexact=username)


class User(AbstractUser):
    """
    Custom user extends the standard Django user model, providing additional properties
    """

    objects = CustomUserManager()  # Custom user manager used to allow for case-insensitive usernames

    role = models.ForeignKey(UserRole, on_delete=models.SET_NULL, blank=True, null=True)

    @property
    def name(self):
        if self.first_name and self.last_name:
            return ' '.join((self.first_name, self.last_name))
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            # If no first or last name provided, return first half of email
            return self.username.split('@')[0]  # e.g. mike.allaway in mike.allaway@bham.ac.uk

    @property
    def is_admin(self):
        return self.role.name == 'admin'

    @property
    def is_participant(self):
        return self.role.name == 'participant'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Force email and username to be lower case and identical, so users can login with email
        self.email = self.email.strip().lower()
        self.username = self.email

        # User Roles (to be used below)
        role_admin = UserRole.objects.get(name='admin')
        role_participant = UserRole.objects.get(name='participant')

        # New users will be set as an admin by default
        if not self.role:
            self.role = role_admin

        # Set values for each user role:
        # Admins (full control)
        if self.role == role_admin:
            self.is_staff = True
            self.is_superuser = True
        # Participants (limited access)
        elif self.role == role_participant:
            self.is_staff = False
            self.is_superuser = False

        super().save(*args, **kwargs)

    class Meta:
        ordering = [Upper('first_name'), Upper('last_name'), Upper('email'), 'id']
