import pytest

from resiris.interpreter import Interpreter, RuntimeErrorResiris, TypeErrorResiris
from resiris.parser import Parser
from resiris.tokenizer import Tokenizer


def parse(source):
    return Parser(Tokenizer().tokenize(source)).parse()


def run(source, interpreter=None):
    interpreter = interpreter or Interpreter()
    return interpreter.run(parse(source))


def value(source, name):
    return run(source)[name].value


# ---------------------------------------------------------------------------
# BASIC IF
# ---------------------------------------------------------------------------

def test_if_true_executes_body():
    assert value("v x int = 0\nif true:\n\tx = 1\n", "x") == 1


def test_if_false_skips_body():
    assert value("v x int = 0\nif false:\n\tx = 1\n", "x") == 0


def test_if_false_with_no_else_continues_after_block():
    assert value("v x int = 0\nif false:\n\tx = 1\nx = 2\n", "x") == 2


def test_if_true_with_no_else_continues_after_block():
    assert value("v x int = 0\nif true:\n\tx = 1\nx += 1\n", "x") == 2


def test_if_condition_can_be_bool_variable():
    assert value("v condition bool = true\nv x int = 0\nif condition:\n\tx = 7\n", "x") == 7


def test_if_condition_can_be_bool_constant():
    assert value("c condition bool = true\nv x int = 0\nif condition:\n\tx = 7\n", "x") == 7


def test_if_condition_can_be_comparison():
    assert value("v x int = 5\nif x > 3:\n\tx = 9\n", "x") == 9


def test_if_condition_can_be_equality_comparison():
    assert value("v x int = 5\nif x == 5:\n\tx = 9\n", "x") == 9


def test_if_condition_can_be_inequality_comparison():
    assert value("v x int = 5\nif x != 4:\n\tx = 9\n", "x") == 9


def test_if_condition_can_be_less_than():
    assert value("v x int = 2\nif x < 3:\n\tx = 9\n", "x") == 9


def test_if_condition_can_be_less_equal():
    assert value("v x int = 3\nif x <= 3:\n\tx = 9\n", "x") == 9


def test_if_condition_can_be_greater_equal():
    assert value("v x int = 3\nif x >= 3:\n\tx = 9\n", "x") == 9


# ---------------------------------------------------------------------------
# IF / ELSE
# ---------------------------------------------------------------------------

def test_else_executes_when_if_false():
    assert value("v x int = 0\nif false:\n\tx = 1\nelse:\n\tx = 2\n", "x") == 2


def test_else_does_not_execute_when_if_true():
    assert value("v x int = 0\nif true:\n\tx = 1\nelse:\n\tx = 2\n", "x") == 1


def test_if_else_executes_exactly_one_branch():
    env = run(
        "v first int = 0\n"
        "v second int = 0\n"
        "if true:\n"
        "\tfirst = 1\n"
        "else:\n"
        "\tsecond = 1\n"
    )
    assert env["first"].value == 1
    assert env["second"].value == 0


def test_else_body_can_have_multiple_statements():
    env = run(
        "v x int = 0\n"
        "v y int = 0\n"
        "if false:\n"
        "\tx = 1\n"
        "else:\n"
        "\tx = 5\n"
        "\ty = 6\n"
    )
    assert env["x"].value == 5
    assert env["y"].value == 6


# ---------------------------------------------------------------------------
# ELIF
# ---------------------------------------------------------------------------

def test_first_elif_executes():
    assert value(
        "v x int = 2\n"
        "v result int = 0\n"
        "if x == 1:\n\tresult = 1\n"
        "elif x == 2:\n\tresult = 2\n"
        "else:\n\tresult = 3\n",
        "result",
    ) == 2


def test_second_elif_executes():
    assert value(
        "v x int = 3\n"
        "v result int = 0\n"
        "if x == 1:\n\tresult = 1\n"
        "elif x == 2:\n\tresult = 2\n"
        "elif x == 3:\n\tresult = 3\n"
        "else:\n\tresult = 4\n",
        "result",
    ) == 3


def test_last_elif_executes_without_else():
    assert value(
        "v x int = 3\n"
        "v result int = 0\n"
        "if x == 1:\n\tresult = 1\n"
        "elif x == 2:\n\tresult = 2\n"
        "elif x == 3:\n\tresult = 3\n",
        "result",
    ) == 3


def test_else_executes_after_all_elif_conditions_are_false():
    assert value(
        "v x int = 9\n"
        "v result int = 0\n"
        "if x == 1:\n\tresult = 1\n"
        "elif x == 2:\n\tresult = 2\n"
        "elif x == 3:\n\tresult = 3\n"
        "else:\n\tresult = 4\n",
        "result",
    ) == 4


def test_only_first_matching_elif_branch_executes():
    assert value(
        "v result int = 0\n"
        "if false:\n\tresult = 1\n"
        "elif true:\n\tresult = 2\n"
        "elif true:\n\tresult = 3\n"
        "else:\n\tresult = 4\n",
        "result",
    ) == 2


def test_elif_is_not_evaluated_after_if_matches():
    env = run(
        "v x int = 0\n"
        "if true:\n"
        "\tx = 1\n"
        "elif missing == 1:\n"
        "\tx = 2\n"
    )
    assert env["x"].value == 1


def test_later_elif_is_not_evaluated_after_previous_elif_matches():
    env = run(
        "v x int = 0\n"
        "if false:\n"
        "\tpass\n"
        "elif true:\n"
        "\tx = 1\n"
        "elif missing == 1:\n"
        "\tx = 2\n"
    )
    assert env["x"].value == 1


# ---------------------------------------------------------------------------
# NESTED CONTROL FLOW
# ---------------------------------------------------------------------------

def test_nested_if_true_true():
    assert value(
        "v result int = 0\n"
        "if true:\n"
        "\tif true:\n"
        "\t\tresult = 10\n",
        "result",
    ) == 10


def test_nested_if_outer_true_inner_false():
    assert value(
        "v result int = 0\n"
        "if true:\n"
        "\tif false:\n"
        "\t\tresult = 10\n"
        "\telse:\n"
        "\t\tresult = 20\n",
        "result",
    ) == 20


def test_nested_if_outer_false_inner_is_not_executed():
    assert value(
        "v result int = 0\n"
        "if false:\n"
        "\tif true:\n"
        "\t\tresult = 10\n",
        "result",
    ) == 0


def test_nested_elif_chain():
    assert value(
        "v result int = 0\n"
        "if false:\n"
        "\tresult = 1\n"
        "elif true:\n"
        "\tif false:\n"
        "\t\tresult = 2\n"
        "\telif true:\n"
        "\t\tresult = 3\n"
        "\telse:\n"
        "\t\tresult = 4\n"
        "else:\n"
        "\tresult = 5\n",
        "result",
    ) == 3


def test_if_body_can_contain_if_and_following_statement():
    assert value(
        "v result int = 0\n"
        "if true:\n"
        "\tif true:\n"
        "\t\tresult = 1\n"
        "\tresult += 2\n",
        "result",
    ) == 3


# ---------------------------------------------------------------------------
# FUNCTIONS + IF
# ---------------------------------------------------------------------------

def test_if_inside_function():
    assert value(
        "fn choose(x):\n"
        "\tif x > 0:\n"
        "\t\treturn 1\n"
        "\telse:\n"
        "\t\treturn 2\n"
        "v result int = choose(5)\n",
        "result",
    ) == 1


def test_elif_inside_function():
    assert value(
        "fn choose(x):\n"
        "\tif x == 1:\n"
        "\t\treturn 1\n"
        "\telif x == 2:\n"
        "\t\treturn 2\n"
        "\telse:\n"
        "\t\treturn 3\n"
        "v result int = choose(2)\n",
        "result",
    ) == 2


def test_if_function_branch_can_assign_local():
    assert value(
        "fn choose(x):\n"
        "\tv result int = 0\n"
        "\tif x > 0:\n"
        "\t\tresult = 10\n"
        "\telse:\n"
        "\t\tresult = 20\n"
        "\treturn result\n"
        "v answer int = choose(-1)\n",
        "answer",
    ) == 20


def test_if_can_use_function_result_as_condition():
    assert value(
        "fn is_positive(x):\n"
        "\treturn x > 0\n"
        "v result int = 0\n"
        "if is_positive(5):\n"
        "\tresult = 42\n",
        "result",
    ) == 42


def test_if_false_function_result_skips_body():
    assert value(
        "fn is_positive(x):\n"
        "\treturn x > 0\n"
        "v result int = 0\n"
        "if is_positive(-5):\n"
        "\tresult = 42\n",
        "result",
    ) == 0


# ---------------------------------------------------------------------------
# EXPRESSIONS AND TYPES IN CONDITIONS
# ---------------------------------------------------------------------------

def test_if_comparison_expression_has_expected_truth_value():
    assert value(
        "v a int = 4\n"
        "v b int = 6\n"
        "v result int = 0\n"
        "if a + 2 == b:\n"
        "\tresult = 1\n",
        "result",
    ) == 1


def test_if_parenthesized_comparison_expression():
    assert value(
        "v result int = 0\n"
        "if (2 + 3) == 5:\n"
        "\tresult = 1\n",
        "result",
    ) == 1


def test_if_bool_expression_from_comparison_can_be_stored_first():
    env = run(
        "v comparison bool = 2 < 3\n"
        "v result int = 0\n"
        "if comparison:\n"
        "\tresult = 8\n"
    )
    assert env["comparison"].value is True
    assert env["result"].value == 8


def test_if_rejects_int_condition():
    with pytest.raises(TypeErrorResiris, match="if condition"):
        run("if 1:\n\tpass\n")


def test_if_rejects_float_condition():
    with pytest.raises(TypeErrorResiris, match="if condition"):
        run("if 1.0:\n\tpass\n")


def test_if_rejects_string_condition():
    with pytest.raises(TypeErrorResiris, match="if condition"):
        run('if "true":\n\tpass\n')


def test_elif_rejects_int_condition_when_reached():
    with pytest.raises(TypeErrorResiris, match="elif condition"):
        run("if false:\n\tpass\nelif 1:\n\tpass\n")


def test_elif_rejects_float_condition_when_reached():
    with pytest.raises(TypeErrorResiris, match="elif condition"):
        run("if false:\n\tpass\nelif 1.0:\n\tpass\n")


def test_elif_rejects_string_condition_when_reached():
    with pytest.raises(TypeErrorResiris, match="elif condition"):
        run('if false:\n\tpass\nelif "x":\n\tpass\n')


# ---------------------------------------------------------------------------
# EXECUTION ORDER / SIDE EFFECTS
# ---------------------------------------------------------------------------

def test_if_branch_statements_execute_in_order():
    env = run(
        "v x int = 1\n"
        "if true:\n"
        "\tx += 2\n"
        "\tx *= 3\n"
    )
    assert env["x"].value == 9


def test_only_selected_branch_changes_state():
    env = run(
        "v x int = 0\n"
        "if false:\n"
        "\tx = 1\n"
        "elif true:\n"
        "\tx = 2\n"
        "else:\n"
        "\tx = 3\n"
    )
    assert env["x"].value == 2


def test_code_after_if_runs_after_selected_branch():
    env = run(
        "v x int = 0\n"
        "if true:\n"
        "\tx = 5\n"
        "else:\n"
        "\tx = 7\n"
        "x += 10\n"
    )
    assert env["x"].value == 15


def test_code_after_elif_chain_runs_after_chain():
    env = run(
        "v x int = 0\n"
        "if false:\n"
        "\tx = 1\n"
        "elif true:\n"
        "\tx = 2\n"
        "else:\n"
        "\tx = 3\n"
        "x += 10\n"
    )
    assert env["x"].value == 12


def test_multiple_independent_if_statements_both_run():
    env = run(
        "v x int = 0\n"
        "if true:\n"
        "\tx += 1\n"
        "if true:\n"
        "\tx += 2\n"
    )
    assert env["x"].value == 3


# ---------------------------------------------------------------------------
# PASS / RETURN INSIDE BRANCHES
# ---------------------------------------------------------------------------

def test_pass_inside_if_does_not_stop_if_block():
    assert value(
        "v x int = 0\n"
        "if true:\n"
        "\tpass\n"
        "\tx = 5\n",
        "x",
    ) == 5


def test_pass_inside_elif_does_not_stop_elif_block():
    assert value(
        "v x int = 0\n"
        "if false:\n"
        "\tpass\n"
        "elif true:\n"
        "\tpass\n"
        "\tx = 5\n",
        "x",
    ) == 5


def test_return_inside_if_returns_selected_value():
    assert value(
        "fn choose(x):\n"
        "\tif x > 0:\n"
        "\t\treturn 10\n"
        "\treturn 20\n"
        "v result int = choose(1)\n",
        "result",
    ) == 10


def test_return_inside_else_returns_selected_value():
    assert value(
        "fn choose(x):\n"
        "\tif x > 0:\n"
        "\t\treturn 10\n"
        "\telse:\n"
        "\t\treturn 20\n"
        "v result int = choose(-1)\n",
        "result",
    ) == 20


def test_return_inside_elif_returns_selected_value():
    assert value(
        "fn choose(x):\n"
        "\tif x == 1:\n"
        "\t\treturn 10\n"
        "\telif x == 2:\n"
        "\t\treturn 20\n"
        "\telse:\n"
        "\t\treturn 30\n"
        "v result int = choose(2)\n",
        "result",
    ) == 20


# ---------------------------------------------------------------------------
# SCOPE / DECLARATIONS IN BRANCHES
# ---------------------------------------------------------------------------

def test_branch_can_assign_existing_global_varint():
    env = run(
        "v x int = 0\n"
        "if true:\n"
        "\tx = 9\n"
    )
    assert env["x"].value == 9


def test_branch_can_read_global_varint():
    env = run(
        "v x int = 9\n"
        "v result int = 0\n"
        "if x == 9:\n"
        "\tresult = x\n"
    )
    assert env["result"].value == 9


def test_branch_can_read_constant():
    env = run(
        "c expected int = 9\n"
        "v result int = 0\n"
        "if expected == 9:\n"
        "\tresult = 1\n"
    )
    assert env["result"].value == 1


# ---------------------------------------------------------------------------
# PARSER / SYNTAX NEGATIVE CASES
# ---------------------------------------------------------------------------

def test_if_missing_colon_is_syntax_error():
    with pytest.raises(Exception):
        parse("if true\n\tpass\n")


def test_if_missing_body_is_syntax_error():
    with pytest.raises(Exception):
        parse("if true:\n")


def test_elif_missing_colon_is_syntax_error():
    with pytest.raises(Exception):
        parse("if false:\n\tpass\nelif true\n\tpass\n")


def test_else_missing_colon_is_syntax_error():
    with pytest.raises(Exception):
        parse("if false:\n\tpass\nelse\n\tpass\n")


def test_else_must_follow_if_chain():
    with pytest.raises(Exception):
        parse("else:\n\tpass\n")


def test_elif_must_follow_if():
    with pytest.raises(Exception):
        parse("elif true:\n\tpass\n")


def test_if_body_must_be_indented():
    with pytest.raises(Exception):
        parse("if true:\npass\n")


def test_elif_body_must_be_indented():
    with pytest.raises(Exception):
        parse("if false:\n\tpass\nelif true:\npass\n")


def test_else_body_must_be_indented():
    with pytest.raises(Exception):
        parse("if false:\n\tpass\nelse:\npass\n")
