from pathlib import Path

from resiris.ast_nodes import Include, Program
from resiris.interpreter import Interpreter


def test_bundled_rsmath_metadata():
    project_root = Path(__file__).resolve().parents[1]
    interpreter = Interpreter(modules_dir=project_root / "Modules")
    interpreter.run(Program([Include(["RSMath"])]))

    info = interpreter.module_loader.info["RSMath"]
    assert info.name == "RSMath"
    assert info.functions == (
        "abs, sqrt, cbrt, pow, floor, ceil, round, ln, log10, "
        "sin, cos, tan, asin, acos, atan, hypot, factorial, ncr, npr, "
        "gcd, lcm, mod, min, max, clamp, is_nan, is_inf, is_finite, pythagoras"
    )
    assert info.variables == "PI:float, E:float"
