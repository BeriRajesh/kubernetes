import re
import traceback


def get_urls_from_plain_part(email_data):
    """
    Extracts URLs from plain text string.
    """
    try:
        pattern = re.compile('(https?://[^\n\r ]*)')
        urls = pattern.findall(email_data.decode())

        return urls
    except Exception as err:
        print(f"ERROR: Exception when parsing plain text for urls: {err}")
        traceback.print_exc()
        return []
