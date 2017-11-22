# time-log-reporter

This application is intended to give a high-level view of team members time tracking to provide insight from the team as well as managers. Time tracking is important as it provides great data to better understand the business and plan.

Take a look at a [possible approach](https://www.getharvest.com/blog/2016/02/using-harvest-api-radical-transparency-clients-almanac/#more-13023).


## Concepts

### Teams
Groups of members that have an administrator (that must be a registered user).

### Members
Defined by a name, they belong to a team.

### Superusers
Managers of teams. They can control entire application.

### Administrators
Managers of specific groups.


## Install

1. Create the settings.py file in time_log_reporter/time_log_reporter from the settings.py.txt file. Edit the database connection credentials and the timezone.
```bash
cp time_log_reporter/time_log_reporter/settings.py.txt time_log_reporter/time_log_reporter/settings.py
```
2. Create the db schema
```bash
cd time_log_reporter
python manage.py makemigrations reports
python manage.py sqlmigrate reports 0001
python manage.py migrate
```
3. Create a superuser for the app
```bash
python manage.py createsuperuser
```

## Run

```bash
python manage.py runserver
```

Open in your browser http://localhost:8000/admin


## Running custom commands

```
python manage.py sendreports
```