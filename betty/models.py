import os
import json

from sqlalchemy import Column, Integer, String
from sqlalchemy.types import TypeDecorator, VARCHAR

from wand.image import Image as WandImage

from betty.database import Base
from betty import app


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

class Ratio(object):
    def __init__(self, ratio):
        self.string = ratio
        self.height = 0
        self.width = 0

        if ratio != "original":
            if len(ratio.split("x")) != 2:
                raise ValueError("Improper ratio!")
            self.width = int(ratio.split("x")[0])
            self.height = int(ratio.split("x")[1])

class Image(Base):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    width = Column(Integer)
    height = Column(Integer)
    credit = Column(String(120))
    selections = Column(JSONEncodedDict(1024))

    def __init__(self, name, credit=None, selections=None):
        self.name = name
        self.credit = credit
        self.selections = selections

    def get_height(self):
        if self.height in (None, 0):
            with WandImage(filename=self.path()) as img:
                self.height = img.size[0]
                self.width = img.size[1]
        return self.height

    def get_width(self):
        if self.width in (None, 0):
            with WandImage(filename=self.path()) as img:
                self.height = img.size[0]
                self.width = img.size[1]
        return self.width

    def path(self):
        id_string = ""
        for index,char in enumerate(str(self.id)):
            if index % 4 == 0:
                id_string += "/"
            id_string += char
        return os.path.join(app.config['BETTY']['IMAGE_ROOT'], id_string[1:], "src")

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'width': self.get_width(),
            'height': self.get_height(),
            'credit': self.credit,
            'selections': {}
        }
        for ratio in app.config['BETTY']['RATIOS']:
            data['selections'][ratio] = self.get_selection(Ratio(ratio))
        return data


    def get_selection(self, ratio):
        selection = None
        if self.selections is not None:
            selection = self.selections.get(ratio.string)

        if selection is not None:
            if selection['y1'] > self.get_height() or selection['x1'] > self.get_width():
                selection = None
            if selection['x0'] < 0 or selection['y0'] < 0:
                selection = None

        if selection is None:
            source_aspect = self.get_width() / self.get_height()
            selection_aspect = ratio.width / float(ratio.height)

            min_x = 0
            min_y = 0
            
            max_x = self.get_width()
            max_y = self.get_height()

            if source_aspect > selection_aspect:
                offset = (max_x - (max_y * ratio.width / ratio.height)) / 2.0
                min_x = offset
                max_x -= offset
            if source_aspect < selection_aspect:
                offset = (max_y - (max_x * ratio.height / ratio.width)) / 2.0
                min_y = offset
                max_y -= offset
            selection = {
                'x0': int(min_x),
                'y0': int(min_y),
                'x1': int(max_x),
                'y1': int(max_y)        
            }
        return selection


    def __repr__(self):
        return '<Image %r>' % (self.id)
