"""Core cropping code, sharable between the Flask and Django versions.
"""

from wand.image import Image as WandImage

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


class BettyImageMixin(object):
    """This mixin provides utilites for image management"""

    def __repr__(self):
        return '<Image %r>' % (self.id)

    @classmethod
    def get_settings(cls):
        """Returns the betty cropper settings"""

    def get_height(self):
        """Lazily returns the height of the image

        If the width exists in the database, that value will be returned,
        otherwise the width will be read from the filesystem."""
        if self.height in (None, 0):
            with WandImage(filename=self.src_path()) as img:
                self.height = img.size[1]
                self.width = img.size[0]
        return self.height

    def get_width(self):
        """Lazily returns the width of the image

        If the width exists in the database, that value will be returned,
        otherwise the width will be read from the filesystem."""
        if self.width in (None, 0):
            with WandImage(filename=self.src_path()) as img:
                self.height = img.size[1]
                self.width = img.size[0]
        return self.width

    def src_path(self):
        """Returns the path to the image source"""
        raise NotImplemented()

    def to_native(self):
        """Returns a Python dictionary, sutiable for Serialization"""
        data = {
            'id': self.id,
            'name': self.name,
            'width': self.get_width(),
            'height': self.get_height(),
            'credit': self.credit,
            'selections': {}
        }
        for ratio in self.get_settings()['RATIOS']:
            data['selections'][ratio] = self.get_selection(Ratio(ratio))
        return data

    def get_selection(self, ratio):
        """Returns the image selection for a given ratio

        If the selection for this ratio has been set manually, that value
        is returned exactly, otherwise the selection is auto-generated."""
        selection = None
        if self.selections is not None:
            if ratio.string in self.selections:
                selection = self.selections.get(ratio.string)

                # Here I need to check for all kinds of bad data. Because we have some *awful* data right now.
                if selection['y1'] > self.get_height() or selection['x1'] > self.get_width():
                    selection = None
                elif selection['y1'] < selection['y0'] or selection['x1'] < selection['x0']:
                    selection = None
                else:
                    for key in ('x0', 'x1', 'y0', 'y1'):
                        if selection[key] < 0:
                            selection = None
                            break

        if selection is None:
            source_aspect = self.get_width() / float(self.get_height())
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

        if selection['y1'] > self.get_height():
            selection['y1'] = int(self.get_height())

        if selection['x1'] > self.get_width():
            selection['x1'] = int(self.get_width())

        if selection['x0'] < 0:
            selection['x0'] = 0

        if selection['y0'] < 0:
            selection['y0'] = 0

        return selection