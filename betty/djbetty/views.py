from .conf import settings

from django.http import Http404, HttpResponse, HttpResponseServerError, HttpResponseRedirect
from django.core.urlresolvers import reverse

def crop(request, pk, ratio_slug, width, extension):
    if ratio_slug != "original" and ratio_slug not in settings.BETTY_CROPPER["RATIOS"]:
        raise Http404

    try:
        width = int(width)
    except ValueError:
        return HttpResponseServerError()

    if width > 2000:
        return HttpResponseServerError()

    if len(pk) > 4 and "/" not in pk:
        id_string = ""
        for index,char in enumerate(pk):
            if index % 4 == 0 and index != 0:
                id_string += "/"
            id_string += char

        return HttpResponseRedirect(reverse('betty.djbetty.views.crop', args=(id_string, ratio_slug, width, extension)))

    return HttpResponse("Whatevs")