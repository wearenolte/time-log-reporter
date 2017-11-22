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
    def clean_admin(self):
        # When adding or editing a team, the assigned admin cannot be assigned to another team
        admin = self.cleaned_data['admin']
        ok = True
        try:
            current_team = Team.objects.get(admin = admin.id)
            if current_team.id != self.instance.id:
                ok = False
        except Team.DoesNotExist:
            ok = True
        if not ok:
            raise ValidationError("The new administrator is already administrating another group")
        return admin


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


class MemberForm(forms.ModelForm):
    def clean_name(self):
        # When adding or editing a team, the admin can not be assigned to another team
        name = self.cleaned_data['name']
        if Member.objects.filter(name = name).exclude(id = self.instance.id).count() > 0:
            raise ValidationError("Member already exists")
        return name


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
            queryset = self.model.objects.filter(team=request.team.id)
        return queryset, use_distinct
        
    def get_form(self, request, obj=None, **kwargs):
        # Dont ask for the team if it is an admin
        if not request.user.is_superuser:
            self.exclude.append('team')
        return super(MemberAdmin, self).get_form(request, obj, **kwargs)
        
    def save_model(self, request, obj, form, change):
        # If an admin, lets set its team
        if not request.user.is_superuser:
            obj.team = request.team
        super(MemberAdmin, self).save_model(request, obj, form, change)
        
    def has_change_permission(self, request, obj = None):
        # Do not allow admins to change members of other teams
        has_class_permission = super(MemberAdmin, self).has_change_permission(request, obj)
        if not has_class_permission:
            return False
        if obj is not None and not request.user.is_superuser and request.team != obj.team:
            return False
        return True

    

admin.site.register(Team, TeamAdmin)
admin.site.register(Member, MemberAdmin)


admin.site.site_title = 'Time Log Reporter'
admin.site.site_header = 'Time Log Reporter'
admin.site.index_title = 'Administration'