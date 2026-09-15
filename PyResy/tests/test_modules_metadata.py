from pathlib import Path

import pytest

from resiris.ast_nodes import Include, Program
from resiris.interpreter import Interpreter, RuntimeErrorResiris


def write_module(modules_dir: Path, name: str, body: str):
    modules_dir.mkdir(parents=True, exist_ok=True)
    (modules_dir / f"{name}.py").write_text(body, encoding="utf-8")


def test_module_metadata_is_posted(tmp_path):
    modules_dir = tmp_path / "Modules"
    write_module(
        modules_dir,
        "MetaTest",
        '''NAME = "MetaTest"\nFUNCTIONS = "one,two"\nVARIABLES = "PI:float,FLAG:bool"\n\ndef _INIT_():\n    pass\n''',
    )

    interpreter = Interpreter(modules_dir=modules_dir)
    interpreter.run(Program([Include(["MetaTest"])]))

    info = interpreter.module_loader.info["MetaTest"]
    assert info.name == "MetaTest"
    assert info.functions == "one,two"
    assert info.variables == "PI:float,FLAG:bool"


def test_module_requires_metadata(tmp_path):
    modules_dir = tmp_path / "Modules"
    write_module(
        modules_dir,
        "Broken",
        '''NAME = "Broken"\nFUNCTIONS = "test"\n\ndef _INIT_():\n    pass\n''',
    )

    with pytest.raises(RuntimeErrorResiris, match=r'required constant "VARIABLES" is missing'):
        Interpreter(modules_dir=modules_dir).run(Program([Include(["Broken"])]))


def test_module_metadata_must_be_strings(tmp_path):
    modules_dir = tmp_path / "Modules"
    write_module(
        modules_dir,
        "Broken",
        '''NAME = "Broken"\nFUNCTIONS = 123\nVARIABLES = ""\n\ndef _INIT_():\n    pass\n''',
    )

    with pytest.raises(RuntimeErrorResiris, match=r'"FUNCTIONS" must be a string'):
        Interpreter(modules_dir=modules_dir).run(Program([Include(["Broken"])]))


def test_module_name_must_match_requested_name(tmp_path):
    modules_dir = tmp_path / "Modules"
    write_module(
        modules_dir,
        "RSMath",
        '''NAME = "OtherName"\nFUNCTIONS = "sqrt"\nVARIABLES = ""\n\ndef _INIT_():\n    pass\n''',
    )

    with pytest.raises(RuntimeErrorResiris, match=r'NAME constant must be "RSMath"'):
        Interpreter(modules_dir=modules_dir).run(Program([Include(["RSMath"])]))
