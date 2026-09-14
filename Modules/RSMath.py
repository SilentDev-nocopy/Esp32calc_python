# Python-side prototype module. The final module ABI will be C++.

import math

NAME = "RSMath"
FUNCTIONS = "sqrt"
VARIABLES = ""


def _INIT_():
    pass


def sqrt(value):
    return math.sqrt(value)
