from django.core.files.storage import Storage

from betty.conf.app import settings

import requests


class BettyCropperStorage(Storage):

    def delete(self, name):
        raise NotImplementedError

    def exists(self, name):
        base_url = settings.BETTY_IMAGE_URL
        if base_url[-1] == "/":
            base_url = base_url[:-1]

        detail_url = "{base_url}/api/{id}".format(base_url=base_url, id=name)
        r = requests.get(detail_url, headers={"X-Betty-Api-Key": settings.BETTY_PUBLIC_TOKEN})
        print(r.content)
        return r.status_code == 200

    def listdir(self, path):
        raise NotImplementedError

    def size(self, name):
        raise NotImplementedError

    def url(self, name, ratio="original", width=600, format="jpg"):
        # Trim the slash, if it's there.
        base_url = settings.BETTY_IMAGE_URL
        if base_url[-1] == "/":
            base_url = base_url[:-1]

        # TODO: id string bullshit

        return "{base_url}/{id_string}/{ratio}/{width}.{format}".format(
            base_url=base_url,
            id_string=name,
            ratio=ratio,
            width=width,
            format=format)
