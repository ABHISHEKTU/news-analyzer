# app/scraper/utils.py
import html
import re
from bs4 import BeautifulSoup

BROKEN_ENTITY_PATTERN = re.compile(r'#(\d+);')

def fix_broken_entities(text: str) -> str:
    """Some feeds drop the leading & from numeric entities. Patch known cases."""
    return BROKEN_ENTITY_PATTERN.sub(lambda m: chr(int(m.group(1))), text)

def clean_html(raw: str) -> str:
    """Strip HTML tags, decode entities, patch broken entity patterns."""
    if not raw:
        return ""
    text = BeautifulSoup(raw, "html.parser").get_text(strip=True)
    text = html.unescape(text)
    text = fix_broken_entities(text)
    return text