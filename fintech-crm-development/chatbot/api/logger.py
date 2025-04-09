import logging

from opencensus.ext.azure.log_exporter import AzureLogHandler

from api.settings import settings


def setup_logging():
    logger = logging.getLogger(__name__)
    azure_handler = AzureLogHandler(
        connection_string=settings.AZURE_APPINSIGHTS_INSTRUMENTATIONKEY
    )

    logger.addHandler(azure_handler)

    return logger


logger = setup_logging()
