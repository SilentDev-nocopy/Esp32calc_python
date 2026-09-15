"use strict";

const vscode = require("vscode");

function activate(context) {
  const provider = vscode.languages.registerCompletionItemProvider(
    { language: "resiris" },
    {
      provideCompletionItems(document) {
        const items = [];

        const start = new vscode.CompletionItem(
          "start",
          vscode.CompletionItemKind.Snippet
        );
        start.detail = "Resiris start";
        start.documentation = "Resiris lifecycle entry point";
        start.insertText = new vscode.SnippetString("START():\n\t$0");
        items.push(start);

        const process = new vscode.CompletionItem(
          "process",
          vscode.CompletionItemKind.Snippet
        );
        process.detail = "Resiris process";
        process.documentation = "Resiris repeated lifecycle function";
        if (hasFpsConstant(document)) {
          process.insertText = new vscode.SnippetString("PROCESS(FPS):\n\t$0");
        } else {
          process.insertText = new vscode.SnippetString(
            "## FPS: hányszor fut a PROCESS egy másodperc alatt\n" +
              "c FPS float = 30.0\n" +
              "\n" +
              "PROCESS(FPS):\n" +
              "\t$0"
          );
        }
        items.push(process);

        return items;
      },
    }
  );

  context.subscriptions.push(provider);
}

function hasFpsConstant(document) {
  return /^\s*c\s+FPS\s+float\b/m.test(document.getText());
}

function deactivate() {}

module.exports = { activate, deactivate };