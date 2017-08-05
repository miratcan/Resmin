import os
import sys
import site
from django.core.wsgi import get_wsgi_application

sys.path.append("/home/miratcan/webapps/resmin/")
sys.path.append("/home/miratcan/webapps/resmin/Resmin/")
sys.path.append("/home/miratcan/webapps/resmin/Resmin/resmin/")

os.environ['DJANGO_SETTINGS_MODULE'] = 'resmin.config.settings'
application = get_wsgi_application()

