from locales.uz import texts as uz_texts
from locales.ru import texts as ru_texts

_all_texts: dict[str, dict[str, str]] = {
    "uz": uz_texts,
    "ru": ru_texts,
}


def get_text(lang: str, key: str, **kwargs) -> str:
    """
    Retrieve a localized text string by language code and key.

    Falls back to Uzbek if the requested language or key is not found.
    Supports format-string interpolation via keyword arguments.

    Args:
        lang: Language code ('uz' or 'ru').
        key: Text key to look up.
        **kwargs: Format string parameters.

    Returns:
        The localized (and optionally formatted) text string.
    """
    texts = _all_texts.get(lang, uz_texts)
    text = texts.get(key, uz_texts.get(key, key))
    if kwargs:
        return text.format(**kwargs)
    return text
