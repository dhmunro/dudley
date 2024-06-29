# The tables and rules skeletons are generated automatically by bisonx.py
# from the .y grammar file and bison-produced .tab.c file.  The rules
# skeletons are modified here to generate the internal representation
# of the Dudley layout.

tables = dict(
    pact = [
        -46, 102, -46, -46, 109,  -5,  14, -46, -46, -46,
        -46,   6,  47,  47, -46,  47, 107,  47, -46, -46,
        -46, -46, -46, -46, -46, -46,   7, -46,   5, -46,
        -46, -46, -46, -46, -46,  -3, -46, -46,   2,  25,
          2,  72,   2, -46,  28, -46, -46,   6,  17,  16,
        -46,  17,   2, -46, -46, -46,  50, -46, -46, -46,
        -46,  -3,  57, -46,  39,   6,  47,  47, -46,  24,
         38, -46, -46, -46, -46, -46,  47, -46, -46,  45,
          5, -46,  -3,   2, -46,  -3,  -3, -46, -46,  36,
        -46, -46,  70,  68, -46,   2,   2, -46, -46, -46,
          2,  73,  82,  74, -46,   5, -46,  -3, -46, -46,
        -46, -46, -46, -46,  57,  -3,  -3,  -3, -46,  89,
        -46, -46, -46,  57, -46, -46, -46, -46, -46,  77,
        -46,
    ],
    defact = [
         3,  0,  1, 18,  0,  0,  0, 16, 17,  2,
         4,  0,  0,  0, 61,  0,  0,  0, 19, 21,
        22, 23, 24,  9, 20, 14,  0, 54,  8, 25,
        12, 28, 26, 29,  5, 49, 32, 30, 34,  0,
        34,  0,  0, 78,  0, 79, 62,  0,  0,  0,
        74,  0, 34, 46, 47, 55,  0, 27, 44, 45,
        35, 49,  0, 70,  0,  0,  0,  0, 72,  0,
        49, 59, 63, 64, 15, 60,  0, 61, 66,  0,
        53, 77, 49, 34, 73, 49, 49, 48, 13, 40,
        36, 43, 37,  0, 68, 34, 34, 31, 71,  6,
        34,  0,  0,  0,  7, 52, 75, 49, 76, 11,
        41, 38, 39, 33,  0, 49, 49, 49, 57,  0,
        58, 65, 50,  0, 10, 42, 67, 69, 56,  0,
        51,
    ],
    pgoto = [
        -46, -46, -46, -24,   0, -31, -46, -46, -46, -46,
        -46, -33,   1, -11, -46, -37,  42, -22, -46,  -1,
        -45,  -4,  48, -46, -46,  46, -46,  51, -34, -46,
        -46, -46,  60, -46, -46,  81, -46,
    ],
    defgoto = [
         0,   1,  9, 10,  47, 12, 13, 14, 15, 16,
        17,  34, 37, 38,  39, 61, 62, 91, 92, 93,
        57,  58, 59, 80, 104, 28, 75, 41, 48, 77,
        78, 102, 68, 69,  49, 50, 51,
    ],
    table = [
         27,  11,  40,  70,  42,  67,  52,  76,  66,  31,
         32,  53,  35,  29,  81,  86,  88,  43,  30,  44,
         31,  60,  26,  56,  55,  63,  63,  64,  64,  45,
         26,  54,  94,  18,  46,  67,  33, 106,  66,  65,
        108, 109,  46,  46,  18,  83, 107,  33,  35,  82,
         31, 110,  85,  97,  87,  95,  96,  24, 115, 116,
         89,  90, 124, 117,  56, 100,  35,  76, 103,  65,
        126, 127, 128,  71,  71,  36,  27,  33, 121,  72,
         72,  73,  73,   3,  79, 119, 111, 112, 113, 114,
         46,  46, 125,   7, 122, 123,  20, 130, 114,  74,
        118,  55,   2,   3,   8,   4,   5,  24,  43, 120,
         44,  25,   6,   7,  18,  19,  20,  21,  99,   0,
         45,  22, 129,  23,   8,  46, 105,  24, 101,  98,
         84,  25,   0,   0,  26,
    ],
    check = [
          4,   1,  13,  40, 15, 39, 17,  41,  39,  3,
          4,   4,  11,  18, 47, 52, 61,   1,   4,  3,
          3,  19,  25,  26, 28,  1,  1,   3,   3, 13,
         25,  24,  65,   5, 18, 69, 30,  82,  69, 39,
         85,  86,  18,  18,  5, 29, 83,  30,  47, 48,
          3,  15,  51,  29,  4, 66, 67,  18,  95, 96,
          3,   4, 107, 100, 26, 76, 65, 101,  23, 69,
        115, 116, 117,   1,  1, 28, 80,  30, 102,  7,
          7,   9,   9,   1, 42,  3, 16,  17,  20, 21,
         18,  18, 114,  11, 20, 21,  7,  20,  21, 27,
         27, 105,   0,   1, 22,  3,  4,  18,   1, 27,
          3,  22,  10,  11,  5,  6,  7,   8,  70, -1,
         13,  12, 123,  14, 22, 18, 80,  18,  77, 69,
         49,  22,  -1,  -1, 25,
    ],
    r1 = [
         0, 31, 32, 32, 33, 33, 33, 33, 33, 33,
        33, 33, 33, 34, 34, 34, 34, 34, 34, 35,
        36, 37, 38, 39, 40, 41, 42, 42, 43, 43,
        44, 44, 45, 46, 46, 47, 48, 48, 48, 48,
        49, 49, 50, 50, 51, 51, 52, 52, 53, 53,
        54, 54, 55, 55, 56, 56, 57, 57, 57, 57,
        58, 58, 59, 60, 61, 62, 62, 63, 63, 63,
        63, 64, 64, 65, 65, 66, 66, 66, 66, 67,
    ],
    r2 = [
        0, 2, 2, 0, 1, 2, 4, 4, 2, 2,
        5, 4, 2, 4, 2, 3, 1, 1, 1, 2,
        2, 2, 2, 2, 2, 2, 1, 2, 1, 1,
        1, 3, 1, 3, 0, 1, 1, 1, 2, 2,
        1, 2, 3, 1, 1, 1, 2, 2, 2, 0,
        3, 5, 1, 0, 1, 2, 4, 3, 3, 1,
        2, 0, 1, 1, 1, 2, 0, 4, 2, 4,
        1, 2, 1, 2, 1, 3, 3, 2, 1, 1,
    ],
    stos = [
         0, 32,  0,  1,  3,  4, 10, 11, 22, 33,
        34, 35, 36, 37, 38, 39, 40, 41,  5,  6,
         7,  8, 12, 14, 18, 22, 25, 52, 56, 18,
         4,  3,  4, 30, 42, 43, 28, 43, 44, 45,
        44, 58, 44,  1,  3, 13, 18, 35, 59, 65,
        66, 67, 44,  4, 24, 52, 26, 51, 52, 53,
        19, 46, 47,  1,  3, 35, 36, 59, 63, 64,
        46,  1,  7,  9, 27, 57, 59, 60, 61, 47,
        54, 42, 43, 29, 66, 43, 46,  4, 51,  3,
         4, 48, 49, 50, 42, 44, 44, 29, 63, 53,
        44, 58, 62, 23, 55, 56, 51, 46, 51, 51,
        15, 16, 17, 20, 21, 46, 46, 46, 27,  3,
        27, 34, 20, 21, 51, 48, 51, 51, 51, 50,
        20,
    ],
    tname = [
        "\"end of file\"", "error", "\"invalid token\"", "SYMBOL", "INTEGER",
        "CEQ", "EEQ", "EQB", "SEQ", "SLASHB", "BAT", "DOTDOT", "QCURLY",
        "ATEQ", "QSLASH", "QUEST", "PLUSSES", "MINUSES", "EQ", "LPAREN",
        "RPAREN", "COMMA", "SLASH", "STAR", "DOT", "AT", "PCNT", "RBRACK",
        "LCURLY", "RCURLY", "PRIMTYPE", "$accept", "layout", "statement",
        "group_item", "paramdef", "arraydef", "typedef", "listdef",
        "uarraydef", "rootdef", "pointee", "parameter", "basetype", "type",
        "struct", "shape", "shapedef", "dimension", "symbolq", "dimensions",
        "location", "address", "alignment", "ushape", "uaddress",
        "address_list", "list_item", "list_items", "anonarray", "anonlist",
        "anongroup", "group_items", "member", "members", "root_params",
        "root_param", "anonloc", "",
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
def rule(group_item):
    """4 statement: group_item"""

@rules(range(-2, 0), "def_param")
def rule(name, parameter):
    """5 statement: paramdef parameter"""

@rules(range(-4, 0), "def_type")
def rule(name, atype, shape, alignment):
    """6 statement: typedef type shape alignment"""

@rules(range(-4, 0), "def_array")
def rule(name, atype, shape, address):
    """7 statement: uarraydef type ushape uaddress"""

@rules(range(-2, 0), "extend_array")
def rule(name, address_list):
    """8 statement: SYMBOL address_list"""

@rules([-2], "cdroot")
def rule(name):
    """9 statement: SYMBOL QSLASH"""

@rules(range(-2, 0), "close_rootdef")
def rule(shape, location):
    """10 statement: rootdef root_params RCURLY shape location"""

@rules(range(-4, 0), "def_array")
def rule(address, atype, shape, location):
    """11 statement: pointee type shape location"""

@rules([-1], "set_address")
def rule(address):
    """12 statement: BAT INTEGER"""

@rules(range(-4, 0), "def_array")
def rule(name, atype, shape, location):
    """13 group_item: arraydef type shape location"""

@rules([-2], "cd")
def rule(name):
    """14 group_item: SYMBOL SLASH"""

@rules([], "close_list")
def rule():
    """15 group_item: listdef list_items RBRACK"""

@rules([], "cdup")
def rule():
    """16 group_item: DOTDOT"""

@rules([], "cdtop")
def rule():
    """17 group_item: SLASH"""

@rules([-1], "error18")
def rule(error):
    """18 group_item: error"""

@rules([-2])
def rule(name):
    """19 paramdef: SYMBOL CEQ"""
    return name

@rules([-2])
def rule(name):
    """20 arraydef: SYMBOL EQ"""
    return name

@rules([-2])
def rule(name):
    """21 typedef: SYMBOL EEQ"""
    return name

@rules([-2])
def rule(name):
    """22 listdef: SYMBOL EQB"""
    return name

@rules([-2])
def rule(name):
    """23 uarraydef: SYMBOL SEQ"""
    return name

@rules([-2])
def rule(name):
    """24 rootdef: SYMBOL QCURLY"""
    return name

@rules([-2])
def rule(address):
    """25 pointee: INTEGER EQ"""
    return address

@rules([-1], "make_param")
def rule(value):
    """26 parameter: INTEGER"""

@rules(range(-2, 0), "make_param")
def rule(atype, location):
    """27 parameter: basetype location"""

@rules([-1], "make_atype")
def rule():
    """28 basetype: SYMBOL"""

@rules([-1], "make_atype")
def rule():
    """29 basetype: PRIMTYPE"""

@rules([-1])
def rule(basetype):
    """30 type: basetype"""
    return basetype

@rules([], "close_struct")
def rule():
    """31 type: struct members RCURLY"""

@rules([], "open_struct")
def rule():
    """32 struct: LCURLY"""

@rules([], "close_shape")
def rule():
    """33 shape: shapedef dimensions RPAREN"""

@rules([])
def rule():
    """34 shape: <empty>"""

@rules([], "open_shape")
def rule():
    """35 shapedef: LPAREN"""

@rules([-1], "set_dim")
def rule(value):
    """36 dimension: INTEGER"""

@rules([-1])
def rule():
    """37 dimension: symbolq"""

@rules([])
def rule():
    """38 dimension: symbolq PLUSSES"""

@rules([])
def rule():
    """39 dimension: symbolq MINUSES"""

@rules([])
def rule():
    """40 symbolq: SYMBOL"""

@rules([])
def rule():
    """41 symbolq: SYMBOL QUEST"""

@rules([])
def rule():
    """42 dimensions: dimensions COMMA dimension"""

@rules([])
def rule():
    """43 dimensions: dimension"""

@rules([])
def rule():
    """44 location: address"""

@rules([])
def rule():
    """45 location: alignment"""

@rules([])
def rule():
    """46 address: AT INTEGER"""

@rules([])
def rule():
    """47 address: AT DOT"""

@rules([])
def rule():
    """48 alignment: PCNT INTEGER"""

@rules([])
def rule():
    """49 alignment: <empty>"""

@rules([])
def rule():
    """50 ushape: shapedef STAR RPAREN"""

@rules([])
def rule():
    """51 ushape: shapedef STAR COMMA dimensions RPAREN"""

@rules([])
def rule():
    """52 uaddress: address_list"""

@rules([])
def rule():
    """53 uaddress: <empty>"""

@rules([])
def rule():
    """54 address_list: address"""

@rules([])
def rule():
    """55 address_list: address_list address"""

@rules([])
def rule():
    """56 list_item: anonarray type shape location"""

@rules([])
def rule():
    """57 list_item: anonlist list_items RBRACK"""

@rules([])
def rule():
    """58 list_item: anongroup group_items RBRACK"""

@rules([])
def rule():
    """59 list_item: error"""

@rules([])
def rule():
    """60 list_items: list_items list_item"""

@rules([])
def rule():
    """61 list_items: <empty>"""

@rules([])
def rule():
    """62 anonarray: EQ"""

@rules([])
def rule():
    """63 anonlist: EQB"""

@rules([])
def rule():
    """64 anongroup: SLASHB"""

@rules([])
def rule():
    """65 group_items: group_items group_item"""

@rules([])
def rule():
    """66 group_items: <empty>"""

@rules([])
def rule():
    """67 member: arraydef type shape location"""

@rules([])
def rule():
    """68 member: paramdef parameter"""

@rules([])
def rule():
    """69 member: anonarray type shape location"""

@rules([])
def rule():
    """70 member: error"""

@rules([])
def rule():
    """71 members: members member"""

@rules([])
def rule():
    """72 members: member"""

@rules([])
def rule():
    """73 root_params: root_params root_param"""

@rules([])
def rule():
    """74 root_params: root_param"""

@rules([])
def rule():
    """75 root_param: anonarray basetype location"""

@rules([])
def rule():
    """76 root_param: anonloc basetype location"""

@rules([])
def rule():
    """77 root_param: paramdef parameter"""

@rules([])
def rule():
    """78 root_param: error"""

@rules([])
def rule():
    """79 anonloc: ATEQ"""
del rule
