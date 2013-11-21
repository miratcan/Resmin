from django.utils import simplejson as json

from django.http import HttpResponse


def render_to_json(python_dict):
    """
    Function to convert the given python dict
    to a JSON string and wraps it in a HttpResponse
    object.
    """
    j = json.dumps(python_dict)
    return HttpResponse(j, mimetype='application/json')
