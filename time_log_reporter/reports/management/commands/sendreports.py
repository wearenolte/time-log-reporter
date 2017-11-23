# https://docs.djangoproject.com/en/1.11/howto/custom-management-commands/


from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from ...models import Member
from django.template.loader import render_to_string
from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    res = dictionary.get(key)
    if res == None:
        return ''
    return res

@register.filter
def round_if_not_empty(value):
    if value != '':
        r = round(value, 1)
        if r.is_integer():
            return int(r)
        return r
    return ''


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
    
    
    def handle(self, *args, **options):
        self.stdout.write('Starting')
        debug = True
        
        # Import the needed tools
        import urllib.request
        import json
        import datetime
        
        # Lets get members and its data
        members = Member.objects.all()
        members_per_id = {}
        for member in members:
            members_per_id[member.name] = member
        # if debug:
            # print('Members:')
            # print(members_per_id)
        
        # Lets calculate the start and end date
        today = datetime.date.today()
        previous_week = today - datetime.timedelta(weeks=1)
        today = (today - datetime.timedelta(1)).strftime("%Y-%m-%d")
        previous_week = previous_week.strftime("%Y-%m-%d")
        
        # Building the request for time entries
        all_time_entries = []
        next_page = 1
        
        # Requesting each page
        while next_page != None:
            if debug:
                print('Requesting page ' + str(next_page))
                
            # req = urllib.request.Request('https://api.harvestapp.com/api/v2/time_entries?from=' + previous_week + '&to=' + today + '&page=' + str(next_page))
            req = urllib.request.Request('https://api.harvestapp.com/api/v2/time_entries?from=2017-09-20&to=2017-11-23&page=' + str(next_page))
            req.add_header('Harvest-Account-ID', settings.HARVEST_ACCOUNT_ID)
            req.add_header('Authorization', 'Bearer ' + settings.HARVEST_ACCOUNT_TOKEN)
            response = urllib.request.urlopen(req)
            data = json.load(response)
            
            time_entries = data.get('time_entries', None)
            if time_entries != None:
                all_time_entries = all_time_entries + time_entries
                
            next_page = data.get('next_page', None)
            
        if debug:
            print('Total time entries: ' + str(len(time_entries)))
        
        # Lets read them and calculate the different summaries
        time_entries = reversed(time_entries)
        users_without_team = {}
        time_per_team = {}
        time_per_team_per_day = {}
        time_per_team_and_project = {}
        time_per_team_and_project_per_day = {}
        tasks_by_member = {}
        
        for entry in time_entries:
            member_name = entry.get('user').get('name')
            project_name = entry.get('project').get('name')
            task_name = entry.get('task').get('name')
            hours = entry.get('hours')
            notes = entry.get('notes')
            spent_day_of_week = datetime.datetime.strptime(entry.get('spent_date'), "%Y-%m-%d").weekday()
            
            team = None
            member = members_per_id.get(member_name)
            if member == None:
                users_without_team[member_name] = True
                continue
            team = member.team.name
            
            self.__add_to_summary(time_per_team, [team], 0, hours)
            self.__add_to_summary(time_per_team_per_day, [team, spent_day_of_week], 0, hours)
            self.__add_to_summary(time_per_team_and_project, [team, project_name], 0, hours)
            self.__add_to_summary(time_per_team_and_project_per_day, [team, project_name, spent_day_of_week], 0, hours)
            self.__add_to_summary(tasks_by_member, [team, project_name, member_name, spent_day_of_week, task_name, 'description'], '', notes + "\n")
            self.__add_to_summary(tasks_by_member, [team, project_name, member_name, spent_day_of_week, task_name, 'hours'], 0, hours)        
        
        # # Lets output the results
        # if debug:
            # if len(users_without_team) > 0:
                # print('Users without a team:')
                # print(users_without_team)
            # print('Time per team:')
            # print(time_per_team)
            # print('Time per team per day:')
            print(time_per_team_per_day)
            # print('Time per team and project:')
            # print(time_per_team_and_project)
            # print('Time per team and project per day:')
            # print(time_per_team_and_project_per_day)
            # print('Tasks_per_member')
            # print(tasks_by_member)
            
        # Lets create the text for the email for superadmins
        rendered = render_to_string('report_email_superadmin.html', {'users_without_team': users_without_team, 'time_per_team': time_per_team, 'time_per_team_per_day': time_per_team_per_day, 'time_per_team_and_project': time_per_team_and_project, 'time_per_team_and_project_per_day': time_per_team_and_project_per_day, 'tasks_by_member': tasks_by_member})
        print('El email que vamos a mandar:')
        print(rendered)


        # Lets send it to every superuser
        
        self.stdout.write('Finishing')
        