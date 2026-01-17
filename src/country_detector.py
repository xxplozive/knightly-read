"""Detects countries mentioned in article titles and returns flag emojis."""
import re

# Country name to flag emoji mapping
COUNTRY_FLAGS = {
    # Europe
    'ukraine': '🇺🇦', 'russia': '🇷🇺', 'russian': '🇷🇺', 'moscow': '🇷🇺', 'kremlin': '🇷🇺',
    'germany': '🇩🇪', 'german': '🇩🇪', 'berlin': '🇩🇪',
    'france': '🇫🇷', 'french': '🇫🇷', 'paris': '🇫🇷',
    'uk': '🇬🇧', 'britain': '🇬🇧', 'british': '🇬🇧', 'england': '🇬🇧', 'london': '🇬🇧', 'scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
    'italy': '🇮🇹', 'italian': '🇮🇹', 'rome': '🇮🇹',
    'spain': '🇪🇸', 'spanish': '🇪🇸', 'madrid': '🇪🇸',
    'poland': '🇵🇱', 'polish': '🇵🇱', 'warsaw': '🇵🇱',
    'netherlands': '🇳🇱', 'dutch': '🇳🇱', 'amsterdam': '🇳🇱',
    'belgium': '🇧🇪', 'brussels': '🇧🇪',
    'sweden': '🇸🇪', 'swedish': '🇸🇪',
    'norway': '🇳🇴', 'norwegian': '🇳🇴',
    'denmark': '🇩🇰', 'danish': '🇩🇰',
    'finland': '🇫🇮', 'finnish': '🇫🇮',
    'greece': '🇬🇷', 'greek': '🇬🇷', 'athens': '🇬🇷',
    'turkey': '🇹🇷', 'turkish': '🇹🇷', 'ankara': '🇹🇷', 'istanbul': '🇹🇷',
    'switzerland': '🇨🇭', 'swiss': '🇨🇭',
    'austria': '🇦🇹', 'vienna': '🇦🇹',
    'portugal': '🇵🇹', 'lisbon': '🇵🇹',
    'ireland': '🇮🇪', 'irish': '🇮🇪', 'dublin': '🇮🇪',
    'czech': '🇨🇿', 'prague': '🇨🇿',
    'hungary': '🇭🇺', 'budapest': '🇭🇺',
    'romania': '🇷🇴',
    'serbia': '🇷🇸', 'belgrade': '🇷🇸',
    'croatia': '🇭🇷',
    'slovakia': '🇸🇰',
    'slovenia': '🇸🇮',
    'bulgaria': '🇧🇬',
    'albania': '🇦🇱',
    'kosovo': '🇽🇰',
    'bosnia': '🇧🇦',
    'montenegro': '🇲🇪',
    'macedonia': '🇲🇰', 'north macedonia': '🇲🇰',
    'latvia': '🇱🇻',
    'lithuania': '🇱🇹',
    'estonia': '🇪🇪',
    'belarus': '🇧🇾', 'minsk': '🇧🇾',
    'moldova': '🇲🇩',

    # Asia
    'china': '🇨🇳', 'chinese': '🇨🇳', 'beijing': '🇨🇳', 'shanghai': '🇨🇳',
    'japan': '🇯🇵', 'japanese': '🇯🇵', 'tokyo': '🇯🇵',
    'south korea': '🇰🇷', 'korean': '🇰🇷', 'seoul': '🇰🇷', 'korea': '🇰🇷',
    'north korea': '🇰🇵', 'pyongyang': '🇰🇵',
    'india': '🇮🇳', 'indian': '🇮🇳', 'delhi': '🇮🇳', 'mumbai': '🇮🇳',
    'pakistan': '🇵🇰', 'pakistani': '🇵🇰',
    'bangladesh': '🇧🇩',
    'vietnam': '🇻🇳', 'vietnamese': '🇻🇳', 'hanoi': '🇻🇳',
    'thailand': '🇹🇭', 'thai': '🇹🇭', 'bangkok': '🇹🇭',
    'indonesia': '🇮🇩', 'indonesian': '🇮🇩', 'jakarta': '🇮🇩',
    'philippines': '🇵🇭', 'filipino': '🇵🇭', 'manila': '🇵🇭',
    'malaysia': '🇲🇾', 'malaysian': '🇲🇾',
    'singapore': '🇸🇬',
    'taiwan': '🇹🇼', 'taiwanese': '🇹🇼', 'taipei': '🇹🇼',
    'hong kong': '🇭🇰',
    'myanmar': '🇲🇲', 'burma': '🇲🇲',
    'cambodia': '🇰🇭',
    'laos': '🇱🇦',
    'nepal': '🇳🇵',
    'sri lanka': '🇱🇰',
    'mongolia': '🇲🇳',
    'afghanistan': '🇦🇫', 'afghan': '🇦🇫', 'kabul': '🇦🇫', 'taliban': '🇦🇫',

    # Middle East
    'israel': '🇮🇱', 'israeli': '🇮🇱', 'tel aviv': '🇮🇱', 'jerusalem': '🇮🇱',
    'palestine': '🇵🇸', 'palestinian': '🇵🇸', 'gaza': '🇵🇸', 'hamas': '🇵🇸', 'west bank': '🇵🇸',
    'iran': '🇮🇷', 'iranian': '🇮🇷', 'tehran': '🇮🇷',
    'iraq': '🇮🇶', 'iraqi': '🇮🇶', 'baghdad': '🇮🇶',
    'syria': '🇸🇾', 'syrian': '🇸🇾', 'damascus': '🇸🇾',
    'lebanon': '🇱🇧', 'lebanese': '🇱🇧', 'beirut': '🇱🇧', 'hezbollah': '🇱🇧',
    'jordan': '🇯🇴',
    'saudi': '🇸🇦', 'saudi arabia': '🇸🇦', 'riyadh': '🇸🇦',
    'uae': '🇦🇪', 'emirates': '🇦🇪', 'dubai': '🇦🇪', 'abu dhabi': '🇦🇪',
    'qatar': '🇶🇦', 'doha': '🇶🇦',
    'kuwait': '🇰🇼',
    'bahrain': '🇧🇭',
    'oman': '🇴🇲',
    'yemen': '🇾🇪', 'yemeni': '🇾🇪', 'houthi': '🇾🇪',

    # Africa
    'egypt': '🇪🇬', 'egyptian': '🇪🇬', 'cairo': '🇪🇬',
    'south africa': '🇿🇦',
    'nigeria': '🇳🇬', 'nigerian': '🇳🇬', 'lagos': '🇳🇬',
    'kenya': '🇰🇪', 'kenyan': '🇰🇪', 'nairobi': '🇰🇪',
    'ethiopia': '🇪🇹', 'ethiopian': '🇪🇹',
    'ghana': '🇬🇭',
    'morocco': '🇲🇦', 'moroccan': '🇲🇦',
    'algeria': '🇩🇿',
    'tunisia': '🇹🇳',
    'libya': '🇱🇾', 'libyan': '🇱🇾',
    'sudan': '🇸🇩', 'sudanese': '🇸🇩', 'khartoum': '🇸🇩',
    'congo': '🇨🇩', 'drc': '🇨🇩',
    'tanzania': '🇹🇿',
    'uganda': '🇺🇬',
    'rwanda': '🇷🇼',
    'somalia': '🇸🇴', 'somali': '🇸🇴', 'mogadishu': '🇸🇴',
    'zimbabwe': '🇿🇼',
    'senegal': '🇸🇳',
    'ivory coast': '🇨🇮', 'cote d\'ivoire': '🇨🇮',
    'cameroon': '🇨🇲',
    'mali': '🇲🇱',
    'niger': '🇳🇪',
    'burkina faso': '🇧🇫',
    'mozambique': '🇲🇿',
    'angola': '🇦🇴',
    'zambia': '🇿🇲',
    'botswana': '🇧🇼',
    'namibia': '🇳🇦',
    'madagascar': '🇲🇬',

    # Americas
    'usa': '🇺🇸', 'u.s.': '🇺🇸', 'united states': '🇺🇸', 'american': '🇺🇸', 'washington': '🇺🇸',
    'canada': '🇨🇦', 'canadian': '🇨🇦', 'ottawa': '🇨🇦', 'toronto': '🇨🇦',
    'mexico': '🇲🇽', 'mexican': '🇲🇽', 'mexico city': '🇲🇽',
    'brazil': '🇧🇷', 'brazilian': '🇧🇷', 'rio': '🇧🇷', 'sao paulo': '🇧🇷',
    'argentina': '🇦🇷', 'argentine': '🇦🇷', 'buenos aires': '🇦🇷',
    'colombia': '🇨🇴', 'colombian': '🇨🇴', 'bogota': '🇨🇴',
    'venezuela': '🇻🇪', 'venezuelan': '🇻🇪', 'caracas': '🇻🇪',
    'chile': '🇨🇱', 'chilean': '🇨🇱', 'santiago': '🇨🇱',
    'peru': '🇵🇪', 'peruvian': '🇵🇪', 'lima': '🇵🇪',
    'ecuador': '🇪🇨',
    'bolivia': '🇧🇴',
    'paraguay': '🇵🇾',
    'uruguay': '🇺🇾',
    'cuba': '🇨🇺', 'cuban': '🇨🇺', 'havana': '🇨🇺',
    'haiti': '🇭🇹', 'haitian': '🇭🇹',
    'dominican': '🇩🇴',
    'puerto rico': '🇵🇷',
    'jamaica': '🇯🇲',
    'guatemala': '🇬🇹',
    'honduras': '🇭🇳',
    'el salvador': '🇸🇻',
    'nicaragua': '🇳🇮',
    'costa rica': '🇨🇷',
    'panama': '🇵🇦',

    # Oceania
    'australia': '🇦🇺', 'australian': '🇦🇺', 'sydney': '🇦🇺', 'melbourne': '🇦🇺', 'canberra': '🇦🇺',
    'new zealand': '🇳🇿', 'kiwi': '🇳🇿', 'auckland': '🇳🇿', 'wellington': '🇳🇿',
    'fiji': '🇫🇯',
    'papua new guinea': '🇵🇬',
}

# Compile regex pattern for efficient matching
_PATTERN = None

def _get_pattern():
    global _PATTERN
    if _PATTERN is None:
        # Sort by length (longest first) to match "south korea" before "korea"
        sorted_countries = sorted(COUNTRY_FLAGS.keys(), key=len, reverse=True)
        escaped = [re.escape(c) for c in sorted_countries]
        _PATTERN = re.compile(r'\b(' + '|'.join(escaped) + r')\b', re.IGNORECASE)
    return _PATTERN


def detect_country(title: str) -> tuple:
    """
    Detect country mentioned in title.
    Returns (country_name, flag_emoji) or (None, None) if not found.
    """
    pattern = _get_pattern()
    match = pattern.search(title)

    if match:
        country = match.group(1).lower()
        return (country.title(), COUNTRY_FLAGS.get(country, '🌍'))

    return (None, '🌍')  # Default globe emoji if no country detected
