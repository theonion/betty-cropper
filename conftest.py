from logan.runner import configure_app

configure_app(
    project="betty",
    default_settings="betty.conf.server",
    config_path="./tests/betty.testconf.py"
)
