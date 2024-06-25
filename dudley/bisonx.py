#!/usr/bin/env python
"""
The bisonx utility extracts parser tables from a .tab.c file produced by Bison.

If the correspondinng .y grammar file is available, bisonx additionally
builds a skeleton for defining the reduction rules for this grammar.
"""
from __future__ import print_function

import re
import sys
from os.path import expanduser, expandvars, abspath
from glob import glob


def main(tab_file=None, grammar_file=None, outfile=None):
    if not tab_file:
        tab_file = "*.tab.c"
    tab_file = check_file(tab_file)
    tables = parse_tables(tab_file)
    if not grammar_file:
        if tab_file.endswith(".tab.c"):
            grammar_file = tab_file[:-6] + ".y"
            if not glob(grammar_file):
                grammar_file = None
    if grammar_file:
        grammar_file = check_file(grammar_file)
        rules = parse_grammar(grammar_file)
        if len(rules) != len(tables["r1"]):
            print("WARNING: {} rules in .y, but {} rules in .tab.c"
                  .format(len(rules), len(tables["r1"])))
    else:
        rules = []
    tables = parse_tables(tab_file)
    if not outfile:
        outfile = "bparser.py"
    with open(outfile, "w") as f:
        dump_tables(tables, f)
        if rules:
            dump_rules(rules, f)


def check_file(name):
    files = glob(expanduser(expandvars(name)))
    if not files:
        raise ValueError("no such file as " + name)
    elif len(files) > 1:
        raise ValueError("{} files match {}".format(len(files), name))
    return abspath(files[0])

# .tab.c file regexps
_yytables = [("final", re.compile(r"#define\s+YYFINAL\s+(\d+)")),
             ("tname", re.compile(r"char\s*\*.*yytname.*=")),
             ("pact", re.compile(r"int.*\syypact.*=")),
             ("defact", re.compile(r"int.*\syydefact.*=")),
             ("pgoto", re.compile(r"int.*\syypgoto.*=")),
             ("defgoto", re.compile(r"int.*\syydefgoto.*=")),
             ("table", re.compile(r"int.*\syytable.*=")),
             ("check", re.compile(r"int.*\syycheck.*=")),
             ("stos", re.compile(r"int.*\syystos.*=")),
             ("r1", re.compile(r"int.*\syyr1.*=")),
             ("r2", re.compile(r"int.*\syyr2.*="))]
_yysplit = re.compile(r"\s*(?!'),(?!')\s*")  # unquoted comma


def parse_tables(tab_file):
    tables = {}
    with open(tab_file) as f:
        fi = iter(f)
        for line in fi:
            for key, re in _yytables:
                m = re.search(line)
                if m:
                    break
            else:
                continue
            if key == "final":
                tables[key] = int(m.group(1))
                continue
            while not line.rstrip().endswith("{"):
                line = next(fi)
            table = []
            convert = (lambda x: x) if key == "tname" else int
            while True:
                line = next(fi).lstrip()
                if line.startswith("}"):
                    break
                items = [x.strip() for x in _yysplit.split(line)]
                if not items[-1]:
                    del items[-1:]
                if items[-1] == "YY_NULLPTR":
                    items[-1] = '""'
                table.extend(convert(x) for x in items)
            tables[key] = table
    return tables

# grammar file regexps
_section = re.compile(r"\s*%%")
_lhs = re.compile(r"\s*([A-Za-z_]\w*\s*:|\|)\s*")
_end_rule = re.compile(r".*;")


def parse_grammar(grammar_file):
    rules = ["$error?", "$accept: . $end"]
    current_rule = ""

    def append_rule():
        if current_rule:
            rule = current_rule
            if rule.endswith(": "):
                rule += "<empty>"
            rules.append(rule)
            return ""

    with open(grammar_file) as f:
        lhs = ""
        skip_section = True
        empty_rule = False
        for line in f:
            m = _section.match(line)
            if skip_section:
                skip_section = not m
                continue
            elif m:
                break
            # Only get here for lines in second %% section of file.
            m = _lhs.match(line)
            mend = _end_rule.match(line, m.end() if m else 0)
            if m:
                if current_rule:
                    current_rule = append_rule()
                txt = m.group(1)
                if txt != "|":
                    lhs = txt
                end = mend.start() if mend else None
                current_rule = lhs + " " + line[m.end():end].rstrip()
                if mend:
                    current_rule = append_rule()
            else:
                end = mend.start() if mend else None
                txt = line[:end].strip()
                if txt and current_rule:
                    if current_rule.endswith(" "):
                        current_rule += txt
                    else:
                        current_rule += " " + txt
                    current_rule = append_rule()
        current_rule = append_rule()
    return rules


def dump_tables(tables, f=sys.stdout):
    f.write("tables = dict(\n")
    for key in ["pact", "defact", "pgoto", "defgoto", "table", "check",
                "r1", "r2", "stos", "tname"]:
        f.write("    {} = [\n".format(key))
        if key != "tname":
            dump_cols(tables[key], f, 8)
        else:
            dump_strs(tables[key], f, 8)
        f.write("    ],\n".format(key))
    f.write("    final = {})\n".format(tables["final"]))


def dump_strs(xlist, f=sys.stdout, indent=0, width=80):
    line = prefix = " " * indent
    n = indent
    for x in xlist:
        n += len(x) + 2
        if n > width:
            f.write(line.rstrip() + "\n")
            line = prefix
            n = indent + len(x) + 2
        line += x + ", "
    if n > indent:
        f.write(line.rstrip() + "\n")


def dump_cols(xlist, f=sys.stdout, indent=0, width=80):
    ncols = 10
    n = len(xlist)
    if n < ncols:
        if not n: return
        ncols = n
    xlist = _yysplit.split(repr(xlist)[1:-1])  # convert to strings
    nrows = n // ncols
    nextra = n % ncols
    if nextra:
        xlist += [""] * (ncols - nextra)
    rows = [xlist[i:i+ncols] for i in range(0, n, ncols)]
    cols = zip(*rows)
    widths = [max(len(v) for v in col) for col in cols]
    fmts = ["{{:>{}}}".format(width) for width in widths]
    fmt = ", ".join(fmts)
    if nextra:
        del rows[-1][nextra:]
    for row in rows:
        if len(row) > nextra:
            f.write(" "*indent + fmt.format(*row) + ",\n")
        else:
            f.write(" "*indent + ", ".join(fmts[:nextra]).format(*row) + ",\n")


def dump_rules(rules, f=sys.stdout):
    f.write("\n\nclass FunctionList(list):\n")
    f.write("    def __call__(self, f)\n")
    f.write("        self.append(f)\n")
    f.write("        return f\n")
    f.write("\nrules = FunctionList()\n")
    for i, rule in enumerate(rules):
        f.write("\n\n@rules  # {} {}\n".format(i, rule))
        f.write("def _rule(args):\n    pass\n")


if __name__ == "__main__":
    main()
