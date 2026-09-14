from pathlib import Path

import pytest

from resiris.interpreter import Interpreter, RuntimeErrorResiris
from resiris.parser import Parser
from resiris.tokenizer import Tokenizer


def parse(source: str):
    return Parser(Tokenizer().tokenize(source)).parse()


def make_interpreter(tmp_path: Path, body: str) -> Interpreter:
    modules = tmp_path / "Modules"
    modules.mkdir()
    (modules / "TestMod.py").write_text(body, encoding="utf-8")
    return Interpreter(modules_dir=modules)


def test_module_function_call_returns_value(tmp_path):
    interpreter = make_interpreter(
        tmp_path,
        """NAME = "TestMod"
FUNCTIONS = "double"
VARIABLES = ""

def _INIT_():
    pass

def double(value):
    return value * 2
""",
    )
    program = parse("<include> TestMod\nv result int = TestMod.double(21)\n")
    variables = interpreter.run(program)
    assert variables["result"].value == 42
    assert variables["result"].type_name == "int"


def test_bundled_rsmath_sqrt():
    project_root = Path(__file__).resolve().parents[1]
    interpreter = Interpreter(modules_dir=project_root / "Modules")
    program = parse("<include> RSMath\nv result float = RSMath.sqrt(25)\n")
    variables = interpreter.run(program)
    assert variables["result"].value == 5.0


@pytest.mark.parametrize(
    "literal, expected",
    [("12", 12), ("1.5", 1.5), ('"hello"', "hello"), ("true", True)],
)
def test_module_function_accepts_allowed_argument_types(tmp_path, literal, expected):
    interpreter = make_interpreter(
        tmp_path,
        """NAME = "TestMod"
FUNCTIONS = "identity"
VARIABLES = ""

def _INIT_():
    pass

def identity(value):
    return value
""",
    )
    variables = interpreter.run(
        parse(
            f"<include> TestMod\n"
            f"v result UnknownObject = TestMod.identity({literal})\n"
        )
    )
    assert variables["result"].value == expected


def test_module_function_rejects_functional_object_argument(tmp_path):
    interpreter = make_interpreter(
        tmp_path,
        """NAME = "TestMod"
FUNCTIONS = "take"
VARIABLES = ""

def _INIT_():
    pass

def take(value):
    return 1
""",
    )
    source = """<include> TestMod
v f FunctionalObject = FunctionalObject.new():
	return 1
v result int = TestMod.take(f)
"""
    with pytest.raises(RuntimeErrorResiris, match=r"UnknownModuleArgument"):
        interpreter.run(parse(source))


def test_unknown_module_function_is_rejected(tmp_path):
    interpreter = make_interpreter(
        tmp_path,
        """NAME = "TestMod"
FUNCTIONS = "double"
VARIABLES = ""

def _INIT_():
    pass

def double(value):
    return value * 2
""",
    )
    with pytest.raises(RuntimeErrorResiris, match="unknown module function"):
        interpreter.run(parse("<include> TestMod\nv result int = TestMod.triple(2)\n"))


def test_module_access_requires_include(tmp_path):
    interpreter = make_interpreter(
        tmp_path,
        """NAME = "TestMod"
FUNCTIONS = "double"
VARIABLES = ""

def _INIT_():
    pass

def double(value):
    return value * 2
""",
    )
    with pytest.raises(RuntimeErrorResiris, match="module is not included"):
        interpreter.run(parse("v result int = TestMod.double(2)\n"))


def test_module_function_can_be_nested_in_print_cmd(tmp_path, capsys):
    interpreter = make_interpreter(
        tmp_path,
        """NAME = "TestMod"
FUNCTIONS = "double"
VARIABLES = ""

def _INIT_():
    pass

def double(value):
    return value * 2
""",
    )
    interpreter.run(parse("<include> TestMod\nprint_cmd(TestMod.double(7))\n"))
    assert capsys.readouterr().out == "14\n"


def test_module_access_ast():
    from resiris.ast_nodes import CallExpr, ModuleAccessExpr

    program = parse("<include> TestMod\nv result int = TestMod.double(2)\n")
    declaration = program.statements[1]
    assert isinstance(declaration.value, CallExpr)
    assert isinstance(declaration.value.function, ModuleAccessExpr)
    assert declaration.value.function.module_name == "TestMod"
    assert declaration.value.function.member_name == "double"


def test_module_exported_constant_can_be_read(tmp_path):
    interpreter = make_interpreter(
        tmp_path,
        """NAME = "TestMod"
FUNCTIONS = ""
VARIABLES = "PI:float"

PI = 3.14

def _INIT_():
    pass
""",
    )
    variables = interpreter.run(
        parse("<include> TestMod\nv result float = TestMod.PI\n")
    )
    assert variables["result"].value == 3.14


def test_non_exported_module_member_is_rejected(tmp_path):
    interpreter = make_interpreter(
        tmp_path,
        """NAME = "TestMod"
FUNCTIONS = ""
VARIABLES = ""

SECRET = 42

def _INIT_():
    pass
""",
    )
    with pytest.raises(RuntimeErrorResiris, match="unknown module constant"):
        interpreter.run(parse("<include> TestMod\nv result int = TestMod.SECRET\n"))


def test_module_function_wrong_argument_count_is_resiris_error(tmp_path):
    interpreter = make_interpreter(
        tmp_path,
        """NAME = "TestMod"
FUNCTIONS = "double"
VARIABLES = ""

def _INIT_():
    pass

def double(value):
    return value * 2
""",
    )
    with pytest.raises(RuntimeErrorResiris, match="invalid argument count"):
        interpreter.run(parse("<include> TestMod\nv result int = TestMod.double(1, 2)\n"))
