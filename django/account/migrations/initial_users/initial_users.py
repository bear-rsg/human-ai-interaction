"""
A list of default users to add to the database upon initial creation

This data is used in account/migrations/0002_initial_data.py

Data is kept in this separate file to keep users' details confidental
as this file is ignored from git
"""

from django.contrib.auth.hashers import make_password

INITIAL_USERS = [

    # Admins
    {
        "first_name": "Mike",
        "last_name": "Allaway",
        "email": "m.j.allaway@bham.ac.uk",
        "role": "admin",
        "password": make_password('ChangeMe345')
    },
    {
        "first_name": "Marcus",
        "last_name": "Perlman",
        "email": "m.perlman@bham.ac.uk",
        "role": "admin",
        "password": make_password('ChangeMe744')
    },
    {
        "first_name": "Matteo",
        "last_name": "Fuoli",
        "email": "m.fuoli@bham.ac.uk",
        "role": "admin",
        "password": make_password('ChangeMe859')
    },

]
