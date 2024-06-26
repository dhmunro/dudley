"""Data required to build Dudley parser.

The tables and rules skeleton are automatically generated by bisonx.py
using the dudley.y grammar file and the .tab.c file Bison gnerates from it.
"""
import re
from ast import literal_eval

__all__ = ["regexp", "handler", "tables", "rules"]

# Bison prepends EOF, error, and UNDEF tokens to %token declaration in .y,
# so add 2 to re group number to get bison symbol kind.
regexp = re.compile(r'(?:((?:"(?:\\.|[^"\\])+"'
                    r"|'(?:\\.|[^'\\])+'|[A-Za-z_][0-9A-Za-z_]*))"  # 1 SYMBOL
                    r"|(0x[0-9aA-Fa-f]+|\d+)"  # 2 INTEGER
                    r"|(:=)"  # 3 CEQ
                    r"|(==)"  # 4 EEQ
                    r"|(=\[)"  # 5 EQB
                    r"|(/\{)"  # 6 SLASHC
                    r"|(!@)"  # 7 BAT
                    r"|(\.\.)"  # 8 DOTDOT
                    r"|(\?{)"  # 9 QCURLY
                    r"|(@=)"  # 10 ATEQ
                    r"|(\?/)"  # 11 QSLASH
                    r"|(\?)"  # 12 QUEST
                    r"|(\++)"  # 13 PLUSSES
                    r"|(-+)"  # 14 MINUSES
                    r"|(=)"  # 15 EQ
                    r"|(\[)"  # 16 LBRACK
                    r"|(\])"  # 17 RBRACK
                    r"|(,)"  # 18 COMMA
                    r"|(/)"  # 19 SLASH
                    r"|(\*)"  # 20 STAR
                    r"|(\.)"  # 21 DOT
                    r"|(@)"  # 22 AT
                    r"|(%)"  # 23 PCNT
                    r"|(\{)"  # 24 LCURLY
                    r"|(\})"  # 25 RCURLY
                    r"|([<>|](?:[iu][1248]|f[248]"
                    r"|c(?:4|8|16)|S1|U[124]|p[48]))"  # 26 PRIMTYPE
                    r"|(![A-Za-z_][0-9A-Za-z_]*)"  # 27 SPECIAL
                    r"|(#.*)"  # 28 COMMENT
                    r"|(\S))", re.ASCII)  # 29 UNKNOWN single character
quoted = re.compile(r"[\"']")
# several token kinds need special handling:
SYMBOL, INTEGER, QUEST, PLUSSES, MINUSES, PRIMTYPE = 3, 4, 15, 16, 28
UNKOWN = 31
EOF, UNDEF = 0, 2  # Bison EOF and undefined token indexes


def handler(m, mprev):
    itok = m.lastindex + 2
    value = None
    if itok == SYMBOL:
        value = m.group()
        if quoted.match(value):
            value = literal_eval(value)
    elif itok == INTEGER:
        value = int(m.group(), 0)
    elif itok == QUEST:
        if not mprev or m.start() != mprev.end():  
            itok = UNDEF
    elif itok == PLUSSES or itok == MINUSES:
        start, end = m.span()
        if mprev and start == mprev.end():  
            value = m.end() - m.start()
        else:
            itok = UNDEF
    elif itok >= PRIMTYPE and itok < UNKNOWN:
        value = m.group()
        if value == "!DUDLEY":
            itok = EOF
    else:
        itok = UNDEF
    return itok, value


# The tables and rules skeletons are generated automatically by bisonx.py
# from the .y grammar file and bison-produced .tab.c file.  The rules
# skeletons are modified here to generate the internal representation
# of the Dudley layout.

tables = dict(
    pact = [
        -43,  59, -43, -43,  78,  -6,  16, -43, -43, -43,
        -43,  64, -43,   3,  15, -43, -43, -43,  15, -43,
          6, -43,  -2,  15, -43, -43,  21,   5,   5,  20,
        -43,  97, -43, -43, -43, -43,  28, -43, -43,  10,
         71,  12, -43, -43, -43,  10,   3,  28,  28,  10,
        -43, -43, -43, -43,  15, -43, -43, -43, -43,  45,
        -43, -43, -43, -43,  54,  30, -43,   7,  15, -43,
         37,  39,  28,  73,  -2,  28, -43, -43, -43,  28,
         10, 100,  24, -43,  52, -43, -43,  96, 101, -43,
          3,  15,  10, -43, -43, -43, -43, -43,  54, -43,
         -2, -43, -43,  28, -43,  89, -43, -43, -43, -43,
        -43, -43,  54, -43,  10,  28, 103, -43,  15, -43,
         28, -43, -43,  10, -43,
    ],
    defact = [
         3,  0,  1, 18,  0,  0,  0, 16, 17,  2,
         4,  0, 57,  0,  0, 26, 25,  8,  0, 14,
         0, 50,  7,  0, 11, 73,  0,  0,  0,  0,
        69,  0, 21, 19, 22, 13, 47, 27, 23, 30,
         0, 30, 44, 45, 51, 30,  0, 47, 47, 30,
        68, 55, 58, 59,  0, 15, 56, 57, 61,  0,
        20, 42, 43, 28,  0, 47, 65,  0,  0, 67,
         0, 28, 47,  0, 49, 47, 72, 71, 70, 47,
        30,  0,  0, 46, 38, 34, 41, 35,  0,  5,
         0,  0, 30, 24, 66, 31, 12, 32,  0,  6,
        48, 10,  9, 47, 53,  0, 54, 60, 39, 36,
        37, 29,  0, 63, 30, 47,  0, 52,  0, 40,
        47, 64, 33, 30, 62,
    ],
    pgoto = [
        -43, -43, -43,  -7, -42, -11, -18, -43, -43, -43,
        -43, -36, -43, -43, -35, -43, -12, -33,  -3,  25,
        -43,  29, -43,  56, -43, -43, -43,  48, -43, -43,
         80,
    ],
    defgoto = [
         0,  1,  9, 10, 35, 38, 39, 11, 12, 40,
        64, 72, 73, 74, 86, 87, 88, 60, 61, 62,
        99, 22, 56, 31, 57, 58, 82, 69, 70, 29,
        30,
    ],
    table = [
         41,  21,  36,  65,  76,  45,  32,  33,  32,  75,
         42,  23,  90,  79,  77,  78,  47,  48,  32,  44,
         24,  25,  20,  26,  91,   3,  46, 105,  63,  43,
         71,  34,  27,  34,   7,  36,  80,  28,  66,  96,
         67,  37, 101,  34, 103,   8, 102,  49, 113,  83,
         92, 106,  20,  59,  68,  59, 115,  84,  85,   2,
          3,  95,   4,   5,  93,  25, 108,  26,   6,   7,
        117,  21,  66, 114,  67, 107,  27, 119, 120,  36,
          8,  28, 121,  13,  14,  15, 116, 124,  68,  16,
         89,  17,  97,  98,  13,  18,  15,  44,  51,  19,
        123,  51,  20, 100,  52,  53, 118,  52,  53,  50,
         19, 109, 110,  81,  54,   0,  55,  54,  94, 104,
        111, 112, 122, 112,
    ],
    check = [
         18,  4,  13, 39, 46, 23,  3,   4,   3, 45,
          4, 17,   5, 49, 47, 48, 27,  28,   3, 22,
          4,  1,  24,  3, 17,  1,  5,   3,  18, 23,
         18, 28,  12, 28, 10, 46, 54,  17,   1, 72,
          3, 26,  75, 28, 80, 21, 79,  27,  90,  4,
         68, 27,  24, 25, 17, 25, 92,   3,   4,  0,
          1, 22,   3,  4, 27,  1, 14,   3,   9, 10,
        103, 74,   1, 91,  3, 82, 12, 112, 114, 90,
         21, 17, 115,  5,  6,  7, 98, 120,  17, 11,
         65, 13,  19, 20,  5, 17,  7, 100,   1, 21,
        118,  1,  24, 74,  7,  8, 17,   7,   8, 29,
         21, 15,  16, 57, 17, -1, 19,  17,  70, 19,
         19, 20,  19, 20,
    ],
    r1 = [
         0, 29, 30, 30, 31, 31, 31, 31, 31, 31,
        31, 31, 32, 32, 32, 32, 32, 32, 32, 33,
        33, 34, 34, 35, 35, 36, 37, 38, 39, 40,
        40, 41, 42, 42, 43, 43, 43, 43, 44, 44,
        45, 45, 46, 46, 47, 47, 48, 48, 49, 49,
        50, 50, 51, 51, 51, 51, 52, 52, 53, 54,
        55, 55, 56, 56, 56, 56, 57, 57, 58, 58,
        59, 59, 59, 59,
    ],
    r2 = [
        0, 2, 2, 0, 1, 5, 5, 2, 2, 5,
        5, 2, 5, 3, 2, 3, 1, 1, 1, 1,
        2, 1, 1, 1, 3, 2, 2, 1, 1, 3,
        0, 2, 2, 4, 1, 1, 2, 2, 1, 2,
        3, 1, 1, 1, 2, 2, 2, 0, 1, 0,
        1, 2, 4, 3, 3, 1, 2, 0, 1, 1,
        2, 0, 5, 3, 4, 1, 2, 1, 2, 1,
        3, 3, 3, 1,
    ],
    stos = [
         0, 30,  0,  1,  3,  4,  9, 10, 21, 31,
        32, 36, 37,  5,  6,  7, 11, 13, 17, 21,
        24, 47, 50, 17,  4,  1,  3, 12, 17, 58,
        59, 52,  3,  4, 28, 33, 34, 26, 34, 35,
        38, 35,  4, 23, 47, 35,  5, 34, 34, 27,
        59,  1,  7,  8, 17, 19, 51, 53, 54, 25,
        46, 47, 48, 18, 39, 40,  1,  3, 17, 56,
        57, 18, 40, 41, 42, 40, 33, 46, 46, 40,
        35, 52, 55,  4,  3,  4, 43, 44, 45, 48,
         5, 17, 35, 27, 56, 22, 46, 19, 20, 49,
        50, 46, 46, 40, 19,  3, 27, 32, 14, 15,
        16, 19, 20, 33, 35, 40, 45, 46, 17, 43,
        40, 46, 19, 35, 46,
    ],
    tname = [
        "\"end of file\"", "error", "\"invalid token\"", "SYMBOL", "INTEGER",
        "CEQ", "EEQ", "EQB", "SLASHC", "BAT", "DOTDOT", "QCURLY", "ATEQ",
        "QSLASH", "QUEST", "PLUSSES", "MINUSES", "EQ", "LBRACK", "RBRACK",
        "COMMA", "SLASH", "STAR", "DOT", "AT", "PCNT", "LCURLY", "RCURLY",
        "PRIMTYPE", "$accept", "layout", "statement", "group_item",
        "parameter", "basetype", "type", "rootdef", "listdef", "struct",
        "shapedef", "shape", "ushapedef", "ushape", "dimension", "symbolq",
        "dimensions", "location", "address", "alignment", "uaddress",
        "address_list", "list_item", "list_items", "anonlist", "anongroup",
        "group_items", "member", "members", "root_params", "root_param", "",
    ],
    final = 2)


class FunctionList(list):
    def __call__(self, args, method=None):

        def __call__(self, f):
            f.method = method
            f.args = args
            self.append(f)
            return f

        return rule

    def bind_to(self, builder):
        for i, rule in enumerate(self):
            method = rule.method
            if not method:
                continue
            method = builder[method]
            method.args = args
            method.rule = rule.__doc__
            self[i] = method


rules = FunctionList()

# Each rule function must return the LHS value (or None).
# The RHS values on the parser stack are indexed from -N
# to -1 if there are N symbols on the RHS (-N is first RHS.
# value and -1 is last RHS value).
# With @rule([-2, -4, -1]), the parser calls rule like this:
#   rule(value[-2], value[-4], value[-1])
# In other words, only the values of the specifically listed
# elements are passed to the rule.  An empty list passes no
# arguments to the rule.
# With @rule(arglist, 'method_name'), you can later invoke
#   rule.bind_to(builder)
# to make the parser call builder.method_name with the
# values for the specified stack elements.  (Leave the rule
# function body empty in this case - it is discarded.)
# The bind_to method adds a .args attribute to the method,
# which is required by the parser, and a .rule attribute
# recording the docstring of the rule for informational
# purposes.


@rules([])
def rule():
    """0 $error?"""

@rules([])
def rule():
    """1 $accept: . $end"""

@rules([])
def rule():
    """2 layout: layout statement"""

@rules([])
def rule():
    """3 layout: <empty>"""

@rules([])
def rule():
    """4 statement: group_item"""

@rules([-5, -3, -2, -1], "atype")
def rule(name, atype, shape, alignment):
    """5 statement: SYMBOL EEQ type shape alignment"""

@rules([-5, -3, -2, -1], "var")
def rule(name, atype, ushape, uaddress):
    """6 statement: SYMBOL EQ type ushape uaddress"""

@rules([-2, -1], "var_extend")
def rule(name, address_list):
    """7 statement: SYMBOL address_list"""

@rules([-1], "cdroot")
def rule(name):
    """8 statement: SYMBOL QSLASH"""

@rules([-2, -1], "close_root")
def rule(shape, location):
    """9 statement: rootdef root_params RCURLY shape location"""

@rules([-5, -3, -2, -1], "pointee")
def rule(value, atype, shape, location):
    """10 statement: INTEGER EQ type shape location"""

@rules([-1], "set_address")
def rule(address):
    """11 statement: BAT INTEGER"""

@rules([-5, -3, -2, -1], "var")
def rule(name, atype, shape, location):
    """12 group_item: SYMBOL EQ type shape location"""

@rules([-3, -1], "param")
def rule(name, parameter):
    """13 group_item: SYMBOL CEQ parameter"""

@rules([-2], "cd")
def rule():
    """14 group_item: SYMBOL SLASH"""

@rules([], "close_list")
def rule():
    """15 group_item: listdef list_items RBRACK"""

@rules([], "cdup")
def rule():
    """16 group_item: DOTDOT"""

@rules([], "cd")
def rule():
    """17 group_item: SLASH"""

@rules([-1], "error18")
def rule():
    """18 group_item: error"""

@rules([-1])
def rule(value):
    """19 parameter: INTEGER"""
    return value

@rules([-2, -1])
def rule(basetype, location):
    """20 parameter: basetype location"""
    return basetype, location

@rules([-1])
def rule(name):
    """21 basetype: SYMBOL"""
    return name

@rules([-1])
def rule(name):
    """22 basetype: PRIMTYPE"""
    return name

@rules([-1])
def rule(basetype):
    """23 type: basetype"""
    return basetype

@rules([], "close_struct")
def rule():
    """24 type: struct members RCURLY"""

@rules([-2], "open_root")
def rule(name):
    """25 rootdef: SYMBOL QCURLY"""

@rules([-2], "open_list")
def rule():
    """26 listdef: SYMBOL EQB"""

@rules([], "open_struct")
def rule():
    """27 struct: LCURLY"""

@rules([])
def rule():
    """28 shapedef: LBRACK"""

@rules([-2], "shape")
def rule(dimensions):
    """29 shape: shapedef dimensions RBRACK"""

@rules([])
def rule():
    """30 shape: <empty>"""

@rules([])
def rule():
    """31 ushapedef: LBRACK STAR"""

@rules([-2], "shape")
def rule(umarker):
    """32 ushape: ushapedef RBRACK"""

@rules([-4, -2], "shape")
def rule(umarker, dimensions):
    """33 ushape: ushapedef COMMA dimensions RBRACK"""

@rules([-1])
def rule(value):
    """34 dimension: INTEGER"""
    return value

@rules([-1])
def rule(name):
    """35 dimension: symbolq"""
    return name

@rules([-2, -1])
def rule(name, inc):
    """36 dimension: symbolq PLUSSES"""
    return (name, 0, inc) if isinstance(name, tuple) else (name, inc)

@rules([-2, -1])
def rule(name, dec):
    """37 dimension: symbolq MINUSES"""
    return (name, 0, -dec) if isinstance(name, tuple) else (name, -dec)

@rules([-1])
def rule(name):
    """38 symbolq: SYMBOL"""
    return name

@rules([-2])
def rule(name):
    """39 symbolq: SYMBOL QUEST"""
    return (name, 0)

@rules([-2, -1])
def rule(dimensions, dimension):
    """40 dimensions: dimensions COMMA dimension"""
    return dimensions.append(dimension)

@rules([-1])
def rule():
    """41 dimensions: dimension"""
    return [dimension]

@rules([-1])
def rule(address):
    """42 location: address"""
    return address

@rules([-1])
def rule(alignment):
    """43 location: alignment"""
    return alignment

@rules([-1])
def rule(address):
    """44 address: AT INTEGER"""
    return address

@rules([])
def rule():
    """45 address: AT DOT"""
    return Ellipsis  # signal to use current address

@rules([-1])
def rule(alignment):
    """46 alignment: PCNT INTEGER"""
    return -alignment

@rules([])
def rule():
    """47 alignment: <empty>"""

@rules([-1])
def rule(address_list):
    """48 uaddress: address_list"""
    return address_list

@rules([])
def rule():
    """49 uaddress: <empty>"""

@rules([-1])
def rule(address):
    """50 address_list: address"""
    return [address]

@rules([-2, -1])
def rule(address_list, address):
    """51 address_list: address_list address"""
    return address_list.append(address)

@rules([-4, -3, -2, -1], "var")
def rule(anon, atype, shape, location):
    """52 list_item: EQ type shape location"""

@rules([], "close_list")
def rule():
    """53 list_item: anonlist list_items RBRACK"""

@rules([], "close_group")
def rule():
    """54 list_item: anongroup group_items RCURLY"""

@rules([-1], "error55")
def rule(error):
    """55 list_item: error"""

@rules([])
def rule():
    """56 list_items: list_items list_item"""

@rules([])
def rule():
    """57 list_items: <empty>"""

@rules([], "open_list")
def rule():
    """58 anonlist: EQB"""

@rules([], "open_group")
def rule():
    """59 anongroup: SLASHC"""

@rules([])
def rule():
    """60 group_items: group_items group_item"""

@rules([])
def rule():
    """61 group_items: <empty>"""

@rules([-5, -3, -2, -1], "var")
def rule(name, atype, shape, location):
    """62 member: SYMBOL EQ type shape location"""

@rules([-3, -1], "param")
def rule(name, parameter):
    """63 member: SYMBOL CEQ parameter"""

@rules([-4, -3, -2, -1], "var")
def rule(anon, atype, shape, location):
    """64 member: EQ type shape location"""

@rules([-1], "error65")
def rule(error):
    """65 member: error"""

@rules([])
def rule():
    """66 members: members member"""

@rules([])
def rule():
    """67 members: member"""

@rules([])
def rule():
    """68 root_params: root_params root_param"""

@rules([])
def rule():
    """69 root_params: root_param"""

@rules([-3, -2, -3, -1], "var")
def rule(anon, basetype, noshape, location):
    """70 root_param: EQ basetype location"""

@rules([-2, -1], "atvar")
def rule(basetype, location):
    """71 root_param: ATEQ basetype location"""

@rules([-3, -1], "param")
def rule():
    """72 root_param: SYMBOL CEQ parameter"""

@rules([-1], "error73")
def rule(error):
    """73 root_param: error"""
del rule
