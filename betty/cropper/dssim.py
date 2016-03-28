try:
    import numpy as np
    import scipy.ndimage
except ImportError:
    pass

from betty.conf.app import settings
import io
import math

from PIL import Image


MIN_UNIQUE_COLORS = 4096
COLOR_DENSITY_RATIO = 0.11

QUALITY_IN_MIN = 82

ERROR_THRESHOLD = 1.3

ERROR_THRESHOLD_INACCURACY = 0.01


def compute_ssim(im1, im2, l=255):

    # k1,k2 & c1,c2 depend on L (width of color map)
    k_1 = 0.01
    c_1 = (k_1 * l) ** 2
    k_2 = 0.03
    c_2 = (k_2 * l) ** 2

    window = np.ones((8, 8)) / 64.0

    # Convert image matrices to double precision (like in the Matlab version)
    im1 = im1.astype(np.float)
    im2 = im2.astype(np.float)

    # Means obtained by Gaussian filtering of inputs
    mu_1 = scipy.ndimage.filters.convolve(im1, window)
    mu_2 = scipy.ndimage.filters.convolve(im2, window)

    # Squares of means
    mu_1_sq = mu_1 ** 2
    mu_2_sq = mu_2 ** 2
    mu_1_mu_2 = mu_1 * mu_2

    # Squares of input matrices
    im1_sq = im1 ** 2
    im2_sq = im2 ** 2
    im12 = im1 * im2

    # Variances obtained by Gaussian filtering of inputs' squares
    sigma_1_sq = scipy.ndimage.filters.convolve(im1_sq, window)
    sigma_2_sq = scipy.ndimage.filters.convolve(im2_sq, window)

    # Covariance
    sigma_12 = scipy.ndimage.filters.convolve(im12, window)

    # Centered squares of variances
    sigma_1_sq -= mu_1_sq
    sigma_2_sq -= mu_2_sq
    sigma_12 -= mu_1_mu_2

    if (c_1 > 0) & (c_2 > 0):
        ssim_map = (((2 * mu_1_mu_2 + c_1) * (2 * sigma_12 + c_2)) /
                    ((mu_1_sq + mu_2_sq + c_1) * (sigma_1_sq + sigma_2_sq + c_2)))
    else:
        numerator1 = 2 * mu_1_mu_2 + c_1
        numerator2 = 2 * sigma_12 + c_2

        denominator1 = mu_1_sq + mu_2_sq + c_1
        denominator2 = sigma_1_sq + sigma_2_sq + c_2

        ssim_map = np.ones(mu_1.size)

        index = (denominator1 * denominator2 > 0)

        ssim_map[index] = ((numerator1[index] * numerator2[index]) /
                           (denominator1[index] * denominator2[index]))
        index = (denominator1 != 0) & (denominator2 == 0)
        ssim_map[index] = numerator1[index] / denominator1[index]

    # return MSSIM
    index = np.mean(ssim_map)

    return index


def unique_colors(img):
    # For RGB, we need to get unique "rows" basically, as the color dimesion is an array.
    # This is taken from: http://stackoverflow.com/a/16973510
    color_view = np.ascontiguousarray(img).view(np.dtype((np.void,
                                                          img.dtype.itemsize * img.shape[2])))
    unique = np.unique(color_view)
    return unique.size


def color_density(img):
    area = img.shape[0] * img.shape[1]
    density = unique_colors(img) / float(area)
    return density


def enough_colors(img):
    return True
    if unique_colors(img) < MIN_UNIQUE_COLORS:
        return False

    # Someday, check if the image is greyscale...
    return True


def get_distortion(one, two):
    # This computes the "DSSIM" of the images, using the SSIM of each channel

    ssims = []

    for channel in range(one.shape[2]):
        one_channeled = np.ascontiguousarray(one[:, :, channel])
        two_channeled = np.ascontiguousarray(two[:, :, channel])

        ssim = compute_ssim(one_channeled, two_channeled)

        ssims.append(ssim)

    return (1 / np.mean(ssims) - 1) * 20


def detect_optimal_quality(image_buffer, width=None, verbose=False):
    """Returns the optimal quality for a given image, at a given width"""

    # Open the image...
    pil_original = Image.open(image_buffer)
    icc_profile = pil_original.info.get("icc_profile")

    if pil_original.format != "JPEG":
        # Uhoh, this isn't a JPEG, let's convert it to one.
        pillow_kwargs = {
            "format": "jpeg",
            "quality": 100,
            "subsampling": 2
        }
        if icc_profile:
            pillow_kwargs["icc_profile"] = icc_profile
        tmp = io.BytesIO()
        pil_original.save(tmp, **pillow_kwargs)
        tmp.seek(0)
        pil_original = Image.open(tmp)

    if width:
        height = int(math.ceil((pil_original.size[1] * width) / float(pil_original.size[0])))
        pil_original = pil_original.resize((width, height), resample=Image.ANTIALIAS)

    np_original = np.asarray(pil_original)
    original_density = color_density(np_original)

    # Check if there are enough colors (assuming RGB for the moment)
    if not enough_colors(np_original):
        return None

    # TODO: Check if the quality is lower than we'd want... (probably impossible)
    qmin = settings.BETTY_JPEG_QUALITY_RANGE[0]
    qmax = settings.BETTY_JPEG_QUALITY_RANGE[1]

    # Do a binary search of image quality...
    while qmax > qmin + 1:
        quality = int(round((qmax + qmin) / 2.0))

        tmp = io.BytesIO()
        pillow_kwargs = {
            "format": "jpeg",
            "quality": quality,
            "subsampling": 2
        }

        if icc_profile:
            pillow_kwargs["icc_profile"] = icc_profile
        pil_original.save(tmp, **pillow_kwargs)
        tmp.seek(0)
        pil_compressed = Image.open(tmp)

        np_compressed = np.asarray(pil_compressed)
        density_ratio = abs(color_density(np_compressed) - original_density) / original_density

        error = get_distortion(np_original, np_compressed)

        if density_ratio > COLOR_DENSITY_RATIO:
            error *= 1.25 + density_ratio

        if error > ERROR_THRESHOLD:
            qmin = quality
        else:
            qmax = quality

        if verbose:
            print("{:.2f}/{:.2f}@{}".format(error, density_ratio, quality))

        if abs(error - ERROR_THRESHOLD) < ERROR_THRESHOLD * ERROR_THRESHOLD_INACCURACY:
            # Close enough!
            qmax = quality
            break

    return qmax
