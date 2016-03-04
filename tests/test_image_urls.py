from betty.cropper.models import Image


def test_id_string():
    image = Image(id=123456)
    assert image.id_string == "1234/56"

    image = Image(id=123)
    assert image.id_string == "123"


def test_image_url():
    image = Image(id=123456)
    assert image.get_absolute_url() == "/images/1234/56/original/600.jpg"

    assert image.get_absolute_url(format="png") == "/images/1234/56/original/600.png"
    assert image.get_absolute_url(width=900) == "/images/1234/56/original/900.jpg"
    assert image.get_absolute_url(ratio="16x9") == "/images/1234/56/16x9/600.jpg"
    assert image.get_absolute_url(format="png",
                                  width=900, ratio="16x9") == "/images/1234/56/16x9/900.png"

    image = Image(id=123)
    assert image.get_absolute_url() == "/images/123/original/600.jpg"
