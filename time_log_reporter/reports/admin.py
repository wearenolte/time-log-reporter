from django import forms
from django.contrib import admin
from django.views.decorators.cache import never_cache
from django.core.exceptions import ValidationError

from .models import Team
from .models import Member



class TeamForm(forms.ModelForm):
    class Meta:
        labels = {
            'admin': 'Administrator',
        }


class MembersInline(admin.TabularInline):
    model = Member
    extra = 0
    fields = ['name']
    readonly_fields = ['name']
    can_delete = False
    max_num = 0


class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'administrator', 'members_amount')
    inlines = [MembersInline]
    form = TeamForm

    def administrator(self, object):
        return object.admin
    administrator.short_description = 'Administrator'
    
    def members_amount(self, object):
        return object.members.count()
    members_amount.short_description = 'Members'
    
    def get_form(self, request, obj=None, **kwargs):
        # Dont ask for the admin if it is an admin
        if not request.user.is_superuser:
            self.exclude = ['admin']
            self.readonly_fields = ['name']
        return super(TeamAdmin, self).get_form(request, obj, **kwargs)
    
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super(TeamAdmin, self).get_search_results(request, queryset, search_term)
        # If not a superuser then dont show members from other teams
        if not request.user.is_superuser:
            queryset = self.model.objects.filter(id__in=request.teams).order_by('id')
        return queryset, use_distinct
        
    def has_add_permission(self, request):
        # Only superusers may add teams
        if request.user.is_superuser:
            return True
        return False
        
    def has_change_permission(self, request, obj = None):
        # Do not allow admins to change teams of others
        has_class_permission = super(TeamAdmin, self).has_change_permission(request, obj)
        if not has_class_permission:
            return False
        if obj is not None and not request.user.is_superuser and request.teams.filter(id = obj.id).count() == 0:
            return False
        return True
        
    def has_delete_permission(self, request, obj = None):
        # Do not allow admins to delete teams of others
        has_class_permission = super(TeamAdmin, self).has_delete_permission(request, obj)
        if not has_class_permission:
            return False
        if obj is not None and not request.user.is_superuser and request.teams.filter(id = obj.id).count() == 0:
            return False
        return True


class MemberForm(forms.ModelForm):
    def clean_name(self):
        # When adding or editing a team, the admin can not be assigned to another team
        name = self.cleaned_data['name']
        if Member.objects.filter(name = name).exclude(id = self.instance.id).count() > 0:
            raise ValidationError("Member already exists")
        return name

    def clean_team(self):
        # When adding or editing a team, the admin can not be assigned to another team
        team = self.cleaned_data['team']
        if not self.request.user.is_superuser and self.request.teams.filter(id = team.id).count() == 0:
            raise ValidationError("Choose a valid team")
        return team


class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'team_admin')
    exclude = ['avatar']
    form = MemberForm
    
    def team_admin(self, object):
        return object.team.name + ' / ' + object.team.admin.username
    team_admin.short_description = 'Team / Administrator'
    
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super(MemberAdmin, self).get_search_results(request, queryset, search_term)
        # If not a superuser then dont show members from other teams
        if not request.user.is_superuser:
            queryset = self.model.objects.filter(team__in=request.teams).order_by('id')
        return queryset, use_distinct
        
    def get_form(self, request, obj=None, **kwargs):
        # Lets save the request object in the form
        form = super(MemberAdmin, self).get_form(request, obj=obj, **kwargs)
        form.request = request
        return form
        
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Only a team from the same admin can be assigned
        if not request.user.is_superuser and db_field.name == "team":
            kwargs["queryset"] = request.teams
        return super(MemberAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
        
    def has_change_permission(self, request, obj = None):
        # Do not allow admins to change members of other teams
        has_class_permission = super(MemberAdmin, self).has_change_permission(request, obj)
        if not has_class_permission:
            return False
        if obj is not None and not request.user.is_superuser and request.teams.filter(id = obj.team.id).count() == 0:
            return False
        return True
        
    def has_delete_permission(self, request, obj = None):
        # Do not allow admins to delete teams of others
        has_class_permission = super(MemberAdmin, self).has_delete_permission(request, obj)
        if not has_class_permission:
            return False
        if obj is not None and not request.user.is_superuser and request.teams.filter(id = obj.team.id).count() == 0:
            return False
        return True

    

admin.site.register(Team, TeamAdmin)
admin.site.register(Member, MemberAdmin)


admin.site.site_title = 'Time Log Reporter'
admin.site.site_header = 'Time Log Reporter'
admin.site.index_title = 'Administration'