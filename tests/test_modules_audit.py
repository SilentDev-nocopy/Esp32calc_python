from pathlib import Path

import pytest

from resiris.ast_nodes import Include, Program
from resiris.interpreter import Interpreter, RuntimeErrorResiris
from resiris.module_loader import ModuleLoader
from resiris.parser import Parser
from resiris.tokenizer import Tokenizer, ResirisSyntaxError


def parse(source: str):
    return Parser(Tokenizer().tokenize(source)).parse()


def write_module(modules_dir: Path, name: str, body: str | None = None):
    modules_dir.mkdir(parents=True, exist_ok=True)
    if body is None:
        body = (
            f'NAME = "{name}"\n'
            'FUNCTIONS = ""\n'
            'VARIABLES = ""\n\n'
            'def _INIT_():\n'
            '    pass\n'
        )
    (modules_dir / f"{name}.py").write_text(body, encoding="utf-8")


def load_one(tmp_path: Path, name="TestMod", body=None):
    modules = tmp_path / "Modules"
    write_module(modules, name, body)
    interpreter = Interpreter(modules_dir=modules)
    interpreter.run(Program([Include([name])]))
    return interpreter


# ---------------------------------------------------------------------------
# CURRENT parser syntax
# ---------------------------------------------------------------------------

def test_include_requires_angle_brackets():
    with pytest.raises(ResirisSyntaxError):
        parse("include RSMath\n")


def test_include_requires_module_name():
    with pytest.raises(ResirisSyntaxError):
        parse("<include>\n")


def test_include_without_final_newline_is_accepted_by_current_parser():
    program = parse("<include> RSMath")
    assert program.statements[0].modules == ["RSMath"]


def test_single_include_ast():
    program = parse("<include> RSMath\n")
    assert program.statements == [Include(["RSMath"])]


def test_multiple_modules_one_include_ast():
    program = parse("<include> RSMath, Module2\n")
    assert program.statements[0].modules == ["RSMath", "Module2"]


def test_multiple_include_lines_ast():
    program = parse("<include> RSMath\n<include> Module2\n")
    assert program.statements[0].modules == ["RSMath"]
    assert program.statements[1].modules == ["Module2"]


def test_include_module_names_must_be_identifiers():
    with pytest.raises(ResirisSyntaxError):
        parse("<include> 123\n")


def test_include_trailing_comma_is_rejected():
    with pytest.raises(ResirisSyntaxError):
        parse("<include> RSMath,\n")


# ---------------------------------------------------------------------------
# CURRENT module loader
# ---------------------------------------------------------------------------

def test_module_file_is_found_and_loaded(tmp_path):
    interpreter = load_one(tmp_path)
    assert "TestMod" in interpreter.modules


def test_missing_module_has_missing_module_error(tmp_path):
    interpreter = Interpreter(modules_dir=tmp_path / "Modules")
    with pytest.raises(RuntimeErrorResiris, match=r'TestMod not found! Error code:"MissingModule"'):
        interpreter.run(Program([Include(["TestMod"])]))


def test_duplicate_include_has_same_module_error(tmp_path):
    modules = tmp_path / "Modules"
    write_module(modules, "TestMod")
    interpreter = Interpreter(modules_dir=modules)
    with pytest.raises(RuntimeErrorResiris, match=r'Error code:"SameModuleMultiCall"'):
        interpreter.run(Program([Include(["TestMod"]), Include(["TestMod"])]))


def test_duplicate_modules_on_same_include_line_are_rejected(tmp_path):
    modules = tmp_path / "Modules"
    write_module(modules, "TestMod")
    interpreter = Interpreter(modules_dir=modules)
    with pytest.raises(RuntimeErrorResiris, match=r'Error code:"SameModuleMultiCall"'):
        interpreter.run(Program([Include(["TestMod", "TestMod"])]))


def test_two_different_modules_can_be_loaded(tmp_path):
    modules = tmp_path / "Modules"
    write_module(modules, "One")
    write_module(modules, "Two")
    interpreter = Interpreter(modules_dir=modules)
    interpreter.run(Program([Include(["One", "Two"])]))
    assert "One" in interpreter.modules
    assert "Two" in interpreter.modules


def test_module_init_is_required(tmp_path):
    body = 'NAME = "Broken"\nFUNCTIONS = ""\nVARIABLES = ""\n'
    with pytest.raises(RuntimeErrorResiris, match=r'_INIT_ function is required'):
        load_one(tmp_path, "Broken", body)


def test_module_init_runs(tmp_path):
    marker = tmp_path / "init.txt"
    body = (
        'NAME = "InitTest"\n'
        'FUNCTIONS = ""\n'
        'VARIABLES = ""\n\n'
        'def _INIT_():\n'
        f'    open({str(marker)!r}, "w").write("ok")\n'
    )
    load_one(tmp_path, "InitTest", body)
    assert marker.read_text(encoding="utf-8") == "ok"


def test_init_failure_does_not_leave_metadata(tmp_path):
    body = (
        'NAME = "Broken"\n'
        'FUNCTIONS = ""\n'
        'VARIABLES = ""\n\n'
        'def _INIT_():\n'
        '    raise RuntimeError("boom")\n'
    )
    interpreter = Interpreter(modules_dir=tmp_path / "Modules")
    write_module(tmp_path / "Modules", "Broken", body)
    with pytest.raises(RuntimeError):
        interpreter.run(Program([Include(["Broken"])]))
    assert "Broken" not in interpreter.module_loader.info
    assert "Broken" not in interpreter.modules


def test_module_metadata_is_stored(tmp_path):
    body = (
        'NAME = "Meta"\n'
        'FUNCTIONS = "one,two"\n'
        'VARIABLES = "A:int,B:float"\n\n'
        'def _INIT_():\n'
        '    pass\n'
    )
    interpreter = load_one(tmp_path, "Meta", body)
    info = interpreter.module_loader.info["Meta"]
    assert info.name == "Meta"
    assert info.functions == "one,two"
    assert info.variables == "A:int,B:float"


def test_name_metadata_is_required(tmp_path):
    body = 'FUNCTIONS = ""\nVARIABLES = ""\n\ndef _INIT_():\n    pass\n'
    with pytest.raises(RuntimeErrorResiris, match=r'required constant "NAME" is missing'):
        load_one(tmp_path, "Broken", body)


def test_functions_metadata_is_required(tmp_path):
    body = 'NAME = "Broken"\nVARIABLES = ""\n\ndef _INIT_():\n    pass\n'
    with pytest.raises(RuntimeErrorResiris, match=r'required constant "FUNCTIONS" is missing'):
        load_one(tmp_path, "Broken", body)


def test_variables_metadata_is_required(tmp_path):
    body = 'NAME = "Broken"\nFUNCTIONS = ""\n\ndef _INIT_():\n    pass\n'
    with pytest.raises(RuntimeErrorResiris, match=r'required constant "VARIABLES" is missing'):
        load_one(tmp_path, "Broken", body)


@pytest.mark.parametrize("constant_name", ["NAME", "FUNCTIONS", "VARIABLES"])
def test_metadata_constants_must_be_strings(tmp_path, constant_name):
    values = {
        "NAME": '"Broken"',
        "FUNCTIONS": '""',
        "VARIABLES": '""',
    }
    values[constant_name] = "123"
    body = (
        f'NAME = {values["NAME"]}\n'
        f'FUNCTIONS = {values["FUNCTIONS"]}\n'
        f'VARIABLES = {values["VARIABLES"]}\n\n'
        'def _INIT_():\n'
        '    pass\n'
    )
    with pytest.raises(RuntimeErrorResiris, match=rf'"{constant_name}" must be a string'):
        load_one(tmp_path, "Broken", body)


def test_name_metadata_must_match_requested_module(tmp_path):
    body = (
        'NAME = "Other"\n'
        'FUNCTIONS = ""\n'
        'VARIABLES = ""\n\n'
        'def _INIT_():\n'
        '    pass\n'
    )
    with pytest.raises(RuntimeErrorResiris, match=r'NAME constant must be "Requested"'):
        load_one(tmp_path, "Requested", body)


def test_loaded_module_is_registered_after_successful_load(tmp_path):
    interpreter = load_one(tmp_path, "Registered")
    assert interpreter.module_loader.loaded["Registered"] is interpreter.modules["Registered"]


def test_metadata_is_not_posted_when_name_validation_fails(tmp_path):
    body = (
        'NAME = "Other"\n'
        'FUNCTIONS = "f"\n'
        'VARIABLES = "x:int"\n\n'
        'def _INIT_():\n'
        '    pass\n'
    )
    interpreter = Interpreter(modules_dir=tmp_path / "Modules")
    write_module(tmp_path / "Modules", "Requested", body)
    with pytest.raises(RuntimeErrorResiris):
        interpreter.run(Program([Include(["Requested"])]))
    assert "Requested" not in interpreter.module_loader.info
    assert "Requested" not in interpreter.module_loader.loaded


def test_metadata_is_not_posted_when_required_field_is_missing(tmp_path):
    body = (
        'NAME = "Broken"\n'
        'FUNCTIONS = "f"\n\n'
        'def _INIT_():\n'
        '    pass\n'
    )
    interpreter = Interpreter(modules_dir=tmp_path / "Modules")
    write_module(tmp_path / "Modules", "Broken", body)
    with pytest.raises(RuntimeErrorResiris):
        interpreter.run(Program([Include(["Broken"])]))
    assert "Broken" not in interpreter.module_loader.info
    assert "Broken" not in interpreter.module_loader.loaded


def test_module_can_have_empty_functions_metadata(tmp_path):
    interpreter = load_one(tmp_path, "EmptyFns")
    assert interpreter.module_loader.info["EmptyFns"].functions == ""


def test_module_can_have_empty_variables_metadata(tmp_path):
    interpreter = load_one(tmp_path, "EmptyVars")
    assert interpreter.module_loader.info["EmptyVars"].variables == ""


def test_module_metadata_can_contain_comma_separated_function_names(tmp_path):
    body = (
        'NAME = "Fns"\n'
        'FUNCTIONS = "a,b,c"\n'
        'VARIABLES = ""\n\n'
        'def _INIT_():\n'
        '    pass\n'
    )
    interpreter = load_one(tmp_path, "Fns", body)
    assert interpreter.module_loader.info["Fns"].functions == "a,b,c"


def test_module_metadata_can_contain_variable_descriptions(tmp_path):
    body = (
        'NAME = "Vars"\n'
        'FUNCTIONS = ""\n'
        'VARIABLES = "PI:float,FLAG:bool"\n\n'
        'def _INIT_():\n'
        '    pass\n'
    )
    interpreter = load_one(tmp_path, "Vars", body)
    assert interpreter.module_loader.info["Vars"].variables == "PI:float,FLAG:bool"


def test_module_names_can_include_version_suffix(tmp_path):
    interpreter = load_one(tmp_path, "RSMath2")
    assert "RSMath2" in interpreter.modules
    assert interpreter.module_loader.info["RSMath2"].name == "RSMath2"


def test_module_loader_can_be_used_directly(tmp_path):
    modules = tmp_path / "Modules"
    write_module(modules, "Direct")
    loader = ModuleLoader(modules)
    module = loader.load("Direct")
    assert module.NAME == "Direct"
    assert loader.info["Direct"].name == "Direct"


def test_direct_loader_missing_module(tmp_path):
    loader = ModuleLoader(tmp_path / "Modules")
    with pytest.raises(Exception, match=r'Missing not found!'):
        loader.load("Missing")


def test_direct_loader_duplicate_load(tmp_path):
    modules = tmp_path / "Modules"
    write_module(modules, "Direct")
    loader = ModuleLoader(modules)
    loader.load("Direct")
    with pytest.raises(Exception, match=r'already included'):
        loader.load("Direct")
