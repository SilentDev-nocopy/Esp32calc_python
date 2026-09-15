import pytest

from resiris.tokenizer import Tokenizer
from resiris.parser import Parser
from resiris.interpreter import Interpreter, IntDivisionError


def run(source: str):
    tokens = Tokenizer().tokenize(source)
    ast = Parser(tokens).parse()
    return Interpreter().run(ast)


def test_int_division_raises_int_division_error():
    with pytest.raises(
        IntDivisionError,
        match=r'Cant division with int type! Must use float! Error code:"IntDivisionError"',
    ):
        run(
            "v a int = 10\n"
            "v b float = 2.0\n"
            "v result float = a / b\n"
        )


def test_float_division_works():
    env = run(
        "v a float = 10.0\n"
        "v b int = 2\n"
        "v result float = a / b\n"
    )
    assert env["result"].value == 5.0


def test_int_compound_division_raises_int_division_error():
    with pytest.raises(
        IntDivisionError,
        match=r'Cant division with int type! Must use float! Error code:"IntDivisionError"',
    ):
        run(
            "v result int = 10\n"
            "result /= 2.0\n"
        )
