import os
import sys
import site

site.addsitedir('/home/miratcan/envs/cb2/lib/python2.7/site-packages/')
sys.path.append("/home/miratcan/webapps/resmin/")
sys.path.append("/home/miratcan/webapps/resmin/resmin/")
sys.path.append("/home/miratcan/webapps/resmin/resmin/resmin/")

os.environ['DJANGO_SETTINGS_MODULE'] = 'resmin.config.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
