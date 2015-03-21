from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import Manager
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from logging import getLogger

logger = getLogger('notification')


class EmailNotificationManager(Manager):

    def from_meta(self, nmeta):
        """
        Try to render subject and body, if successful return True,
        else log missing template and return False.
        """

        def _body_tname(nmeta, postfix):
            """
            Generic method for getting body template name.
            """
            return '%s/email_body.%s' % (nmeta.get_template_prefix(),
                                         postfix)

        def subject_tname(nmeta):
            """
            Return subject template name.
            """
            return '%s%s' % (nmeta.get_template_prefix(), 'email_subject.txt')

        def body_txt_tname(nmeta):
            """
            Return txt version of body template.
            """
            return _body_tname(nmeta, 'txt')

        def body_html_tname(nmeta):
            """
            Return html version of body template.
            """
            return _body_tname(nmeta, 'html')
        ctx = {'nm': nmeta, 'site': Site.objects.get_current()}
        rendered = True
        try:
            subject = render_to_string(subject_tname(nmeta), ctx)
            body_txt = render_to_string(body_txt_tname(nmeta), ctx)
        except TemplateDoesNotExist as err:
            rendered = False
            logger.error('Could\'nt send email notification. Template: '
                         '"%s" missing.' % err.args[0])
        except Exception as err:
            rendered = False
            logger.error(err)

        if not rendered:
            return None

        try:
            body_html = render_to_string(body_html_tname(nmeta), ctx)
        except TemplateDoesNotExist:
            body_html = ''

        return self.model.objects.create(
            meta=nmeta, subject=subject, body_txt=body_txt,
            body_html=body_html, from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_email=nmeta.recipient.email)
