from decimal import Decimal, ROUND_HALF_UP, getcontext

# Set a sane default context for financial calculations
getcontext().prec = 28  # high precision to avoid intermediate rounding errors

TWOPLACES = Decimal('0.01')


def to_decimal(value, quant=TWOPLACES):
    """
    Convert a numeric value to Decimal and quantize to 2 decimal places using ROUND_HALF_UP.
    Accepts Decimal, int, float, or str.
    """
    if isinstance(value, Decimal):
        d = value
    else:
        d = Decimal(str(value))
    return d.quantize(quant, rounding=ROUND_HALF_UP)


def zero():
    return TWOPLACES * 0


def quantize_money(value):
    """Alias to explicitly quantize a Decimal monetary amount to 2dp."""
    return to_decimal(value, TWOPLACES)
