from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.account.models import Invitation


class Command(BaseCommand):
    args = '<username amount...>'
    help = 'Generates given amount of '

    def handle(self, *args, **options):
        username = args[0]

        if username == 'all':
            users = User.objects.all()
        else:
            users = User.objects.filter(username=username)
        try:
            use_limit = int(args[1])
        except KeyError:
            use_limit = None

        for user in users:
            invitation = Invitation.objects.create(owner=user,
                                                   use_limit=use_limit)
            print "Invitation with use_limit:%s for %s created. " % (
                invitation.use_limit, user)
