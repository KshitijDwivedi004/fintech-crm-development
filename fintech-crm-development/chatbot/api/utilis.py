import logging
from datetime import datetime

from pytz import UTC, timezone

# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def convert_datetime_to_timezone(datetime_str, timezone_str):
    try:
        # Parse the datetime string
        datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%fZ")

        # Get the target timezone
        target_timezone = timezone(timezone_str)

        # Set the source timezone as UTC
        datetime_obj = datetime_obj.replace(tzinfo=UTC)

        # Convert the datetime to the target timezone
        target_datetime = datetime_obj.astimezone(target_timezone)

        # Format the datetime in the target timezone
        target_datetime_str = target_datetime.strftime("%B %d, %Y, %I:%M %p")

        return target_datetime_str
    except (ValueError, TypeError) as e:
        logging.log("Error while converting timezone:", e)
