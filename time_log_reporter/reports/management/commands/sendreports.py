# https://docs.djangoproject.com/en/1.11/howto/custom-management-commands/


from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from ...models import Member
from ...models import Team


class Command(BaseCommand):
    help = 'Sends the reports of the current week'


    def __add_to_summary(self, dictionary, keys, initial_value, add_value):
        iteration = dictionary
        for index, key in enumerate(keys):
            if iteration.get(key) == None:
                if index != len(keys) - 1:
                    iteration[key] = {}
                else:
                    iteration[key] = initial_value
            if index == len(keys) - 1:
                iteration[key] += add_value
            else:
                iteration = iteration[key]
    
    
    def __get_summary_for_teams(self, members_per_id, time_entries, teams_to_consider):
        import datetime
        # Lets read them and calculate the different summaries
        users_without_team = {}
        time_per_team = {}
        time_per_team_per_day = {}
        time_per_team_and_project = {}
        time_per_team_and_project_per_day = {}
        time_per_team_project_member = {}
        time_per_team_project_member_day = {}
        
        for entry in time_entries:
            member_name = entry.get('user').get('name')
            project_name = entry.get('project').get('name')
            task_name = entry.get('task').get('name')
            hours = entry.get('hours')
            notes = entry.get('notes')
            notes = notes if notes != None else ''
            spent_day_of_week = datetime.datetime.strptime(entry.get('spent_date'), "%Y-%m-%d").weekday()
            
            team = None
            member = members_per_id.get(member_name)
            if member == None:
                users_without_team[member_name] = True
                continue
            team = member.team.name
            
            if len(teams_to_consider) > 0 and not team in teams_to_consider:
                continue
            
            self.__add_to_summary(time_per_team, [team], 0, hours)
            self.__add_to_summary(time_per_team_per_day, [team, spent_day_of_week], 0, hours)
            self.__add_to_summary(time_per_team_and_project, [team, project_name], 0, hours)
            self.__add_to_summary(time_per_team_and_project_per_day, [team, project_name, spent_day_of_week], 0, hours)
            self.__add_to_summary(time_per_team_project_member, [team, project_name, member_name], 0, hours)
            self.__add_to_summary(time_per_team_project_member_day, [team, project_name, member_name, spent_day_of_week, 'description'], '', task_name + ': ' + notes + "\n")
            self.__add_to_summary(time_per_team_project_member_day, [team, project_name, member_name, spent_day_of_week, 'hours'], 0, hours)        
            
        # Lets create the text for the email
        return render_to_string('report_email.html', {'users_without_team': users_without_team, 'time_per_team': time_per_team, 'time_per_team_per_day': time_per_team_per_day, 'time_per_team_and_project': time_per_team_and_project, 'time_per_team_and_project_per_day': time_per_team_and_project_per_day, 'time_per_team_project_member': time_per_team_project_member, 'time_per_team_project_member_day': time_per_team_project_member_day})

    
    
    def handle(self, *args, **options):
    
        import datetime
        
        # Only run on saturday
        weekday = datetime.datetime.today().weekday()
        if weekday != 5:
            import sys
            sys.exit()
        
        # Import the needed tools
        import urllib.request
        import json
        import os.path
        
        # Lets get members and its data
        members = Member.objects.all()
        members_per_id = {}
        for member in members:
            members_per_id[member.name] = member
        
        # Lets calculate the start and end date
        today = datetime.date.today()
        previous_week = today - datetime.timedelta(weeks=1)
        today = (today - datetime.timedelta(1))
        
        title_date_range = 'from ' + previous_week.strftime("%b %d") + ' to ' + today.strftime("%b %d, %Y")
        if previous_week.strftime("%Y") != today.strftime("%Y"):
            title_date_range = 'from ' + previous_week.strftime("%b %d, %Y") + ' to ' + today.strftime("%b %d, %Y")
        
        today = today.strftime("%Y-%m-%d")
        previous_week = previous_week.strftime("%Y-%m-%d")
        
        # Lets get the time entries we want
        all_time_entries = []
        next_page = 1
        total_pages = None
        
        # Requesting each page
        while next_page != None:
            req = urllib.request.Request('https://api.harvestapp.com/api/v2/time_entries?from=' + previous_week + '&to=' + today + '&page=' + str(next_page))
            req.add_header('Harvest-Account-ID', settings.HARVEST_ACCOUNT_ID)
            req.add_header('Authorization', 'Bearer ' + settings.HARVEST_ACCOUNT_TOKEN)
            response = urllib.request.urlopen(req)
            data = json.load(response)
            
            time_entries = data.get('time_entries', None)
            if time_entries != None:
                all_time_entries = all_time_entries + time_entries
                
            next_page = data.get('next_page', None)
            total_pages = data.get('total_pages', None)

        # Lets start sending the email
        email_messages = []
        users = User.objects.all()        
        superadmin_email_addresses = []
        
        for user in users:
            if user.is_superuser and user.email != None and user.email != '':
                superadmin_email_addresses.append(user.email)

        if len(superadmin_email_addresses) > 0:
            email_message = EmailMessage(
                'WeAreNolte: ' + title_date_range,
                self.__get_summary_for_teams(members_per_id, all_time_entries, []),
                settings.EMAIL_FROM_ADDRESS,
                bcc = superadmin_email_addresses,
            )
            email_message.content_subtype = 'html'
            email_messages.append(email_message)
            
        # Lets prepare and send every mail for every admin of a team
        teams = Team.objects.all()
        admins_and_teams = {}
        for team in teams:
            if not team.admin.is_superuser and team.admin.email != None and team.admin.email != '':
                if admins_and_teams.get(team.admin.email) == None:
                    admins_and_teams[team.admin.email] = []
                admins_and_teams[team.admin.email].append(team.name)
                
        for admin_email, teams in admins_and_teams.items():
            email_message = EmailMessage(
                'WeAreNolte: ' + title_date_range,
                self.__get_summary_for_teams(members_per_id, all_time_entries, teams),
                settings.EMAIL_FROM_ADDRESS,
                [admin_email],
            )
            email_message.content_subtype = 'html'
            email_messages.append(email_message)
            
        # Finally, send the emails
        connection = mail.get_connection()
        connection.send_messages(email_messages)
        