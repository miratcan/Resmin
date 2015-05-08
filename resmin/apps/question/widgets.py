from django import forms
from django.contrib.admin.widgets import url_params_from_lookup_dict
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.text import Truncator


class ForeignKeyRawIdWidget(forms.TextInput):
    """
    A Widget for displaying ForeignKeys in the "raw_id" interface rather than
    in a <select> box.
    """
    def __init__(self, model, admin_site, limit_choices_to=None, attrs=None,
                 using=None):
        self.model = model
        self.limit_choices_to = limit_choices_to
        self.admin_site = admin_site
        self.db = using
        super(ForeignKeyRawIdWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        rel_to = self.model
        if attrs is None:
            attrs = {}
        extra = []
        if rel_to in self.admin_site._registry:
            # The related object is registered with the same AdminSite
            related_url = reverse(
                'admin:%s_%s_changelist' % (
                    rel_to._meta.app_label,
                    rel_to._meta.model_name,
                ),
                current_app=self.admin_site.name,
            )

            params = self.url_parameters()
            if params:
                url = '?' + '&amp;'.join('%s=%s' % (k, v) for k, v in
                                         params.items())
            else:
                url = ''
            if "class" not in attrs:
                attrs['class'] = 'vForeignKeyRawIdAdminField'
            extra.append('<a href="%s%s" class="related-lookup" '
                         'id="lookup_id_%s" title="%s"></a>' % (related_url,
                                                                url,
                                                                name,
                                                                _('Lookup')))

        output = [super(ForeignKeyRawIdWidget, self)
                  .render(name, value, attrs)] + extra
        if value:
            output.append(self.label_for_value(value))
        return mark_safe(''.join(output))

    def base_url_parameters(self):
        limit_choices_to = self.limit_choices_to
        if callable(limit_choices_to):
            limit_choices_to = limit_choices_to()
        return url_params_from_lookup_dict(limit_choices_to)

    def url_parameters(self):
        from django.contrib.admin.views.main import TO_FIELD_VAR
        params = self.base_url_parameters()
        params.update({TO_FIELD_VAR: self.rel.get_related_field().name})
        return params

    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        try:
            obj = self.rel.model._default_manager.using(self.db).get(
                **{key: value})
            return '&nbsp;<strong>%s</strong>' %\
                escape(Truncator(obj).words(14, truncate='...'))
        except (ValueError, self.rel.model.DoesNotExist):
            return ''
