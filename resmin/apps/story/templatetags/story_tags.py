from django.template import Library

register = Library()


@register.filter
def more_loop(value):
    if value > 1:
        return range(min(value - 1, 5))
    else:
        return []
