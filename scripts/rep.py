import argparse
import json
import re

FORMULA_DELIMS = [
    (r"\\\[", r"\\\]"),
    (r"\$", r"\$"),
    (r"\$\$", r"\$\$"),
    (r"\\begin\{align\*\}", r"\\end\{align\*\}"),
    (r"\\begin\{align\}", r"\\end\{align\}"),
    (r"\\begin\{equation\*\}", r"\\end\{equation\*\}"),
    (r"\\begin\{equation\}", r"\\end\{equation\}"),
]

REGEXES = [
    re.compile("%.*"), # Comments.
    re.compile("|".join(
        rf"({beg}(.|\n)*?{end})"
        for beg, end in FORMULA_DELIMS
    )),  # Formulae.
    re.compile(r"\\(begin|end|label|cite|eqref|ref)\{.*?\}"), # Commands with special meaning
    re.compile(r"\\(\w|\*)+"), # slash command
]


def replace_forward(s):
    count = 0
    def gen_unique_key():
        nonlocal count
        count += 1
        return f"xyz{count:04}qwe"

    replacements = {}
    def repl(mo: re.Match):
        nonlocal replacements
        stub = replacements.get(mo.group(0))
        if stub is not None:
            return stub
        stub = gen_unique_key()
        replacements[mo.group(0)] = stub
        return stub

    for regex in REGEXES:
        s = re.sub(regex, repl, s)
    return s, replacements

def replace_backward(s: str, replacements):
    # Reverse sort order to reconstruct the exact file (matters if replacements we embedded).
    for before, after in sorted(replacements.items(), key=lambda t: t[1], reverse=True):
        s = s.replace(after, before)
    return s


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backward", action="store_true")
    parser.add_argument("--src", required=True)
    parser.add_argument("--dst", required=True)
    parser.add_argument("--replacements", required=True)

    args = parser.parse_args()
    with open(args.src) as f:
        s = f.read()

    if args.backward:
        with open(args.replacements) as f:
            replacements = json.load(f)
        res = replace_backward(s, replacements)
    else:
        res, replacements = replace_forward(s)
        with open(args.replacements, "w") as f:
            json.dump(replacements, f)

    with open(args.dst, "w") as f:
        f.write(res)


if __name__ == "__main__":
    main()
