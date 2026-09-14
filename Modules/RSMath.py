# Python-side prototype module. The final module ABI will be C++.

import builtins
import math

NAME = "RSMath"
FUNCTIONS = (
    "abs, sqrt, cbrt, pow, floor, ceil, round, ln, log10, "
    "sin, cos, tan, asin, acos, atan, hypot, factorial, ncr, npr, "
    "gcd, lcm, mod, min, max, clamp, is_nan, is_inf, is_finite, pythagoras"
)
VARIABLES = "PI:float, E:float"

PI = math.pi
E = math.e


def _INIT_():
    pass


def abs(value):
    return math.fabs(value) if isinstance(value, float) else builtins.abs(value)


def sqrt(value):
    return math.sqrt(value)


def cbrt(value):
    return math.cbrt(value)


def pow(base, exponent):
    return math.pow(base, exponent)


def floor(value):
    return math.floor(value)


def ceil(value):
    return math.ceil(value)


def round(value):
    return builtins.round(value)


def ln(value):
    return math.log(value)


def log10(value):
    return math.log10(value)


def sin(value):
    return math.sin(value)


def cos(value):
    return math.cos(value)


def tan(value):
    return math.tan(value)


def asin(value):
    return math.asin(value)


def acos(value):
    return math.acos(value)


def atan(value):
    return math.atan(value)


def hypot(a, b):
    return math.hypot(a, b)


def factorial(value):
    return math.factorial(value)


def ncr(n, r):
    return math.comb(n, r)


def npr(n, r):
    return math.perm(n, r)


def gcd(a, b):
    return math.gcd(a, b)


def lcm(a, b):
    return math.lcm(a, b)


def mod(a, b):
    return a % b


def min(a, b):
    return builtins.min(a, b)


def max(a, b):
    return builtins.max(a, b)


def clamp(value, minimum, maximum):
    return builtins.min(builtins.max(value, minimum), maximum)


def is_nan(value):
    return math.isnan(value)


def is_inf(value):
    return math.isinf(value)


def is_finite(value):
    return math.isfinite(value)


def pythagoras(a, b):
    """Return the hypotenuse from the two perpendicular sides."""
    return math.hypot(a, b)
