from json import dumps
from django.http import HttpResponse


def render_to_json(python_dict, response_class=HttpResponse, status=200):
    return response_class(dumps(python_dict),
                          mimetype='application/json',
                          status=status)
