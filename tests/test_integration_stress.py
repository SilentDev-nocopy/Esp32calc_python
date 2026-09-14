from resiris.tokenizer import Tokenizer
from resiris.parser import Parser
from resiris.interpreter import Interpreter


def run(source: str):
    tokens = Tokenizer().tokenize(source)
    ast = Parser(tokens).parse()
    interpreter = Interpreter()
    return interpreter.run(ast)


def test_varint_expression_and_compound_assignment_chain():
    source = (
        "v a int = 10\n"
        "v b int = 5\n"
        "v result int = a + b * 2\n"
        "result += 3\n"
        "result -= 2\n"
        "result *= 2\n"
        "result /= 2\n"
    )

    env = run(source)

    # / produces float in the current interpreter.
    # This test documents the current behavior.
    assert env["a"].value == 10
    assert env["b"].value == 5
    assert env["result"].value == 21.0


def test_function_local_value_does_not_replace_global_value():
    source = (
        "v value int = 10\n"
        "fn make_value():\n"
        "\tv value int = 99\n"
        "\treturn value\n"
        "v result int = make_value()\n"
    )

    env = run(source)

    assert env["value"].value == 10
    assert env["result"].value == 99


def test_mat_inside_function_with_return():
    source = (
        "fn classify(x):\n"
        "\tmat x:\n"
        "\t\t1:\n"
        "\t\t\treturn 10\n"
        "\t\t2:\n"
        "\t\t\treturn 20\n"
        "\t\telse:\n"
        "\t\t\treturn 0\n"
        "v a int = classify(1)\n"
        "v b int = classify(2)\n"
        "v case_result int = classify(99)\n"
    )

    env = run(source)

    assert env["a"].value == 10
    assert env["b"].value == 20
    assert env["case_result"].value == 0


def test_type_conversion_chain():
    source = (
        "v a int = 5\n"
        "v b float = a.type(float)\n"
        "v text_value string = b.type(string)\n"
    )

    env = run(source)

    assert env["a"].value == 5
    assert env["b"].value == 5.0
    assert env["text_value"].value == "5.0"


def test_function_uses_if_then_mat_and_returns():
    source = (
        "fn calculate(x):\n"
        "\tif x < 0:\n"
        "\t\treturn -1\n"
        "\tmat x:\n"
        "\t\t0:\n"
        "\t\t\treturn 100\n"
        "\t\t1:\n"
        "\t\t\treturn 200\n"
        "\t\telse:\n"
        "\t\t\treturn 300\n"
        "v a int = calculate(-5)\n"
        "v b int = calculate(0)\n"
        "v case_result int = calculate(1)\n"
        "v d int = calculate(9)\n"
    )

    env = run(source)

    assert env["a"].value == -1
    assert env["b"].value == 100
    assert env["case_result"].value == 200
    assert env["d"].value == 300


def test_deep_nested_control_flow():
    source = (
        "fn evaluate(x):\n"
        "\tif x > 0:\n"
        "\t\tmat x:\n"
        "\t\t\t1:\n"
        "\t\t\t\treturn 11\n"
        "\t\t\t2:\n"
        "\t\t\t\treturn 22\n"
        "\t\t\telse:\n"
        "\t\t\t\treturn 33\n"
        "\telse:\n"
        "\t\treturn 0\n"
        "v a int = evaluate(1)\n"
        "v b int = evaluate(2)\n"
        "v case_result int = evaluate(9)\n"
        "v d int = evaluate(0)\n"
    )

    env = run(source)

    assert env["a"].value == 11
    assert env["b"].value == 22
    assert env["case_result"].value == 33
    assert env["d"].value == 0