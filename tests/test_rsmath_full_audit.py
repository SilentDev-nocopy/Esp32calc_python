import math
from pathlib import Path

import pytest

from resiris.interpreter import Interpreter, RuntimeErrorResiris
from resiris.parser import Parser
from resiris.tokenizer import Tokenizer


EXPECTED_FUNCTIONS = [
    "abs", "sqrt", "cbrt", "pow", "floor", "ceil", "round",
    "ln", "log10", "sin", "cos", "tan", "asin", "acos", "atan",
    "hypot", "factorial", "ncr", "npr", "gcd", "lcm", "mod",
    "min", "max", "clamp", "is_nan", "is_inf", "is_finite", "pythagoras",
]


def parse(source: str):
    return Parser(Tokenizer().tokenize(source)).parse()


def make_interpreter():
    project_root = Path(__file__).resolve().parents[1]
    return Interpreter(modules_dir=project_root / "Modules")


def run_expr(expression: str):
    interpreter = make_interpreter()
    program = parse(
        f"<include> RSMath\n"
        f"v result UnknownObject = {expression}\n"
    )
    variables = interpreter.run(program)
    return variables["result"].value


def run_program(source: str):
    return make_interpreter().run(parse(source))


# ---------------------------------------------------------------------------
# Module registration / exported surface
# ---------------------------------------------------------------------------


def test_rsmath_module_can_be_included():
    variables = run_program("<include> RSMath\n")
    assert variables == {}


def test_rsmath_exports_exact_function_list():
    exported = run_expr("RSMath[FUNCTIONS]")
    assert exported == ", ".join(EXPECTED_FUNCTIONS)


def test_rsmath_exports_exact_variable_list():
    exported = run_expr("RSMath[VARIABLES]")
    assert exported == "PI:float, E:float"


def test_rsmath_pi_constant():
    assert math.isclose(run_expr("RSMath[PI]"), math.pi, rel_tol=0.0, abs_tol=1e-15)


def test_rsmath_e_constant():
    assert math.isclose(run_expr("RSMath[E]"), math.e, rel_tol=0.0, abs_tol=1e-15)


def test_rsmath_constant_can_be_converted_with_type():
    assert math.isclose(
        run_expr("RSMath[PI].type(float)"),
        math.pi,
        rel_tol=0.0,
        abs_tol=1e-15,
    )


# ---------------------------------------------------------------------------
# Basic mathematics
# ---------------------------------------------------------------------------


def test_abs_int_and_float():
    assert run_expr("RSMath.abs(-7)") == 7
    assert run_expr("RSMath.abs(-7.5)") == 7.5


def test_sqrt():
    assert run_expr("RSMath.sqrt(25)") == 5.0
    assert math.isclose(run_expr("RSMath.sqrt(RSMath[PI])"), math.sqrt(math.pi))


def test_cbrt():
    assert math.isclose(run_expr("RSMath.cbrt(27)"), 3.0)
    assert math.isclose(run_expr("RSMath.cbrt(-8)"), -2.0)


def test_pow():
    assert run_expr("RSMath.pow(2, 5)") == 32.0
    assert math.isclose(run_expr("RSMath.pow(9, 0.5)"), 3.0)


# ---------------------------------------------------------------------------
# Rounding
# ---------------------------------------------------------------------------


def test_floor():
    assert run_expr("RSMath.floor(3.9)") == 3
    assert run_expr("RSMath.floor(-3.1)") == -4


def test_ceil():
    assert run_expr("RSMath.ceil(3.1)") == 4
    assert run_expr("RSMath.ceil(-3.9)") == -3


def test_round():
    assert run_expr("RSMath.round(3.5)") == 4
    assert run_expr("RSMath.round(3.4)") == 3


# ---------------------------------------------------------------------------
# Logarithms / exponential-style calculations
# ---------------------------------------------------------------------------


def test_ln():
    assert math.isclose(run_expr("RSMath.ln(RSMath[E])"), 1.0, abs_tol=1e-12)
    assert math.isclose(run_expr("RSMath.ln(1.0)"), 0.0, abs_tol=1e-12)


def test_log10():
    assert math.isclose(run_expr("RSMath.log10(1000)"), 3.0)
    assert math.isclose(run_expr("RSMath.log10(1.0)"), 0.0)


# ---------------------------------------------------------------------------
# Trigonometry (radians)
# ---------------------------------------------------------------------------


def test_sin_cos_tan():
    assert math.isclose(run_expr("RSMath.sin(RSMath[PI] / 2.0)"), 1.0, abs_tol=1e-12)
    assert math.isclose(run_expr("RSMath.cos(0.0)"), 1.0, abs_tol=1e-12)
    assert math.isclose(run_expr("RSMath.tan(0.0)"), 0.0, abs_tol=1e-12)


def test_inverse_trigonometry():
    assert math.isclose(run_expr("RSMath.asin(1.0)"), math.pi / 2, abs_tol=1e-12)
    assert math.isclose(run_expr("RSMath.acos(1.0)"), 0.0, abs_tol=1e-12)
    assert math.isclose(run_expr("RSMath.atan(1.0)"), math.pi / 4, abs_tol=1e-12)


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------


def test_hypot():
    assert math.isclose(run_expr("RSMath.hypot(3.0, 4.0)"), 5.0)


def test_pythagoras():
    assert math.isclose(run_expr("RSMath.pythagoras(3.0, 4.0)"), 5.0)
    assert math.isclose(run_expr("RSMath.pythagoras(5.0, 12.0)"), 13.0)


def test_pythagoras_is_usable_inside_expression():
    assert math.isclose(
        run_expr("RSMath.pythagoras(3.0, 4.0) + 1.0"),
        6.0,
    )


# ---------------------------------------------------------------------------
# Combinatorics
# ---------------------------------------------------------------------------


def test_factorial():
    assert run_expr("RSMath.factorial(0)") == 1
    assert run_expr("RSMath.factorial(5)") == 120


def test_ncr():
    assert run_expr("RSMath.ncr(10, 3)") == 120
    assert run_expr("RSMath.ncr(10, 0)") == 1


def test_npr():
    assert run_expr("RSMath.npr(10, 3)") == 720
    assert run_expr("RSMath.npr(10, 0)") == 1


# ---------------------------------------------------------------------------
# Number theory
# ---------------------------------------------------------------------------


def test_gcd():
    assert run_expr("RSMath.gcd(48, 18)") == 6
    assert run_expr("RSMath.gcd(17, 5)") == 1


def test_lcm():
    assert run_expr("RSMath.lcm(12, 18)") == 36
    assert run_expr("RSMath.lcm(7, 5)") == 35


def test_mod():
    assert run_expr("RSMath.mod(17, 5)") == 2
    assert run_expr("RSMath.mod(20, 4)") == 0


# ---------------------------------------------------------------------------
# Min / max / clamp
# ---------------------------------------------------------------------------


def test_min_max():
    assert run_expr("RSMath.min(3, 7)") == 3
    assert run_expr("RSMath.max(3, 7)") == 7


def test_clamp():
    assert run_expr("RSMath.clamp(12, 0, 10)") == 10
    assert run_expr("RSMath.clamp(-2, 0, 10)") == 0
    assert run_expr("RSMath.clamp(5, 0, 10)") == 5


# ---------------------------------------------------------------------------
# Floating-point predicates
# ---------------------------------------------------------------------------


def test_is_nan():
    assert run_expr("RSMath.is_nan(0.0)") is False


def test_is_inf():
    assert run_expr("RSMath.is_inf(0.0)") is False


def test_is_finite():
    assert run_expr("RSMath.is_finite(0.0)") is True


# ---------------------------------------------------------------------------
# Integration / module access rules
# ---------------------------------------------------------------------------


def test_rsmath_function_call_can_be_assigned_to_typed_var():
    variables = run_program(
        "<include> RSMath\n"
        "v result float = RSMath.sqrt(25)\n"
    )
    assert variables["result"].value == 5.0
    assert variables["result"].type_name == "float"


def test_rsmath_function_call_can_be_printed(capsys):
    run_program("<include> RSMath\nprint_cmd(RSMath.pythagoras(3.0, 4.0))\n")
    assert capsys.readouterr().out == "5.0\n"


def test_rsmath_function_accepts_variable_arguments():
    variables = run_program(
        "<include> RSMath\n"
        "v a float = 3\n"
        "v b float = 4\n"
        "v result float = RSMath.pythagoras(a, b)\n"
    )
    assert variables["result"].value == 5.0


def test_rsmath_can_be_called_from_user_function():
    variables = run_program(
        "<include> RSMath\n"
        "fn calculate():\n"
        "\treturn RSMath.sqrt(81)\n"
        "v result float = calculate()\n"
    )
    assert variables["result"].value == 9.0


def test_unknown_rsmath_function_is_rejected():
    with pytest.raises(RuntimeErrorResiris, match="unknown module function"):
        run_expr("RSMath.does_not_exist(1)")


def test_unexported_rsmath_constant_is_rejected():
    with pytest.raises(RuntimeErrorResiris, match="unknown module constant"):
        run_expr("RSMath[DOES_NOT_EXIST]")


def test_module_constant_dot_access_is_not_allowed():
    with pytest.raises(RuntimeErrorResiris, match="only valid for function calls"):
        run_expr("RSMath.PI")


def test_rsmath_function_argument_count_is_checked():
    with pytest.raises(RuntimeErrorResiris, match="invalid argument count"):
        run_expr("RSMath.sqrt(1, 2)")
