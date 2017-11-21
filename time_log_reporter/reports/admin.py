from django.contrib import admin
from django.views.decorators.cache import never_cache

from .models import Team
from .models import Member
from .models import Membership
from .models import Project



class MembersInline(admin.TabularInline):
    model = Member
    extra = 0
    fields = ['name']
    readonly_fields = ['name']
    can_delete = False
    max_num = 0


class ProjectsInline(admin.TabularInline):
    model = Project
    extra = 0
    fields = ['name', 'estimated_hours']
    readonly_fields = ['name', 'estimated_hours']
    can_delete = False
    max_num = 0


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0


class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'administrator', 'members_amount', 'projects_amount')
    inlines = [MembersInline, ProjectsInline]

    def administrator(self, object):
        return object.admin
    administrator.short_description = 'Administrator'
    
    def members_amount(self, object):
        return object.members.count()
    members_amount.short_description = 'Members'
    
    def projects_amount(self, object):
        return object.projects.count()
    projects_amount.short_description = 'Projects'


class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'team_admin', 'memberships_amount')
    inlines = [MembershipInline]
    
    def team_admin(self, object):
        return object.team.name + ' / ' + object.team.admin.username
    team_admin.short_description = 'Team / Administrator'
    
    def memberships_amount(self, object):
        return object.memberships.count()
    memberships_amount.short_description = 'Projects in'

    
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'estimated_hours', 'team_admin', 'members_amount')
    inlines = [MembershipInline]
    
    def team_admin(self, object):
        return object.team.name + ' / ' + object.team.admin.username
    team_admin.short_description = 'Team / Administrator'

    def members_amount(self, object):
        return object.members.count()
    members_amount.short_description = 'Members'


admin.site.register(Team, TeamAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Project, ProjectAdmin)


admin.site.site_title = 'Time Log Reporter'
admin.site.site_header = 'Time Log Reporter'
admin.site.index_title = 'Administration'