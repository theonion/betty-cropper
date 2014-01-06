import os
from flask import Flask

__version__ = "0.1"
app = Flask(__name__)
app.config.from_object(os.environ.get('SETTINGS_MODULE', 'settings'))

import betty.views