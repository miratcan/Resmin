from django.core.management.base import BaseCommand
from apps.notification.models import NotificationType
from os.path import join, isdir
from os import makedirs
import errno
from django.conf import settings

tr = settings.TEMPLATE_DIRS[0]


def mkdir(path):
    try:
        makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and isdir(path):
            pass
        else:
            raise


class Command(BaseCommand):
    help = 'Generates templates for notification types'

    def handle(self, *args, **options):
        for nt in NotificationType.objects.all():
            msl = [False]
            mol = [False]
            if nt.plural == NotificationType.PLURAL_SUB:
                msl.append(True)
            elif nt.plural == NotificationType.PLURAL_OBJ:
                mol.append(True)
            elif nt.plural == NotificationType.PLURAL_BOTH:
                msl.append(True)
                mol.append(True)
            for ms in msl:
                for mo in mol:
                    p = nt.get_template_prefix(ms, mo)
                    mkdir(join(tr, p))
                    for fn in ['site_notification.txt',
                               'email_subject.txt',
                               'email_body.txt',
                               'email_body.html']:
                        with open(join(tr, p, fn), 'w') as f:
                            f.write('Subject: %s, Object: %s' % (
                                nt.s_ct.model, nt.o_ct.model))
                            print 'Created: %s' % join(tr, p, fn)
