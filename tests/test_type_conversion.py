import pytest

from resiris.interpreter import Interpreter, RuntimeErrorResiris, TypeErrorResiris
from resiris.parser import Parser
from resiris.tokenizer import Tokenizer


def run(source):
    tokens = Tokenizer().tokenize(source)
    program = Parser(tokens).parse()
    return Interpreter().run(program)


def test_type_int_to_float_without_modifying_original():
    variables = run("""\nv x int = 10\nv y float = x.type(float)\n""")
    assert variables["x"].value == 10
    assert variables["x"].type_name == "int"
    assert variables["y"].value == 10.0
    assert variables["y"].type_name == "float"


def test_type_number_to_bool():
    variables = run("""\nv a int = 0\nv b int = -3\nv cval int = 4\nv aa bool = a.type(bool)\nv bb bool = b.type(bool)\nv cc bool = cval.type(bool)\n""")
    assert variables["aa"].value is False
    assert variables["bb"].value is False
    assert variables["cc"].value is True


def test_type_float_to_int_rounds_half_up():
    variables = run("""\nv a float = 0.4\nv b float = 0.5\nv cval float = 1.4\nv d float = 1.5\nv aa int = a.type(int)\nv bb int = b.type(int)\nv cc int = cval.type(int)\nv dd int = d.type(int)\n""")
    assert variables["aa"].value == 0
    assert variables["bb"].value == 1
    assert variables["cc"].value == 1
    assert variables["dd"].value == 2


def test_type_numeric_to_string():
    variables = run("""\nv a int = 10\nv b float = 2.5\nv aa string = a.type(string)\nv bb string = b.type(string)\n""")
    assert variables["aa"].value == "10"
    assert variables["bb"].value == "2.5"


def test_type_bool_conversions():
    variables = run("""\nv a bool = true\nv b bool = false\nv ai int = a.type(int)\nv bi int = b.type(int)\nv af float = a.type(float)\nv bf float = b.type(float)\nv ass string = a.type(string)\nv bss string = b.type(string)\n""")
    assert variables["ai"].value == 1
    assert variables["bi"].value == 0
    assert variables["af"].value == 1.0
    assert variables["bf"].value == 0.0
    assert variables["ass"].value == "true"
    assert variables["bss"].value == "false"


def test_type_zero_arguments_queries_type():
    variables = run("""\nv x int = 10\nv y string = x.type()\n""")
    assert variables["y"].value == "int"
    assert variables["y"].type_name == "string"


def test_type_string_to_numeric_or_bool_is_forbidden():
    with pytest.raises(RuntimeErrorResiris, match="ConversionFail"):
        run('v x string = "10"\nv y int = x.type(int)\n')
    with pytest.raises(RuntimeErrorResiris, match="ConversionFail"):
        run('v x string = "10.0"\nv y float = x.type(float)\n')
    with pytest.raises(RuntimeErrorResiris, match="ConversionFail"):
        run('v x string = "true"\nv y bool = x.type(bool)\n')


def test_type_rejects_invalid_target_type():
    with pytest.raises(Exception):
        run("v x int = 10\nv y int = x.type(UnknownObject)\n")


def test_type_rejects_more_than_one_argument():
    with pytest.raises(Exception):
        run("v x int = 10\nv y int = x.type(float, int)\n")


def test_type_works_on_constants():
    variables = run("""\nc x int = 10\nv y float = x.type(float)\n""")
    assert variables["x"].value == 10
    assert variables["x"].type_name == "int"
    assert variables["y"].value == 10.0
