
import pytest

from resiris.parser import Parser
from resiris.tokenizer import Tokenizer, ResirisSyntaxError
from resiris.interpreter import Interpreter, RuntimeErrorResiris


def run(source):
    program = Parser(Tokenizer().tokenize(source)).parse()
    return Interpreter().run(program)


def test_mat_matches_int_and_continues_after_mat(capsys):
    run("""\
v x int = 2
mat x:
\t1:
\t\tprint_cmd("one")
\t2:
\t\tprint_cmd("two")
print_cmd("after")
""")
    assert capsys.readouterr().out == "two\nafter\n"


def test_mat_else_and_no_fallthrough(capsys):
    run("""\
v x int = 3
mat x:
\t1:
\t\tprint_cmd("one")
\t2:
\t\tprint_cmd("two")
\telse:
\t\tprint_cmd("other")
""")
    assert capsys.readouterr().out == "other\n"


def test_mat_type_match(capsys):
    run("""\
v x int = 10
mat x.type():
\tint:
\t\tprint_cmd("int")
\tfloat:
\t\tprint_cmd("float")
""")
    assert capsys.readouterr().out == "int\n"


def test_mat_string_result(capsys):
    run("""\
v x int = 10
mat x.string():
\t"10":
\t\tprint_cmd("string")
""")
    assert capsys.readouterr().out == "string\n"


def test_mat_skips_wrong_type(capsys):
    run("""\
v x float = 2.0
mat x:
\t1:
\t\tprint_cmd("int")
\telse:
\t\tprint_cmd("float")
""")
    assert capsys.readouterr().out == "float\n"


def test_mat_duplicate_case():
    with pytest.raises(ResirisSyntaxError, match="SameCaseMultiCall"):
        Parser(Tokenizer().tokenize("""\
v x int = 1
mat x:
\t1:
\t\tpass
\t1:
\t\tpass
""")).parse()


def test_mat_mixed_case_types():
    with pytest.raises(ResirisSyntaxError):
        Parser(Tokenizer().tokenize("""\
v x int = 1
mat x:
\t1:
\t\tpass
\t"1":
\t\tpass
""")).parse()


def test_mat_nested_forbidden():
    with pytest.raises(ResirisSyntaxError, match="NestedMatchError"):
        Parser(Tokenizer().tokenize("""\
v x int = 1
mat x:
\t1:
\t\tmat x:
\t\t\t1:
\t\t\t\tpass
""")).parse()


def test_mat_literal_checked_value_forbidden():
    with pytest.raises(ResirisSyntaxError):
        Parser(Tokenizer().tokenize("""\
mat 1:
\t1:
\t\tpass
""")).parse()


def test_mat_missing_value_runtime_error():
    with pytest.raises(RuntimeErrorResiris):
        run("""\
mat missing:
\t1:
\t\tpass
""")


def test_mat_return_from_case():
    variables = run("""\
v x int = 1
fn test():
\tmat x:
\t\t1:
\t\t\treturn 42
v result int = test()
""")
    assert variables["result"].value == 42
