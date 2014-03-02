from logan.runner import run_app


def generate_settings():
    """
    This command is run when ``default_path`` doesn't exist, or ``init`` is
    run and returns a string representing the default data to put into their
    settings file.
    """
    return """
BETTY_IMAGE_ROOT = "images"
BETTY_IMAGE_URL = "/"
BETTY_RATIOS = ("1x1", "2x1", "3x1", "3x4", "4x3", "16x9")
BETTY_WIDTHS = (80, 150, 240, 300, 320, 400, 480, 620, 640, 820, 960, 1200, 1600)
BETTY_PLACEHOLDER = True
"""


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
