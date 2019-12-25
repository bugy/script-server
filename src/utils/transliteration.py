import unicodedata

replacements = {
    # cyrillic
    'а': 'a',
    'б': 'b',
    'в': 'v',
    'г': 'g',
    'д': 'd',
    'е': 'e',
    'ё': 'yo',
    'ж': 'zh',
    'з': 'z',
    'и': 'i',
    'й': 'y',
    'к': 'k',
    'л': 'l',
    'м': 'm',
    'н': 'n',
    'о': 'o',
    'п': 'p',
    'р': 'r',
    'с': 's',
    'т': 't',
    'у': 'u',
    'ф': 'f',
    'х': 'h',
    'ц': 'ts',
    'ч': 'ch',
    'ш': 'sh',
    'щ': 'sch',
    'ъ': '\'',
    'ы': 'y',
    'ь': '\'',
    'э': 'e',
    'ю': 'yu',
    'я': 'ya',

    # german
    'ö': 'oe',
    'ä': 'ae',
    'ü': 'ue',
    'ß': 'ss',

    # greek
    'α': 'a',
    'β': 'v',
    'γ': 'g',
    'δ': 'd',
    'ε': 'e',
    'ζ': 'z',
    'η': 'e',
    'θ': 'th',
    'ι': 'i',
    'κ': 'k',
    'λ': 'l',
    'μ': 'm',
    'ν': 'n',
    'ξ': 'x',
    'ο': 'o',
    'π': 'p',
    'ρ': 'r',
    'σ': 's',
    'τ': 't',
    'υ': 'y',
    'φ': 'f',
    'χ': 'ch',
    'ψ': 'ps',
    'ω': 'o',
    'ς': 's'
}

for key, value in replacements.copy().items():
    upper_key = key.upper()
    if (key == upper_key) or len(upper_key) != 1:
        continue

    if not value:
        replacements[upper_key] = value
        continue

    upper_value = value[0].upper() + value[1:]
    replacements[upper_key] = upper_value

table = str.maketrans(replacements)


def transliterate(text):
    transliterated = text.translate(table)

    try:
        transliterated.encode('ascii')
        return transliterated

    # if there are some non-english characters, fallback to removal of accents
    # which is okeyish for most european languages
    except UnicodeEncodeError:
        normalized = unicodedata.normalize('NFKD', transliterated)
        # exclude accent characters
        without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        # and try to transliterate again, for letters like ά ῆ
        return without_accents.translate(table)
