# Resiris

A PC-side development environment and interpreter for the Resiris programming language.

The current prototype runs `.resy` source files through the Resiris tokenizer, parser, AST and interpreter.

## Requirements

You need:

- Python 3

For the `.resy` file integration, these are optional:

- VS Code / Code - OSS / VSCodium
- `xdg-mime`
- `update-mime-database`

## How to use

Download or clone this repository, then open a terminal in the project folder.

To run a specific Resiris program:

```bash
python3 -m resiris program.resy
```

You can also use the project launcher:

```bash
./bin/resiris program.resy
```

If you run Resiris without a file, it does not automatically open `main.resy`. Instead, it shows the Resiris CLI main page:

```bash
resiris
```

## Using `resiris` as a terminal command

If you want to start Resiris by simply typing:

```bash
resiris
```

Run this from inside the project folder:

```bash
./install_reseris.sh
```

The installer creates the `resiris` symlink in `~/.local/bin` and installs the `.resy` Linux file-manager integration. If a VS Code-compatible CLI is available, the installer explicitly asks whether the **Resiris Language Support** extension should also be installed. The extension is **not** installed automatically.

The VS Code extension provides `.resy` language support (syntax highlighting, Resiris indentation settings and snippets) and the custom Resiris `.resy` file icon through the Resiris Seti icon theme. Installing the terminal tool alone does not install the VS Code extension or its VS Code icon theme.

You can also install the VS Code extension directly from VS Code without installing the terminal tool.

Then you can run Resiris from any terminal:

```bash
resiris program.resy
```

Running only:

```bash
resiris
```

shows the Resiris CLI main page. It does not run `main.resy` automatically.

## Error output

Resiris errors are printed as concise CLI errors without exposing the internal Python traceback. Source errors from the tokenizer, parser or runtime include the Resiris error type and its message.

For example:

```text
UnknownVariableError: line 1, column 1: x: unknown name
```

Invalid command-line arguments are reported separately as `Resiris CLI error:` messages instead of printing the full argparse usage page.

## Removing it

To remove the installed terminal command, `.resy` Linux integration and any installed Resiris VS Code extension, run:

```bash
./uninstall_reseris.sh
```

The project files themselves are not deleted.
