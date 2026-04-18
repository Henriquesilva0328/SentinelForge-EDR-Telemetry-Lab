import logging

from pythonjsonlogger.json import JsonFormatter

from sentinelforge.core.settings import get_settings


def configure_logging() -> None:
    """
    Configura logging estruturado em JSON.
    """
    settings = get_settings()

    handler = logging.StreamHandler()
    handler.setFormatter(
        JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level)