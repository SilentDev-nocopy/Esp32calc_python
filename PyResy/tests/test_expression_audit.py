"""
Resiris – nagy expression/operator audit tesztcsomag.

Cél:
    A jelenlegi Resiris expression- és operátorviselkedésének
    széles körű, izolált ellenőrzése.

Ez a fájl NEM vezet be új Resiris szabályt.
Csak a jelenlegi implementációban már létező operátorokat és
kifejezéseket teszteli.

Futtatás:
    pytest -q tests/test_expression_audit.py
"""

import pytest

from resiris.interpreter import (
    IntDivisionError,
    Interpreter,
    RuntimeErrorResiris,
    ResirisTypeError,
    UnknownVariableError,
)
from resiris.parser import Parser
from resiris.tokenizer import Tokenizer


def parse(source):
    return Parser(Tokenizer().tokenize(source)).parse()


def run(source, *, interpreter=None):
    interpreter = interpreter or Interpreter()
    return interpreter.run(parse(source))


def value(source, name):
    return run(source)[name].value


# ===========================================================================
# ALAP ARITMETIKA
# ===========================================================================

def test_add_ints():
    assert value("v x int = 10 + 5\n", "x") == 15


def test_subtract_ints():
    assert value("v x int = 10 - 5\n", "x") == 5


def test_multiply_ints():
    assert value("v x int = 10 * 5\n", "x") == 50


def test_modulo_ints():
    assert value("v x int = 17 % 5\n", "x") == 2


def test_add_floats():
    assert value("v x float = 1.5 + 2.5\n", "x") == 4.0


def test_subtract_floats():
    assert value("v x float = 5.5 - 2.0\n", "x") == 3.5


def test_multiply_floats():
    assert value("v x float = 2.5 * 4\n", "x") == 10.0


def test_modulo_floats():
    assert value("v x float = 7.5 % 2.0\n", "x") == 1.5


# ===========================================================================
# OSZTÁS – CURRENT INTDIVISIONERROR SZABÁLY
# ===========================================================================

def test_float_divided_by_int_is_valid():
    assert value("v x float = 10.0 / 2\n", "x") == 5.0


def test_float_divided_by_float_is_valid():
    assert value("v x float = 10.0 / 2.0\n", "x") == 5.0


def test_int_divided_by_int_is_rejected():
    with pytest.raises(
        IntDivisionError,
        match=r'Cant division with int type! Must use float! Error code:"IntDivisionError"',
    ):
        run("v x float = 10 / 2\n")


def test_int_divided_by_float_is_rejected():
    with pytest.raises(
        IntDivisionError,
        match=r'Cant division with int type! Must use float! Error code:"IntDivisionError"',
    ):
        run("v x float = 10 / 2.0\n")


def test_int_compound_division_is_rejected():
    with pytest.raises(
        IntDivisionError,
        match=r'Cant division with int type! Must use float! Error code:"IntDivisionError"',
    ):
        run(
            "v x int = 10\n"
            "x /= 2\n"
        )


def test_float_compound_division_by_int_is_valid():
    variables = run(
        "v x float = 10.0\n"
        "x /= 2\n"
    )
    assert variables["x"].value == 5.0
    assert variables["x"].type_name == "float"


def test_float_compound_division_by_float_is_valid():
    variables = run(
        "v x float = 10.0\n"
        "x /= 2.0\n"
    )
    assert variables["x"].value == 5.0


def test_division_by_zero_is_rejected():
    with pytest.raises(RuntimeErrorResiris, match="division by zero"):
        run("v x float = 10.0 / 0\n")


def test_float_compound_division_by_zero_is_rejected():
    with pytest.raises(RuntimeErrorResiris, match="division by zero"):
        run(
            "v x float = 10.0\n"
            "x /= 0\n"
        )


# ===========================================================================
# PRECEDENCIA ÉS ZÁRÓJELEK
# ===========================================================================

def test_multiplication_has_higher_precedence_than_addition():
    assert value("v x int = 2 + 3 * 4\n", "x") == 14


def test_multiplication_has_higher_precedence_than_subtraction():
    assert value("v x int = 20 - 3 * 4\n", "x") == 8


def test_modulo_has_multiplicative_precedence():
    assert value("v x int = 2 + 17 % 5\n", "x") == 4


def test_parentheses_override_addition_precedence():
    assert value("v x int = (2 + 3) * 4\n", "x") == 20


def test_nested_parentheses():
    assert value("v x int = ((2 + 3) * (4 + 1))\n", "x") == 25


def test_parentheses_can_change_expression_result():
    assert value("v x int = 20 - (3 * 4)\n", "x") == 8


def test_complex_precedence_expression():
    assert value("v x int = 2 + 3 * 4 - 5 % 2\n", "x") == 13


# ===========================================================================
# UNARY OPERÁTOROK
# ===========================================================================

def test_unary_minus_int():
    assert value("v x int = -10\n", "x") == -10


def test_unary_plus_int():
    assert value("v x int = +10\n", "x") == 10


def test_unary_minus_float():
    assert value("v x float = -2.5\n", "x") == -2.5


def test_unary_plus_float():
    assert value("v x float = +2.5\n", "x") == 2.5


def test_unary_minus_can_be_used_in_expression():
    assert value("v x int = 10 + -3\n", "x") == 7


def test_unary_plus_can_be_used_in_expression():
    assert value("v x int = 10 + +3\n", "x") == 13


# ===========================================================================
# OPERÁTOROK VARIANTOKKAL
# ===========================================================================

def test_binary_operators_use_variable_values():
    variables = run(
        "v a int = 10\n"
        "v b int = 3\n"
        "v add int = a + b\n"
        "v sub int = a - b\n"
        "v mul int = a * b\n"
        "v mod int = a % b\n"
    )

    assert variables["add"].value == 13
    assert variables["sub"].value == 7
    assert variables["mul"].value == 30
    assert variables["mod"].value == 1


def test_float_variable_division():
    variables = run(
        "v a float = 10.0\n"
        "v b int = 4\n"
        "v result float = a / b\n"
    )
    assert variables["result"].value == 2.5


def test_mixed_numeric_addition_is_accepted_by_float_target():
    variables = run(
        "v a int = 10\n"
        "v b float = 2.5\n"
        "v result float = a + b\n"
    )
    assert variables["result"].value == 12.5


def test_mixed_numeric_subtraction_is_accepted_by_float_target():
    variables = run(
        "v a int = 10\n"
        "v b float = 2.5\n"
        "v result float = a - b\n"
    )
    assert variables["result"].value == 7.5


def test_mixed_numeric_multiplication_is_accepted_by_float_target():
    variables = run(
        "v a int = 10\n"
        "v b float = 2.5\n"
        "v result float = a * b\n"
    )
    assert variables["result"].value == 25.0


def test_mixed_numeric_modulo_is_accepted_by_float_target():
    variables = run(
        "v a int = 10\n"
        "v b float = 2.5\n"
        "v result float = a % b\n"
    )
    assert variables["result"].value == 0.0


# ===========================================================================
# COMPOUND ASSIGNMENT
# ===========================================================================

def test_compound_addition():
    variables = run(
        "v x int = 10\n"
        "x += 5\n"
    )
    assert variables["x"].value == 15


def test_compound_subtraction():
    variables = run(
        "v x int = 10\n"
        "x -= 5\n"
    )
    assert variables["x"].value == 5


def test_compound_multiplication():
    variables = run(
        "v x int = 10\n"
        "x *= 5\n"
    )
    assert variables["x"].value == 50


def test_compound_operations_can_be_chained():
    variables = run(
        "v x int = 10\n"
        "x += 5\n"
        "x -= 3\n"
        "x *= 2\n"
    )
    assert variables["x"].value == 24


def test_compound_assignment_preserves_int_type():
    variables = run(
        "v x int = 10\n"
        "x += 2\n"
        "x -= 1\n"
        "x *= 3\n"
    )
    assert variables["x"].type_name == "int"
    assert variables["x"].value == 33


def test_compound_assignment_preserves_float_type():
    variables = run(
        "v x float = 10.0\n"
        "x += 2\n"
        "x -= 1\n"
        "x *= 3\n"
    )
    assert variables["x"].type_name == "float"
    assert variables["x"].value == 33.0


# ===========================================================================
# ÖSSZEHASONLÍTÁSOK
# ===========================================================================

def test_equal_true():
    assert value("v x bool = 5 == 5\n", "x") is True


def test_equal_false():
    assert value("v x bool = 5 == 6\n", "x") is False


def test_not_equal_true():
    assert value("v x bool = 5 != 6\n", "x") is True


def test_not_equal_false():
    assert value("v x bool = 5 != 5\n", "x") is False


def test_greater_true():
    assert value("v x bool = 6 > 5\n", "x") is True


def test_greater_false():
    assert value("v x bool = 5 > 6\n", "x") is False


def test_less_true():
    assert value("v x bool = 5 < 6\n", "x") is True


def test_less_false():
    assert value("v x bool = 6 < 5\n", "x") is False


def test_greater_equal_true_when_equal():
    assert value("v x bool = 5 >= 5\n", "x") is True


def test_greater_equal_true_when_greater():
    assert value("v x bool = 6 >= 5\n", "x") is True


def test_greater_equal_false():
    assert value("v x bool = 4 >= 5\n", "x") is False


def test_less_equal_true_when_equal():
    assert value("v x bool = 5 <= 5\n", "x") is True


def test_less_equal_true_when_less():
    assert value("v x bool = 4 <= 5\n", "x") is True


def test_less_equal_false():
    assert value("v x bool = 6 <= 5\n", "x") is False


def test_comparisons_work_with_variables():
    variables = run(
        "v a int = 10\n"
        "v b int = 5\n"
        "v eq bool = a == b\n"
        "v neq bool = a != b\n"
        "v gt bool = a > b\n"
        "v lt bool = a < b\n"
        "v ge bool = a >= b\n"
        "v le bool = a <= b\n"
    )

    assert variables["eq"].value is False
    assert variables["neq"].value is True
    assert variables["gt"].value is True
    assert variables["lt"].value is False
    assert variables["ge"].value is True
    assert variables["le"].value is False


# ===========================================================================
# STRING EXPRESSIONÖK
# ===========================================================================

def test_string_concatenation():
    assert value('v x string = "hello" + " world"\n', "x") == "hello world"


def test_string_concatenation_can_use_variables():
    variables = run(
        'v a string = "hello"\n'
        'v b string = " world"\n'
        "v result string = a + b\n"
    )
    assert variables["result"].value == "hello world"


def test_string_plus_int_is_rejected():
    with pytest.raises(ResirisTypeError):
        run('v x string = "value: " + 10\n')


def test_string_plus_float_is_rejected():
    with pytest.raises(ResirisTypeError):
        run('v x string = "value: " + 2.5\n')


def test_string_plus_bool_is_rejected():
    with pytest.raises(ResirisTypeError):
        run('v x string = "value: " + true\n')


def test_string_subtraction_is_rejected():
    with pytest.raises(ResirisTypeError):
        run('v x string = "abc" - "a"\n')


def test_string_multiplication_is_rejected():
    with pytest.raises(ResirisTypeError):
        run('v x string = "abc" * 2\n')


# ===========================================================================
# TÍPUSHATÁROK / HIBÁS OPERANDUSOK
# ===========================================================================

def test_bool_is_not_accepted_as_numeric_addition_operand():
    with pytest.raises(ResirisTypeError):
        run("v x int = true + 1\n")


def test_bool_is_not_accepted_as_numeric_subtraction_operand():
    with pytest.raises(ResirisTypeError):
        run("v x int = true - 1\n")


def test_bool_is_not_accepted_as_numeric_multiplication_operand():
    with pytest.raises(ResirisTypeError):
        run("v x int = true * 2\n")


def test_bool_is_not_accepted_as_numeric_division_operand():
    with pytest.raises(ResirisTypeError):
        run("v x float = 10.0 / true\n")


def test_bool_is_not_accepted_as_numeric_modulo_operand():
    with pytest.raises(ResirisTypeError):
        run("v x int = 10 % true\n")


def test_unknown_variable_in_expression_is_rejected():
    with pytest.raises(UnknownVariableError):
        run("v x int = missing + 1\n")


def test_unknown_variable_on_right_side_is_rejected():
    with pytest.raises(UnknownVariableError):
        run("v x int = 1 + missing\n")


# ===========================================================================
# KOMPLEX KIFEJEZÉSEK
# ===========================================================================

def test_complex_numeric_expression():
    variables = run(
        "v a int = 10\n"
        "v b int = 3\n"
        "v factor float = 2.5\n"
        "v result float = (a + b) * factor\n"
    )
    assert variables["result"].value == 32.5


def test_complex_expression_with_comparison():
    variables = run(
        "v a int = 10\n"
        "v b int = 3\n"
        "v result bool = (a + b) > 10\n"
    )
    assert variables["result"].value is True


def test_expression_result_can_be_used_in_if():
    variables = run(
        "v a int = 10\n"
        "v b int = 3\n"
        "v result int = 0\n"
        "if (a + b) > 10:\n"
        "\tresult = 1\n"
        "else:\n"
        "\tresult = 2\n"
    )
    assert variables["result"].value == 1


def test_expression_result_can_be_used_in_function_argument():
    variables = run(
        "fn identity(x):\n"
        "\treturn x\n"
        "v result int = identity(2 + 3 * 4)\n"
    )
    assert variables["result"].value == 14


def test_expression_can_combine_multiple_variables():
    variables = run(
        "v a int = 2\n"
        "v b int = 3\n"
        "v factor int = 4\n"
        "v result int = a + b * factor\n"
    )
    assert variables["result"].value == 14


# ===========================================================================
# CONSTANTS KIFEJEZÉSBEN
# ===========================================================================

def test_constant_can_be_used_in_arithmetic():
    variables = run(
        "c base int = 10\n"
        "v result int = base + 5\n"
    )
    assert variables["result"].value == 15


def test_constant_can_be_used_in_comparison():
    variables = run(
        "c limit int = 10\n"
        "v result bool = limit >= 10\n"
    )
    assert variables["result"].value is True


# ===========================================================================
# NINCS VÉLETLEN IMPLICIT STRING KONVERZIÓ
# ===========================================================================

def test_numeric_to_string_is_not_implicit_in_addition():
    with pytest.raises(ResirisTypeError):
        run('v x string = "x" + 5\n')


# ===========================================================================
# KÖZVETLEN EXPRESSION STATEMENTEK
# ===========================================================================

def test_expression_statement_can_execute_arithmetic_without_assignment():
    variables = run(
        "v x int = 1\n"
        "x + 2\n"
    )
    assert variables["x"].value == 1


def test_expression_statement_can_execute_comparison_without_assignment():
    variables = run(
        "v x int = 1\n"
        "x == 1\n"
    )
    assert variables["x"].value == 1
