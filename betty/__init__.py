import os
from flask import Flask
app = Flask(__name__)
app.config.from_object(os.environ.get('SETTINGS_MODULE', 'settings'))

import betty.views