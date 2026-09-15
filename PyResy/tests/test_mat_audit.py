import pytest

from resiris.parser import Parser
from resiris.tokenizer import Tokenizer, ResirisSyntaxError
from resiris.interpreter import Interpreter, RuntimeErrorResiris


def parse(source):
    return Parser(Tokenizer().tokenize(source)).parse()


def run(source):
    return Interpreter().run(parse(source))


# ---------------------------------------------------------------------------
# Basic matching / control flow
# ---------------------------------------------------------------------------

def test_mat_matches_int(capsys):
    run("""\
v x int = 2
mat x:
\t1:
\t\tprint_cmd("one")
\t2:
\t\tprint_cmd("two")
""")
    assert capsys.readouterr().out == "two\n"


def test_mat_matches_float(capsys):
    run("""\
v x float = 2.5
mat x:
\t1.5:
\t\tprint_cmd("one")
\t2.5:
\t\tprint_cmd("two")
""")
    assert capsys.readouterr().out == "two\n"


def test_mat_matches_string(capsys):
    run("""\
v x string = "hello"
mat x:
\t"hello":
\t\tprint_cmd("matched")
""")
    assert capsys.readouterr().out == "matched\n"


def test_mat_matches_bool(capsys):
    run("""\
v x bool = true
mat x:
\ttrue:
\t\tprint_cmd("true")
\tfalse:
\t\tprint_cmd("false")
""")
    assert capsys.readouterr().out == "true\n"


def test_mat_else_when_no_case_matches(capsys):
    run("""\
v x int = 99
mat x:
\t1:
\t\tprint_cmd("one")
\t2:
\t\tprint_cmd("two")
\telse:
\t\tprint_cmd("other")
""")
    assert capsys.readouterr().out == "other\n"


def test_mat_without_else_continues_after_statement(capsys):
    run("""\
v x int = 99
mat x:
\t1:
\t\tprint_cmd("one")
print_cmd("after")
""")
    assert capsys.readouterr().out == "after\n"


def test_mat_continues_after_mat_when_case_matches(capsys):
    run("""\
v x int = 1
mat x:
\t1:
\t\tprint_cmd("case")
print_cmd("after")
""")
    assert capsys.readouterr().out == "case\nafter\n"


def test_mat_has_no_fallthrough(capsys):
    run("""\
v x int = 1
mat x:
\t1:
\t\tprint_cmd("one")
\t2:
\t\tprint_cmd("two")
\telse:
\t\tprint_cmd("else")
""")
    assert capsys.readouterr().out == "one\n"


def test_mat_case_executes_every_statement(capsys):
    run("""\
v x int = 1
mat x:
\t1:
\t\tprint_cmd("first")
\t\tprint_cmd("second")
""")
    assert capsys.readouterr().out == "first\nsecond\n"


def test_mat_else_executes_every_statement(capsys):
    run("""\
v x int = 2
mat x:
\t1:
\t\tpass
\telse:
\t\tprint_cmd("first")
\t\tprint_cmd("second")
""")
    assert capsys.readouterr().out == "first\nsecond\n"


# ---------------------------------------------------------------------------
# Exact type matching
# ---------------------------------------------------------------------------

def test_mat_skips_case_with_different_type(capsys):
    run("""\
v x float = 2.0
mat x:
\t2:
\t\tprint_cmd("int")
\telse:
\t\tprint_cmd("float")
""")
    assert capsys.readouterr().out == "float\n"


def test_mat_mixed_int_and_float_cases_are_rejected():
    with pytest.raises(ResirisSyntaxError):
        parse("""\
v x float = 2.0
mat x:
	2:
		pass
	2.0:
		pass
""")

def test_mat_mixed_bool_and_int_cases_are_rejected():
    with pytest.raises(ResirisSyntaxError):
        parse("""\
v x bool = true
mat x:
	1:
		pass
	true:
		pass
""")

def test_mat_string_does_not_match_numeric_case(capsys):
    run("""\
v x string = "1"
mat x:
\t1:
\t\tprint_cmd("int")
\telse:
\t\tprint_cmd("string")
""")
    assert capsys.readouterr().out == "string\n"


def test_mat_float_does_not_match_string_case(capsys):
    run("""\
v x float = 1.0
mat x:
\t"1.0":
\t\tprint_cmd("string")
\telse:
\t\tprint_cmd("float")
""")
    assert capsys.readouterr().out == "float\n"


# ---------------------------------------------------------------------------
# .type() matching
# ---------------------------------------------------------------------------

def test_mat_type_case_int(capsys):
    run("""\
v x int = 10
mat x.type():
\tint:
\t\tprint_cmd("int")
\tfloat:
\t\tprint_cmd("float")
""")
    assert capsys.readouterr().out == "int\n"


def test_mat_type_case_float(capsys):
    run("""\
v x float = 10.0
mat x.type():
\tint:
\t\tprint_cmd("int")
\tfloat:
\t\tprint_cmd("float")
""")
    assert capsys.readouterr().out == "float\n"


def test_mat_type_case_string(capsys):
    run("""\
v x string = "x"
mat x.type():
\tint:
\t\tprint_cmd("int")
\tstring:
\t\tprint_cmd("string")
""")
    assert capsys.readouterr().out == "string\n"


def test_mat_type_case_bool(capsys):
    run("""\
v x bool = true
mat x.type():
\tbool:
\t\tprint_cmd("bool")
\tint:
\t\tprint_cmd("int")
""")
    assert capsys.readouterr().out == "bool\n"


def test_mat_type_case_else(capsys):
    run("""\
v x int = 10
mat x.type():
\tfloat:
\t\tprint_cmd("float")
\telse:
\t\tprint_cmd("other")
""")
    assert capsys.readouterr().out == "other\n"


def test_mat_type_cases_cannot_be_used_without_type_value():
    with pytest.raises(ResirisSyntaxError):
        parse("""\
v x int = 10
mat x:
\tint:
\t\tpass
""")


# ---------------------------------------------------------------------------
# .string() as checked value
# ---------------------------------------------------------------------------

def test_mat_string_result_matches(capsys):
    run("""\
v x int = 10
mat x.string():
\t"10":
\t\tprint_cmd("matched")
""")
    assert capsys.readouterr().out == "matched\n"


def test_mat_string_result_can_use_else(capsys):
    run("""\
v x int = 10
mat x.string():
\t"20":
\t\tprint_cmd("twenty")
\telse:
\t\tprint_cmd("other")
""")
    assert capsys.readouterr().out == "other\n"


# ---------------------------------------------------------------------------
# Multiple cases / case values
# ---------------------------------------------------------------------------

def test_mat_supports_multiple_int_cases(capsys):
    run("""\
v x int = 4
mat x:
\t1:
\t\tprint_cmd("one")
\t2:
\t\tprint_cmd("two")
\t3:
\t\tprint_cmd("three")
\t4:
\t\tprint_cmd("four")
""")
    assert capsys.readouterr().out == "four\n"


def test_mat_supports_multiple_float_cases(capsys):
    run("""\
v x float = 3.5
mat x:
\t1.5:
\t\tprint_cmd("one")
\t2.5:
\t\tprint_cmd("two")
\t3.5:
\t\tprint_cmd("three")
""")
    assert capsys.readouterr().out == "three\n"


def test_mat_supports_multiple_string_cases(capsys):
    run("""\
v x string = "b"
mat x:
\t"a":
\t\tprint_cmd("a")
\t"b":
\t\tprint_cmd("b")
\t"c":
\t\tprint_cmd("c")
""")
    assert capsys.readouterr().out == "b\n"


def test_mat_supports_multiple_bool_cases(capsys):
    run("""\
v x bool = false
mat x:
\ttrue:
\t\tprint_cmd("true")
\tfalse:
\t\tprint_cmd("false")
""")
    assert capsys.readouterr().out == "false\n"


def test_mat_case_order_does_not_change_exact_match(capsys):
    run("""\
v x int = 2
mat x:
\t3:
\t\tprint_cmd("three")
\t2:
\t\tprint_cmd("two")
\t1:
\t\tprint_cmd("one")
""")
    assert capsys.readouterr().out == "two\n"


# ---------------------------------------------------------------------------
# Return / pass / valid locations
# ---------------------------------------------------------------------------

def test_mat_return_from_mat_case():
    env = run("""\
v x int = 2
fn test():
\tmat x:
\t\t1:
\t\t\treturn 10
\t\t2:
\t\t\treturn 20
\treturn 30
v result int = test()
""")
    assert env["result"].value == 20


def test_mat_return_from_else():
    env = run("""\
v x int = 99
fn test():
\tmat x:
\t\t1:
\t\t\treturn 10
\t\telse:
\t\t\treturn 20
v result int = test()
""")
    assert env["result"].value == 20


def test_mat_pass_does_not_skip_following_mat_statement(capsys):
    run("""\
v x int = 1
mat x:
\t1:
\t\tpass
print_cmd("after")
""")
    assert capsys.readouterr().out == "after\n"


def test_mat_inside_if(capsys):
    run("""\
v x int = 2
if true:
\tmat x:
\t\t2:
\t\t\tprint_cmd("matched")
""")
    assert capsys.readouterr().out == "matched\n"


def test_mat_inside_elif(capsys):
    run("""\
v x int = 2
if false:
\tprint_cmd("if")
elif true:
\tmat x:
\t\t2:
\t\t\tprint_cmd("matched")
""")
    assert capsys.readouterr().out == "matched\n"


def test_mat_inside_else(capsys):
    run("""\
v x int = 2
if false:
\tpass
else:
\tmat x:
\t\t2:
\t\t\tprint_cmd("matched")
""")
    assert capsys.readouterr().out == "matched\n"


def test_mat_inside_function(capsys):
    run("""\
v x int = 5
fn test():
\tmat x:
\t\t5:
\t\t\tprint_cmd("matched")
test()
""")
    assert capsys.readouterr().out == "matched\n"


def test_mat_is_parsed_inside_start():
    program = parse("""\
start():
	v x int = 5
	mat x:
		5:
			print_cmd("matched")
""")
    assert len(program.statements) == 1

def test_mat_is_parsed_inside_process():
    program = parse("""\
process(delta):
	v x int = 5
	mat x:
		5:
			print_cmd("matched")
""")
    assert len(program.statements) == 1

def test_mat_duplicate_int_case():
    with pytest.raises(ResirisSyntaxError, match="SameCaseMultiCall"):
        parse("""\
v x int = 1
mat x:
\t1:
\t\tpass
\t1:
\t\tpass
""")


def test_mat_duplicate_string_case():
    with pytest.raises(ResirisSyntaxError, match="SameCaseMultiCall"):
        parse("""\
v x string = "x"
mat x:
\t"x":
\t\tpass
\t"x":
\t\tpass
""")


def test_mat_duplicate_bool_case():
    with pytest.raises(ResirisSyntaxError, match="SameCaseMultiCall"):
        parse("""\
v x bool = true
mat x:
\ttrue:
\t\tpass
\ttrue:
\t\tpass
""")


def test_mat_mixed_int_and_string_cases_rejected():
    with pytest.raises(ResirisSyntaxError):
        parse("""\
v x int = 1
mat x:
\t1:
\t\tpass
\t"1":
\t\tpass
""")


def test_mat_mixed_int_and_bool_cases_rejected():
    with pytest.raises(ResirisSyntaxError):
        parse("""\
v x int = 1
mat x:
\t1:
\t\tpass
\ttrue:
\t\tpass
""")


def test_mat_mixed_string_and_bool_cases_rejected():
    with pytest.raises(ResirisSyntaxError):
        parse("""\
v x string = "x"
mat x:
\t"x":
\t\tpass
\ttrue:
\t\tpass
""")


def test_mat_expression_case_is_rejected():
    with pytest.raises(ResirisSyntaxError):
        parse("""\
v x int = 3
mat x:
	1 + 2:
		pass
""")

def test_mat_variable_case_rejected():
    with pytest.raises(ResirisSyntaxError, match="InvalidCaseValue"):
        parse("""\
v x int = 3
v case_value int = 3
mat x:
\tcase_value:
\t\tpass
""")


def test_mat_constant_case_rejected():
    with pytest.raises(ResirisSyntaxError, match="InvalidCaseValue"):
        parse("""\
v x int = 3
c case_value int = 3
mat x:
\tcase_value:
\t\tpass
""")


def test_mat_literal_checked_value_rejected():
    with pytest.raises(ResirisSyntaxError):
        parse("""\
mat 1:
\t1:
\t\tpass
""")


def test_mat_unknown_value_fails_at_runtime():
    with pytest.raises(RuntimeErrorResiris):
        run("""\
mat missing:
\t1:
\t\tpass
""")


def test_mat_unknown_object_first_value_resolves_its_type():
    env = run("""\
v x UnknownObject = 1
mat x:
	1:
		pass
""")
    assert env["x"].value == 1

def test_mat_only_else_rejected():
    with pytest.raises(ResirisSyntaxError, match="EmptyMatchBody"):
        parse("""\
v x int = 1
mat x:
\telse:
\t\tpass
""")


def test_mat_empty_body_is_rejected():
    with pytest.raises(ResirisSyntaxError):
        parse("""\
v x int = 1
mat x:
""")


def test_mat_case_without_body_rejected():
    with pytest.raises(ResirisSyntaxError, match="MissingCaseBody"):
        parse("""\
v x int = 1
mat x:
\t1:
""")


def test_mat_nested_inside_case_rejected():
    with pytest.raises(ResirisSyntaxError, match="NestedMatchError"):
        parse("""\
v x int = 1
mat x:
\t1:
\t\tmat x:
\t\t\t1:
\t\t\t\tpass
""")


# ---------------------------------------------------------------------------
# Else rules
# ---------------------------------------------------------------------------

def test_mat_multiple_else_rejected():
    with pytest.raises(ResirisSyntaxError):
        parse("""\
v x int = 1
mat x:
\t1:
\t\tpass
\telse:
\t\tpass
\telse:
\t\tpass
""")


def test_mat_else_must_be_last():
    with pytest.raises(ResirisSyntaxError):
        parse("""\
v x int = 1
mat x:
\t1:
\t\tpass
\telse:
\t\tpass
\t2:
\t\tpass
""")


# ---------------------------------------------------------------------------
# Evaluation / execution behavior
# ---------------------------------------------------------------------------

def test_mat_checked_value_is_evaluated_once(capsys):
    run("""\
fn get():
\tprint_cmd("evaluated")
\treturn 2
mat get():
\t2:
\t\tprint_cmd("matched")
""")
    assert capsys.readouterr().out == "evaluated\nmatched\n"


def test_mat_match_error_gets_match_case_execution_error():
    with pytest.raises(RuntimeErrorResiris, match="MatchCaseExecutionError"):
        run("""\
v x int = 1
mat x:
\t1:
\t\tv y int = missing
""")


def test_mat_case_error_stops_case_execution(capsys):
    with pytest.raises(RuntimeErrorResiris, match="MatchCaseExecutionError"):
        run("""\
v x int = 1
mat x:
\t1:
\t\tprint_cmd("before")
\t\tv y int = missing
\t\tprint_cmd("after")
""")
    assert capsys.readouterr().out == "before\n"


def test_mat_no_match_does_not_execute_any_case(capsys):
    run("""\
v x int = 9
mat x:
\t1:
\t\tprint_cmd("one")
\t2:
\t\tprint_cmd("two")
\t3:
\t\tprint_cmd("three")
print_cmd("after")
""")
    assert capsys.readouterr().out == "after\n"


def test_mat_else_only_runs_after_all_cases_fail(capsys):
    run("""\
v x int = 9
mat x:
\t1:
\t\tprint_cmd("one")
\t2:
\t\tprint_cmd("two")
\telse:
\t\tprint_cmd("else")
""")
    assert capsys.readouterr().out == "else\n"


def test_mat_matching_case_does_not_run_else(capsys):
    run("""\
v x int = 1
mat x:
\t1:
\t\tprint_cmd("case")
\telse:
\t\tprint_cmd("else")
""")
    assert capsys.readouterr().out == "case\n"


# ---------------------------------------------------------------------------
# Syntax / indentation coverage
# ---------------------------------------------------------------------------

def test_mat_missing_colon_rejected():
    with pytest.raises(ResirisSyntaxError):
        parse("""\
v x int = 1
mat x
\t1:
\t\tpass
""")


def test_mat_case_missing_colon_rejected():
    with pytest.raises(ResirisSyntaxError):
        parse("""\
v x int = 1
mat x:
\t1
\t\tpass
""")


def test_mat_else_missing_colon_rejected():
    with pytest.raises(ResirisSyntaxError):
        parse("""\
v x int = 1
mat x:
\t1:
\t\tpass
\telse
\t\tpass
""")


def test_mat_case_body_must_be_indented():
    with pytest.raises(ResirisSyntaxError, match="MissingCaseBody"):
        parse("""\
v x int = 1
mat x:
\t1:
print_cmd("outside")
""")


def test_mat_multiple_statements_after_match(capsys):
    run("""\
v x int = 2
mat x:
\t2:
\t\tprint_cmd("matched")
print_cmd("after1")
print_cmd("after2")
""")
    assert capsys.readouterr().out == "matched\nafter1\nafter2\n"


def test_mat_in_nested_if_block(capsys):
    run("""\
v x int = 2
if true:
\tif true:
\t\tmat x:
\t\t\t2:
\t\t\t\tprint_cmd("deep")
""")
    assert capsys.readouterr().out == "deep\n"
