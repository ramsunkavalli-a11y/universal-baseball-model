"""Remove explicitly labeled staff before parsing static player identities."""
from bs4 import BeautifulSoup
from universal_baseball.npb_hitter_2026_identity import names as original_names


def names(html, team):
    soup = BeautifulSoup(html, 'html.parser')
    for row in soup.select('tr.rosterPlayer'):
        header = row.find_previous_sibling('tr', class_='rosterMainHead')
        node = header.select_one('.rosterPos') if header else None
        section = node.get_text(strip=True) if node else None
        if section in ('監督', 'コーチ'):
            row.decompose()
        elif section not in ('投手', '捕手', '内野手', '外野手'):
            raise ValueError('Unknown player versus staff source section')
    return original_names(str(soup), team)
