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
    help = 'Sends alerts regarding registered hours yesterday'

    
    def handle(self, *args, **options):
    
        import datetime
        
        # Only run from tuesday to saturday
        weekday = datetime.datetime.today().weekday()
        if weekday == 0 or weekday == 6:
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
            
        # Lets define where intermediate data will be stored
        users_without_team = {}
        user_with_less_than_7_hours = {}
        user_with_less_than_7_hours_per_team = {}
        
        # Lets calculate the start and end date
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        yesterday_title = yesterday.strftime("%b %d, %Y")
        yesterday = yesterday.strftime("%Y-%m-%d")
        
        # Lets get the time entries we want
        all_time_entries = []
        next_page = 1
        total_pages = None
        
        # Requesting each page
        while next_page != None:
            req = urllib.request.Request('https://api.harvestapp.com/api/v2/time_entries?from=' + yesterday + '&to=' + yesterday + '&page=' + str(next_page))
            req.add_header('Harvest-Account-ID', settings.HARVEST_ACCOUNT_ID)
            req.add_header('Authorization', 'Bearer ' + settings.HARVEST_ACCOUNT_TOKEN)
            response = urllib.request.urlopen(req)
            data = json.load(response)
            
            time_entries = data.get('time_entries', None)
            if time_entries != None:
                all_time_entries = all_time_entries + time_entries
            
            next_page = data.get('next_page', None)
            total_pages = data.get('total_pages', None)
        
        # Lets start calculating which emails have to be sent
        email_messages = []
        hours_per_member = {}

        # Lets group time entries by member
        for entry in time_entries:
            member_name = entry.get('user').get('name')
            hours = float(entry.get('hours'))
            
            if not member_name in hours_per_member:
                hours_per_member[member_name] = 0
            
            hours_per_member[member_name] += hours
        
        # Lets register whoever logged less than 7 hours
        for member_name, hours in hours_per_member.items():
            # Lets check if it logged less than 7 hours
            if hours >= 7.0:
                continue
                
            user_with_less_than_7_hours[member_name] = hours

            # Lets check if it has a team
            member = members_per_id.get(member_name)
            if member == None:
                users_without_team[member_name] = True
                continue
            
            team_name = member.team.name
        
            # Lets register members per team with less than 7 hours
            if not team_name in user_with_less_than_7_hours_per_team:
                user_with_less_than_7_hours_per_team[team_name] = {}
            user_with_less_than_7_hours_per_team[team_name][member_name] = hours
        
        # Lets register whoever did not log any hour
        for member in members:
            if not member.name in hours_per_member:
                user_with_less_than_7_hours[member.name] = 0.0
                if not member.team.name in user_with_less_than_7_hours_per_team:
                    user_with_less_than_7_hours_per_team[member.team.name] = {}
                user_with_less_than_7_hours_per_team[member.team.name][member.name] = 0.0

        # If there is some alert to send then lets send it to superadmins first
        if users_without_team or user_with_less_than_7_hours:
            users = User.objects.all()        
            superadmin_email_addresses = []
            
            for user in users:
                if user.is_superuser and user.email != None and user.email != '':
                    superadmin_email_addresses.append(user.email)

            if len(superadmin_email_addresses) > 0:
                email_message = EmailMessage(
                    'Time logging exceptions: ' + yesterday_title,
                    render_to_string('report_alerts.html', {'users_without_team': users_without_team, 'user_with_less_than_7_hours': user_with_less_than_7_hours}),
                    settings.EMAIL_FROM_ADDRESS,
                    bcc = superadmin_email_addresses,
                )
                email_message.content_subtype = 'html'
                email_messages.append(email_message)
            
        # Lets find out the teams of an admin
        teams = Team.objects.all()
        admins_and_teams = {}
        for team in teams:
            if not team.admin.is_superuser and team.admin.email != None and team.admin.email != '':
                if admins_and_teams.get(team.admin.email) == None:
                    admins_and_teams[team.admin.email] = []
                admins_and_teams[team.admin.email].append(team.name)
                
        # Lets find out if there is any member of any team of the admin with less than 7 hours. If so then send an email to that admin
        for admin_email, teams in admins_and_teams.items():
            user_with_less_than_7_hours_for_admin = {}
            for team_name in teams:
                if team_name in user_with_less_than_7_hours_per_team:
                    for member_name, hours in user_with_less_than_7_hours_per_team[team_name].items():
                        user_with_less_than_7_hours_for_admin[member_name] = hours
                    
            if user_with_less_than_7_hours_for_admin:
                email_message = EmailMessage(
                    'Time logging exceptions: ' + yesterday_title,
                    render_to_string('report_alerts.html', {'users_without_team': {}, 'user_with_less_than_7_hours': user_with_less_than_7_hours_for_admin}),
                    settings.EMAIL_FROM_ADDRESS,
                    [admin_email],
                )
                email_message.content_subtype = 'html'
                email_messages.append(email_message)
            
        # Finally, send the emails
        if len(email_messages) > 0:
            connection = mail.get_connection()
            connection.send_messages(email_messages)
        