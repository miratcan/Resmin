import os
import sys
import site

site.addsitedir('/home/miratcan/envs/cb2/lib/python2.7/site-packages/')
sys.path.append("/home/miratcan/webapps/resmin/")
sys.path.append("/home/miratcan/webapps/resmin/cb2/")

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
