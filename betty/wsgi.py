import os
import os.path
import sys

# Add the project to the python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.stdout = sys.stderr

# Configure the application (Logan)
from betty.cropper.utils.runner import configure  # NOQA
configure()

# Build the wsgi app
import django.core.wsgi  # NOQA

# Run WSGI handler for the application
application = django.core.wsgi.get_wsgi_application()
