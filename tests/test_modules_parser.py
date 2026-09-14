from resiris.ast_nodes import Include
from resiris.parser import Parser
from resiris.tokenizer import Tokenizer


def parse(source: str):
    return Parser(Tokenizer().tokenize(source)).parse()


def test_single_module():
    program = parse("<include> RSMath\n")

    assert len(program.statements) == 1
    assert isinstance(program.statements[0], Include)
    assert program.statements[0].modules == ["RSMath"]


def test_multiple_modules_on_one_include_line():
    program = parse("<include> RSMath, ModuleName2\n")

    assert program.statements[0].modules == ["RSMath", "ModuleName2"]


def test_multiple_include_lines():
    program = parse("<include> RSMath\n<include> ModuleName2\n")

    assert program.statements[0].modules == ["RSMath"]
    assert program.statements[1].modules == ["ModuleName2"]


def test_module_constant_access_uses_brackets():
    from resiris.ast_nodes import Declaration, ModuleConstantAccessExpr

    program = parse("<include> RSMath\nv pi float = RSMath[PI]\n")
    value = program.statements[1].value
    assert isinstance(value, ModuleConstantAccessExpr)
    assert value.module_name == "RSMath"
    assert value.constant_name == "PI"


def test_module_constant_access_requires_constant_name():
    from resiris.tokenizer import ResirisSyntaxError

    import pytest

    with pytest.raises(ResirisSyntaxError):
        parse("<include> RSMath\nv pi float = RSMath[]\n")


def test_module_constant_access_requires_closing_bracket():
    from resiris.tokenizer import ResirisSyntaxError

    import pytest

    with pytest.raises(ResirisSyntaxError):
        parse("<include> RSMath\nv pi float = RSMath[PI\n")
