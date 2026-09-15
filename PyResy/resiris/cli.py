from __future__ import annotations

import argparse
from pathlib import Path

from .interpreter import Interpreter, RuntimeErrorResiris
from .parser import Parser, ast_to_dict
from .tokenizer import ResirisSyntaxError, Tokenizer


# Terminal colors

RED = "\033[31m"
GREEN = "\033[32m"
BLUE = "\033[34m"
RESET = "\033[0m"


# Resiris CLI banner

VERSION = "1.8"

BANNER = f"""{RED}
██████╗ ███████╗███████╗██╗██████╗ ██╗███████╗
██╔══██╗██╔════╝██╔════╝██║██╔══██╗██║██╔════╝
██████╔╝█████╗  ███████╗██║██████╔╝██║███████╗
██╔══██╗██╔══╝  ╚════██║██║██╔══██╗██║╚════██║
██║  ██║███████╗███████║██║██║  ██║██║███████║
╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚═╝  ╚═╝╚══════╝
{RESET}"""


def print_banner() -> None:
    print(BANNER)
    print("Resiris CLI")
    print(f"Version:{VERSION}")
    print()


# Run .resy file

FRONTEND_CONFIG_DIR = Path.home() / ".config" / "resiris"
FRONTEND_CONFIG_FILE = FRONTEND_CONFIG_DIR / "frontend_visibility"


class ResirisArgumentParser(argparse.ArgumentParser):
    """Argument parser that keeps command-line errors compact."""

    def error(self, message: str) -> None:
        self.exit(2, f"{RED}Resiris CLI error:{RESET} {message}\n")


def frontend_visibility_enabled() -> bool:
    return FRONTEND_CONFIG_FILE.is_file()


def set_frontend_visibility(enabled: bool) -> None:
    if enabled:
        FRONTEND_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        FRONTEND_CONFIG_FILE.write_text("enabled\n", encoding="utf-8")
    else:
        try:
            FRONTEND_CONFIG_FILE.unlink()
        except FileNotFoundError:
            pass


def run_file(source_path: Path, show_frontend: bool = False) -> int:
    if source_path.suffix.lower() != ".resy":
        print(
            f"{RED}ResirisError:{RESET} "
            "Resiris files must have the .resy extension."
        )
        return 1

    if not source_path.is_file():
        print(
            f"{RED}ResirisError:{RESET} "
            f"file not found: {source_path}"
        )
        return 1

    try:
        source = source_path.read_text(encoding="utf-8")

        tokens = Tokenizer().tokenize(source)
        program = Parser(tokens).parse()

        Interpreter().run(program)

        if show_frontend:
            print()
            print("<TOKENS>")
            for token in tokens:
                print(token)

            print()
            print("<AST>")
            print(ast_to_dict(program))

    except (ResirisSyntaxError, RuntimeErrorResiris) as error:
        print(
            f"{RED}{type(error).__name__}:{RESET} {error}"
        )
        return 1

    except UnicodeDecodeError:
        print(
            f"{RED}ResirisError:{RESET} "
            f"file is not UTF-8 encoded: {source_path}"
        )
        return 1

    except OSError as error:
        print(
            f"{RED}ResirisError:{RESET} "
            f"file cannot be read: {error}"
        )
        return 1

    return 0


def main() -> int:
    parser = ResirisArgumentParser(
        prog="resiris",
    )

    frontend_group = parser.add_mutually_exclusive_group()

    frontend_group.add_argument(
        "--enable-frontend-visibility",
        action="store_true",
        help="Enable frontend output for all subsequently run .resy files",
    )

    frontend_group.add_argument(
        "--disable-frontend-visibility",
        action="store_true",
        help="Disable frontend output for subsequently run .resy files",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"Version:{VERSION}",
        help="Show the Resiris version",
    )

    parser.add_argument(
        "file",
        nargs="?",
        help=".resy file to run",
    )

    args = parser.parse_args()

    # These switches are persistent settings. A file is optional.
    if args.enable_frontend_visibility:
        set_frontend_visibility(True)
        print(f"{GREEN}Frontend visibility enabled.{RESET}")
        if args.file is None:
            return 0

    if args.disable_frontend_visibility:
        set_frontend_visibility(False)
        print(f"{GREEN}Frontend visibility disabled.{RESET}")
        if args.file is None:
            return 0

    # No file supplied and no setting change.
    if args.file is None:
        print_banner()

        print("Usage:")
        print("  resiris <file.resy>")
        print()

        print("Example:")
        print("  resiris main.resy")
        print()

        print(f"{BLUE}Options:{RESET}")
        print("  --enable-frontend-visibility")
        print("               Enable frontend output for .resy files")
        print("  --disable-frontend-visibility")
        print("               Disable frontend output for .resy files")
        print("  --help       Show this help message")
        print("  --version    Show the Resiris version")

        return 0

    return run_file(
        Path(args.file),
        show_frontend=frontend_visibility_enabled(),
    )


if __name__ == "__main__":
    raise SystemExit(main())