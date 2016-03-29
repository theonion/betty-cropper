from storages.backends.s3boto import S3BotoStorage

from betty.conf.app import settings

logger = __import__('logging').getLogger(__name__)


class MigratedS3BotoStorage(S3BotoStorage):

    """Workaround for allowing using 2 different storage systems in parallel during migration to S3
    storage.

        Use this storage intead of S3BotoStorage to allow easy re-wiring of path locations from
        filesystem to S3-based, and read-only safety (by overriding save()).

        Required Settings:
            BETTY_STORAGE_MIGRATION_OLD_ROOT - Old localfilesystem root directory
            BETTY_STORAGE_MIGRATION_NEW_ROOT - S3 key root
    """

    def _clean_name(self, name):
        if name.startswith(settings.BETTY_STORAGE_MIGRATION_OLD_ROOT):
            old_name = name
            name = (settings.BETTY_STORAGE_MIGRATION_NEW_ROOT +
                    name[len(settings.BETTY_STORAGE_MIGRATION_OLD_ROOT):])
            logger.info('Remap name: %s --> %s', old_name, name)
        return super(MigratedS3BotoStorage, self)._clean_name(name)

    def save(self, name, content):
        # Just to be safe, lets block all saving. This is just a temporary storage for read-only
        # testing, so isn't pretty.
        raise NotImplementedError('Should not be saving with MigratedS3BotoStorage!')
