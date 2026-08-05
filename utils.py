def format_rupiah(value) -> str:
    """Formats a number as Rp x.xxx.xxx,xx (dot thousands, comma decimals) -
    Indonesian convention, independent of the machine's locale settings."""
    if value is None:
        value = 0
    s = f"{value:,.2f}"  # e.g. "6,639,625.00" (US style)
    s = s.replace(",", "§").replace(".", ",").replace("§", ".")
    return f"Rp {s}"
