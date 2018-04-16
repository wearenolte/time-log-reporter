# https://docs.djangoproject.com/en/1.11/howto/custom-management-commands/


from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string


class Command(BaseCommand):
    help = 'Sends the reports regarding yesterday'


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
    
    
    def __get_summary(self, time_entries):
        import datetime
        # Lets read them and calculate the different summaries
        time_per_user = {}
        time_per_project_per_user = {}
        
        for entry in time_entries:
            user_name = entry.get('user').get('name')
            project_name = entry.get('project').get('name')
            task_name = entry.get('task').get('name')
            hours = entry.get('hours')
            notes = entry.get('notes')
            notes = notes if notes != None else ''
            
            self.__add_to_summary(time_per_user, [user_name], 0, hours)
            self.__add_to_summary(time_per_project_per_user, [project_name, user_name, 'description'], '', task_name + ': ' + notes + "\n")
            self.__add_to_summary(time_per_project_per_user, [project_name, user_name, 'hours'], 0, hours)

            
        # Lets create the text for the email
        return render_to_string('report_email.html', {'time_per_user': time_per_user, 'time_per_project_per_user': time_per_project_per_user})

    
    
    def handle(self, *args, **options):
    
        # Import the needed tools
        import datetime
        import urllib.request
        import json
        import os.path
        import sys
        
        # # Only run on weekdays
        # weekday = datetime.datetime.today().weekday()
        # if weekday == 5 or weekday == 6:
            # sys.exit()
        
        # Lets calculate the start and end date
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        yesterday_title = yesterday.strftime("%b %d, %Y")
        yesterday = yesterday.strftime("%Y-%m-%d")
        
        # Lets get the time entries we want
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

        # Lets start sending the email
        email_messages = []
        users = User.objects.all()        
        superadmin_email_addresses = []
        
        for user in users:
            if user.is_superuser and user.email != None and user.email != '':
                superadmin_email_addresses.append(user.email)

        if len(superadmin_email_addresses) > 0:
            email_message = EmailMessage(
                'Summary: ' + yesterday_title,
                self.__get_summary(all_time_entries),
                settings.EMAIL_FROM_ADDRESS,
                bcc = superadmin_email_addresses,
            )
            email_message.content_subtype = 'html'
            email_messages.append(email_message)
            
        # Finally, send the emails
        connection = mail.get_connection()
        connection.send_messages(email_messages)
        