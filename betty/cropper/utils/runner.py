import os

from logan.runner import run_app, configure_app

BETTY_IMAGE_ROOT = os.path.normpath(os.path.join(os.getcwd(), "images"))


def generate_settings():
    """
    This command is run when ``default_path`` doesn't exist, or ``init`` is
    run and returns a string representing the default data to put into their
    settings file.
    """
    return """
BETTY_IMAGE_ROOT = "{0}"
BETTY_IMAGE_URL = "/"
BETTY_RATIOS = ("1x1", "2x1", "3x1", "3x4", "4x3", "16x9")
BETTY_PLACEHOLDER = True
""".format(BETTY_IMAGE_ROOT)


def configure():
    configure_app(
        project='betty',
        default_config_path='betty.conf.py',
        default_settings='betty.conf.server',
        settings_initializer=generate_settings,
        settings_envvar='BETTY_CONF',
    )


def main():
    run_app(
        project='betty',
        default_config_path='betty.conf.py',
        default_settings='betty.conf.server',
        settings_initializer=generate_settings,
        settings_envvar='BETTY_CONF',
    )

if __name__ == '__main__':
    main()
