CURRENCY_CONFIG = {
    "jpy": {"symbol": "\u00a5", "decimals": 0, "thousands_sep": ",", "decimal_sep": "."},
}
DEFAULT_CURRENCY = {"symbol": "Rp", "decimals": 2, "thousands_sep": ".", "decimal_sep": ","}


def format_currency(value, user_id: str = None) -> str:
    """Formats a number using each account's own currency convention:
    Rp x.xxx.xxx,xx (Indonesian) by default, or \u00a5x,xxx,xxx (Japanese
    Yen, no decimals) for the jpy account."""
    cfg = CURRENCY_CONFIG.get(user_id, DEFAULT_CURRENCY)
    if value is None:
        value = 0
    s = f"{value:,.{cfg['decimals']}f}"
    if cfg["decimal_sep"] != "." or cfg["thousands_sep"] != ",":
        s = s.replace(",", "\u00a7").replace(".", cfg["decimal_sep"]).replace("\u00a7", cfg["thousands_sep"])
    return f"{cfg['symbol']} {s}"