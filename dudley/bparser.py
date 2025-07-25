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
                    r"|(-?(?:0x[0-9aA-Fa-f]+|\d+))"  # 2 INTEGER
                    r"|(=)"  # 3 EQ
                    r"|(:=)"  # 4 CEQ
                    r"|(==)"  # 5 EEQ
                    r"|(\+=)"  # 6 PEQ
                    r"|(/)"  # 7 SLASH
                    r"|(\.\.)"  # 8 DOTDOT
                    r"|(\.)"  # 9 DOT
                    r"|(\[)"  # 10 LBRACK
                    r"|(\])"  # 11 RBRACK
                    r"|(,)"  # 12 COMMA
                    r"|(@)"  # 13 AT
                    r"|(%)"  # 14 PCNT
                    r"|(\{)"  # 15 LCURLY
                    r"|(\})"  # 16 RCURLY
                    r"|(!{)"  # 17 BCURLY
                    r"|(@=)"  # 18 ATEQ
                    r"|(\?)"  # 19 QUEST
                    r"|(\++)"  # 20 PLUSSES
                    r"|(-+)"  # 21 MINUSES
                    r"|([<>|](?:[iu][1248]|f[248]"
                    r"|c(?:4|8|16)|S1|U[124]|p[48]))"  # 22 PRIMTYPE
                    r"|(![A-Za-z_][0-9A-Za-z_]*)"  # 23 SPECIAL
                    r"|(#.*)"  # 24 COMMENT
                    r"|(\S))", re.ASCII)  # 25 UNKNOWN single character
quoted = re.compile(r"[\"']")
# several token kinds need special handling:
SYMBOL, INTEGER, QUEST, PLUSSES, MINUSES, PRIMTYPE = 3, 4, 21, 22, 23
UNKNOWN = 25
EOF, UNDEF = 0, 2  # Bison EOF and undefined token indexes (1 is error)


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
    pact=[
        -12,  33, -12, -12,  51,  23, -12, -12, -12, -12,
        -12,   3,   7,   2,  10, -12,  61, -12,  16,   2,
         44, -12,   0, -12, -12, -12, -12,  27, -12, -12,
        -12,  58,  27, -12, -12, -12, -12, -12, -12,  70,
          2, -12, -12, -12, -12, -12, -12,  64, -12,  50,
         76,  58,  46, -12, -12, -12,  38,   2,   7, -12,
         60, -12,  15, -12,  47, -12,  68, -12,  62, -12,
        -12, -12, -12, -12,  35,  72, -12, -12, -12, -12,
         76, -12, -12, -12,
    ],
    defact=[
         3,  0,  1, 16,  0,  0, 14, 13, 53,  2,
         4,  0,  0,  0,  0, 12,  0, 50,  6,  0,
         0, 19,  0, 53, 20, 22, 11, 25, 15, 17,
        10, 39, 25,  5, 36, 37, 51,  8, 57,  0,
         0,  9, 52, 47, 49, 44, 45,  0, 41,  0,
         0, 39,  0, 18, 34, 35, 39,  0,  0, 56,
         0, 40,  0, 23, 32, 28,  0, 27, 29, 21,
        38,  7, 55, 54,  0, 14, 48, 42, 33, 24,
         0, 30, 31, 26,
    ],
    pgoto=[
        -12, -12, -12,  4, 13, -10, -11, 74,  56, -12,
          9, -12,  39, 17, 36,  -7, -12, 29, -12, -12,
         71, -12,
    ],
    defgoto=[
         0,  1,  9, 10, 30, 25, 45, 27, 51, 66,
        67, 68, 53, 54, 55, 46, 47, 48, 60, 18,
        20, 42,
    ],
    table=[
        26, 43, 31,  21,  28,  21,  21, 33, 37, 44,
        21, 29, 22, -43, -43,  22,  43, 23, 21, 23,
        23, 17, 22,  24,  44,  24,  24, 22, 19, 59,
        24, 16, 23,   2,   3,  36,   4,  5, 24, 50,
        11, 12,  6,   7,  15,  38,  72, 39, 31, 40,
        70, 38,  8,  39,  52,  40,  11, 12, 13, 14,
        15,  3, 41,  74,  76,  34,  16, 78, 63, 75,
         7, 73, 35,  16,  52,  57,  58, 61, 62, 64,
        65, 79, 80,  81,  82, -46, -46, 32, 56, 83,
        69, 77, 71,   0,  49,
    ],
    check=[
        11,  1, 12,  3, 11,  3,  3, 14, 19,  9,
         3,  4, 12, 13, 14, 12,  1, 17,  3, 17,
        17,  4, 12, 23,  9, 23, 23, 12,  5, 40,
        23, 15, 17,  0,  1, 18,  3,  4, 23, 12,
         5,  6,  9, 10,  9,  1, 57,  3, 58,  5,
         4,  1, 19,  3, 16,  5,  5,  6,  7,  8,
         9,  1, 18,  3, 60,  4, 15, 20, 18,  9,
        10, 58, 11, 15, 16,  5,  6, 13, 14,  3,
         4, 13, 14, 21, 22, 13, 14, 13, 32, 80,
        51, 62, 56, -1, 23,
    ],
    r1=[
         0, 24, 25, 25, 26, 26, 26, 26, 26, 26,
        27, 27, 27, 27, 27, 27, 27, 28, 28, 29,
        29, 30, 31, 31, 32, 32, 33, 33, 34, 34,
        34, 34, 35, 35, 36, 36, 37, 37, 38, 38,
        39, 40, 40, 40, 41, 41, 41, 41, 42, 42,
        43, 43, 44, 44, 45, 45, 45, 45,
    ],
    r2=[
        0, 2, 2, 0, 1, 3, 2, 5, 3, 3,
        3, 3, 2, 1, 1, 3, 1, 1, 2, 1,
        1, 3, 1, 3, 3, 0, 3, 1, 1, 1,
        2, 2, 1, 2, 1, 1, 2, 2, 2, 0,
        3, 1, 3, 0, 1, 1, 3, 1, 2, 0,
        1, 2, 2, 0, 3, 3, 2, 1,
    ],
    stos=[
         0, 25,  0,  1,  3,  4,  9, 10, 19, 26,
        27,  5,  6,  7,  8,  9, 15, 37, 43,  5,
        44,  3, 12, 17, 23, 29, 30, 31, 39,  4,
        28, 29, 31, 39,  4, 11, 37, 30,  1,  3,
         5, 18, 45,  1,  9, 30, 39, 40, 41, 44,
        12, 32, 16, 36, 37, 38, 32,  5,  6, 30,
        42, 13, 14, 18,  3,  4, 33, 34, 35, 36,
         4, 38, 30, 28,  3,  9, 27, 41, 20, 13,
        14, 21, 22, 34,
    ],
    tname=[
        "\"end of file\"", "error", "\"invalid token\"", "SYMBOL", "INTEGER",
        "EQ", "CEQ", "EEQ", "PEQ", "SLASH", "DOTDOT", "DOT", "LBRACK",
        "RBRACK", "COMMA", "AT", "PCNT", "LCURLY", "RCURLY", "BCURLY", "QUEST",
        "PLUSSES", "MINUSES", "PRIMTYPE", "$accept", "layout", "statement",
        "group_member", "parameter", "basetype", "array", "datatype", "shape",
        "dimensions", "dimension", "symbolq", "location", "address",
        "alignment", "list", "items", "item", "group_members", "address_list",
        "members", "member", "",
    ],
    final=2)


class FunctionList(list):
    def __call__(self, args, method=None):

        def rule(self, f):
            f.method = method
            f.args = args
            f.rule = f.__doc__
            self.append(f)
            return f

        return rule

    def bind_to(self, builder):
        rules = []
        for rule in self:
            method = rule.method
            if not method:
                method = rule
            else:
                method = getattr(builder, method)
                if hasattr(method, "rule"):
                    method.rule += "\n" + rule.__doc__
                else:
                    method.rule = rule.__doc__
            rules.append(method)
        return rules


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


@rules([-1], "add")
def rule():
    """4 statement: group_member"""


@rules([-3, -1])
def rule(name, items):
    """5 statement: SYMBOL PEQ list"""
    return (name,), items


@rules([-2, -1])
def rule(name, addrs):
    """6 statement: SYMBOL address_list"""
    return (name,), addrs


@rules([-5, -3, -2, -1], "typedef")
def rule(name, datatype, shape, alignment):
    """7 statement: SYMBOL EEQ datatype shape alignment"""


@rules([-3, -1], "pointee")
def rule(pntr, arraydef):
    """8 statement: INTEGER EQ array"""


@rules([-2], "index_file")
def rule(members):
    """9 statement: BCURLY members RCURLY"""


@rules([-3, -1])
def rule(name, param):
    """10 group_member: SYMBOL CEQ parameter"""
    return name, param


@rules([-3, -1])
def rule(name, arraydef):
    """11 group_member: SYMBOL EQ array"""
    return name, arraydef


@rules([-2])
def rule(name):
    """12 group_member: SYMBOL SLASH"""
    return name, dict


@rules([])
def rule():
    """13 group_member: DOTDOT"""
    return Ellipsis, dict


@rules([])
def rule():
    """14 group_member: SLASH"""
    return None, dict


@rules([-3, -1])
def rule(name, items):
    """15 group_member: SYMBOL EQ list"""
    return name, items


@rules([-1], "error_group")
def rule(error):
    """16 group_member: error"""


@rules([-1], "newparam")
def rule(value):
    """17 parameter: INTEGER"""


@rules([-2, -1], "newparam")
def rule(basetype, location):
    """18 parameter: basetype location"""


@rules([-1])
def rule(name):
    """19 basetype: SYMBOL"""
    return name


@rules([-1])
def rule(name):
    """20 basetype: PRIMTYPE"""
    return name


@rules([-3, -2, -1], "newarray")
def rule(datatype, shape, location):
    """21 array: datatype shape location"""


@rules([-1])
def rule(basetype):
    """22 datatype: basetype"""
    return basetype


@rules([-2])
def rule(struct):
    """23 datatype: LCURLY members RCURLY"""
    return struct


@rules([-2])
def rule(dimensions):
    """24 shape: LBRACK dimensions RBRACK"""
    return dimensions


@rules([])
def rule():
    """25 shape: <empty>"""


@rules([-3, -1])
def rule(dims, dim):
    """26 dimensions: dimensions COMMA dimension"""
    return dims + (dim,)


@rules([-1])
def rule(dim):
    """27 dimensions: dimension"""
    return (dim,)


@rules([-1])
def rule(dim):
    """28 dimension: INTEGER"""
    return dim


@rules([-1])
def rule(dim):
    """29 dimension: symbolq"""
    return dim


@rules([-2, -1])
def rule(dim, delta):
    """30 dimension: symbolq PLUSSES"""
    return (dim + (delta,)) if isinstance(dim, tuple) else (dim, 0, delta)


@rules([-2, -1])
def rule(dim, delta):
    """31 dimension: symbolq MINUSES"""
    return (dim + (-delta,)) if isinstance(dim, tuple) else (dim, 0, -delta)


@rules([-1])
def rule(dim):
    """32 symbolq: SYMBOL"""
    return dim


@rules([-2])
def rule(dim):
    """33 symbolq: SYMBOL QUEST"""
    return dim, 1


@rules([-1])
def rule(addr):
    """34 location: address"""
    return addr


@rules([-1])
def rule(align):
    """35 location: alignment"""
    return -align if align else None


@rules([-1])
def rule(addr):
    """36 address: AT INTEGER"""
    return addr


@rules([])
def rule():
    """37 address: AT DOT"""


@rules([-1])
def rule(align):
    """38 alignment: PCNT INTEGER"""
    return align


@rules([])
def rule():
    """39 alignment: <empty>"""


@rules([-1])
def rule(items):
    """40 list: LBRACK items RBRACK"""
    return items


@rules([-1], "newlist")
def rule(item):
    """41 items: item"""


@rules([-3, -1])
def rule(items, item):
    """42 items: items COMMA item"""
    return items + item


@rules([], "newlist")
def rule():
    """43 items: <empty>"""


@rules([-1])
def rule(item):
    """44 item: array"""
    return item


@rules([-1])
def rule(item):
    """45 item: list"""
    return item


@rules([-2])
def rule(item):
    """46 item: SLASH group_members SLASH"""
    return item


@rules([-1], "error_list")
def rule(error):
    """47 item: error"""


@rules([-2, -1])
def rule(group, memb):
    """48 group_members: group_members group_member"""
    return group + memb


@rules([], "newgroup")
def rule():
    """49 group_members: <empty>"""


@rules([-1])
def rule(addr):
    """50 address_list: address"""
    return [addr]


@rules([-1])
def rule(addr_list, addr):
    """51 address_list: address_list address"""
    addr_list.append(addr)
    return addr_list


@rules([-2, -1])
def rule(struct, memb):
    """52 members: members member"""
    return struct + memb


@rules([], "newstruct")
def rule():
    """53 members: <empty>"""


@rules([-3, -1])
def rule(name, param):
    """54 member: SYMBOL CEQ parameter"""
    return name, param


@rules([-3, -1])
def rule(name, arraydef):
    """55 member: SYMBOL EQ array"""
    return name, arraydef


@rules([-1])
def rule(arraydef):
    """56 member: EQ array"""
    return None, arraydef


@rules([-1], "error_struct")
def rule(error):
    """57 member: error"""


del rule

# builder methods:
#   add((name, item))  --> this and group.__add__ recognize (name, dict)
#       ((name,), item) for += list or addr_list
#   newparam(int or (basetype, location))
#   newarray(datatype, shape, location)
#   newlist(item) or newlist()
#   newgroup()  ->  group + (name, item)  or  ((name,), item)
#   newstruct()
#   typedef(name, datatype, shape, align)
#   pointee(pntr, array)
#   index_file(group)
#   error_group, error_list, error_struct
