# Copy this initial_users.example.py file within this initial_users dir as initial_users.py

"""
A list of default users to add to the database upon initial creation

This data is used in account/migrations/0002_initial_data.py

Data is kept in this separate file to keep users' details confidental
as this file is ignored from git
"""

from django.contrib.auth.hashers import make_password

# Example users - replace with actual users (or leave as an empty list if not needed)
INITIAL_USERS = [
    {
        "username": "joe.bloggs@uni.ac.uk",
        "password": make_password('examplepassword'),
        "role": "admin",

        "first_name": "Joe",
        "last_name": "Bloggs",
    },
    {
        "username": "exampleparticipant",
        "password": make_password('examplepassword'),
        "role": "participant",
    },
]
