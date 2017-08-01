from django import template

register = template.Library()


@register.inclusion_tag('user/inc_username.html')
def user(user):
    return {'user': user}
