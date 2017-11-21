from django.contrib import admin
from django.contrib.admin import AdminSite
from django.views.decorators.cache import never_cache

from .models import Team
from .models import Member
from .models import Membership
from .models import Project



class MyAdminSite(AdminSite):
    site_title = 'Time Log Reporter'
    site_header = 'Time Log Reporter'
    index_title = 'Administration'
    
    @never_cache
    def index(self, request, extra_context=None):
        return super(self.__class__, self).index(request, extra_context)
    

class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'team')

    
class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1


class ProjectAdmin(admin.ModelAdmin):
    inlines = [MembershipInline]
    list_display = ('name', 'estimated_hours')



admin_site = MyAdminSite(name='myadmin')
admin_site.register(Team)
admin_site.register(Member, MemberAdmin)
admin_site.register(Project, ProjectAdmin)
