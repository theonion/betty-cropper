# Betty Cropper Change Log

## Version 2.0.0

- Refactored storage system to use Django Storage API instead of raw filesystem calls, allowing configurable storage backends. Primarily tested with local filesystem and S3 backends.
- Saving crops to local disk is now optional:
    - Added `BETTY_SAVE_CROPS_TO_DISK` boolean setting (default == `True`) to optionally disable writing crops to local disk
    - Added `BETTY_SAVE_CROPS_TO_DISK_ROOT` to specify root directory on local disk for crops (else will use `BETTY_IMAGE_ROOT` path)
- Animated images (`/animated/original.{gif,jpg}`) are now created on-demand like crops via a new view. Previously these were created on demand and leaned on nginx to serve cached files from disk. This new approach plays better with generic storage API.

### Upgrade Notes:

This new version can be dropped into an existing Betty environment without any settings or behavior changes (legacy image + crop writes to local filesystem) so long as `BETTY_IMAGE_ROOT` is an absolute path. Else you need to set `MEDIA_URL = BETTY_IMAGE_ROOT` (as this is used by default `FileSystemStorage` backend).

## Version less than 2.0.0

* These change notes have been lost to the mists of github *
