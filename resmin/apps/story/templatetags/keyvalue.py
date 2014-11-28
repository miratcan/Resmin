from django import template
register = template.Library()


@register.filter
def keyvalue(d, k):
    if type(d) == dict:
        return d.get(k)
    else:
        return False
