from ..models import Team
from ..models import Member


class LoadExtraData(object):
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        
        if not request.user.is_superuser:
            try:
                teams = Team.objects.filter(admin = request.user.id)
            except Team.DoesNotExist:
                teams = None
            request.teams = teams

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response