tables = dict(
    pact = [
        -41,  28, -41, -41,  98,  -8,  32, -41, -41, -41,
        -41, -41,  23,  15,  15, -41,  15,  82,  15, -41,
        -41, -41, -41, -41, -41, -41, -41,  64, -41,  21,
        -41, -41, -41, -41, -41, -41, -11, -41, -41,  41,
        108,  41,  71,  41, -41, 103, -41, -41,  23,  31,
          7, -41,  31,  41, -41, -41, -41,  65, -41, -41,
        -41, -41, -11,  12, -41,  46,  23,  15,  15, -41,
         20,  93, -41, -41, -41, -41, -41,  15, -41, -41,
         99,  21, -41, -11,  41, -41, -11, -11, -41, -41,
         75, -41, -41,  74, -41,  41,  41, -41, -41, -41,
         41,  72,  81,  94, -41,  21, -41, -11, -41, -41,
        -41, -41, -41,  12, -11, -11, -11, -41,  79, -41,
        -41, -41,  12, -41, -41, -41, -41, -41,  97, -41,
    ],
    defact = [
         3,  0,  1, 19,  0,  0,  0, 17, 18, 13,
         2,  4,  0,  0,  0, 60,  0,  0,  0, 20,
        22, 23, 24, 25,  9, 21, 15,  0, 53,  8,
        26, 12, 29, 27, 30,  5, 48, 33, 31, 35,
         0, 35,  0,  0, 77,  0, 78, 61,  0,  0,
         0, 73,  0, 35, 45, 46, 54,  0, 28, 43,
        44, 36, 48,  0, 69,  0,  0,  0,  0, 71,
         0, 48, 58, 62, 63, 16, 59,  0, 60, 65,
         0, 52, 76, 48, 35, 72, 48, 48, 47, 14,
        38, 37, 42,  0, 67, 35, 35, 32, 70,  6,
        35,  0,  0,  0,  7, 51, 74, 48, 75, 11,
        39, 40, 34,  0, 48, 48, 48, 56,  0, 57,
        64, 49,  0, 10, 41, 66, 68, 55,  0, 50,
    ],
    pgoto = [
        -41, -41, -41,  18,   0, -29, -41, -41, -41, -41,
        -41, -36,   5, -12, -41, -34,  80,  11,   4, -40,
         -4,  56, -41, -41,  47, -41,  51, -37, -41, -41,
        -41,  60, -41, -41,  83, -41,
    ],
    defgoto = [
          0,  1, 10,  11, 48, 13, 14, 15, 16, 17,
         18, 35, 38,  39, 40, 62, 63, 92, 93, 58,
         59, 60, 81, 104, 29, 76, 42, 49, 78, 79,
        102, 69, 70,  50, 51, 52,
    ],
    table = [
         28,  12,  41,  68,  43,  77,  53,  71,  44,  30,
         45,  67,  82,  27,  57,  90,  91,  36,  32,  87,
         46,  64,  89,  65,  47,  56,  32,  33,   2,   3,
         94,   4,   5,  68,  32,  84,  31,  47,   6,   7,
         66,  67,  37, 106,  34,  27, 108, 109,  97,   8,
        107,  19,  34,  36,  83,  95,  96,  86,   9,  61,
         34, 114, 115,  25,  77, 100, 116, 123,  54,  88,
         66,  36,  72,  72, 125, 126, 127,  28,  73,  73,
         74,  74,   3,  44, 118,  45,  21,  55,  47,  47,
        110, 111,   7, 112, 113,  46,  25,  75, 117,  47,
         26,  56,   8,  19,  20,  21,  22, 119,  19,  64,
         23,  65,  24, 121, 122,  25, 129, 113,  57,  26,
        120, 103,  27,  80, 124,  47, 128,  99, 105, 101,
         98,   0,   0,  85,
    ],
    check = [
          4,   1, 14, 40,  16,  42,  18,  41,  1, 17,
          3,  40, 48, 24,  25,   3,   4,  12,  3, 53,
         13,   1, 62,  3,  17,  29,   3,   4,  0,  1,
         66,   3,  4, 70,   3,  28,   4,  17, 10, 11,
         40,  70, 27, 83,  29,  24,  86,  87, 28, 21,
         84,   5, 29, 48,  49,  67,  68,  52, 30, 18,
         29,  95, 96, 17, 101,  77, 100, 107,  4,  4,
         70,  66,  1,  1, 114, 115, 116,  81,  7,  7,
          9,   9,  1,  1,   3,   3,   7,  23, 17, 17,
         15,  16, 11, 19,  20,  13,  17,  26, 26, 17,
         21, 105, 21,  5,   6,   7,   8,  26,  5,  1,
         12,   3, 14, 19,  20,  17,  19,  20, 25, 21,
        102,  22, 24, 43, 113,  17, 122,  71, 81, 78,
         70,  -1, -1, 50,
    ],
    r1 = [
         0, 31, 32, 32, 33, 33, 33, 33, 33, 33,
        33, 33, 33, 33, 34, 34, 34, 34, 34, 34,
        35, 36, 37, 38, 39, 40, 41, 42, 42, 43,
        43, 44, 44, 45, 46, 46, 47, 48, 48, 48,
        48, 49, 49, 50, 50, 51, 51, 52, 52, 53,
        53, 54, 54, 55, 55, 56, 56, 56, 56, 57,
        57, 58, 59, 60, 61, 61, 62, 62, 62, 62,
        63, 63, 64, 64, 65, 65, 65, 65, 66,
    ],
    r2 = [
        0, 2, 2, 0, 1, 2, 4, 4, 2, 2,
        5, 4, 2, 1, 4, 2, 3, 1, 1, 1,
        2, 2, 2, 2, 2, 2, 2, 1, 2, 1,
        1, 1, 3, 1, 3, 0, 1, 1, 1, 2,
        2, 3, 1, 1, 1, 2, 2, 2, 0, 3,
        5, 1, 0, 1, 2, 4, 3, 3, 1, 2,
        0, 1, 1, 1, 2, 0, 4, 2, 4, 1,
        2, 1, 2, 1, 3, 3, 2, 1, 1,
    ],
    stos = [
         0, 32,  0,  1,  3,  4, 10, 11, 21, 30,
        33, 34, 35, 36, 37, 38, 39, 40, 41,  5,
         6,  7,  8, 12, 14, 17, 21, 24, 51, 55,
        17,  4,  3,  4, 29, 42, 43, 27, 43, 44,
        45, 44, 57, 44,  1,  3, 13, 17, 35, 58,
        64, 65, 66, 44,  4, 23, 51, 25, 50, 51,
        52, 18, 46, 47,  1,  3, 35, 36, 58, 62,
        63, 46,  1,  7,  9, 26, 56, 58, 59, 60,
        47, 53, 42, 43, 28, 65, 43, 46,  4, 50,
         3,  4, 48, 49, 42, 44, 44, 28, 62, 52,
        44, 57, 61, 22, 54, 55, 50, 46, 50, 50,
        15, 16, 19, 20, 46, 46, 46, 26,  3, 26,
        34, 19, 20, 50, 48, 50, 50, 50, 49, 19,
    ],
    tname = [
        "\"end of file\"", "error", "\"invalid token\"", "SYMBOL", "INTEGER",
        "CEQ", "EEQ", "EQB", "SEQ", "SLASHB", "BAT", "DOTDOT", "QCURLY",
        "ATEQ", "QSLASH", "PLUSSES", "MINUSES", "EQ", "LPAREN", "RPAREN",
        "COMMA", "SLASH", "STAR", "DOT", "AT", "PCNT", "RBRACK", "LCURLY",
        "RCURLY", "PRIMTYPE", "SPECIAL", "$accept", "layout", "statement",
        "group_item", "paramdef", "arraydef", "typedef", "listdef",
        "uarraydef", "rootdef", "pointee", "parameter", "basetype", "type",
        "struct", "shape", "shapedef", "dimension", "dimensions", "location",
        "address", "alignment", "ushape", "uaddress", "address_list",
        "list_item", "list_items", "anonarray", "anonlist", "anongroup",
        "group_items", "member", "members", "root_params", "root_param",
        "anonloc", "",
    ],
    final = 2)


class FunctionList(list):
    def __call__(self, f)
        self.append(f)
        return f

rules = FunctionList()


@rules  # 0 $error?
def _rule(args):
    pass


@rules  # 1 $accept: . $end
def _rule(args):
    pass


@rules  # 2 layout: layout statement
def _rule(args):
    pass


@rules  # 3 layout: <empty>
def _rule(args):
    pass


@rules  # 4 statement: group_item
def _rule(args):
    pass


@rules  # 5 statement: paramdef parameter
def _rule(args):
    layout.def_param(*args)


@rules  # 6 statement: typedef type shape alignment
def _rule(args):
    layout.def_type(*args)


@rules  # 7 statement: uarraydef type ushape uaddress
def _rule(args):
    layout.def_uarray(*args)


@rules  # 8 statement: SYMBOL address_list
def _rule(args):
    layout.uextend(*args)


@rules  # 9 statement: SYMBOL QSLASH
def _rule(args):
    layout.def_rgroup(args[0])


@rules  # 10 statement: rootdef root_params RCURLY shape location
def _rule(args):
    rootdef, root_params, _, shape, location = args
    layout.def_root(rootdef, root_params, shape, location)


@rules  # 11 statement: pointee type shape location
def _rule(args):
    layout.def_pointee(*args)


@rules  # 12 statement: BAT INTEGER
def _rule(args):
    layout.set_address(args[1])


@rules  # 13 statement: SPECIAL
def _rule(args):
    pass


@rules  # 14 group_item: arraydef type shape location
def _rule(args):
    layout.def_array(*args)


@rules  # 15 group_item: SYMBOL SLASH
def _rule(args):
    layout.change_group(args[0])


@rules  # 16 group_item: listdef list_items RBRACK
def _rule(args):
    return layout.pop_list()


@rules  # 17 group_item: DOTDOT
def _rule(args):
    layout.change_group("..")


@rules  # 18 group_item: SLASH
def _rule(args):
    layout.change_group("/")


@rules  # 19 group_item: error
def _rule(args):
    return layout.error(*args)


@rules  # 20 paramdef: SYMBOL CEQ
def _rule(args):
    return layout.push_param(args[0])


@rules  # 21 arraydef: SYMBOL EQ
def _rule(args):
    return layout.push_array(args[0])


@rules  # 22 typedef: SYMBOL EEQ
def _rule(args):
    return layout.push_typedef(args[0])


@rules  # 23 listdef: SYMBOL EQB
def _rule(args):
    return layout.push_list(args[0])


@rules  # 24 uarraydef: SYMBOL SEQ
def _rule(args):
    return layout.push_uarray(args[0])


@rules  # 25 rootdef: SYMBOL QCURLY
def _rule(args):
    return layout.push_root(args[0])


@rules  # 26 pointee: INTEGER EQ
def _rule(args):
    return layout.push_pointee(args[0])


@rules  # 27 parameter: INTEGER
def _rule(args):
    return layout.param_value(args[0])


@rules  # 28 parameter: basetype location
def _rule(args):
    return layout.param_value(*args)


@rules  # 29 basetype: SYMBOL
def _rule(args):
    return layout.check_basetype(args[0])


@rules  # 30 basetype: PRIMTYPE
def _rule(args):
    return args[0]


@rules  # 31 type: basetype
def _rule(args):
    return args[0]


@rules  # 32 type: struct members RCURLY
def _rule(args):
    return args[0]


@rules  # 33 struct: LCURLY
def _rule(args):
    return layout.push_struct()


@rules  # 34 shape: shapedef dimensions RPAREN
def _rule(args):
    return layout.pop_shape()


@rules  # 35 shape: <empty>
def _rule(args):
    pass


@rules  # 36 shapedef: LPAREN
def _rule(args):
    return layout.push_shape()


@rules  # 37 dimension: INTEGER
def _rule(args):
    return layout.append_shape(args[0])


@rules  # 38 dimension: SYMBOL
def _rule(args):
    return layout.append_shape(args[0], 0)


@rules  # 39 dimension: SYMBOL PLUSSES
def _rule(args):
    return layout.append_shape(args[0], args[1])


@rules  # 40 dimension: SYMBOL MINUSES
def _rule(args):
    return layout.append_shape(args[0], -args[1])


@rules  # 41 dimensions: dimensions COMMA dimension
def _rule(args):
    pass


@rules  # 42 dimensions: dimension
def _rule(args):
    pass


@rules  # 43 location: address
def _rule(args):
    return args[0]


@rules  # 44 location: alignment
def _rule(args):
    return args[0]


@rules  # 45 address: AT INTEGER
def _rule(args):
    return layout.address(args[1])


@rules  # 46 address: AT DOT
def _rule(args):
    return layout.address(args[1], 0)


@rules  # 47 alignment: PCNT INTEGER
def _rule(args):
    return layout.address(args[1], 1)


@rules  # 48 alignment: <empty>
def _rule(args):
    pass


@rules  # 49 ushape: shapedef STAR RPAREN
def _rule(args):
    return layout.push_shape(True)


@rules  # 50 ushape: shapedef STAR COMMA dimensions RPAREN
def _rule(args):
    return layout.pop_shape()


@rules  # 51 uaddress: address_list
def _rule(args):
    return args[0]


@rules  # 52 uaddress: <empty>
def _rule(args):
    pass


@rules  # 53 address_list: address
def _rule(args):
    return [args[0]]


@rules  # 54 address_list: address_list address
def _rule(args):
    return args[0].append(args[1])


@rules  # 55 list_item: anonarray type shape location
def _rule(args):
    layout.def_array(*args)


@rules  # 56 list_item: anonlist list_items RBRACK
def _rule(args):
    return layout.pop_list()


@rules  # 57 list_item: anongroup group_items RBRACK
def _rule(args):
    return layout.change_group("/")


@rules  # 58 list_item: error
def _rule(args):
    return layout.error(*args)


@rules  # 59 list_items: list_items list_item
def _rule(args):
    pass


@rules  # 60 list_items: <empty>
def _rule(args):
    pass


@rules  # 61 anonarray: EQ
def _rule(args):
    return layout.push_array(None)


@rules  # 62 anonlist: EQB
def _rule(args):
    return layout.push_list(None)


@rules  # 63 anongroup: SLASHB
def _rule(args):
    return layout.change_group(None)


@rules  # 64 group_items: group_items group_item
def _rule(args):
    pass


@rules  # 65 group_items: <empty>
def _rule(args):
    pass


@rules  # 66 member: arraydef type shape location
def _rule(args):
    layout.def_array(*args)


@rules  # 67 member: paramdef parameter
def _rule(args):
    layout.def_param(*args)


@rules  # 68 member: anonarray type shape location
def _rule(args):
    layout.def_array(*args)


@rules  # 69 member: error
def _rule(args):
    return layout.error(*args)


@rules  # 70 members: members member
def _rule(args):
    pass


@rules  # 71 members: member
def _rule(args):
    pass


@rules  # 72 root_params: root_params root_param
def _rule(args):
    pass


@rules  # 73 root_params: root_param
def _rule(args):
    pass


@rules  # 74 root_param: anonarray basetype location
def _rule(args):
    layout.def_array(None, args[1], None, args[2])


@rules  # 75 root_param: anonloc basetype location
def _rule(args):
    layout.def_array(Ellipsis, args[1], None, args[2])


@rules  # 76 root_param: paramdef parameter
def _rule(args):
    layout.def_param(*args)


@rules  # 77 root_param: error
def _rule(args):
    return layout.error(*args)


@rules  # 78 anonloc: ATEQ
def _rule(args):
    return layout.push_array(Ellipsis)
