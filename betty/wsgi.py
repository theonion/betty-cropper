import os
import os.path
import sys

# Add the project to the python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.stdout = sys.stderr

# Configure the application (Logan)
from betty.server.utils.runner import configure
configure()

# Build the wsgi app
import django.core.handlers.wsgi

# Run WSGI handler for the application
application = django.core.handlers.wsgi.WSGIHandler()
