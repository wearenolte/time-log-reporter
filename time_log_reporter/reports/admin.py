from django.contrib import admin
from .models import Team
from .models import Member
from .models import Membership
from .models import Project



class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1


class ProjectAdmin(admin.ModelAdmin):
    inlines = [MembershipInline]



admin.site.register(Team)
admin.site.register(Member)
admin.site.register(Project, ProjectAdmin)
