"""
Resiris – return / pass audit.

CURRENT scope:
    Tests the currently implemented return and pass behavior without
    introducing new language rules.
"""

import pytest

from resiris.interpreter import (
    FunctionError,
    Interpreter,
    RuntimeErrorResiris,
)
from resiris.parser import Parser
from resiris.tokenizer import Tokenizer


def parse(source):
    return Parser(Tokenizer().tokenize(source)).parse()


def run(source):
    return Interpreter().run(parse(source))


# ---------------------------------------------------------------------------
# RETURN
# ---------------------------------------------------------------------------

def test_return_int_value():
    env = run(
        "fn get():\n"
        "\treturn 42\n"
        "v result int = get()\n"
    )
    assert env["result"].value == 42


def test_return_float_value():
    env = run(
        "fn get():\n"
        "\treturn 4.5\n"
        "v result float = get()\n"
    )
    assert env["result"].value == 4.5


def test_return_string_value():
    env = run(
        "fn get():\n"
        '\treturn "hello"\n'
        "v result string = get()\n"
    )
    assert env["result"].value == "hello"


def test_return_bool_value():
    env = run(
        "fn get():\n"
        "\treturn true\n"
        "v result bool = get()\n"
    )
    assert env["result"].value is True


def test_return_expression():
    env = run(
        "fn calculate(a, b):\n"
        "\treturn a + b * 2\n"
        "v result int = calculate(3, 4)\n"
    )
    assert env["result"].value == 11


def test_return_uses_local_variable():
    env = run(
        "fn calculate(a):\n"
        "\tv result int = a * 2\n"
        "\treturn result\n"
        "v output int = calculate(5)\n"
    )
    assert env["output"].value == 10


def test_return_uses_global_variable():
    env = run(
        "v value int = 25\n"
        "fn get():\n"
        "\treturn value\n"
        "v result int = get()\n"
    )
    assert env["result"].value == 25


def test_return_uses_parameter():
    env = run(
        "fn identity(value):\n"
        "\treturn value\n"
        "v result int = identity(17)\n"
    )
    assert env["result"].value == 17


def test_return_exits_before_following_assignment():
    env = run(
        "fn test():\n"
        "\treturn 10\n"
        "\tv never int = 99\n"
        "v result int = test()\n"
    )
    assert env["result"].value == 10


def test_return_exits_before_following_pass():
    env = run(
        "fn test():\n"
        "\treturn 10\n"
        "\tpass\n"
        "v result int = test()\n"
    )
    assert env["result"].value == 10


def test_return_inside_if():
    env = run(
        "fn choose(value):\n"
        "\tif value > 0:\n"
        "\t\treturn 1\n"
        "\treturn 2\n"
        "v result int = choose(5)\n"
    )
    assert env["result"].value == 1


def test_return_inside_else():
    env = run(
        "fn choose(value):\n"
        "\tif value > 0:\n"
        "\t\treturn 1\n"
        "\telse:\n"
        "\t\treturn 2\n"
        "v result int = choose(-1)\n"
    )
    assert env["result"].value == 2


def test_return_inside_elif():
    env = run(
        "fn choose(value):\n"
        "\tif value < 0:\n"
        "\t\treturn 1\n"
        "\telif value == 0:\n"
        "\t\treturn 2\n"
        "\telse:\n"
        "\t\treturn 3\n"
        "v result int = choose(0)\n"
    )
    assert env["result"].value == 2


def test_return_inside_nested_if():
    env = run(
        "fn choose(value):\n"
        "\tif value > 0:\n"
        "\t\tif value > 10:\n"
        "\t\t\treturn 3\n"
        "\t\treturn 2\n"
        "\treturn 1\n"
        "v result int = choose(20)\n"
    )
    assert env["result"].value == 3


def test_return_inside_mat_case():
    env = run(
        "fn choose(value):\n"
        "\tmat value:\n"
        "\t\t1:\n"
        "\t\t\treturn 10\n"
        "\t\t2:\n"
        "\t\t\treturn 20\n"
        "\tv result int = 30\n"
        "\treturn result\n"
        "v output int = choose(2)\n"
    )
    assert env["output"].value == 20


def test_return_inside_mat_else():
    env = run(
        "fn choose(value):\n"
        "\tmat value:\n"
        "\t\t1:\n"
        "\t\t\treturn 10\n"
        "\t\telse:\n"
        "\t\t\treturn 99\n"
        "v output int = choose(5)\n"
    )
    assert env["output"].value == 99


def test_return_from_nested_function_call():
    env = run(
        "fn inner():\n"
        "\treturn 42\n"
        "fn outer():\n"
        "\treturn inner()\n"
        "v result int = outer()\n"
    )
    assert env["result"].value == 42


def test_return_does_not_exit_caller_function_early():
    env = run(
        "fn inner():\n"
        "\treturn 5\n"
        "fn outer():\n"
        "\tv x int = inner()\n"
        "\treturn x + 10\n"
        "v result int = outer()\n"
    )
    assert env["result"].value == 15


def test_return_value_can_be_used_in_arithmetic():
    env = run(
        "fn get():\n"
        "\treturn 5\n"
        "v result int = get() * 3\n"
    )
    assert env["result"].value == 15


def test_return_value_can_be_passed_to_function():
    env = run(
        "fn get():\n"
        "\treturn 5\n"
        "fn double(value):\n"
        "\treturn value * 2\n"
        "v result int = double(get())\n"
    )
    assert env["result"].value == 10


def test_return_value_type_is_checked_by_assignment():
    with pytest.raises(RuntimeErrorResiris):
        run(
            "fn get():\n"
            "\treturn 1.5\n"
            "v result int = get()\n"
        )


def test_return_without_value_is_allowed_by_current_parser():
    # CURRENT implementation permits a return statement without an expression.
    run(
        "fn test():\n"
        "\treturn\n"
        "test()\n"
    )


def test_return_without_value_exits_function():
    env = run(
        "fn test():\n"
        "\treturn\n"
        "\tv never int = 99\n"
        "v marker int = 1\n"
        "test()\n"
    )
    assert env["marker"].value == 1
    assert "never" not in env


def test_return_outside_function_raises_function_error():
    with pytest.raises(FunctionError):
        run("return 42\n")


def test_return_outside_function_without_value_raises_function_error():
    with pytest.raises(FunctionError):
        run("return\n")


def test_return_in_function_does_not_leak_local_scope():
    interpreter = Interpreter()
    run(
        "fn test():\n"
        "\tv local int = 42\n"
        "\treturn local\n"
        "v result int = test()\n",
    )
    assert "local" not in interpreter.variables


# ---------------------------------------------------------------------------
# PASS
# ---------------------------------------------------------------------------

def test_pass_at_top_level_is_noop():
    env = run(
        "pass\n"
        "v result int = 1\n"
    )
    assert env["result"].value == 1


def test_pass_does_not_stop_top_level_execution():
    env = run(
        "v result int = 0\n"
        "pass\n"
        "result = 10\n"
    )
    assert env["result"].value == 10


def test_multiple_pass_statements_are_noops():
    env = run(
        "pass\n"
        "pass\n"
        "pass\n"
        "v result int = 7\n"
    )
    assert env["result"].value == 7


def test_pass_inside_if():
    env = run(
        "v result int = 0\n"
        "if true:\n"
        "\tpass\n"
        "\tresult = 5\n"
    )
    assert env["result"].value == 5


def test_pass_inside_else():
    env = run(
        "v result int = 0\n"
        "if false:\n"
        "\tresult = 1\n"
        "else:\n"
        "\tpass\n"
        "\tresult = 2\n"
    )
    assert env["result"].value == 2


def test_pass_inside_elif():
    env = run(
        "v result int = 0\n"
        "if false:\n"
        "\tresult = 1\n"
        "elif true:\n"
        "\tpass\n"
        "\tresult = 2\n"
        "else:\n"
        "\tresult = 3\n"
    )
    assert env["result"].value == 2


def test_pass_inside_nested_if():
    env = run(
        "v result int = 0\n"
        "if true:\n"
        "\tif true:\n"
        "\t\tpass\n"
        "\t\tresult = 5\n"
    )
    assert env["result"].value == 5


def test_pass_inside_mat_case():
    env = run(
        "v value int = 1\n"
        "v result int = 0\n"
        "mat value:\n"
        "\t1:\n"
        "\t\tpass\n"
        "\t\tresult = 10\n"
    )
    assert env["result"].value == 10


def test_pass_inside_mat_else():
    env = run(
        "v value int = 9\n"
        "v result int = 0\n"
        "mat value:\n"
        "\t1:\n"
        "\t\tresult = 1\n"
        "\telse:\n"
        "\t\tpass\n"
        "\t\tresult = 2\n"
    )
    assert env["result"].value == 2


def test_pass_inside_function_does_not_stop_function():
    env = run(
        "fn test():\n"
        "\tpass\n"
        "\treturn 42\n"
        "v result int = test()\n"
    )
    assert env["result"].value == 42


def test_pass_can_appear_before_local_declaration():
    env = run(
        "fn test():\n"
        "\tpass\n"
        "\tv result int = 42\n"
        "\treturn result\n"
        "v output int = test()\n"
    )
    assert env["output"].value == 42


def test_pass_between_assignments():
    env = run(
        "v result int = 1\n"
        "pass\n"
        "result = 2\n"
        "pass\n"
        "result = 3\n"
    )
    assert env["result"].value == 3


def test_pass_does_not_change_variable_value():
    env = run(
        "v result int = 42\n"
        "pass\n"
    )
    assert env["result"].value == 42


def test_pass_does_not_create_variable():
    env = run("pass\n")
    assert "pass" not in env


def test_pass_followed_by_return():
    env = run(
        "fn test():\n"
        "\tpass\n"
        "\treturn 42\n"
        "v result int = test()\n"
    )
    assert env["result"].value == 42


def test_return_followed_by_pass_does_not_execute_pass():
    env = run(
        "fn test():\n"
        "\treturn 42\n"
        "\tpass\n"
        "v result int = test()\n"
    )
    assert env["result"].value == 42


def test_multiple_passes_followed_by_return():
    env = run(
        "fn test():\n"
        "\tpass\n"
        "\tpass\n"
        "\tpass\n"
        "\treturn 99\n"
        "v result int = test()\n"
    )
    assert env["result"].value == 99


def test_pass_in_both_branches():
    env = run(
        "v result int = 0\n"
        "if true:\n"
        "\tpass\n"
        "\tresult = 1\n"
        "else:\n"
        "\tpass\n"
        "\tresult = 2\n"
    )
    assert env["result"].value == 1


def test_pass_does_not_skip_next_sibling_statement():
    env = run(
        "v a int = 1\n"
        "pass\n"
        "v b int = 2\n"
        "v result int = a + b\n"
    )
    assert env["result"].value == 3


def test_return_and_pass_can_coexist_in_nested_control_flow():
    env = run(
        "fn test(value):\n"
        "\tif value > 0:\n"
        "\t\tpass\n"
        "\t\tif value > 10:\n"
        "\t\t\treturn 3\n"
        "\treturn 1\n"
        "v result int = test(20)\n"
    )
    assert env["result"].value == 3


def test_return_after_mat_without_match():
    env = run(
        "fn test(value):\n"
        "\tmat value:\n"
        "\t\t1:\n"
        "\t\t\tpass\n"
        "\treturn 42\n"
        "v result int = test(2)\n"
    )
    assert env["result"].value == 42


def test_return_after_mat_else():
    env = run(
        "fn test(value):\n"
        "\tmat value:\n"
        "\t\t1:\n"
        "\t\t\tpass\n"
        "\t\telse:\n"
        "\t\t\tpass\n"
        "\treturn 42\n"
        "v result int = test(2)\n"
    )
    assert env["result"].value == 42


def test_return_value_from_nested_control_flow_is_preserved():
    env = run(
        "fn test(value):\n"
        "\tif value == 1:\n"
        "\t\tmat value:\n"
        "\t\t\t1:\n"
        "\t\t\t\treturn 100\n"
        "\treturn 0\n"
        "v result int = test(1)\n"
    )
    assert env["result"].value == 100


def test_function_without_return_is_callable():
    env = run(
        "fn do_nothing():\n"
        "\tpass\n"
        "v marker int = 7\n"
        "do_nothing()\n"
    )
    assert env["marker"].value == 7


def test_pass_does_not_modify_global_state():
    env = run(
        "v value int = 10\n"
        "pass\n"
        "v result int = value\n"
    )
    assert env["result"].value == 10
