from resiris.tokenizer import Tokenizer, TokenType
from resiris.parser import Parser, ast_to_dict


SOURCE = """\
## Minimal Resiris test

v number int = 10
v other int = 5

number = number + other

if number > 10:
	number += 2
elif number == 10:
	number = 20
else:
	pass

fn add(a, b):
	return a + b

start():
	add(number, 3)
"""


def main():
    tokens = Tokenizer().tokenize(SOURCE)

    print("<TOKENS>")
    for token in tokens:
        print(token)

    print("\n<AST>")
    tree = Parser(tokens).parse()
    print(ast_to_dict(tree))


if __name__ == "__main__":
    main()
