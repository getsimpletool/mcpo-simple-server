import os
import gettext as gettext_module
import threading
from typing import Dict

# Gettext locale directory
LOCALEDIR = os.path.join(os.path.dirname(__file__), 'locales')

# Gettext domain
DOMAIN = 'messages'
threadLocalData = threading.local()

# set default locale for the webapp
threadLocalData.locale = 'en'

# find out all supported locales in locale directory
LOCALES = []
try:
    for dirpath, dirnames, filenames in os.walk(LOCALEDIR):
        for dirname in dirnames:
            if os.path.isdir(os.path.join(dirpath, dirname, 'LC_MESSAGES')):
                LOCALES.append(dirname)
        break
except FileNotFoundError:
    # If locales directory doesn't exist
    pass

# Always ensure 'en' is in the list of locales
if 'en' not in LOCALES:
    LOCALES.append('en')

# Create language code aliases (e.g., 'fr' for 'fr_FR' if only one fr_* exists)
language_aliases = {}
language_variants = {}

# Group locales by their base language code
for locale in LOCALES:
    if '_' in locale:
        base_lang = locale.split('_')[0]
        if base_lang not in language_variants:
            language_variants[base_lang] = []
        language_variants[base_lang].append(locale)

# Create aliases for languages with only one variant
for base_lang, variants in language_variants.items():
    if len(variants) == 1 and base_lang not in LOCALES:
        language_aliases[base_lang] = variants[0]

# print("Available locales:", LOCALES)
# print("Language aliases:", language_aliases)

# Dictionary to store translation objects
AllTranslations: Dict[str, gettext_module.NullTranslations] = {}

# Load translations for each locale
for locale in LOCALES:
    try:
        AllTranslations[locale] = gettext_module.translation(DOMAIN, LOCALEDIR, [locale])
    except FileNotFoundError:
        # Fallback to NullTranslations if translation file not found
        AllTranslations[locale] = gettext_module.NullTranslations()

# Add aliases to the translations dictionary
for alias, target in language_aliases.items():
    AllTranslations[alias] = AllTranslations[target]

# Always ensure 'en' is available as a fallback
if 'en' not in AllTranslations:
    AllTranslations['en'] = gettext_module.NullTranslations()


def translate(message: str) -> str:
    """Get translated message for the current locale"""
    current_locale = getattr(threadLocalData, 'locale', 'en')

    # Check if the locale exists directly
    if current_locale in AllTranslations:
        return AllTranslations[current_locale].gettext(message)

    # Check if there's an alias for this locale
    locale_base = current_locale.split('_', maxsplit=1)[0] if '_' in current_locale else current_locale
    if locale_base in AllTranslations:
        return AllTranslations[locale_base].gettext(message)

    # Fallback to 'en'
    return AllTranslations['en'].gettext(message)


def ngettext(singular: str, plural: str, n: int) -> str:
    """Get translated singular/plural message for the current locale based on count"""
    current_locale = getattr(threadLocalData, 'locale', 'en')

    # Check if the locale exists directly
    if current_locale in AllTranslations:
        return AllTranslations[current_locale].ngettext(singular, plural, n)

    # Check if there's an alias for this locale
    locale_base = current_locale.split('_', maxsplit=1)[0] if '_' in current_locale else current_locale
    if locale_base in AllTranslations:
        return AllTranslations[locale_base].ngettext(singular, plural, n)

    # Fallback to 'en'
    return AllTranslations['en'].ngettext(singular, plural, n)


def set_locale(locale_code: str) -> None:
    """Set the current locale for the thread"""
    # Check if the locale exists directly
    if locale_code in LOCALES or locale_code in language_aliases:
        threadLocalData.locale = locale_code
    else:
        # Check if there's a variant of this locale
        locale_base = locale_code.split('_', maxsplit=1)[0] if '_' in locale_code else locale_code
        if locale_base in language_aliases:
            threadLocalData.locale = language_aliases[locale_base]
        else:
            threadLocalData.locale = 'en'


def get_locale() -> str:
    """Get the current locale for the thread"""
    return getattr(threadLocalData, 'locale', 'en')


def get_translations() -> gettext_module.NullTranslations:
    """Get the translations object for the current locale"""
    current_locale = getattr(threadLocalData, 'locale', 'en')

    # Check if the locale exists directly
    if current_locale in AllTranslations:
        return AllTranslations[current_locale]

    # Check if there's an alias for this locale
    locale_base = current_locale.split('_', maxsplit=1)[0] if '_' in current_locale else current_locale
    if locale_base in AllTranslations:
        return AllTranslations[locale_base]

    # Fallback to 'en'
    return AllTranslations['en']


def get_supported_locales() -> list:
    """Get list of supported locales including aliases"""
    # Return both actual locales and their aliases
    return list(set(LOCALES + list(language_aliases.keys())))


def setup_jinja2_translation(jinja2_env) -> None:
    """Setup Jinja2 environment with gettext translations"""
    jinja2_env.install_gettext_translations(get_translations(), newstyle=True)
