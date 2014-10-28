from json import dumps
from django.http import HttpResponse


def render_to_json(python_dict):
    return HttpResponse(dumps(python_dict), mimetype='application/json')

