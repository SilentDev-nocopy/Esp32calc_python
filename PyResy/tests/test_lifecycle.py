import pytest

from resiris.ast_nodes import LifecycleDef
from resiris.interpreter import Interpreter, TypeErrorResiris, UnknownVariableError
from resiris.parser import Parser
from resiris.tokenizer import ResirisSyntaxError, TokenType, Tokenizer


def parse(source):
    return Parser(Tokenizer().tokenize(source)).parse()


def test_tokenizer_recognizes_uppercase_lifecycle_tokens():
    tokens = Tokenizer().tokenize("START():\n\tpass\nPROCESS(FPS):\n\tpass\n")
    types = [token.type for token in tokens]

    assert TokenType.START in types
    assert TokenType.PROCESS in types


def test_lifecycle_is_case_sensitive():
    with pytest.raises(ResirisSyntaxError):
        parse("start():\n\tpass\n")

    with pytest.raises(ResirisSyntaxError):
        parse("process(FPS):\n\tpass\n")


def test_start_and_process_have_current_lifecycle_shapes():
    program = parse(
        "START():\n"
        "\tpass\n"
        "PROCESS(FPS):\n"
        "\tpass\n"
    )

    start, process = program.statements
    assert isinstance(start, LifecycleDef)
    assert start.name == "START"
    assert start.parameters == []
    assert isinstance(process, LifecycleDef)
    assert process.name == "PROCESS"
    assert process.parameters == [("FPS", "float")]


def test_start_runs_once_before_process_frames(capsys):
    interpreter = Interpreter()
    program = parse(
        "c FPS float = 2.0\n"
        "START():\n"
        "\tprint_cmd(\"start\")\n"
        "PROCESS(FPS):\n"
        "\tprint_cmd(FPS)\n"
    )

    interpreter.run(program, process_frames=3, sleep_fn=lambda _: None)

    assert capsys.readouterr().out.splitlines() == ["start", "2.0", "2.0", "2.0"]


def test_process_receives_fps_as_float(capsys):
    interpreter = Interpreter()
    program = parse(
        "c FPS float = 30.0\n"
        "PROCESS(FPS):\n"
        "\tprint_cmd(FPS.type())\n"
    )

    interpreter.run(program, process_frames=1, sleep_fn=lambda _: None)

    assert capsys.readouterr().out == "float\n"


def test_process_waits_one_fps_period_between_frames():
    delays = []
    interpreter = Interpreter()
    program = parse(
        "c FPS float = 4.0\n"
        "PROCESS(FPS):\n"
        "\tpass\n"
    )

    interpreter.run(program, process_frames=3, sleep_fn=delays.append)

    assert delays == [0.25, 0.25]


def test_process_requires_global_float_constant_fps():
    interpreter = Interpreter()
    program = parse(
        "v FPS float = 30.0\n"
        "PROCESS(FPS):\n"
        "\tpass\n"
    )

    with pytest.raises(TypeErrorResiris, match="global constant"):
        interpreter.run(program, process_frames=1, sleep_fn=lambda _: None)


def test_process_requires_float_fps():
    interpreter = Interpreter()
    program = parse(
        "c FPS int = 30\n"
        "PROCESS(FPS):\n"
        "\tpass\n"
    )

    with pytest.raises(TypeErrorResiris, match="float"):
        interpreter.run(program, process_frames=1, sleep_fn=lambda _: None)


def test_process_requires_positive_fps():
    interpreter = Interpreter()
    program = parse(
        "c FPS float = 0.0\n"
        "PROCESS(FPS):\n"
        "\tpass\n"
    )

    with pytest.raises(TypeErrorResiris, match="greater than 0"):
        interpreter.run(program, process_frames=1, sleep_fn=lambda _: None)


def test_process_requires_fps_constant_to_exist():
    interpreter = Interpreter()
    program = parse(
        "PROCESS(FPS):\n"
        "\tpass\n"
    )

    with pytest.raises(UnknownVariableError, match="FPS"):
        interpreter.run(program, process_frames=1, sleep_fn=lambda _: None)


def test_start_does_not_accept_parameters():
    with pytest.raises(ResirisSyntaxError):
        parse("START(FPS):\n\tpass\n")


def test_process_requires_fps_parameter():
    with pytest.raises(ResirisSyntaxError):
        parse("PROCESS():\n\tpass\n")


def test_process_parameter_must_be_named_fps():
    with pytest.raises(ResirisSyntaxError):
        parse("PROCESS(delta):\n\tpass\n")
