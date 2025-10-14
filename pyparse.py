"""Parse a Dudley layout from a file, stream, or str

A file automatically serializes whatever it contains by address.  Hence at the
lowest level, file or stream contents must be a sequence of type-shape pairs
describing how to decode the bytes of the stream into n-dimensional arrays of
numbers or strings of text.  The fastest way to read or write all the data is
inevitably in this storage order.  Dudley assumes that, once written, the
structure of a file - its low level sequence of type-shape pairs - will never
change.  This is by far the most common use case for binary data files
associated with scientific data or simulation states.  Note that general
database files are designed for much broader use, in which data may be
removed or structurally altered.  Dudley does not handle such cases, nor does
it attempt to build indexes to search file contents as you would expect in
a database file.

However, Dudley does support grouping data arrays as either anonymous lists or
as dictionaries ("dicts") of named variables, and these groupings may contain
other groupings in addition to arrays.  These lists and dicts match the basic
organizing tools in any scientific programming language.  Dudley also supports
arrays of structured data analogous to C structs in addition to primitive
numeric and text data types.  Finally, Dudley supports symbolic names for
array dimensions.  Scientific data archives frequently contain many arrays
which share common dimensions, and the only difference between many data files
is the particular values of these dimensions.  Symbolic dimension names, or
integer valued parameters, enable a single Dudley description to apply to
many different files or streams.

The low level sequence of objects in a file includes these organizational
elements as well as the type-shape pairs, so there are a total of five
different kinds of objects in the Dudley low-level list:

1. DArray (datatype, shape, alignment)
2. DDict (named objects)
3. DList (anonymous objects)
4. DParam (array dimension)
   a. Static (fixed integer value)
   b. Dynamic (scalar integer stored in stream)
5. DType (array data type)
   a. Compound (sequence of named DArray members - a C struct)
   b. Typedef (single anonymous DArray)

The index of each of these objects in the low-level list is how other objects
refer to it.  There are two kinds of object Dudley requires which do not
correspond to any item in the low-level list: primitive data types and
non-parametrized array dimensions.  Since the index representing any the other
kinds of object are non-negative, negative integers can be used for these
special cases.  An object's index in the main list thus serves as its id.

Parametrized array dimensions are indicated by the id of the parameter, which
must be greater than zero, since id zero is the root dict.  Since no actual
dimension can be less than zero, the negative of any non-parametrized dimension
can therefore be distinguished from a parameter id, and that is what Dudley
uses in array shapes.

Dudley recognizes 19 primitive data types:
u1 u2 u4 u8    unsigned integers (1, 2, 4, or 8 byte)
i1 i2 i4 i8    signed integers (1, 2, 4, or 8 byte)
b1             boolean (1 byte)
   f2 f4 f8    IEEE 754 floats (2, 4, or 8 byte)
S1             ASCII, CP1252, or Latin1 character (1 byte)
   c4 c8 c16   IEEE 754 complex (2, 4, or 8 byte re,im pairs)
U1 U2 U4       UTF-8, UTF-16, or UTF-32 character (1, 2, or 4 byte)

Bigger floating point types - f12 or f16 - are not in this list because they
may not be present or have a standard format for some numpy implementations.
Note that the S and U suffixes are bytes per character, unlike in the numpy
array protocol - the number of characters in the string is the fastest varying
dimension in Dudley.

Addresses are kept in a parallel list to the items to allow multiple streams
to share the layout.  Dynamic parameter values are also stored in a separate
list, as are document strings and item attributes.

DDict: parent, name itemid map, paramid map, typeid map,  where map[name]->id
DList: parent, name, items[i]->id
DData: parent, name, typeid, align, shape
DParam: parent, name, value   (static)
        parent, name, typeid, align, pid=dynamic parameter index   (dynamic)
    address, if any, kept in separate global address[id] list
DType: parent, name, item_map[name]->id   (compound)
       parent, name, dtype, align, shape   (typedef)

A higher level API relies on temporary DItem objects which have both the items
list and the index into items.
"""
from __future__ import absolute_import

import sys
from io import StringIO

PY2 = sys.version_info < (3,)
if PY2:
    from collections import OrderedDict as dict

# JSON.parse, JSON.stringify in javascript
from ast import literal_eval  # literal_eval() is inverse of str.repr()


D_PRIM, D_DATA, DPARAM, D_DICT, D_LIST, D_TYPE = 0, 1, 2, 3, 4, 5


class DPrim(object):
    """A primitive datatype.  There are exactly 5 + 14*3 = 47 instances:

    Five single byte primitives for which the order is | (same as < or >):
    `|u1`, `|i1`, `|b1`, `|S1`, and `|U1`, respectively unsigned and signed
    integers, boolean, ASCII (or CP1252 or Latin1) character, or unicode
    UTF-8 byte.

    There are also five kinds of multibyte data:`u` for unsigned integers, `i`
    for signed integers (two's complement), `f` for floating point (IEEE 754),
    `c` for complex (pair of floats), and `U` for unicode (UTF-16 or UTF-32).

    The multibyte types each have three possible byte orderings: `|` means
    indeterminate (not quite the same meaning as in the numpy array protocol),
    '<' means least significant byte first (little-endian), and `>` means
    most significant byte first (big-endian).
    
    There are three different byte sizes for each: 2, 4, or 8 bytes per value
    (but for complex values these are a total of 4, 8, or 16 bytes per value), except for the `U` kind, which has only 2 and 4 byte sizes.

    Dudley numbers these primitives from 1 to 50 as follows::

         1  |u1  |i1  |b1  |S1  |U1
         6  |u2  |i2  |f2  |c4  |U2
        11  |u4  |i4  |f4  |c8  |U4
        16  |u8  |i8  |f8  |c16  -
        21  <u2  <i2  <f2  <c4  <U2
        26  <u4  <i4  <f4  <c8  <U4
        31  <u8  <i8  <f8  <c16  -
        36  >u2  >i2  >f2  >c4  >U2
        41  >u4  >i4  >f4  >c8  >U4
        46  >u8  >i8  >f8  >c16  -

    With this numbering, an indeterminate type 5 < datatype < 21 can be
    resolved to little-endian by adding 15, or to big-endian by adding 30.
    Type numbers 20, 35, and 50 are reserved for a quad precision `f16`
    floating point type, which is excluded because it currently lacks
    consistent hardware support (although the same could be said of `f2`).
    In particular, numpy implementations often support `f12` instead of `f16`.

    Dudley also uses type number 0 for the empty compound `{}`, which means
    `None` in python or `null` in javascript/JASON and takes no space in the
    data stream.
    """
    itype = D_PRIM

    def __init__(self, name):
        self.parent = None
        self.name = name
        self.order = name[0]
        self.kind = name[1]  # u i f c S U b
        self.size = int(name[2:])  # bytes per value
        self.align = self.size  # default alignment is size
        if self.kind == "c":
            self.align /= 2  # except for complex, which is same as float
        self.members = None  # for compatibility with DType


class DLayout(list):
    def __init__(self, stream=None, ignore=0):
        super(DLayout, self).__init__((DDict(None)))  # self[0] is root dict
        self.params = []  # params[pid] -> id of dynamic parameter pid
        # Stream instances with this layout will have two lists of the same
        # length as these: a list of addresses the same length as self, and
        # a list of dynamic parameter values the same length as params.
        # Optional lists the same length as items are also created if the
        # layout contains any attributes or documentatation.
        self.atts = None  # atts[id] -> {attributes of item}
        self.docs = None  # docs[id] -> [docstrings for item]
        self.current = 0  # initially, root is the current container
        if stream is not None:
            self.parse(stream, ignore)

    # prim[-typeid] -> DPrim for that type
    prim = [None] + [DPrim(t) for t in ("|u1", "|i1", "|b1", "|S1", "|U1")]
    prim += [DPrim(t) for t in ("|u2", "|i2", "|f2", "|c4", "|U2")]
    prim += [DPrim(t) for t in ("|u4", "|i4", "|f4", "|c8", "|U4")]
    prim += [DPrim(t) for t in ("|u8", "|i8", "|f8", "|c16")] + [None]
    prim += [DPrim(t) for t in ("<u2", "<i2", "<f2", "<c4", "<U2")]
    prim += [DPrim(t) for t in ("<u4", "<i4", "<f4", "<c8", "<U4")]
    prim += [DPrim(t) for t in ("<u8", "<i8", "<f8", "<c16")] + [None]
    prim += [DPrim(t) for t in (">u2", ">i2", ">f2", ">c4", ">U2")]
    prim += [DPrim(t) for t in (">u4", ">i4", ">f4", ">c8", ">U4")]
    prim += [DPrim(t) for t in (">u8", ">i8", ">f8", ">c16")] + [None, None]
    primid = {name: -i for i, name in enumerate(prim) if name}

    def resolve_type(self, idtype):
        t = self.prim[-idtype] if idtype <= 0 else self.items[idtype]
        return t

    def resolve_shape(self, shape):
        pass

    def parse(self, stream, ignore):
        pass


class DData(object):
    __slots__ = "parent", "name", "datatype", "shape", "align", "filter"
    itype = D_DATA

    def __init__(self, parent, name, datatype, shape=None, align=0,
                 filter=None):
        self.parent = parent
        self.name = name
        self.datatype = datatype
        self.shape = shape
        # self.align may hold either alignment or absolute address:
        # If it is an absolute address, align = -2 - address
        # The -2 is chosen so that address -1 can be used to represent
        # an undetermined address or (as yet) non-existent data, like
        # a zero pointer in C.  An address of 0 is a real address, so it
        # cannot be used for this purpose.  Align of 0 means that this
        # data has no special alignmnet, so the alignment is the default
        # for the datatype.
        self.align = align  # if < 0, this is -2-address
        self.filter = filter


class DDict(object):
    __slots__ = "parent", "name", "itemid", "paramid", "typeid"
    itype = D_DICT

    def __init__(self, parent, name=None):
        self.parent = parent
        self.name = name
        self.itemid = {}
        self.paramid = {}
        self.typeid = {}


class DList(list):
    __slots__ = "parent", "name"
    itype = D_LIST

    def __init__(self, parent, name=None):
        self.parent = parent
        self.name = name
        super(DList, self).__init__()


class DParam(object):
    __slots__ = "parent", "name", "datatype", "pid", "align"
    itype = D_PARAM

    def __init__(self, parent, name, datatype, pid, align=0):
        self.parent = parent
        self.name = name
        self.datatype = datatype  # None for static, DType id for dynamic
        self.pid = pid  # If datatype is None, this is static value
        self.align = align  # ignored for static parameter


class DType(object):
    __slots__ = "parent", "name", "members", "align"
    itype = D_TYPE
    # Note: Named types must have a dict as parent.
    # Anonymous types must have the same parent as the (only) array with that
    #   datatype, and that array aill immediately follow them.

    def __init__(self, parent, name=None):
        self.parent = parent
        self.name = name
        # Initialize to unfinished DType, must call DItem.finish_type
        # to set members and align properly.
        self.members = None  # dict for compound, int for typedef (DData id)
        self.align = 0


class DItem(object):
    __slots__ = "layout", "item"
    def __init__(self, layout, item):
        self.layout = layout
        self.item = item

    @property
    def itype(self):
        return self.layout[self.item].itype

    @property
    def root(self):
        return DItem(layout, 0)

    @property
    def parent(self):
        layout = self.layout
        return DItem(layout, layout[self.item].parent)

    @property
    def name(self):
        return self.layout[self.item].name

    @property
    def items(self):
        layout = self.layout
        this = layout[self.item]
        if this.itype == D_DICT:
            return DItems(layout, this.itemid)
        elif this.itype == D_LIST:
            return DElements(layout, this)
        raise TypeError("only dict and list have items")

    @property
    def param(self, name):
        layout = self.layout
        item = layout[self.item]
        while item.itype != D_DICT or name not in item.paramid:
            if not item:
                return None
            item = layout[item.parent]
        return item.paramid[name]

    @property
    def types(self):
        layout = self.layout
        this = layout[self.item]
        if this.itype == D_DICT:
            return DItems(layout, this.typeid)
        raise TypeError("only dict has types")

    @property
    def members(self):
        layout = self.layout
        this = layout[self.item]
        if this.itype == D_TYPE:
            members = this.members
            if isinstance(members, dict):
                return DItems(layout, members)
            elif members is not None:
                return DItem(layout, members)
        raise TypeError("only struct type has members")

    @property
    def datatype(self):
        layout = self.layout
        this = layout[self.item]
        if this.itype not in (D_DATA, D_PARAM):
            return None
        typeid = this.datatype
        if typeid > 0:
            return DItem(layout, typeid)
        return layout.primitives[-typeid]  # What are these objects?

    @property
    def shape(self):
        layout = self.layout
        this = layout[self.item]
        if this.itype != D_DATA or not this.shape:
            return None
        s = ()
        for d in this.shape:  # decode shape
            s += (DItem(layout, d) if d > 0 else -d,)
        return s

    @property
    def align0(self):  # may be 0 if this is data or param
        this = self.layout[self.item]
        if this.itype not in (D_DATA, D_PARAM, D_TYPE):
            return None
        align = this.align
        align = None if align < 0 else align

    @property
    def align(self):   # true alignment, always > 0
        layout = self.layout
        this = layout[self.item]
        if this.itype not in (D_DATA, D_PARAM, D_TYPE):
            return None
        align = this.align
        if align < 0:
            return 1  # absolute address specified
        elif align:
            return align  # alignment specified
        # Otherwise, alignment is inherited from type
        return DItem(layout, this.datatype).datatype.align0

    @property
    def address(self):
        this = self.layout[self.item]
        if this.itype not in (D_DATA, D_PARAM) or this.datatype is None:
            return None
        align = this.align
        return -2 - align if align < 0 else None

    def finish_type(self):
        layout = self.layout
        item = self.item
        this = layout[item]
        first = item + 1
        last = len(layout)
        if last == first + 1 and layout[first].name is None:  # typedef
            this.members = first
            this.align = layout[first].align
        else:  # compound
            members = {}
            align = 0
            for i in range(first, last):
                member = layout[i]
                if member.parent != item or member.itype != D_DATA:
                    continue
                member = DItem(layout, i)
                members[member.name] = i
                a = member.align
                if a > align:
                    align = a
            this.members = members
            this.align = align


class DItems(object):
    __slots__ = "layout", "idmap"
    def __init__(self, layout, idmap):
        self.layout = layout
        self.idmap = idmap

    def __len__(self):
        return len(self.idmap)

    def __getitem__(self, key):
        return DItem(self.layout, self.idmap[key])

    def __contains__(self, key):
        return key in  self.idmap

    def __iter__(self):
        return iter(self.idmap)

    def get(self, key, default=None):
        return DItem(self.layout, self.idmap.get(key, default))

    def items(self):
        layout = self.layout
        itit = self.idmap.items()
        def iteritems():
            for name, item in itit:
                yield name, DItem(layout, item)
        return iteritems()


class DElements(object):
    __slots__ = "layout", "idlist"
    def __init__(self, layout, idlist):
        self.layout = layout
        self.idlist = idlist

    def __len__(self):
        return len(self.idlist)

    def __getitem__(self, index):
        return DItem(self.layout, self.idlist[index])

    def __iter__(self):
        return len(self.idlist)






class DParam(object):
    itype = D_PARAM  # item type

    def __init__(self, layout, item):
        self.layout = layout
        self.item = item


class DDict(object):
    __slots__ = "parent", "itemid", "paramid", "typeid", "names"
    itype = D_DICT  # item type

    def __init__(self, parent):
        self.parent = parent
        self.itemid = {}
        self.names = {}
        self.paramid = self.typeid = None

    def insert(self, layout, name, item):
        itype = item.itype
        id_ = len(layout.items)
        if itype == D_TYPE:
            if not self.typeid:
                self.typeid = {}
            if name in self.typeid:
                raise ValueError("type {} previously declared".format(name))
            self.typeid[name] = id_
        elif itype == D_PARAM:
            if not self.paramid:
                self.paramid = {}
            self.paramid[name] = id_  # possibly replaces previous declaration
        else:
            if name in self.itemid:
                raise ValueError("item {} previously declared".format(name))
            self.itemid[name] = id_
        self.names[id_] = name
        layout.items.append(item)


class DList(object):
    __slots__ = "parent", "itemid"
    itype = D_LIST  # item type

    def __init__(self, parent):
        self.parent = parent
        self.itemid = []

    def insert(self, layout, item):
        if item.itype in (1, 4):
            raise ValueError("cannot insert param or dtype into DList")
        self.itemid.append(len(layout.items))
        layout.items.append(item)


class DType(object):
    __slots__ = "parent", "itemid", "align", "closed"
    itype = D_TYPE  # item type

    def __init__(self, parent):
        self.parent = parent
        self.itemid = None
        self.align = 1
        self.closed = False

    def close(self):
        self.closed = True

    def insert(self, layout, name, item, offset=None):
        if item.itype != D_DATA:
            raise ValueError("can only insert data arrays into DType")
        align = layout.resolve_dtype(item.idtype).align
        id_ = len(layout.items)
        if name is None:
            if self.itemid is not None:
                raise ValueError("anonymous DType member must be only member")
            self.itemid = id_  # this DType is a typedef
            self.align = align
            self.closed = True
        elif self.closed:
            raise ValueError("cannot insert member in closed DType")
        else:
            if not self.itemid:
                self.itemid = {}
            self.itemid[name] = id_
            if align > self.align:
                self.align = align
        layout.items.append(item)


class DLayout(list):
    def __init__(self, filename=None, stream=None, text=None,
                 ignore=0, order="|"):
        super(DLayout, self).__init__()
        self.filename = filename
        self.default_order = order  # default is native order
        self.ignore = ignore  # 1 bit attributes, 2 bit doc comments
        self.attrs = None if ignore & 1 else []
        self.docs = None if ignore & 2 else []
        self.addrs = None  # created only if layout has explicit addresses
        self.skeleton = []
        DDict(self)  # create root dict as skeleton[0]
        if filename is not None:
            with open(filename) as stream:
                self.parse(stream)
        else:
            if text is not None:
                if PY2:
                    if isinstance(text, str):
                        try:
                            text = text.decode("utf-8")
                        except UnicodeDecodeError:
                            text = text.decode("latin1")
                stream = StringIO(text)
            self.parse(stream)

    primitives = set("f2", "f4", "f8", "i1", "i2", "i4", "i8",
                     "u1", "u2", "u4", "u8", "S1", "U1", "U2", "U4",
                     "b1", "c2", "c4", "c8")

    def get_type(self, name):
        dudtype = self.types.get(name)
        if dudtype is not None:
            return dudtype  # already seen this type
        order = name[0]
        if order in "><|":
            name = name[1:]
        else:
            order = ""
        if name in self.primitives:
            dudtype = DType(self, (order or "|") + name)
            self.types[order+name] = dudtype
        elif order:
            raise ValueError("illegal type name {}".format(order+name))
        return dudtype

    def parse(self, stream):
        tokens = DTokenizer(stream, self.ignore)
        default_order = None  # default byte order will come from binary file
        if tokens.peek()[0] in ("<", ">"):  # e.g.- netCDF always >
            self.default_order = tokens.next()[0]
        self.summary = None
        root = DDict(self)
        if tokens.peek()[0] == "{":
            # Summary block, if present, is both a struct datatype and the
            # leading items in the root dict for the layout.
            summary = DType(self)
            summary.parse(tokens)  # parses everthing in {} as struct type
            root.update(summary)  # summary items also begin the root group
            self.summary = summary
        
        stack = []
        containers = [layout.root]
        errors = []

    def add(self, item, parent=None, name=None):
        skeleton = self.skeleton
        me = len(skeleton)
        if parent is None:
            if me:
                raise ValueError("only root dict has no parent")
            p = None
        else:
            p = skeleton[parent]
            if not (p.isdict or p.islist):
                raise ValueError("dict parent must be either dict or list")
        item.me = me  # index into skeleton
        skeleton.append(item)
        item.parent = parent  # index into skeleton or None for root
        if p and parent.islist:
            if item.isparam or item.istype:
                raise ValueError("parameter or type cannot be child of list")
            name = len(p)
            p.append(me)
        elif p:
            if p.isdict:
                if name is None:
                    raise ValueError("child of dict cannot be anonymous")
            elif item.isparam or item.istype:
                raise ValueError("parent of parameter or type must be dict")
            elif p.istype:
                if not item.isdata:
                    raise ValueError("only data can be child of type")
                if name is None and len(p):
                    raise ValueError("child of type cannot be anonymous")
                elif p.get(None):
                    raise ValueError("typedef type cannot have named member")
            else:
                raise ValueError("data or parameter cannot be parent")
            p[name] = me
        item.namex = name

    def add_data(self, parent, name, dtype, shape=None, filt=None, addr=None):
        pass

    def open_dict(self, parent, name=None):
        pass

    def open_list(self, parent, name=None):
        pass

    def add_param(self, parent, name=None):
        pass

    def open_type(self, parent, name=None):
        pass

    def close_container(self, all=False):
        pass


class DDict(dict):
    isdict = True  # test flag for each of the five object types
    islist = isdata = istype = isparam = False

    def __init__(self, layout, parent=None, name=None):
        super(DDict, self).__init__()
        layout.add(self, parent, name)  # sets me, parent, namex
        self.types = self.params = None


class DType(dict):
    istype = True
    isdict = islist = isdata = isparam = False

    def __init__(self, layout, parent=None, name=None):
        super(DType, self).__init__()
        layout.add(self, parent, name)  # sets me, parent, namex


class DList(list):
    islist = True
    isdict = isdata = istype = isparam = False

    def __init__(self, layout, parent, name=None):
        super(DList, self).__init__()
        self.layout = layout
        self.me = len(layout)
        layout.append(self)
        self.parent = parent
        parent = layout[parent]
        if parent.islist:
            namex = len(parent)
            parent.append(self.me)
        elif parent.isdict:
            namex = name
            if name in parent:
                raise ValueError("{} already declared".format(name))
            parent[name] = self.me
        else:
            raise ValueError("DList parent must be DDict or DList")
        self.namex = namex
        self.doc = self.attrs = None


class DData(object):
    isdata = True
    islist = isdict = istype = isparam = False

    def __init__(self, layout, parent, name, dtype, shape=None, addr=None,
                 filt=None):
        self.layout = layout
        self.me = len(layout)
        layout.append(self)
        self.parent = parent
        parent = layout[parent]
        if parent.islist and self.isdata:
            namex = len(parent)
            parent.append(self.me)
        elif parent.isdict or parent.istype:
            namex = name
            defs = parent if self.isdata else parent.params
            if name in defs:
                raise ValueError("{} already declared".format(name))
            defs[name] = self.me
        else:
            raise ValueError("illegal parent for DData or DParam")
        self.namex = namex
        if dtype >= 0:
            if not layout[dtype].istype:
                raise ValueError("illegal data type for DData or DParam")
        self.dtype = dtype
        self.shape = shape
        self.addr = addr
        self.filt = filt
        self.doc = self.attrs = None


class DParam(DData):
    isparam = True
    islist = isdata = isdict = istype = False

    def __init__(self, layout, parent, name, dtype, addr=None):
        super(DParam, self).__init__(layout, parent, name, dtype, None, addr)
        dtype = self.dtype
        if dtype >= 0:
            dtype = layout[dtype]
            dtype = dtype.primitive if dtype.istype else 32
        else:
            dtype = -dtype
        order = dtype & 3
        if dtype >> 2 > 7:
            raise ValueError("DParam must have integer data type")


class DudleySyntax(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class DParser(object):
    def __init__(layout):
        self.layout = layout

    def __call__(stream):
        # yacc error recovery:
        # 1. discards previous tokens until error is acceptable
        # 2. discards subsequent tokens until an error production matches
        # 3. resumes parse from that point
        # 4. no new errors until 3 tokens pushed successfully
        """
        0 $accept: layout $end

        1 layout: dict_items
        2       | preamble dict_items
        3       | preamble
        4       | <empty>

        5 dict_items: dict_item
        6           | dict_items dict_item
        """
        self.tokens = tokens = DTokenizer(stream)
        self.state = []
        self.errors = []
        root = getattr(layout, "root")
        if root is None:
            layout.root = root = DGroup(layout)
            self.preamble()
        containers = [root]  # container stack: DDict, DList, DType objects
        token = tokens.peek()
        while token[0] != "eof":
            current = containers[-1]
            if current.isdict:
                self.dict_item()
            elif current.islist:
                self.list_item()
            elif current.istype:
                self.struct_item()

        # shift: push token as item, goto new state
        # reduce: pop n tokens, push item from rule, goto new state

    # reliable reduction rules are ones which accept error:
    # dict_item, list_item, struct_item, dimension, filter_args
    #   these always reduce to something and any backtracking is internal?

    def preamble(self):  # ["<" | ">" | "|"] struct_def
        """
        51 order: LT
        52      | GT

        53 preamble: order
        54         | order LCURLY template_params RCURLY
        55         | LCURLY template_params RCURLY

        56 template_params: SYMBOL COLON PRIMTYPE
        57                | template_params SYMBOL COLON PRIMTYPE
        58                | error
        """
        layout, tokens = self.layout, self.tokens
        token = tokens.peek()
        if token[0] in "<>":
            layout.default_order = token[0]
            tokens.next()
            token = tokens.peek()
        self.process_comments(root)
        if token[0] == "{":
            symb_quot_prim = self.symb_quot_prim
            root = layout.root
            layout.template = template = DType(layout)
            param = None
            token = symb_quot_prim(tokens.next())
            recovering = False
            while token[0] != "}":
                try:
                    self.process_comments(param if param else root)
                    if token[0] in ("symbol", "quoted"):
                        name = token[1]
                    else:
                        if token[0] in "@%":
                            raise DudleySyntax("explicit address illegal"
                                               " in template")
                        else:
                            raise DudleySyntax("expecting parameter name"
                                               " in template")
                    token = tokens.next()
                    if token[0] != ":":
                        raise DudleySyntax("expecting : after {} in template"
                                           "".format(name))
                    token = tokens.next()
                    prim = token[0] if prim == "primtype" else None
                    if prim:
                        prim = token[1]
                        i = 1 if prim[0] in "<>|" else 0
                        if prim[i] not in "iu":
                            prim = None
                    if not prim:
                        raise DudleySyntax("{} must be i or u primtype"
                                           " in template".format(name))
                    param = root.param_def(name, token[1])
                    template.param_def(name, token[1])
                    token = symb_quot_prim(tokens.next())
                    recovering = False
                except (DudleySyntax, ValueError) as e:
                    if not recovering:
                        recovering = True
                        self.report_error(str(e))
                    token = symb_quot_prim(tokens.next())
            tokens.peek()  # process any comments after }
            self.process_comments(template)

    @staticmethod
    def symb_quot(token):
        return ("symbol", token[1]) if token[0] == "quoted" else token

    @staticmethod
    def symb_quot_prim(token):
        t0 = token[0]
        if t0 == "quoted" or (t0 == "primtype" and token[1][0] not in "<>|"):
            return "symbol", token[1]
        return token

    def param_def(self):
        tokens = self.tokens
        dtype = addr = None
        token = tokens.next()
        if token[0] == "int":
            dtype = token[1]  # an int value rather than a string primtype
        elif token[0] == "primtype":
            dtype = token[1]
            i = 1 if dtype[0] in "<>|" else 0
            token = tokens.peek()
            if token[0] in "@%":
                addr = self.address_align()
            if dtype[i] not in  "iu" or token[0] == "[":
                raise DudleySyntax("parameter must be scalar i or u type")
        else:
            raise DudleySyntax("expecting int parameter value or primtype")
        return dtype, addr

    def dict_item(self):
        """
         7 dict_item: data_param
         8          | SYMBOL SLASH
         9          | SYMBOL list_def
        10          | SYMBOL struct_def
        11          | SYMBOL list_extend
        12          | SLASH
        13          | DOTDOT
        14          | AMP data_item
        15          | error

        16 data_param: SYMBOL EQ data_item
        17           | SYMBOL COLON INTEGER
        18           | SYMBOL COLON PRIMTYPE placement
        """
        layout, tokens, containers = self.layout, self.tokens, self.containers
        symb_quot_prim, symb_quot = self.symb_quot_prim, self.sym_quot
        current = containers[-1]  # guaranteed to be a DDict
        try:
            token = symb_quot_prim(tokens.peek())
            if token[0] == "symbol":
                name = tokens.next()[1]
                token = tokens.peek()
                if token[0] == "=":
                    tokens.next()
                    current.add(name, *self.data_item())
                elif token[0] == ":":
                    tokens.next()
                    current.add_param(name, *self.param_def())
                elif token[0] == "[":
                    tokens.next()
                    containers.append(current.open_list(name))
                elif token[0] == "/":
                    tokens.next()
                    containers.append(current.open_dict(name))
                elif token[0] == "{":
                    tokens.next()
                    containers.append(layout.open_type(name))
                elif token[0] in "@%":
                    addrs = self.list_extend()
                    item = current.get(name)
                    if item is None or not item.islist or not len(item):
                        raise DudleySyntax("{} must be existing non-empty"
                                           " list".format(name))
                    while addr in addrs:
                        item.duplicate_last(addr)
                    self.process_comments(item)
                else:
                    raise DudleySyntax("one of =:[/{{@% must follow name {}"
                                       "".format(name))
            elif token[0] == "..":
                tokens.next()
                containers.pop()
                if not containers or not containers[-1].isdict:
                    containers.append(current)
                    raise DudleySyntax("cannot .. from top level dict")
                return
            elif token[0] == "/":
                tokens.next()
                while len(containers) > 1 and containers[-1].isdict:
                    containers.pop()
            elif token[0] == ",":
                while len(containers) > 1 and containers[-1].isdict:
                    containers.pop()
                if len(containers) > 1 and containers[-2].islist:
                    containers.pop()
                else:
                    raise DudleySyntax("comma separator not allowed in a dict")
            elif token[0] == "&":
                tokens.next()
                self.data_item()
            else:
                raise DudleySyntax("expecting dict item name or"
                                   " cd-like command")
        except (DudleySyntax, ValueError) as e:
            self.report_error(str(e))

    def data_item(self):
        """
        19 data_item: PRIMTYPE shape filter placement
        20          | SYMBOL shape filter placement
        21          | struct_def shape filter placement

        22 shape: LBRACK dimensions RBRACK
        23      | <empty>

        24 dimensions: dimension
        25           | dimensions COMMA dimension

        26 dimension: INTEGER
        27          | SYMBOL
        28          | SYMBOL PLUSSES
        29          | SYMBOL MINUSES
        30          | error

        31 placement: address_align
        32          | <empty>
        """
        layout, tokens = self.layout, self.tokens
        token = tokens.next()
        if token[0] in ("primtype", "symbol", "quoted"):
            dtype = layout.lookup_type(token[1])
        elif token[0] == "{":
            dtype = layout.open_type()  # anonymous type
            containers.append(dtype)
            n = len(containers)
            while len(containers) == n and tokens.peek()[0] != "eof":
                self.struct_item()
        else:
            raise DudleySyntax("expecting type name or anonymous struct")
        shape = filt = addr = None
        token = tokens.peek()
        if token[0] == "[":
            symb_quot = self.symb_quot
            tokens.next()
            shape = []
            nerrs = 0
            while True:
                token = symb_quot(tokens.next(token))
                if token[0] == "int":
                    shape.append(token[1])
                elif token[0] == "symbol":
                    param = token[1]
                    token = tokens.peek()
                    if token[0] in "+-":
                        tokens.next()
                        param = (param, token[1])
                    shape.append(param)
                else:
                    nerrs += 1
                    if token[0] == "]":
                        break
                token = token.next()
                if token[0] == "]":
                    break
                if token[0] != ",":
                    nerrs += 1
            if nerrs:
                raise DudleySyntax("shape must be [dim1, dim2, ...]")
        token = tokens.peek()
        if token[0] in ("->", "<-"):
            filt = self.filter()
        token = tokens.peek()
        if token[0] in "@%":
            addr = self.address_align()
        return dtype, shape, addr, filt

    def address_align(self):
        """
        33 address_align: AT INTEGER
        34              | PCNT INTEGER
        """
        # Assume @ or % was result of previous tokens.peek()
        tokens = self.tokens
        atype = tokens.next()[0]  # guaranteed to be @ or %
        align = atype == "%"
        value = tokens.next()
        if value[0] != "int" or value[1] < 0:
            raise DudleySyntax("expecting integer>=0 after {}".format(atype))
        value = value[1]
        if align:
            if value == 0:
                return None  # no address argument
            value = -value
        return value  # address/alignment argument

    def list_item(self):
        """
        35 list_def: LBRACK list_items RBRACK
    
        36 list_items: list_item
        37           | list_items COMMA list_item
        38           | <empty>
    
        39 list_item: data_item
        40          | list_def
        41          | SLASH dict_items
        42          | error
        """
        tokens = self.tokens
        token = tokens.peek()
        current = containers[-1]  # guaranteed to be a DList
        try:
            if token[0] == "[":
                tokens.next()
                containers.append(current.open_list())
            elif token[0] == "/":
                tokens.next()
                containers.append(current.open_dict())
            else:
                current.add(*self.dict_item())
            token = tokens.next()
            if token[0] == "]":
                containers.pop()
            elif token[0] != ",":
                raise DudleySyntax("expecting , or ] after list item")
        except (DudleySyntax, ValueError) as e:
            self.report_error(str(e))

    def list_extend(self):
        """
        43 list_extend: address_align
        44            | list_extend address_align
        """
        # Assume @ or % was result of previous tokens.peek()
        tokens = self.tokens
        addrs = []
        while True:
            addrs.append(self.address_align())
            if tokens.peek()[0] not in "@%":
                break
        return addrs

    def struct_item(self):
        """
        45 struct_def: LCURLY struct_items RCURLY

        46 struct_items: PCNT INTEGER struct_item
        47             | struct_items struct_item
        48             | <empty>

        49 struct_item: data_param
        50            | error
        """
        tokens = self.tokens
        token = tokens.peek()
        current = containers[-1]  # guaranteed to be a DType
        try:
            token = symb_quot_prim(tokens.peek())
            if token[0] == "symbol":
                name = tokens.next()
                token = tokens.peek()
                if token[0] == "=":
                    tokens.next()
                    current.add(name, *self.data_item())
                elif token[0] == ":":
                    tokens.next()
                    current.add_param(name, *self.param_def())
                else:
                    raise DudleySyntax("expecting = or : after item name {}"
                                       "".format(name))
            elif token[0] == "%":
                if len(current):
                    raise DudleySyntax("alignment must precede struct items")
                current.align = self.address_align()
            else:
                raise DudleySyntax("expecting struct item name")
        except (DudleySyntax, ValueError) as e:
            self.report_error(str(e))


    def filter(self):
        """
        59 filter: filterop SYMBOL
        60       | filterop SYMBOL LPAREN filterarg RPAREN
        61       | <empty>

        62 filterop: LARROW
        63         | RARROW

        64 filterarg: INTEGER
        65          | FLOATING
        66          | error
        """
        # Assume -> or <- was result of previous tokens.peek()
        tokens = self.tokens
        ftype = tokens.next()[0]
        token = symb_quot(tokens.next())
        if token[0] != "symbol":
            raise DudleySyntax("missing {} filter name".format(ftype))
        name = token[1]
        token = tokens.peek()
        if token[0] != "(":
            return name, None  # no arguments
        tokens.next()
        args = []
        nerrs = 0
        while True:
            token = tokens.next()
            if token[0] in ("int", "float"):
                args.append(token[1])
            token = tokens.next()
            if token[0] == ")":
                break
            if token[0] != ",":
                nerrs += 1
        if nerrs:
            raise DudleySyntax("misformatted filter argument list")
        return name, args


#    tokens (terminals of grammar):
# symbol
# quoted   (symbol if attribute name, otherwise text value)
# fixed    (value is int)
# floating (value is float)
# = : [ ] , + - * / .. { } < > | @ % -> <-  (value is character as str)
re_symbol = re.compile(r"[a-zA-Z_]\w*")
re_quoted = re.compile(r'(?:"(?:\\.|[^"\\])*"'
                       r"|(?:'(?:\\.|[^'\\])*')")
re_fixed = re.compile(r"[+-]?([1-9]\d*|0x[[a-fA-F0-9]+|0o[0-7]+|0b[01]+|0+)")
re_floating = re.compile(r"[+-]?(?:\d+\.\d*|\.\d+"
                         r"|(?:\d+|\d+\.\d*|\.\d+)[eE][+-]?\d+)")
re_punctuation = re.compile(r"(?:<-|->|\.\.|[][}{=:,+\-*@%><])")
re_comment = re.compile(r"#.*$", re.M)
re_spaces = re.compile(r"\s+")


class DTokenizer(object):
    def __init__(self, stream, ignore=0):
        self.stream = stream
        self.line = stream.readline()  # read first line
        self.nline = 1
        self.pos = 0  # first unconsumed character of line
        self.ignore = ignore
        self.lookahead = None
        self.docs = self.attribs = self.errors = None

    def next(self):
        token = self.lookahead
        if token:
            if token[0] not in ("error", "eof"):
                self.lookahead = None
            return token
        line, pos = self._skip_spaces_and_comments()
        # Note that attribute and document comments, as well as
        # errors while parsing attribute comments, are stored in self.
        # These are cumulative until pop_docs_attrs_errs() called.
        if not line:
            return "eof",
        match = re_symbol.match(line, pos)
        if match:
            self.pos = match.end()
            return "symbol", match.group()
        match = re_punctuation.match(line, pos)
        if match:
            self.pos = match.end()
            return match.group(),
        match = re_fixed.match(line, pos)
        if match:
            self.pos = match.end()
            return "int", int(match.group(), 0)
        match = re_quoted.match(line, pos)
        if match:
            self.pos = match.end()
            return "symbol", literal_eval(match.group())
        match = re_floating.match(line, pos)
        if match:
            self.pos = match.end()
            return "float", float(match.group())
        # cannot find a legal token
        self.pos = pos + 1
        return "error", pos
    
    def clear(self):
        token = self.lookahead
        if token and token[0] in ("error", "eof"):
            self.lookahead = None

    def peek(self):
        token = self.next()
        self.lookahead = token
        return token

    def pop_docs_attrs_errs(self):
        docs, attribs = self.docs, self.attribs
        self.docs = self.attribs = self.errors = None
        return docs, attribs, errors

    def _skip_spaces_and_comments(self):
        line, pos, ignore = self.line, self.pos, self.ignore
        errors = None
        while True:
            match = re_spaces.match(line, pos)
            if match:
                pos = match.end()
            match = re_comment.match(line, pos)
            if match:
                c = match.group()
                if c.startswith("#:") and not ignore & 1:
                    attribs, dpos, errmsg = self._acomment(c[2:].rstrip())
                    if errmsg is not None:
                        err = self.line, self.nline, pos+2+dpos, errmsg
                        if errors is None:
                            errors = [err]
                        else:
                            errors.append(err)
                    self.attribs.update(attribs)
                if c.startswith("##") and not ignore & 2:
                    docs = self.docs
                    if docs:
                        docs.append(c[2:].rstrip())
                    else:
                        self.docs = [c[2:].rstrip()]
            elif pos < len(line):
                self.errors = errors
                return line, pos  # pos at a token on this line
            self.line = stream.readline()
            self.nline += 1
            if not line:
                self.errors = errors
                return line, pos  # EOF because line is ""

    def _acomment(self, string):
        # Parse attribute comments on a single line.  A single attribute
        # definition may not span multiple lines, and within a single line
        # the definitions must be comma separated.
        attribs = {}
        pos = 0
        posmax = len(string)
        skip_spaces = self._skip_spaces
        get_constant = self._get_constant
        while True:
            pos = skip_spaces(string, pos)
            if pos >= posmax:
                return attribs, None, None
            name, pos = self.get_name(string, pos)
            if name is None:
                return attribs, pos, "expecting attribute name"
            pos = skip_spaces(string, pos)
            if pos < posmax and string[pos] not in "=,":
                return attribs, pos, "expecting attribute name="
            if pos >= posmax or string[pos] == ",":
                attribs[name] = True  # only way to get boolean attribute value
                if pos >= posmax:
                    return attribs, None, None
                pos += 1
                continue
            pos = skip_spaces(string, pos+1)  # skip past = sign
            if pos < posmax and string[pos] == "[":
                pos = skip_spaces(string, pos+1)
                value, pos, expect = get_constant(string, pos)
                if value is None:
                    return attribs, pos, expect
                value = [value]
                while True:
                    pos = skip_spaces(string, pos)
                    if pos < posmax:
                        if string[pos] == "]":
                            attribs[name] = array(value)
                            pos += 1
                            break
                        if string[pos] != ",":
                            return (attribs. pos,
                                    "missing , in attribute name=[v1,...]")
                        pos = skip_spaces(string, pos)
                        v, pos, expect = get_constant(string, pos, expect)
                        if v is None:
                            return attribs, pos, expect
                        value.append(v)
            else:
                pos = skip_spaces(string, pos+1)
                value, pos, expect = get_constant(string, pos)
                if value is None:
                    return attribs, pos, expect
                attribs[name] = value
            pos = skip_spaces(string, pos)
            if pos >= posmax:
                return attribs, None, None
            if string[pos] != ",":
                "expected , between attributes in attribute list"
            pos += 1

    def _skip_spaces(string, pos):
        match = re_spaces.match(string, pos)
        return match.end() if match else pos

    def _get_name(self, string, pos=0):
        name = None
        match = re_symbol.match(string, pos)
        if match:
            pos = match.end()
            name = match.group()
        else:
            match = re_quoted.match(string, pos)
            if match:
                pos = match.end()
                name = literal_eval(match.group())
        return name, pos

    def _get_constant(string, pos, expect=None):
        if expect:
            expect = [expect==1, expect==2, expect==3]
        else:
            expect = [True, True, True]
        match = expect[0] and re_fixed.match(string, pos)
        if match:
            return int(match.group(), 0), match.end(), 1
        match = expect[1] and re_quoted.match(string, pos)
        if match:
            return literal_eval(match.group()), match.end(), 2
        match = expect[2] and re_floating.match(string, pos)
        if match:
            return float(match.group()), match.end(), 3
        if all(expect):
            return None, pos, "expecting fixed, quoted, or float attrib value"
        else:
            return None, pos, "attribute array elements not all same type"

"""BNF Grammar rules

    0 $accept: layout $end

    1 layout: dict_items
    2       | preamble dict_items
    3       | preamble
    4       | <empty>

    5 dict_items: dict_item
    6           | dict_items dict_item

    7 dict_item: data_param
    8          | SYMBOL SLASH
    9          | SYMBOL list_def
   10          | SYMBOL struct_def
   11          | SYMBOL list_extend
   12          | SLASH
   13          | DOTDOT
   14          | AMP data_item
   15          | error

   16 data_param: SYMBOL EQ data_item
   17           | SYMBOL COLON INTEGER
   18           | SYMBOL COLON PRIMTYPE placement

   19 data_item: PRIMTYPE shape filter placement
   20          | SYMBOL shape filter placement
   21          | struct_def shape filter placement

   22 shape: LBRACK dimensions RBRACK
   23      | <empty>

   24 dimensions: dimension
   25           | dimensions COMMA dimension

   26 dimension: INTEGER
   27          | SYMBOL
   28          | SYMBOL PLUSSES
   29          | SYMBOL MINUSES
   30          | error

   31 placement: address_align
   32          | <empty>

   33 address_align: AT INTEGER
   34              | PCNT INTEGER

   35 list_def: LBRACK list_items RBRACK

   36 list_items: list_item
   37           | list_items COMMA list_item
   38           | <empty>

   39 list_item: data_item
   40          | list_def
   41          | SLASH dict_items
   42          | error

   43 list_extend: address_align
   44            | list_extend address_align

   45 struct_def: LCURLY struct_items RCURLY

   46 struct_items: PCNT INTEGER struct_item
   47             | struct_items struct_item
   48             | <empty>

   49 struct_item: data_param
   50            | error

   51 order: LT
   52      | GT

   53 preamble: order
   54         | order LCURLY template_params RCURLY
   55         | LCURLY template_params RCURLY

   56 template_params: SYMBOL COLON PRIMTYPE
   57                | template_params SYMBOL COLON PRIMTYPE
   58                | error

   59 filter: filterop SYMBOL
   60       | filterop SYMBOL LPAREN filterarg RPAREN
   61       | <empty>

   62 filterop: LARROW
   63         | RARROW

   64 filterarg: INTEGER
   65          | FLOATING
   66          | error

--------------
Informal EBNF grammar ([...] optional, {...}* zero or more repeats):

layout: [preamble] {dict_item}* ;
preamble: ["<" | ">" | "|"] struct_def ;
dict_item: SYMBOL (data_param | list_def | struct_def | "/" | address_align)
           | "/" | ".." | "&" data_item | error ;
data_param: SYMBOL ("=" data_item | ":" param_value) ;
data_item: (primitive | SYMBOL | struct_def) [shape] [filter] [placement] ;
param_value: INTEGER | primitive [placement] ;
primitive: ["<" | ">" | "|"] PRIMTYPE ;
shape: "[" dimension {"," dimension}* "]" ;
dimension: INTEGER | SYMBOL [PLUSSES | MINUSES] | error ;
filter: ("->" | "<-") SYMBOL ["(" (INTEGER | FLOATING | error) ")"] ;
placement: ("@" | "%") INTEGER ;
list_def: "[" [list_item {"," list_item}*] "]" ;
list_item: data_item | list_def | "/" {dict_item}* | error ;
struct_def: "{" ["%" INTEGER | error] struct_item {struct_item}* "}" ;
struct_item: data_param | error ;

---------------
Informal EBNF attribute grammar:

attributes: [attribute] {[","] attribute}* ;
attribute: SYMBOL "=" (INTEGER | FLOATING | QUOTED | array_value) | error ;
array_value: "[" INTEGER {"," INTEGER}* "]"
           | "[" FLOATING {"," FLOATING}* "]"
           | "[" QUOTED {"," QUOTED}* "]"
           | "[" error "]"
"""
