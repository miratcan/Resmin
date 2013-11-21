from django.template.loader import get_template

register = Template.register()

@register.inclusion_tag('user/inc_username.html')
def user(user):
    return {'user': user}
