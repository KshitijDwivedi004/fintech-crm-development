import logging
from thefuzz import fuzz

# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

target_strings = ["hi", "hello", "hey","Hi there!","Yo!"]


def check_fuzzy_match(user_input,threshold=70):
    """
    Check if user input has a fuzzy match with any of the target strings.

    Parameters:
    - user_input: The user input string.
    - target_strings: A list of target strings to compare with the user input.
    - threshold: The minimum ratio of similarity required for a match. Default is 70.

    Returns:
    - True if a match is found, False otherwise.
    """
    try:
        for target in target_strings:
            ratio = fuzz.ratio(user_input.lower(), target.lower())
            if ratio >= threshold:
                return True
    except Exception:
        return False