import math
from pathlib import Path

from resiris.interpreter import Interpreter
from resiris.parser import Parser
from resiris.tokenizer import Tokenizer


def parse(source: str):
    return Parser(Tokenizer().tokenize(source)).parse()


def run_expr(expression: str):
    root = Path(__file__).resolve().parents[1]
    interpreter = Interpreter(modules_dir=root / "Modules")
    variables = interpreter.run(
        parse(f"<include> RSMath\nv result UnknownObject = {expression}\n")
    )
    return variables["result"].value


def test_basic_math_functions():
    assert run_expr("RSMath.abs(-7)") == 7
    assert run_expr("RSMath.sqrt(25)") == 5.0
    assert math.isclose(run_expr("RSMath.cbrt(27)"), 3.0)
    assert run_expr("RSMath.pow(2, 5)") == 32.0


def test_rounding_functions():
    assert run_expr("RSMath.floor(3.9)") == 3
    assert run_expr("RSMath.ceil(3.1)") == 4
    assert run_expr("RSMath.round(3.5)") == 4


def test_logarithms():
    assert math.isclose(run_expr("RSMath.ln(RSMath.E)"), 1.0)
    assert math.isclose(run_expr("RSMath.ln(RSMath[E])"), 1.0)
    assert math.isclose(run_expr("RSMath.log10(1000)"), 3.0)


def test_trigonometry_uses_radians():
    assert math.isclose(run_expr("RSMath.sin(RSMath.PI / 2.0)"), 1.0, abs_tol=1e-12)
    assert math.isclose(run_expr("RSMath.sin(RSMath[PI] / 2.0)"), 1.0, abs_tol=1e-12)
    assert math.isclose(run_expr("RSMath.cos(0.0)"), 1.0)
    assert math.isclose(run_expr("RSMath.tan(0.0)"), 0.0)
    assert math.isclose(run_expr("RSMath.asin(1.0)"), RSMath_PI_HALF, abs_tol=1e-12)
    assert math.isclose(run_expr("RSMath.acos(1.0)"), 0.0)
    assert math.isclose(run_expr("RSMath.atan(1.0)"), RSMath_PI_QUARTER, abs_tol=1e-12)


RSMath_PI_HALF = math.pi / 2
RSMath_PI_QUARTER = math.pi / 4


def test_geometry_and_pythagoras():
    assert math.isclose(run_expr("RSMath.hypot(3.0, 4.0)"), 5.0)
    assert math.isclose(run_expr("RSMath.pythagoras(3.0, 4.0)"), 5.0)


def test_combinatorics_and_number_theory():
    assert run_expr("RSMath.factorial(5)") == 120
    assert run_expr("RSMath.ncr(10, 3)") == 120
    assert run_expr("RSMath.npr(10, 3)") == 720
    assert run_expr("RSMath.gcd(48, 18)") == 6
    assert run_expr("RSMath.lcm(12, 18)") == 36
    assert run_expr("RSMath.mod(17, 5)") == 2


def test_min_max_clamp():
    assert run_expr("RSMath.min(3, 7)") == 3
    assert run_expr("RSMath.max(3, 7)") == 7
    assert run_expr("RSMath.clamp(12, 0, 10)") == 10
    assert run_expr("RSMath.clamp(-2, 0, 10)") == 0
    assert run_expr("RSMath.clamp(5, 0, 10)") == 5


def test_floating_point_predicates():
    assert run_expr("RSMath.is_nan(0.0)") is False
    assert run_expr("RSMath.is_inf(0.0)") is False
    assert run_expr("RSMath.is_finite(0.0)") is True
