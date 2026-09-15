import pytest

from resiris.interpreter import (
    Interpreter,
    RuntimeErrorResiris,
    TypeErrorResiris,
)
from resiris.parser import Parser
from resiris.tokenizer import Tokenizer


def parse(source):
    return Parser(Tokenizer().tokenize(source)).parse()


def run(source):
    return Interpreter().run(Parser(Tokenizer().tokenize(source)).parse())


def test_function_without_parameters():
    env = run(
        "fn answer():\n"
        "\tv x int = 42\n"
        "START():\n"
        "\tanswer()\n"
    )
    assert "x" not in env


def test_function_with_one_parameter():
    env = run(
        "fn identity(a):\n"
        "\treturn a\n"
        "v result int = identity(42)\n"
    )
    assert env["result"].value == 42


def test_function_with_multiple_parameters():
    env = run(
        "fn add(a, b):\n"
        "\treturn a + b\n"
        "v result int = add(2, 3)\n"
    )
    assert env["result"].value == 5


def test_function_call_with_expression_arguments():
    env = run(
        "fn add(a, b):\n"
        "\treturn a + b\n"
        "v result int = add(1 + 2, 3 * 4)\n"
    )
    assert env["result"].value == 15


def test_nested_function_call():
    env = run(
        "fn double(a):\n"
        "\treturn a * 2\n"
        "fn add(a, b):\n"
        "\treturn a + b\n"
        "v result int = add(double(3), double(4))\n"
    )
    assert env["result"].value == 14


def test_function_can_call_another_function():
    env = run(
        "fn double(a):\n"
        "\treturn a * 2\n"
        "fn quadruple(a):\n"
        "\treturn double(double(a))\n"
        "v result int = quadruple(3)\n"
    )
    assert env["result"].value == 12


def test_return_value_can_be_used_in_expression():
    env = run(
        "fn get_value():\n"
        "\treturn 10\n"
        "v result int = get_value() + 5\n"
    )
    assert env["result"].value == 15


def test_return_exits_function_immediately():
    env = run(
        "fn test():\n"
        "\tv x int = 1\n"
        "\treturn 42\n"
        "\tx = 99\n"
        "v result int = test()\n"
    )
    assert env["result"].value == 42


def test_function_without_return_is_allowed():
    run(
        "fn do_nothing():\n"
        "\tpass\n"
        "do_nothing()\n"
    )


def test_local_variable_does_not_escape_function():
    with pytest.raises(RuntimeErrorResiris):
        run(
            "fn make():\n"
            "\tv local_value int = 10\n"
            "make()\n"
            "v result int = local_value\n"
        )


def test_parameter_does_not_escape_function():
    with pytest.raises(RuntimeErrorResiris):
        run(
            "fn test(a):\n"
            "\treturn a\n"
            "test(10)\n"
            "v result int = a\n"
        )


def test_function_can_read_global_varint():
    env = run(
        "v global_value int = 10\n"
        "fn get():\n"
        "\treturn global_value\n"
        "v result int = get()\n"
    )
    assert env["result"].value == 10


def test_function_can_read_global_constant():
    env = run(
        "c global_value int = 10\n"
        "fn get():\n"
        "\treturn global_value\n"
        "v result int = get()\n"
    )
    assert env["result"].value == 10


def test_function_can_modify_global_varint():
    env = run(
        "v global_value int = 10\n"
        "fn change():\n"
        "\tglobal_value += 5\n"
        "change()\n"
    )
    assert env["global_value"].value == 15


def test_function_cannot_modify_global_constant():
    with pytest.raises(RuntimeErrorResiris):
        run(
            "c global_value int = 10\n"
            "fn change():\n"
            "\tglobal_value = 20\n"
            "change()\n"
        )


def test_parameter_shadows_global_name():
    env = run(
        "v value int = 100\n"
        "fn get(value):\n"
        "\treturn value\n"
        "v result int = get(5)\n"
    )
    assert env["result"].value == 5


def test_local_variable_can_be_used_inside_function():
    env = run(
        "fn calculate(a):\n"
        "\tv b int = a * 2\n"
        "\treturn b + 1\n"
        "v result int = calculate(4)\n"
    )
    assert env["result"].value == 9


def test_local_variable_does_not_modify_global_same_name():
    env = run(
        "v value int = 100\n"
        "fn test():\n"
        "\tv value int = 5\n"
        "\treturn value\n"
        "v result int = test()\n"
    )
    assert env["result"].value == 5
    assert env["value"].value == 100


def test_function_parameter_count_too_few():
    with pytest.raises(RuntimeErrorResiris):
        run(
            "fn add(a, b):\n"
            "\treturn a + b\n"
            "add(1)\n"
        )


def test_function_parameter_count_too_many():
    with pytest.raises(RuntimeErrorResiris):
        run(
            "fn add(a, b):\n"
            "\treturn a + b\n"
            "add(1, 2, 3)\n"
        )


def test_unknown_function_call_fails():
    with pytest.raises(RuntimeErrorResiris):
        run("missing_function()\n")


def test_recursive_function():
    env = run(
        "fn countdown(n):\n"
        "\tif n == 0:\n"
        "\t\treturn 0\n"
        "\treturn countdown(n - 1)\n"
        "v result int = countdown(5)\n"
    )
    assert env["result"].value == 0


def test_function_can_contain_if():
    env = run(
        "fn choose(a):\n"
        "\tif a > 0:\n"
        "\t\treturn 1\n"
        "\telse:\n"
        "\t\treturn 2\n"
        "v result int = choose(5)\n"
    )
    assert env["result"].value == 1


def test_function_can_contain_pass():
    env = run(
        "fn test():\n"
        "\tpass\n"
        "\treturn 42\n"
        "v result int = test()\n"
    )
    assert env["result"].value == 42


def test_return_type_is_checked_by_receiving_declaration():
    with pytest.raises(TypeErrorResiris):
        run(
            "fn get():\n"
            "\treturn 1.5\n"
            "v result int = get()\n"
        )


def test_function_result_can_be_float():
    env = run(
        "fn get():\n"
        "\treturn 1.5\n"
        "v result float = get()\n"
    )
    assert env["result"].value == 1.5


def test_function_result_can_be_string():
    env = run(
        "fn get():\n"
        '\treturn "hello"\n'
        "v result string = get()\n"
    )
    assert env["result"].value == "hello"


def test_function_result_can_be_bool():
    env = run(
        "fn get():\n"
        "\treturn true\n"
        "v result bool = get()\n"
    )
    assert env["result"].value is True


def test_function_argument_can_be_float():
    env = run(
        "fn half(a):\n"
        "\treturn a / 2\n"
        "v result float = half(10.0)\n"
    )
    assert env["result"].value == 5.0


def test_function_argument_can_be_string():
    env = run(
        "fn join(a, b):\n"
        "\treturn a + b\n"
        'v result string = join("a", "b")\n'
    )
    assert env["result"].value == "ab"


def test_function_argument_can_be_bool():
    env = run(
        "fn get(a):\n"
        "\treturn a\n"
        "v result bool = get(true)\n"
    )
    assert env["result"].value is True


def test_function_can_be_called_multiple_times():
    env = run(
        "fn double(a):\n"
        "\treturn a * 2\n"
        "v a int = double(2)\n"
        "v b int = double(3)\n"
        "v result_c int = double(4)\n"
    )
    assert env["a"].value == 4
    assert env["b"].value == 6
    assert env["result_c"].value == 8


def test_function_calls_do_not_share_local_state():
    env = run(
        "fn make(a):\n"
        "\tv local int = a\n"
        "\treturn local\n"
        "v a int = make(1)\n"
        "v b int = make(2)\n"
    )
    assert env["a"].value == 1
    assert env["b"].value == 2


def test_return_can_return_expression():
    env = run(
        "fn calculate(a, b):\n"
        "\treturn a * b + 10\n"
        "v result int = calculate(2, 3)\n"
    )
    assert env["result"].value == 16


def test_function_call_inside_if_condition():
    env = run(
        "fn positive(a):\n"
        "\treturn a > 0\n"
        "v result bool = positive(5)\n"
        "if result:\n"
        "\tv x int = 1\n"
    )
    assert env["result"].value is True


def test_function_call_as_argument_to_another_function():
    env = run(
        "fn double(a):\n"
        "\treturn a * 2\n"
        "fn add(a, b):\n"
        "\treturn a + b\n"
        "v result int = add(double(2), 5)\n"
    )
    assert env["result"].value == 9


def test_function_definition_does_not_execute_body_immediately():
    env = run(
        "fn test():\n"
        "\tv x int = 99\n"
        "v outside int = 1\n"
    )
    assert env["outside"].value == 1


def test_function_can_use_multiple_local_variables():
    env = run(
        "fn calculate(a):\n"
        "\tv x int = a + 1\n"
        "\tv y int = x * 2\n"
        "\tv z int = y + 3\n"
        "\treturn z\n"
        "v result int = calculate(4)\n"
    )
    assert env["result"].value == 13


def test_function_local_compound_assignment():
    env = run(
        "fn calculate(a):\n"
        "\tv x int = a\n"
        "\tx += 5\n"
        "\tx *= 2\n"
        "\treturn x\n"
        "v result int = calculate(3)\n"
    )
    assert env["result"].value == 16


def test_function_can_return_parameter_directly():
    env = run(
        "fn identity(a):\n"
        "\treturn a\n"
        "v result int = identity(99)\n"
    )
    assert env["result"].value == 99


def test_function_can_return_global_value():
    env = run(
        "v value int = 123\n"
        "fn get():\n"
        "\treturn value\n"
        "v result int = get()\n"
    )
    assert env["result"].value == 123


def test_function_call_result_can_be_assigned_to_varint():
    env = run(
        "fn get():\n"
        "\treturn 42\n"
        "v result int = 0\n"
        "result = get()\n"
    )
    assert env["result"].value == 42


def test_function_call_result_can_be_used_in_compound_assignment():
    env = run(
        "fn get():\n"
        "\treturn 5\n"
        "v result int = 10\n"
        "result += get()\n"
    )
    assert env["result"].value == 15


def test_function_call_inside_return():
    env = run(
        "fn inner():\n"
        "\treturn 5\n"
        "fn outer():\n"
        "\treturn inner()\n"
        "v result int = outer()\n"
    )
    assert env["result"].value == 5


def test_function_chain():
    env = run(
        "fn a(x):\n"
        "\treturn x + 1\n"
        "fn b(x):\n"
        "\treturn a(x) * 2\n"
        "fn c_func(x):\n"
        "\treturn b(x) + 3\n"
        "v result int = c_func(4)\n"
    )
    assert env["result"].value == 13


def test_function_can_return_bool_expression():
    env = run(
        "fn is_positive(x):\n"
        "\treturn x > 0\n"
        "v result bool = is_positive(1)\n"
    )
    assert env["result"].value is True


def test_function_can_return_string_expression():
    env = run(
        "fn greeting(name):\n"
        '\treturn "Hello " + name\n'
        'v result string = greeting("World")\n'
    )
    assert env["result"].value == "Hello World"


def test_function_can_use_global_and_parameter_together():
    env = run(
        "v offset int = 10\n"
        "fn add_offset(x):\n"
        "\treturn x + offset\n"
        "v result int = add_offset(5)\n"
    )
    assert env["result"].value == 15


def test_function_global_assignment_persists_between_calls():
    env = run(
        "v counter int = 0\n"
        "fn increment():\n"
        "\tcounter += 1\n"
        "increment()\n"
        "increment()\n"
        "increment()\n"
    )
    assert env["counter"].value == 3


def test_function_return_inside_nested_if():
    env = run(
        "fn test(x):\n"
        "\tif x > 0:\n"
        "\t\tif x > 10:\n"
        "\t\t\treturn 3\n"
        "\t\treturn 2\n"
        "\treturn 1\n"
        "v result int = test(20)\n"
    )
    assert env["result"].value == 3


def test_function_return_inside_elif():
    env = run(
        "fn test(x):\n"
        "\tif x < 0:\n"
        "\t\treturn 1\n"
        "\telif x == 0:\n"
        "\t\treturn 2\n"
        "\telse:\n"
        "\t\treturn 3\n"
        "v result int = test(0)\n"
    )
    assert env["result"].value == 2


def test_function_return_inside_else():
    env = run(
        "fn test(x):\n"
        "\tif x < 0:\n"
        "\t\treturn 1\n"
        "\telse:\n"
        "\t\treturn 2\n"
        "v result int = test(5)\n"
    )
    assert env["result"].value == 2


def test_function_can_return_float_from_float_argument():
    env = run(
        "fn halve(x):\n"
        "\treturn x / 2\n"
        "v result float = halve(9.0)\n"
    )
    assert env["result"].value == 4.5


def test_function_can_take_many_parameters():
    env = run(
        "fn calculate(a, b, c_arg, d):\n"
        "\treturn a + b + c_arg + d\n"
        "v result int = calculate(1, 2, 3, 4)\n"
    )
    assert env["result"].value == 10


def test_function_call_can_use_constants_as_arguments():
    env = run(
        "c value int = 42\n"
        "fn identity(a):\n"
        "\treturn a\n"
        "v result int = identity(value)\n"
    )
    assert env["result"].value == 42


def test_function_can_read_constant_inside_expression():
    env = run(
        "c value int = 10\n"
        "fn calculate(a):\n"
        "\treturn a + value\n"
        "v result int = calculate(5)\n"
    )
    assert env["result"].value == 15


def test_function_error_from_nested_call_propagates():
    with pytest.raises(RuntimeErrorResiris):
        run(
            "fn inner():\n"
            "\tv x int = 10 / 2\n"
            "\treturn x\n"
            "fn outer():\n"
            "\treturn inner()\n"
            "outer()\n"
        )


def test_start_function_body_can_contain_function_call():
    from resiris.ast_nodes import FunctionDef, LifecycleDef, ExpressionStmt, CallExpr
    program = parse(
        "fn calculate():\n"
        "\treturn 42\n"
        "START():\n"
        "\tcalculate()\n"
    )
    start = next(statement for statement in program.statements
                 if isinstance(statement, LifecycleDef) and statement.name == "START")
    assert isinstance(start.body[0], ExpressionStmt)
    assert isinstance(start.body[0].expression, CallExpr)
    assert start.body[0].expression.function.name == "calculate"


def test_process_function_body_can_contain_function_call():
    from resiris.ast_nodes import FunctionDef, LifecycleDef, ExpressionStmt, CallExpr
    program = parse(
        "fn calculate():\n"
        "\treturn 42\n"
        "PROCESS(FPS):\n"
        "\tcalculate()\n"
    )
    process = next(statement for statement in program.statements
                   if isinstance(statement, LifecycleDef) and statement.name == "PROCESS")
    assert isinstance(process.body[0], ExpressionStmt)
    assert isinstance(process.body[0].expression, CallExpr)
    assert process.body[0].expression.function.name == "calculate"
