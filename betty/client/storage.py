from django.core.files.storage import Storage

from betty.conf.app import settings

import requests


class BettyCropperStorage(Storage):

    def __init__(self, base_url=None, public_token=None, private_token=None):
        if base_url is None:
            base_url = settings.BETTY_IMAGE_URL
        if base_url[-1] == "/":
            base_url = base_url[:-1]
        self.base_url = base_url

        if public_token is None:
            public_token = settings.BETTY_PUBLIC_TOKEN
        self.public_token = public_token

        if private_token is None:
            private_token = settings.BETTY_PRIVATE_TOKEN
        self.private_token = private_token

    @property
    def auth_headers(self):
        return {"X-Betty-Api-Key": self.public_token}

    def delete(self, name):
        raise NotImplementedError

    def exists(self, name):

        detail_url = "{base_url}/api/{id}".format(base_url=self.base_url, id=name)
        r = requests.get(detail_url, headers=self.auth_headers)
        print(r.content)
        return r.status_code == 200

    def listdir(self, path):
        raise NotImplementedError

    def size(self, name):
        raise NotImplementedError

    def get_available_name(self, name):
        return name

    def _save(self, name, content):
        endpoint = "{base_url}/api/new".format(base_url=self.base_url)

        data = {"name": name}
        files = {"image": content}

        r = requests.post(endpoint, data=data, files=files, headers=self.auth_headers)
        if r.status_code != 200:
            print(r.content)
            raise IOError("Save failed")

        return str(r.json()["id"])

    def url(self, name, ratio="original", width=600, format="jpg"):

        # TODO: id string bullshit

        return "{base_url}/{id_string}/{ratio}/{width}.{format}".format(
            base_url=self.base_url,
            id_string=name,
            ratio=ratio,
            width=width,
            format=format)
