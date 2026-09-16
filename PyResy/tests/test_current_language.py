"""
Resiris – nagy, egyfájlos jelenlegi nyelvi/interpreter tesztcsomag.

Cél:
    Egy helyen ellenőrizni a jelenlegi, már implementált Resiris alapokat.

FONTOS:
    - A Resiris kódblokkokban TAB van, nem space.
    - Ez a fájl nem vezet be új nyelvi szabályt.
    - Csak a jelenlegi implementációban már létező elemeket teszteli.

Futtatás:
    pytest -q tests/test_current_language.py
"""

import pytest

from resiris.ast_nodes import (
    Assignment,
    BinaryExpr,
    Declaration,
    FunctionDef,
    IfStmt,
    Literal,
    MatStmt,
    PassStmt,
    ReturnStmt,
)
from resiris.interpreter import (
    ConstantAssignmentError,
    FunctionError,
    IntDivisionError,
    Interpreter,
    RuntimeErrorResiris,
    ResirisTypeError,
    UnknownVariableError,
)
from resiris.parser import Parser
from resiris.tokenizer import ResirisSyntaxError, TokenType, Tokenizer


# ---------------------------------------------------------------------------
# Segédfüggvények
# ---------------------------------------------------------------------------

def parse(source):
    return Parser(Tokenizer().tokenize(source)).parse()


def run(source, *, interpreter=None):
    interpreter = interpreter or Interpreter()
    return interpreter.run(parse(source))


def run_value(source, name):
    variables = run(source)
    return variables[name].value


# ---------------------------------------------------------------------------
# TOKENIZER
# ---------------------------------------------------------------------------

def test_tokenizer_recognizes_core_keywords_and_types():
    tokens = Tokenizer().tokenize(
        "v x int = 10\n"
        "c y float = 2.5\n"
        "v text string = \"hello\"\n"
        "v flag bool = true\n"
    )
    types = [token.type for token in tokens]

    assert TokenType.V in types
    assert TokenType.C in types
    assert TokenType.TYPE_INT in types
    assert TokenType.TYPE_FLOAT in types
    assert TokenType.TYPE_STRING in types
    assert TokenType.TYPE_BOOL in types
    assert TokenType.TRUE in types


def test_tokenizer_recognizes_assignment_and_comparison_operators():
    tokens = Tokenizer().tokenize(
        "v x int = 1\n"
        "x += 1\n"
        "x -= 1\n"
        "x *= 2\n"
        "x /= 2\n"
        "v a bool = x == 1\n"
        "v b bool = x != 1\n"
        "v gt bool = x > 1\n"
        "v d bool = x < 1\n"
        "v e bool = x >= 1\n"
        "v f bool = x <= 1\n"
    )
    token_values = [token.value for token in tokens]

    for operator in ["=", "+=", "-=", "*=", "/=", "==", "!=", ">", "<", ">=", "<="]:
        assert operator in token_values


def test_tokenizer_supports_comments():
    tokens = Tokenizer().tokenize(
        "## teljes soros komment\n"
        "v x int = 10 ## sorvégi komment\n"
    )

    assert any(token.type is TokenType.IDENTIFIER and token.value == "x" for token in tokens)
    assert all(token.value != "##" for token in tokens)


def test_tokenizer_supports_single_and_double_quoted_strings():
    tokens = Tokenizer().tokenize(
        "v a string = 'hello'\n"
        "v b string = \"world\"\n"
    )
    strings = [token.value for token in tokens if token.type is TokenType.STRING]

    assert strings == ["hello", "world"]


def test_tokenizer_supports_string_escapes():
    tokens = Tokenizer().tokenize(
        r'v x string = "a\nb\tc\\d\"e"' + "\n"
    )
    string_token = next(token for token in tokens if token.type is TokenType.STRING)

    assert string_token.value == 'a\nb\tc\\d"e'


def test_tokenizer_rejects_spaces_as_indentation():
    with pytest.raises(ResirisSyntaxError, match="spaces cannot be used for indentation"):
        Tokenizer().tokenize(
            "if true:\n"
            "    pass\n"
        )


def test_tokenizer_rejects_unterminated_string():
    with pytest.raises(ResirisSyntaxError, match="unterminated string"):
        Tokenizer().tokenize('v x string = "hello\n')


def test_tokenizer_rejects_bad_decimal():
    with pytest.raises(ResirisSyntaxError, match="digit is required after the decimal point"):
        Tokenizer().tokenize("v x float = 10.\n")


# ---------------------------------------------------------------------------
# PARSER / AST
# ---------------------------------------------------------------------------

def test_parser_builds_declarations():
    tree = parse(
        "v x int = 10\n"
        "c y float = 2.5\n"
        "v text string = \"ok\"\n"
        "v flag bool = true\n"
    )

    assert len(tree.statements) == 4
    assert isinstance(tree.statements[0], Declaration)
    assert tree.statements[0].kind == "v"
    assert tree.statements[0].name == "x"
    assert tree.statements[0].type_name == "int"
    assert isinstance(tree.statements[1], Declaration)
    assert tree.statements[1].kind == "c"
    assert tree.statements[1].type_name == "float"


def test_parser_builds_assignment():
    tree = parse(
        "v x int = 10\n"
        "x += 5\n"
    )

    statement = tree.statements[1]
    assert isinstance(statement, Assignment)
    assert statement.target == "x"
    assert statement.operator == "+="


def test_parser_builds_if_elif_else():
    tree = parse(
        "v x int = 2\n"
        "if x == 1:\n"
        "\tpass\n"
        "elif x == 2:\n"
        "\tpass\n"
        "else:\n"
        "\tpass\n"
    )

    statement = tree.statements[1]
    assert isinstance(statement, IfStmt)
    assert len(statement.elif_blocks) == 1
    assert statement.else_body is not None


def test_parser_builds_function():
    tree = parse(
        "fn add(a, b):\n"
        "\treturn a + b\n"
    )

    function = tree.statements[0]
    assert isinstance(function, FunctionDef)
    assert function.name == "add"
    assert function.parameters == ["a", "b"]
    assert isinstance(function.body[0], ReturnStmt)


def test_parser_builds_start_lifecycle():
    from resiris.ast_nodes import LifecycleDef

    tree = parse(
        "START():\n"
        "\tpass\n"
    )

    lifecycle = tree.statements[0]
    assert isinstance(lifecycle, LifecycleDef)
    assert lifecycle.name == "START"
    assert lifecycle.parameter_name is None


def test_parser_builds_process_lifecycle_with_fps():
    from resiris.ast_nodes import LifecycleDef

    tree = parse(
        "PROCESS(FPS):\n"
        "\tprint_cmd(FPS)\n"
    )

    lifecycle = tree.statements[0]
    assert isinstance(lifecycle, LifecycleDef)
    assert lifecycle.name == "PROCESS"
    assert lifecycle.parameter_name == "FPS"


def test_process_requires_fps_parameter_name():
    with pytest.raises(ResirisSyntaxError):
        parse(
            "PROCESS(delta):\n"
            "\tpass\n"
        )


def test_start_runs_once():
    source = (
        "v count int = 0\n"
        "START():\n"
        "\tcount += 1\n"
    )
    interpreter = Interpreter()
    interpreter.run(parse(source))
    assert interpreter.variables["count"].value == 1


def test_process_receives_global_fps_as_float():
    source = (
        "c FPS float = 2.5\n"
        "v seen float = 0.0\n"
        "PROCESS(FPS):\n"
        "\tseen = FPS\n"
    )
    interpreter = Interpreter()
    interpreter.run(parse(source))
    interpreter.run_process_frames(1)
    assert interpreter.variables["seen"].value == 2.5


def test_process_frames_runs_requested_number_of_times():
    source = (
        "c FPS float = 10.0\n"
        "v count int = 0\n"
        "PROCESS(FPS):\n"
        "\tcount += 1\n"
    )
    interpreter = Interpreter()
    interpreter.run(parse(source))
    interpreter.run_process_frames(3)
    assert interpreter.variables["count"].value == 3


def test_duplicate_start_is_rejected():
    source = (
        "START():\n"
        "\tpass\n"
        "START():\n"
        "\tpass\n"
    )
    with pytest.raises(FunctionError, match="START: the lifecycle already exists"):
        Interpreter().run(parse(source))


def test_duplicate_process_is_rejected():
    source = (
        "c FPS float = 30.0\n"
        "PROCESS(FPS):\n"
        "\tpass\n"
        "PROCESS(FPS):\n"
        "\tpass\n"
    )
    with pytest.raises(FunctionError, match="PROCESS: the lifecycle already exists"):
        Interpreter().run(parse(source))


def test_start_and_process_can_coexist():
    source = (
        "c FPS float = 30.0\n"
        "START():\n"
        "\tpass\n"
        "PROCESS(FPS):\n"
        "\tpass\n"
    )
    interpreter = Interpreter()
    interpreter.run(parse(source))
    assert interpreter.start_lifecycle is not None
    assert interpreter.process_lifecycle is not None


def test_process_requires_global_float_fps_constant():
    with pytest.raises(RuntimeErrorResiris):
        interpreter = Interpreter()
        interpreter.run(parse(
            "v FPS float = 30.0\n"
            "PROCESS(FPS):\n"
            "\tpass\n"
        ))
        interpreter.run_process_frames(1)


def test_parser_builds_mat():
    tree = parse(
        "v x int = 2\n"
        "mat x:\n"
        "\t1:\n"
        "\t\tpass\n"
        "\t2:\n"
        "\t\tpass\n"
        "\telse:\n"
        "\t\tpass\n"
    )

    statement = tree.statements[1]
    assert isinstance(statement, MatStmt)
    assert len(statement.cases) == 2
    assert statement.else_body is not None


def test_parser_rejects_missing_declaration_type():
    with pytest.raises(ResirisSyntaxError):
        parse("v x = 10\n")


def test_parser_rejects_missing_block_indentation():
    with pytest.raises(ResirisSyntaxError):
        parse(
            "if true:\n"
            "v x int = 1\n"
        )


def test_parser_rejects_invalid_assignment_target():
    with pytest.raises(ResirisSyntaxError):
        parse(
            "1 = 2\n"
        )


# ---------------------------------------------------------------------------
# DECLARATIONS / TÍPUSOK
# ---------------------------------------------------------------------------

def test_int_declaration():
    variables = run("v x int = 10\n")
    assert variables["x"].value == 10
    assert variables["x"].type_name == "int"
    assert variables["x"].is_constant is False


def test_float_declaration():
    variables = run("v x float = 2.5\n")
    assert variables["x"].value == 2.5
    assert variables["x"].type_name == "float"


def test_string_declaration():
    variables = run('v x string = "hello"\n')
    assert variables["x"].value == "hello"
    assert variables["x"].type_name == "string"


def test_bool_declaration():
    variables = run("v a bool = true\n" "v b bool = false\n")
    assert variables["a"].value is True
    assert variables["b"].value is False


def test_unknown_object_infers_int():
    variables = run("v x UnknownObject = 10\n")
    assert variables["x"].value == 10
    assert variables["x"].type_name == "int"


def test_unknown_object_infers_float():
    variables = run("v x UnknownObject = 2.5\n")
    assert variables["x"].value == 2.5
    assert variables["x"].type_name == "float"


def test_unknown_object_infers_string():
    variables = run('v x UnknownObject = "hello"\n')
    assert variables["x"].value == "hello"
    assert variables["x"].type_name == "string"


def test_unknown_object_infers_bool():
    variables = run("v x UnknownObject = true\n")
    assert variables["x"].value is True
    assert variables["x"].type_name == "bool"


def test_unknown_object_requires_first_value():
    from resiris.interpreter import MissingValueError

    with pytest.raises(MissingValueError):
        run("v x UnknownObject\n")


def test_typed_declaration_requires_value():
    from resiris.interpreter import MissingValueError

    with pytest.raises(MissingValueError):
        run("v x int\n")


def test_duplicate_name_in_same_scope_is_rejected():
    with pytest.raises(RuntimeErrorResiris, match="already in use"):
        run(
            "v x int = 1\n"
            "v x int = 2\n"
        )


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

def test_constant_can_be_declared():
    variables = run("c x int = 10\n")
    assert variables["x"].value == 10
    assert variables["x"].is_constant is True


def test_constant_cannot_be_assigned():
    with pytest.raises(ConstantAssignmentError):
        run(
            "c x int = 10\n"
            "x = 20\n"
        )


def test_constant_cannot_use_compound_assignment():
    with pytest.raises(ConstantAssignmentError):
        run(
            "c x int = 10\n"
            "x += 1\n"
        )


# ---------------------------------------------------------------------------
# ARITMETIKA / KIFEJEZÉSEK
# ---------------------------------------------------------------------------

def test_arithmetic_operators():
    variables = run(
        "v a int = 10 + 2\n"
        "v b int = 10 - 2\n"
        "v product int = 10 * 2\n"
        "v d float = 10.0 / 2\n"
        "v e int = 10 % 3\n"
    )

    assert variables["a"].value == 12
    assert variables["b"].value == 8
    assert variables["product"].value == 20
    assert variables["d"].value == 5.0
    assert variables["e"].value == 1


def test_operator_precedence():
    assert run_value("v x int = 2 + 3 * 4\n", "x") == 14


def test_parentheses_override_precedence():
    assert run_value("v x int = (2 + 3) * 4\n", "x") == 20


def test_unary_plus_and_minus():
    variables = run(
        "v a int = -10\n"
        "v b int = +10\n"
    )
    assert variables["a"].value == -10
    assert variables["b"].value == 10


def test_comparison_operators_produce_bool():
    variables = run(
        "v a bool = 2 == 2\n"
        "v b bool = 2 != 3\n"
        "v gt bool = 3 > 2\n"
        "v d bool = 2 < 3\n"
        "v e bool = 3 >= 3\n"
        "v f bool = 2 <= 3\n"
    )

    assert variables["a"].value is True
    assert variables["b"].value is True
    assert variables["gt"].value is True
    assert variables["d"].value is True
    assert variables["e"].value is True
    assert variables["f"].value is True


def test_compound_assignments():
    variables = run(
        "v x float = 10.0\n"
        "x += 5\n"
        "x -= 3\n"
        "x *= 2\n"
        "x /= 4\n"
    )
    assert variables["x"].value == 6.0


def test_unknown_variable_is_rejected():
    with pytest.raises(UnknownVariableError):
        run("v x int = missing + 1\n")


# ---------------------------------------------------------------------------
# TYPE VALIDÁCIÓ
# ---------------------------------------------------------------------------

def test_int_accepts_int_result():
    assert run_value("v x int = 5 + 6\n", "x") == 11


def test_float_accepts_int_result_by_coercion():
    variables = run("v x float = 5 + 6\n")
    assert variables["x"].value == 11.0
    assert variables["x"].type_name == "float"


def test_int_division_raises_int_division_error():
    with pytest.raises(IntDivisionError, match=r'Cant division with int type! Must use float! Error code:"IntDivisionError"'):
        run("v x int = 5 / 2\n")


def test_bool_requires_bool_result():
    with pytest.raises(ResirisTypeError):
        run("v x bool = 1\n")


def test_string_requires_string_result():
    with pytest.raises(ResirisTypeError):
        run("v x string = 1\n")


# ---------------------------------------------------------------------------
# IF / ELIF / ELSE
# ---------------------------------------------------------------------------

def test_if_true_branch_executes():
    variables = run(
        "v x int = 0\n"
        "if true:\n"
        "\tx = 10\n"
        "else:\n"
        "\tx = 20\n"
    )
    assert variables["x"].value == 10


def test_if_false_branch_skips_to_else():
    variables = run(
        "v x int = 0\n"
        "if false:\n"
        "\tx = 10\n"
        "else:\n"
        "\tx = 20\n"
    )
    assert variables["x"].value == 20


def test_elif_branch_executes_when_if_is_false():
    variables = run(
        "v x int = 2\n"
        "v result int = 0\n"
        "if x == 1:\n"
        "\tresult = 10\n"
        "elif x == 2:\n"
        "\tresult = 20\n"
        "else:\n"
        "\tresult = 30\n"
    )
    assert variables["result"].value == 20


def test_only_first_matching_if_elif_branch_runs():
    variables = run(
        "v result int = 0\n"
        "if true:\n"
        "\tresult = 1\n"
        "elif true:\n"
        "\tresult = 2\n"
        "else:\n"
        "\tresult = 3\n"
    )
    assert variables["result"].value == 1


def test_if_requires_bool_condition():
    with pytest.raises(ResirisTypeError):
        run(
            "if 1:\n"
            "\tpass\n"
        )


def test_elif_requires_bool_condition():
    with pytest.raises(ResirisTypeError):
        run(
            "if false:\n"
            "\tpass\n"
            "elif 1:\n"
            "\tpass\n"
        )


# ---------------------------------------------------------------------------
# FUNCTION / SCOPE / RETURN
# ---------------------------------------------------------------------------

def test_function_returns_value():
    variables = run(
        "fn add(a, b):\n"
        "\treturn a + b\n"
        "v result int = add(2, 3)\n"
    )
    assert variables["result"].value == 5


def test_function_can_read_global_v():
    variables = run(
        "v x int = 10\n"
        "fn get():\n"
        "\treturn x\n"
        "v result int = get()\n"
    )
    assert variables["result"].value == 10


def test_function_local_parameter_does_not_become_global():
    interpreter = Interpreter()
    run(
        "fn identity(x):\n"
        "\treturn x\n"
        "v result int = identity(7)\n",
        interpreter=interpreter,
    )
    assert "x" not in interpreter.variables
    assert interpreter.variables["result"].value == 7


def test_function_local_declaration_does_not_become_global():
    interpreter = Interpreter()
    run(
        "fn make():\n"
        "\tv local int = 7\n"
        "\treturn local\n"
        "v result int = make()\n",
        interpreter=interpreter,
    )
    assert "local" not in interpreter.variables
    assert interpreter.variables["result"].value == 7


def test_function_return_exits_function_immediately():
    variables = run(
        "fn test():\n"
        "\treturn 10\n"
        "\tpass\n"
        "v result int = test()\n"
    )
    assert variables["result"].value == 10


def test_return_outside_function_is_rejected():
    with pytest.raises(FunctionError):
        run("return 10\n")


def test_unknown_function_is_rejected():
    with pytest.raises(FunctionError):
        run("v result int = missing(1)\n")


def test_function_argument_count_is_checked():
    with pytest.raises(FunctionError):
        run(
            "fn add(a, b):\n"
            "\treturn a + b\n"
            "v result int = add(1)\n"
        )


def test_function_can_be_called_before_its_definition():
    variables = run(
        "v result int = add(2, 3)\n"
        "fn add(a, b):\n"
        "\treturn a + b\n"
    )
    assert variables["result"].value == 5


def test_function_cannot_have_same_name_as_variable():
    with pytest.raises(FunctionError):
        run(
            "v add int = 1\n"
            "fn add():\n"
            "\tpass\n"
        )


def test_duplicate_function_name_is_rejected():
    with pytest.raises(FunctionError):
        run(
            "fn test():\n"
            "\tpass\n"
            "fn test():\n"
            "\tpass\n"
        )


# ---------------------------------------------------------------------------
# PASS
# ---------------------------------------------------------------------------

def test_pass_is_a_noop_and_execution_continues():
    variables = run(
        "v x int = 0\n"
        "pass\n"
        "x = 10\n"
    )
    assert variables["x"].value == 10


def test_pass_inside_if_does_not_stop_following_statements():
    variables = run(
        "v x int = 0\n"
        "if true:\n"
        "\tpass\n"
        "\tx = 10\n"
    )
    assert variables["x"].value == 10


def test_pass_inside_mat_case_does_not_stop_following_statements():
    variables = run(
        "v x int = 1\n"
        "v result int = 0\n"
        "mat x:\n"
        "\t1:\n"
        "\t\tpass\n"
        "\t\tresult = 10\n"
    )
    assert variables["result"].value == 10


# ---------------------------------------------------------------------------
# type()
# ---------------------------------------------------------------------------

def test_type_query_returns_type_name():
    variables = run(
        "v x int = 10\n"
        "v type_name string = x.type()\n"
    )
    assert variables["type_name"].value == "int"


def test_type_int_to_float():
    variables = run(
        "v x int = 10\n"
        "v y float = x.type(float)\n"
    )
    assert variables["x"].value == 10
    assert variables["x"].type_name == "int"
    assert variables["y"].value == 10.0


def test_type_float_to_int_uses_half_up_rounding():
    variables = run(
        "v a float = 0.4\n"
        "v b float = 0.5\n"
        "v cval float = 1.4\n"
        "v d float = 1.5\n"
        "v aa int = a.type(int)\n"
        "v bb int = b.type(int)\n"
        "v cc int = cval.type(int)\n"
        "v dd int = d.type(int)\n"
    )
    assert variables["aa"].value == 0
    assert variables["bb"].value == 1
    assert variables["cc"].value == 1
    assert variables["dd"].value == 2


def test_type_numeric_to_string():
    variables = run(
        "v a int = 10\n"
        "v b float = 2.5\n"
        "v aa string = a.type(string)\n"
        "v bb string = b.type(string)\n"
    )
    assert variables["aa"].value == "10"
    assert variables["bb"].value == "2.5"


def test_type_bool_conversions():
    variables = run(
        "v a bool = true\n"
        "v b bool = false\n"
        "v ai int = a.type(int)\n"
        "v bi int = b.type(int)\n"
        "v af float = a.type(float)\n"
        "v bf float = b.type(float)\n"
        "v ass string = a.type(string)\n"
        "v bss string = b.type(string)\n"
    )
    assert variables["ai"].value == 1
    assert variables["bi"].value == 0
    assert variables["af"].value == 1.0
    assert variables["bf"].value == 0.0
    assert variables["ass"].value == "true"
    assert variables["bss"].value == "false"


def test_type_string_to_numeric_is_rejected():
    with pytest.raises(RuntimeErrorResiris, match="ConversionFail"):
        run(
            'v x string = "10"\n'
            "v y int = x.type(int)\n"
        )


def test_type_string_to_bool_is_rejected():
    with pytest.raises(RuntimeErrorResiris, match="ConversionFail"):
        run(
            'v x string = "true"\n'
            "v y bool = x.type(bool)\n"
        )


def test_type_invalid_target_is_rejected():
    with pytest.raises(Exception):
        run(
            "v x int = 10\n"
            "v y int = x.type(UnknownObject)\n"
        )


def test_type_too_many_arguments_is_rejected():
    with pytest.raises(Exception):
        run(
            "v x int = 10\n"
            "v y int = x.type(float, int)\n"
        )


def test_type_can_be_used_on_constant():
    variables = run(
        "c x int = 10\n"
        "v y float = x.type(float)\n"
    )
    assert variables["x"].value == 10
    assert variables["y"].value == 10.0


# ---------------------------------------------------------------------------
# str() / .string()
# ---------------------------------------------------------------------------

def test_str_converts_value_to_string():
    variables = run(
        "v x int = 10\n"
        "v text string = str(x)\n"
    )
    assert variables["text"].value == "10"


def test_str_requires_exactly_one_argument():
    with pytest.raises(FunctionError):
        run("v text string = str()\n")

    with pytest.raises(FunctionError):
        run(
            "v text string = str(1, 2)\n"
        )


def test_string_method_converts_value_to_string():
    variables = run(
        "v x int = 10\n"
        "v text string = x.string()\n"
    )
    assert variables["text"].value == "10"


# ---------------------------------------------------------------------------
# print_cmd()
# ---------------------------------------------------------------------------

def test_print_cmd_prints_evaluated_value(capsys):
    run(
        "v x int = 42\n"
        "print_cmd(x)\n"
    )
    assert capsys.readouterr().out == "42\n"


def test_print_cmd_can_print_string(capsys):
    run('print_cmd("hello")\n')
    assert capsys.readouterr().out == "hello\n"


# ---------------------------------------------------------------------------
# mat
# ---------------------------------------------------------------------------

def test_mat_matches_case(capsys):
    run(
        "v x int = 2\n"
        "mat x:\n"
        "\t1:\n"
        "\t\tprint_cmd(\"one\")\n"
        "\t2:\n"
        "\t\tprint_cmd(\"two\")\n"
    )
    assert capsys.readouterr().out == "two\n"


def test_mat_match_and_continue_after_mat(capsys):
    run(
        "v x int = 2\n"
        "mat x:\n"
        "\t1:\n"
        "\t\tprint_cmd(\"one\")\n"
        "\t2:\n"
        "\t\tprint_cmd(\"two\")\n"
        "print_cmd(\"after\")\n"
    )
    assert capsys.readouterr().out == "two\nafter\n"


def test_mat_has_no_fallthrough(capsys):
    run(
        "v x int = 1\n"
        "mat x:\n"
        "\t1:\n"
        "\t\tprint_cmd(\"one\")\n"
        "\t2:\n"
        "\t\tprint_cmd(\"two\")\n"
    )
    assert capsys.readouterr().out == "one\n"


def test_mat_else_runs_when_no_case_matches(capsys):
    run(
        "v x int = 3\n"
        "mat x:\n"
        "\t1:\n"
        "\t\tprint_cmd(\"one\")\n"
        "\t2:\n"
        "\t\tprint_cmd(\"two\")\n"
        "\telse:\n"
        "\t\tprint_cmd(\"other\")\n"
    )
    assert capsys.readouterr().out == "other\n"


def test_mat_without_match_and_without_else_continues(capsys):
    run(
        "v x int = 3\n"
        "mat x:\n"
        "\t1:\n"
        "\t\tprint_cmd(\"one\")\n"
        "print_cmd(\"after\")\n"
    )
    assert capsys.readouterr().out == "after\n"


def test_mat_skips_wrong_case_type_and_can_use_else(capsys):
    run(
        "v x float = 2.0\n"
        "mat x:\n"
        "\t1:\n"
        "\t\tprint_cmd(\"int\")\n"
        "\telse:\n"
        "\t\tprint_cmd(\"float\")\n"
    )
    assert capsys.readouterr().out == "float\n"


def test_mat_type_case(capsys):
    run(
        "v x int = 10\n"
        "mat x.type():\n"
        "\tint:\n"
        "\t\tprint_cmd(\"int\")\n"
        "\tfloat:\n"
        "\t\tprint_cmd(\"float\")\n"
    )
    assert capsys.readouterr().out == "int\n"


def test_mat_string_result(capsys):
    run(
        "v x int = 10\n"
        "mat x.string():\n"
        "\t\"10\":\n"
        "\t\tprint_cmd(\"string\")\n"
    )
    assert capsys.readouterr().out == "string\n"


def test_mat_duplicate_case_is_rejected():
    with pytest.raises(ResirisSyntaxError, match="SameCaseMultiCall"):
        parse(
            "v x int = 1\n"
            "mat x:\n"
            "\t1:\n"
            "\t\tpass\n"
            "\t1:\n"
            "\t\tpass\n"
        )


def test_mat_mixed_case_types_are_rejected():
    with pytest.raises(ResirisSyntaxError):
        parse(
            "v x int = 1\n"
            "mat x:\n"
            "\t1:\n"
            "\t\tpass\n"
            "\t\"1\":\n"
            "\t\tpass\n"
        )


def test_mat_nested_mat_is_rejected():
    with pytest.raises(ResirisSyntaxError, match="NestedMatchError"):
        parse(
            "v x int = 1\n"
            "mat x:\n"
            "\t1:\n"
            "\t\tmat x:\n"
            "\t\t\t1:\n"
            "\t\t\t\tpass\n"
        )


def test_mat_literal_as_checked_value_is_rejected():
    with pytest.raises(ResirisSyntaxError):
        parse(
            "mat 1:\n"
            "\t1:\n"
            "\t\tpass\n"
        )


def test_mat_missing_checked_value_is_runtime_error():
    with pytest.raises(RuntimeErrorResiris):
        run(
            "mat missing:\n"
            "\t1:\n"
            "\t\tpass\n"
        )


def test_mat_case_runtime_error_is_wrapped():
    with pytest.raises(RuntimeErrorResiris, match="MatchCaseExecutionError"):
        run(
            "v x int = 1\n"
            "mat x:\n"
            "\t1:\n"
            "\t\tmissing = 10\n"
        )


def test_mat_return_exits_function():
    variables = run(
        "v x int = 1\n"
        "fn test():\n"
        "\tmat x:\n"
        "\t\t1:\n"
        "\t\t\treturn 42\n"
        "v result int = test()\n"
    )
    assert variables["result"].value == 42


def test_mat_checked_value_is_evaluated_once():
    variables = run(
        "v x int = 1\n"
        "fn get():\n"
        "\tx += 1\n"
        "\treturn x\n"
        "mat get():\n"
        "\t2:\n"
        "\t\tpass\n"
    )
    assert variables["x"].value == 2


def test_mat_else_must_be_last():
    with pytest.raises(ResirisSyntaxError):
        parse(
            "v x int = 1\n"
            "mat x:\n"
            "\telse:\n"
            "\t\tpass\n"
            "\t1:\n"
            "\t\tpass\n"
        )



def test_mat_requires_at_least_one_case():
    with pytest.raises(ResirisSyntaxError, match="EmptyMatchBody"):
        parse(
            "v x int = 1\n"
            "mat x:\n"
            "\telse:\n"
            "\t\tpass\n"
        )


# ---------------------------------------------------------------------------
# KOMBINÁLT / REGRESSZIÓS TESZTEK
# ---------------------------------------------------------------------------

def test_function_if_return_and_type_work_together():
    variables = run(
        "fn calculate(x):\n"
        "\tif x > 10:\n"
        "\t\treturn x.type(float)\n"
        "\telse:\n"
        "\t\treturn 0.0\n"
        "v result float = calculate(20)\n"
    )
    assert variables["result"].value == 20.0


def test_function_mat_and_return_work_together():
    variables = run(
        "fn choose(x):\n"
        "\tmat x:\n"
        "\t\t1:\n"
        "\t\t\treturn 100\n"
        "\t\t2:\n"
        "\t\t\treturn 200\n"
        "v result int = choose(2)\n"
    )
    assert variables["result"].value == 200


def test_global_state_can_be_read_and_modified_from_function():
    variables = run(
        "v x int = 10\n"
        "fn increment():\n"
        "\tx += 1\n"
        "increment()\n"
    )
    assert variables["x"].value == 11


def test_nested_if_inside_function():
    variables = run(
        "fn test(x):\n"
        "\tif x > 0:\n"
        "\t\tif x > 10:\n"
        "\t\t\treturn 2\n"
        "\t\telse:\n"
        "\t\t\treturn 1\n"
        "\telse:\n"
        "\t\treturn 0\n"
        "v a int = test(20)\n"
        "v b int = test(5)\n"
        "v result_c int = test(-1)\n"
    )
    assert variables["a"].value == 2
    assert variables["b"].value == 1
    assert variables["result_c"].value == 0


def test_multiple_program_runs_do_not_share_default_interpreters():
    first = run("v x int = 1\n")
    second = run("v x int = 2\n")

    assert first["x"].value == 1
    assert second["x"].value == 2


# ---------------------------------------------------------------------------
# Egyszerű metateszt: a nagy tesztfájl ténylegesen futtatható pytestből.
# ---------------------------------------------------------------------------

def test_imported_ast_classes_are_real_current_ast_nodes():
    tree = parse(
        "v x int = 1\n"
        "x = x + 1\n"
        "if true:\n"
        "\tpass\n"
    )

    assert isinstance(tree.statements[0], Declaration)
    assert isinstance(tree.statements[1], Assignment)
    assert isinstance(tree.statements[2], IfStmt)
    assert isinstance(tree.statements[2].body[0], PassStmt)
    assert isinstance(tree.statements[1].value, BinaryExpr)
    assert isinstance(tree.statements[1].value.right, Literal)
