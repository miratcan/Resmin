from django import template

register = template.Library()

@register.inclusion_tag('auth/username_inc.html')
def user(user):
    return {'user': user}
