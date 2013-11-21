# templatetags file
from django import template

register = template.Library()


@register.filter(name='is_liked_by')
def is_liked_by(answer, user):
    return answer.is_liked_by(user)
