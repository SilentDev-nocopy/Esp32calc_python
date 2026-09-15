from pathlib import Path

import pytest

from resiris.ast_nodes import Include, Program
from resiris.interpreter import Interpreter, RuntimeErrorResiris


def write_module(modules_dir: Path, name: str, body: str | None = None):
    modules_dir.mkdir(parents=True, exist_ok=True)
    if body is None:
        body = f'NAME = "{name}"\nFUNCTIONS = ""\nVARIABLES = ""\n\ndef _INIT_():\n    pass\n'
    (modules_dir / f"{name}.py").write_text(body, encoding="utf-8")


def test_module_is_found_and_loaded(tmp_path):
    modules_dir = tmp_path / "Modules"
    write_module(modules_dir, "RSMath")

    interpreter = Interpreter(modules_dir=modules_dir)
    interpreter.run(Program([Include(["RSMath"])]))

    assert "RSMath" in interpreter.modules


def test_missing_module(tmp_path):
    interpreter = Interpreter(modules_dir=tmp_path / "Modules")

    with pytest.raises(RuntimeErrorResiris, match=r'RSMath not found! Error code:"MissingModule"'):
        interpreter.run(Program([Include(["RSMath"])]))


def test_same_module_multi_call(tmp_path):
    modules_dir = tmp_path / "Modules"
    write_module(modules_dir, "RSMath")

    interpreter = Interpreter(modules_dir=modules_dir)
    program = Program([Include(["RSMath"]), Include(["RSMath"])])

    with pytest.raises(RuntimeErrorResiris, match=r'is already included\. Error code:"SameModuleMultiCall"'):
        interpreter.run(program)


def test_module_init_runs(tmp_path):
    modules_dir = tmp_path / "Modules"
    marker = tmp_path / "init_ran.txt"
    write_module(
        modules_dir,
        "InitTest",
        f'NAME = "InitTest"\nFUNCTIONS = ""\nVARIABLES = ""\n\ndef _INIT_():\n    {marker.as_posix()!r}\n    open({str(marker)!r}, "w").write("ok")\n',
    )

    Interpreter(modules_dir=modules_dir).run(Program([Include(["InitTest"])]))

    assert marker.read_text(encoding="utf-8") == "ok"
