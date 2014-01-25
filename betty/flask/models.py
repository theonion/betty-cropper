import os
import json

from sqlalchemy import Column, Integer, String
from sqlalchemy.types import TypeDecorator, VARCHAR


from betty.flask import app
from betty.core import BettyImageMixin
from betty.flask.database import Base


class JSONEncodedDict(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class Image(Base, BettyImageMixin):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    width = Column(Integer)
    height = Column(Integer)
    credit = Column(String(120))
    selections = Column(JSONEncodedDict(1024))

    def __init__(self, name, width, height, credit=None, selections=None):
        self.name = name
        self.width = width
        self.height = height
        self.credit = credit
        self.selections = selections

    def src_path(self):
        return os.path.join(self.path(), 'src')

    @classmethod
    def get_settings(cls):
        return app.config

