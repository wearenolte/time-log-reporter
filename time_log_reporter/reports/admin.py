from django.contrib import admin
from django.views.decorators.cache import never_cache

from .models import Team
from .models import Member
from .models import Membership
from .models import Project



class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'team')

    
class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1


class ProjectAdmin(admin.ModelAdmin):
    inlines = [MembershipInline]
    list_display = ('name', 'estimated_hours')



admin.site.register(Team)
admin.site.register(Member, MemberAdmin)
admin.site.register(Project, ProjectAdmin)


admin.site.site_title = 'Time Log Reporter'
admin.site.site_header = 'Time Log Reporter'
admin.site.index_title = 'Administration'