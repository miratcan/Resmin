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

        total = int(args[1])

        for user in users:
            num = Invitation.objects.filter(owner=user).count()
            if num < total:
                print "Creatin invitations for: %s" % user
                for i in range(total-num):
                    i = Invitation.objects.create(owner=user)
                    print i.key
            else:
                print "%s has enought invitations" % user
