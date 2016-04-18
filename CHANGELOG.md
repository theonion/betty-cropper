# Betty Cropper Change Log

## Version 2.1.0
- Improvements to BETTY_CACHE_FLUSHER support:
  - `BETTY_CACHE_FLUSHER` can either be set to a callable object or a string import path
  - Flusher now passed list of string URLS instead of individual strings. This allows for more efficient callback batching logic.
  - Added reference cache flusher `betty.contrib.cacheflush.cachemaster`
  - `Image.clear_crops()` now includes animated files (`.../animated/original.{gif,jpg}`)
- Add optional Docker support

## Version 2.0.6

- Allow configurable "Image JS" cache time via `settings.BETTY_CACHE_IMAGEJS_SEC`. ImageJS requests are cheap but make up over 50% of current production requests, and only rarely changes on deploys.
- Increase (rarely called) "crop redireect" cache times to 1 hour, a good balance between fewer requests and not overcommitting in case this ever changes.

## Version 2.0.5

- Fixes max-width resize regression for cases other than "JPG mode=RGB". Switch to IO buffers requires passing
  a `format` value since no longer a filename to auto-detect via extension.

## Version 2.0.4

- Management command `change_storage_root` uses older option format for compatibility with Django 1.7

## Version 2.0.2

- Added `settings.BETTY_CACHE_CROP_SEC` to allow configurable crop (and animated) cache times. Defaults to original `300` seconds.

## Version 2.0.1

- Added S3 migration support:
    - `betty.cropper.storage.MigratedS3BotoStorage` allows parallel testing against filesystem + S3 storage by altering filesystem path to an S3 path at runtime.
    - New management command `change_storage_root` applies final storage name changes once testing completed.

## Version 2.0.0

- Refactored storage system to use Django Storage API instead of raw filesystem calls, allowing configurable storage backends. Primarily tested with local filesystem and S3 backends.
- Saving crops to local disk is now optional:
    - Added `BETTY_SAVE_CROPS_TO_DISK` boolean setting (default == `True`) to optionally disable writing crops to local disk
    - Added `BETTY_SAVE_CROPS_TO_DISK_ROOT` to specify root directory on local disk for crops (else will use `BETTY_IMAGE_ROOT` path)
- Animated images (`/animated/original.{gif,jpg}`) are now created on-demand like crops via a new view. Previously these were created on demand and leaned on nginx to serve cached files from disk. This new approach plays better with generic storage API.
- Tighten up URL regexes for `/image.js` and `/api/` path matching (were missing start + end markers).

### Upgrade Notes

This new version can be dropped into an existing Betty environment, using same local disk filesystem as before, but may require a single settings change (see below). 

#### FileSystemStorage (Default)

The default filesystem backend remains local disk storage (via `FileSystemStorage`). When upgrading, the `BETTY_IMAGE_ROOT` path must be located within the `MEDIA_ROOT` path, or you'll get a `SupiciousFileOperation` error. One option is to just set `MEDIA_ROOT = BETTY_IMAGE_ROOT`. **So at a minimum, to keep all behavior the same, just add this setting**:

        MEDIA_ROOT = BETTY_IMAGE_ROOT

#### Alternate Storage Backend

To use an alternate storage system, set the `DEFAULT_FILE_STORAGE` setting and configure per that storage's documentation. For example:

        DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
        AWS_ACCESS_KEY_ID = 'MY AWS KEY'
        AWS_SECRET_ACCESS_KEY = 'XXX SECRET KEY XXX'
        AWS_STORAGE_BUCKET_NAME = 'mybucket'

## Version less than 2.0.0

* These change notes have been lost to the mists of github *