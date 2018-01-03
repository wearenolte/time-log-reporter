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
    
        # Import the needed tools
        import urllib.request
        import json
        import os.path        
        import datetime
        import sys

        # Only run from tuesday to saturday
        weekday = datetime.datetime.today().weekday()
        if weekday == 0 or weekday == 6:
            sys.exit()
        
        # Lets get members and its data
        users = {}
        next_page = 1

        # Requesting each page
        while next_page != None:
            req = urllib.request.Request('https://api.harvestapp.com/api/v2/users?is_active=true' + '&page=' + str(next_page))
            req.add_header('Harvest-Account-ID', settings.HARVEST_ACCOUNT_ID)
            req.add_header('Authorization', 'Bearer ' + settings.HARVEST_ACCOUNT_TOKEN)
            response = urllib.request.urlopen(req)
            data = json.load(response)
            # Extract data
            for user in data.get('users', []):
                users[user.get('id')] = {'id': user.get('id'), 'first_name': user.get('first_name'), 'last_name': user.get('last_name'), 'email': user.get('email'), 'is_contractor': user.get('is_contractor')}
            # Go on
            next_page = data.get('next_page', None)
            
        # Lets calculate the start and end date
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        yesterday_title = yesterday.strftime("%b %d, %Y")
        yesterday = yesterday.strftime("%Y-%m-%d")
        
        # Lets get the time entries we want
        minimum_hours = 7.0
        users_with_less_than_minimum_hours = []
        hours_per_user = {}
        all_time_entries = []
        next_page = 1
        
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
        
        # Lets group time entries by user
        for entry in all_time_entries:
            user_id = entry.get('user').get('id')
            hours = float(entry.get('hours'))
            if not user_id in hours_per_user:
                hours_per_user[user_id] = 0
            hours_per_user[user_id] += hours
        
        # Lets register whoever logged less than minimum_hours
        for user_id, hours in hours_per_user.items():
            if hours < minimum_hours:
                users_with_less_than_minimum_hours.append({'user': users[user_id], 'hours': hours})

        # Lets register whoever did not log any hour
        for user_id, user in users.items():
            if not user_id in hours_per_user:
                users_with_less_than_minimum_hours.append({'user': users[user_id], 'hours': 0.0})
                
        # Prepare results for showing in emails
        email_messages = []
        users_with_less_than_minimum_hours = sorted(users_with_less_than_minimum_hours, key = lambda x: x['user']['last_name'])
        regular_users_with_less_than_minimum_hours = []
        contractors_with_less_than_minimum_hours = []
        for e in users_with_less_than_minimum_hours:
            if e['user']['is_contractor']:
                contractors_with_less_than_minimum_hours.append(e)
            else:
                regular_users_with_less_than_minimum_hours.append(e)

        # If there is some alert to send
        if users_with_less_than_minimum_hours:
            # Lets send it to superadmins
            sys_users = User.objects.all()        
            superadmin_email_addresses = []
            
            for sys_user in sys_users:
                if sys_user.is_superuser and sys_user.email != None and sys_user.email != '':
                    superadmin_email_addresses.append(sys_user.email)

            if len(superadmin_email_addresses) > 0:
                email_message = EmailMessage(
                    'Time logging exceptions: ' + yesterday_title,
                    render_to_string('report_alerts.html', {'minimum_hours': minimum_hours, 'regular_users_with_less_than_minimum_hours': regular_users_with_less_than_minimum_hours, 'contractors_with_less_than_minimum_hours': contractors_with_less_than_minimum_hours}),
                    settings.EMAIL_FROM_ADDRESS,
                    bcc = superadmin_email_addresses,
                )
                email_message.content_subtype = 'html'
                email_messages.append(email_message)
            
        # Finally, send the emails
        if len(email_messages) > 0:
            connection = mail.get_connection()
            connection.send_messages(email_messages)
        