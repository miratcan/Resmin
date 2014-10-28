from json import dumps
from django.http import HttpResponse


def render_to_json(python_dict, response_class=HttpResponse):
    return response_class(dumps(python_dict), mimetype='application/json')

