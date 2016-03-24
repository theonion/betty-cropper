# Betty Cropper Change Log

## Version 2.0.0

- Image refactor to use Django Storage API instead of raw filesystem calls, allowing swapping out storage backends. Primarily tested with local filesystem and S3 backends.
- Added `BETTY_SAVE_CROPS_TO_DISK` boolean setting (default == True) to optionally disable writing crops to local disk

TODO: Legacy behavior should "just worth" with BETTY_IMAGE_ROOT + BETTY_IMAGE_URL


## Version less than 2.0.0

* These change notes have been lost to the mists of github *
