"""Build, navigate, and query a Dudley layout."""

__all__ = "Address"

from __future__ import absolute_import

import sys
from io import StringIO
from numbers import Integral
PY2 = sys.version_info < (3,)
if PY2:
    from collections import OrderedDict as dict
else:
    basestring = str

from numpy import array


D_PRIM, D_DATA, D_PARAM, D_DICT, D_LIST, D_TYPE = 0, 1, 2, 3, 4, 5


class _Prim(object):
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
    (except complex have 4, 8, or 16 bytes per floating point pair), except
    for the `U` unicode kind, which has only 2 and 4 byte sizes.  (Note that
    for `U1` and `U2` the number of bytes may be greater than the number of
    characters, and not all possible arrays are legal unicode.)

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
    In particular, numpy implementations often support `f12` but not `f16`.

    Dudley also uses type number 0 for the empty compound `{}`, which means
    `None` in python or `null` in javascript/JASON and takes no space in the
    data stream.  (Note that 0 root dict, never a datatype.)

    All 47 instances are kept in the prim attribute of the Layout class, so
    that Layout.prim[iprim] is primitive number iprim.
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


class Layout(list):
    """Raw Layout objects are not part of the Dudley API.

    The LItem objects, LDict, LList, LData, LType, and LParam, each contain
    a layout attribute which is the Layout object; these are the user-facing
    objects for the Dudley layout interface.

    A Layout is a list of items (in fact list is the base class of Layout).
    Each list item is one of the five kinds of low-level object: _Dict,
    _List, _Data, _Type, or _Param, corresponding to the five kinds of
    object in a Dudley layout.  A sixth low-level object is the _Prim -
    corresponding to a Dudley primitive datatype - but these are global
    objects shared among all layouts rather than element of the Layout list.

    Since every item has its own index in the Layout list, that index serves
    as an identifier or `itemid` for the object.  The low-level objects in the
    list use an `itemid` to refer to other objects in the Layout, like parent
    or child containers, non-primitive datatypes or parameter references in
    array declarations, etc.  The root _Dict always has `itemid=0`.
    
    This strategy avoids a tangle of circular object references among the
    containers and data.  However, it would make a very clumsy layout
    interface.  Therefore, the actual user interface is the LItem objects,
    which are very lightweight temporary objects consisting of nothing more
    than a `(layout, itemid)` pair.  As long as a single LItem object is in
    use, or a stream interface object like an SDict or SList, there
    will be at least one reference to the Layout, keeping it alive.
    Each LItem wraps the corresponding low-level object: an LDict wraps a
    _Dict, an LData wraps a _Data, and so on.
    """
    def __init__(self):
        super(Layout, self).__init__((_Dict(None),))  # self[0] is root dict
        self.params = None  # params[pid] -> id of dynamic parameter pid
        # Stream instances with this layout will have two lists of the same
        # length as these: a list of addresses the same length as self, and
        # a list of dynamic parameter values the same length as params.
        # Optional lists the same length as items are also created if the
        # layout contains any attributes or documentatation.
        self._atts = None  # atts[id] -> {attributes of item}
        self._docs = None  # docs[id] -> [docstrings for item]

    # prim[-typeid] -> _Prim for that type
    prim = [None] + [_Prim(t) for t in ("|u1", "|i1", "|b1", "|S1", "|U1")]
    prim += [_Prim(t) for t in ("|u2", "|i2", "|f2", "|c4", "|U2")]
    prim += [_Prim(t) for t in ("|u4", "|i4", "|f4", "|c8", "|U4")]
    prim += [_Prim(t) for t in ("|u8", "|i8", "|f8", "|c16")] + [None]
    prim += [_Prim(t) for t in ("<u2", "<i2", "<f2", "<c4", "<U2")]
    prim += [_Prim(t) for t in ("<u4", "<i4", "<f4", "<c8", "<U4")]
    prim += [_Prim(t) for t in ("<u8", "<i8", "<f8", "<c16")] + [None]
    prim += [_Prim(t) for t in (">u2", ">i2", ">f2", ">c4", ">U2")]
    prim += [_Prim(t) for t in (">u4", ">i4", ">f4", ">c8", ">U4")]
    prim += [_Prim(t) for t in (">u8", ">i8", ">f8", ">c16")] + [None, None]
    primid = {name: -i for i, name in enumerate(prim) if name}

    def l_item(self, index):
        return _LItem[self[index].itype](self, index)

    def encode_dim(self, d):
        """Encode array dimension as int, including parameter references."""
        if isinstance(d, Integral):
            if d < -1:
                raise ValueError("array dimension < -1 has no meaning")
            return d
        offset = 0
        if isinstance(d, ParamRef):
            d, offset = d.l_param, d.offset
        elif not isinstance(d, LParam):
            raise TypeError("array dimension must be integer or "
                            "parameter reference")
        if d.layout != self:
            raise TypeError("parameter not in same layout as shape")
        return ((-d.itemid) << 6) | (offset + 32)  # less than -64

    def decode_dim(self, d):
        """Decode array dimension to int >= -1 or parameter reference."""
        if d >= -1:
            return d
        offset = (d & 63) - 32  # (d & 63) != 0 since offset >= -31
        paramid = -(d >> 6)  # note that arithmetic right shift is correct
        l_param = LParam(layout, paramid)
        return ParamRef(l_param, offset) if offset else l_param

    def encode_shape(self, shape):
        """Encode array shape as int tuple, including parameter references."""
        if shape:
            encode = self.encode_dim
            return tuple(encode(n) for n in shape)
        else:
            return None

    def decode_shape(self, shape):
        """Decode array shape to tuple of ints and parameter references."""
        if shape:
            decode = self.decode_dim
            return tuple(decode(n) for n in shape)
        else:
            return ()

    def add_item(self, parent, name, *args):
        """Append a new _Data, _Dict, or _List to this layout."""
        pitem = self.l_item(parent)  # LItem for parent
        ptype = pitem.itype
        if ptype == D_DICT and parent.get(name):
            raise TypeError("LDict item {} previously declared".format(name))
        datatype, args = args[0], args[1:]
        if issubclass(datatype, type({})):  # dict is OrderedDict here for PY2
            if ptype == D_TYPE:
                raise TypeError("attempt to add LDict as an LType member")
            item = _Dict(parent, name)
        elif issubclass(datatype, list):
            if ptype == D_TYPE:
                raise TypeError("attempt to add LList as an LType member")
            return self.l_item(listid)
            item = _List(parent, name)
        elif ptype == D_TYPE and datatype is None:
            raise TypeError("attempt to add None as an LType member")
        else:
            item = _Data(parent, name, pitem.get_typeid(datatype), *args)
        itemid = len(self)  # id for the new item
        self.append(item)
        return itemid

    def add_param(self, parent, name, typeid, align=None):
        """Append a new _Param to this layout."""
        itemid = len(self)  # id for the new item
        if typeid is None:
            if not isinstance(align, Integral):
                raise TypeError("fixed parameter value must be integer")
            if align < -1:
                raise ValueError("fixed parameter value must not be negative")
            pid, align = align, None  # pid is value
        else:
            params = self.params
            if params is None:
                self.params = params = []
            pid = len(params)
            params.append(itemid)
        item = _Param(parent, name, pid, typeid, align)
        self.append(item)
        return itemid

    def add_type(self, parent, name,
                 datatype=Ellipsis, shape=None, align=None):
        """Append a new _Type to this layout."""
        if align:
            if align > 0 and (align & (align-1)):
                raise ValueError("illegal alignment {}, must be power of two"
                                 .format(align))
            elif align < 0:
                raise ValueError("cannot specify @address in typedef")
        # parent is guaranteed to be a Dudley dict
        itemid = len(self)  # id for the new _Type item
        if datatype is not Ellipsis:  # this is a typedef
            # append new _TYpe, then immediately its anonymous member
            self.append(_Type(parent, name, itemid+1))
            self.add_item(itemid, None, datatype, shape, align)
            member = layout.l_item(-1)
            item = layout[itemid]
            item.size = member.size
            # Note: align cannot be None - add_item exception if datatype None
            item.align = align if align else member.alignment
        else:  # this is a compound
            self.append(_Type(parent, name, {}))
        return itemid


class LItem(object):
    """Common features of LDict, LList, LType, LData and LParam"""
    __slots__ = "layout", "itemid"

    def __init__(self, layout, itemid):
        # Shared because guaranteed to be called with item of correct itype.
        self.layout = layout
        self.itemid = itemid

    @property
    def root0(self):
        """outermost root dict of entire layout"""
        return self.layout.l_item(0)

    @property
    def root(self):
        """dict ancestor whose parent is not a dict (either root0 or list)"""
        raw = self.layout.raw
        while True:
            parent = raw(self.itemid)

    @property
    def parent(self):
        """parent container (dict, list, or datatype) of item"""
        layout = self.layout
        parent = layout[self.itemid].parent
        return None if parent is None else layout.l_item(parent)

    @property
    def name(self):
        """name of item or None"""
        return self.layout[self.itemid].name

    def get_typeid(self, datatype):
        """return itemid of datatype relative to this LItem"""
        layout = self.layout
        _item = layout[self.itemid]
        while _item.itype != D_DICT:
            _item = layout[_item.parent]
        return _item._get_typeid(datatype, layout)

    def docs(self, *args):
        """retrieve or append to document comments for this item
        
        Parameters
        ----------
        *args : str
            Each argument, if any, appends one line of documentation text
            for this item.

        Returns
        -------
        list
            Each element of the list is one documentation line.
        """
        layout, itemid = self.layout, self.itemid
        docs = layout.docs
        if args:
            while a in args:
                if not isinstance(a, basestr):
                    raise TypeError("Each documentation line must be text")
            args = list(*args)
            if not docs:
                layout.docs = docs = [None]*(itemid + 1)
            elif len(docs) <= itemid:
                docs.extend([None]*(itemid + 1 - len(docs)))
            doc = docs[itemid]
            if not doc:
                docs[itemid] = doc = args
            else:
                doc += args
        elif not docs or len(docs)<=itemid:
            doc = []
        else:
            doc = docs[itemid] or []
        return doc

    def attrs(self, attributes=None, **kwargs):
        if isinstance(arg, type({})):
            for name in attributes:
                if not isinstance(name, basestr):
                    raise TypeError("attribute name must be text")
            attributes.update(kwargs)
        else:
            arg = kwargs
        for name, value in attributes.items():
            if value is None or isinstance(value, basestr):
                continue
            value = array(value + 0)
            if value.ndim > 1:
                raise ValueError("attribute value must be scalar or 1D array")
            if value.dtype.kind not in "if":
                raise ValueError("attribute value must be type int or float")
            if value.ndim == 0:
                value = value[()]
        layout, itemid = self.layout, self.itemid
        atts = layout.atts
        if attributes:
            if atts is None:
                layout.atts = atts = [None]*(itemid + 1)
            elif len(atts) <= itemid:
                atts.extend([None]*(itemid + 1 - len(atts)))
            attribs = atts[itemid]
            if not attribs:
                atts[itemid] = attribs = attributes
            else:
                attribs = attribs.update(attributes)
        elif not atts or len(atts)<=itemid:
            attribs = {}
        else:
            attribs = atts[itemid] or {}
        return attribs


class LData(LItem):
    __slots__ = ()
    itype = D_DATA  # duplicates _Data.itype

    @property
    def datatype(self):
        layout = self.layout
        typeid = layout[self.itemid].typeid
        if typeid < 0:
            return Layout.prim[-typeid]
        return layout.l_item(typeid) if typeid else None
    
    @property
    def shape(self):
        layout = self.layout
        return layout.decode_shape(layout[self.itemid].shape)

    @property
    def align(self):
        return self.layout[self.itemid].align  # an Address instance

    @property
    def address(self):
        align = self.layout[self.itemid].align
        try:
            return align.address
        except AttributeError:
            return -1  # not specified, thus unallocated or NULL

    @property
    def alignment(self):
        """alignment of data array item or None if address specified"""
        item = self.layout[self.itemid]
        align = item.align
        if align:
            return align if align > 0 else None
        # Alignment is determined by datatype.
        typeid = layout[self.itemid].typeid
        if typeid == 0:
            return None  # this is {} (None) object which has no alignment
        elif typeid < 0:
            return Layout.prim[-typeid].size
        return layout.l_item(typeid).align

    @property
    def size(self):
        """byte size of data array item or None if parametrized shape"""
        layout = self.layout
        item = layout[self.itemid]
        if item.typeid is None:
            return 0
        typeid = layout[self.itemid].typeid
        if typeid == 0:
            return 0  # this is {} (None) object which has 0 size
        elif typeid < 0:
            return Layout.prim[-typeid].size
        size = layout.l_item(typeid).size
        if size is not None:  # typedef, compound may have indeterminate size
            for d in self.shape:
                if isinstance(d, (LParam, ParamRef)):
                    d = d.value
                    if d is None:
                        return None  # size is indeterminate
                if d >= 0:
                    size *= d
        return size  # no dynamic parameter references

    @property
    def filt(self):
        return self.layout[self.itemid].filt


class _Data(object):
    __slots__ = "parent", "name", "typeid", "shape", "align", "filt"
    itype = D_DATA

    def __init__(self, parent, name, typeid, shape=None, align=0, filt=None):
        if align and align > 0 and (align & (align-1)):
            raise ValueError("illegal alignment {}, must be power of two"
                             .format(align))
        self.parent = parent.itemid  # parent arg is LDict, LList, or LType
        self.name = name
        self.typeid = typeid
        self.shape = shape
        self.align = align
        self.filt = filt


class LDict(LItem):
    __slots__ = ()
    itype = D_DICT  # duplicates _Dict.itype

    @property
    def params(self):
        return DictParams(self)

    @property
    def types(self):
        return DictTypes(self)

    def __getitem__(self, name):
        layout = self.layout
        items = layout[self.itemid].items
        return layout.l_item(items[name])

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def __bool__(self):
        layout = self.layout
        items = layout[self.itemid].items
        return bool(self.items)

    def __len__(self):
        layout = self.layout
        items = layout[self.itemid].items
        return len(self.items)

    def __iter__(self):
        layout = self.layout
        items = layout[self.itemid].items
        def _items():
            for iid in items:
                yield layout.l_item(iid)
        return _items()

    def items(self):
        layout = self.layout
        items = layout[self.itemid].items
        def _items():
            for name, iid in items.items():
                yield name, layout.l_item(iid)
        return _items()

    def __contains__(self, name):
        layout = self.layout
        items = layout[self.itemid].items
        return name in self.items

    def __setitem__(self, name, value):
        if not isinstance(name, basestring):
            raise TypeError("item name must be a text string")
        if not isinstance(value, tuple):
            value = (value,)
        layout = self.layout
        layout.add_item(self.itemid, name, *value)

    def getdict(self, name):
        if not isinstance(name, basestring):
            raise TypeError("dict name must be a text string")
        item = self.get(name)
        if not item:
            layout = self.layout
            item = layout.l_item(layout.add_item(self.itemid, name, type({})))
        elif item.itype != D_DICT:
            raise TypeError("item exists but is not a dict: {}".format(name))
        return item

    def getlist(self, name):
        if not isinstance(name, basestring):
            raise TypeError("dict name must be a text string")
        item = self.get(name)
        if not item:
            layout = self.layout
            item = layout.l_item(layout.add_item(self.itemid, name, list))
        elif item.itype != D_LIST:
            raise TypeError("item exists but is not a list: {}".format(name))
        return item


class DictParams(object):
    __slots__ = "l_dict", "params"  # parent LDict

    def __init__(self, l_dict):
        self.l_dict = l_dict
        layout = l_dict.layout
        params = layout[l_dict.itemid].params
        self.params = {} if params is None else params

    def __getitem__(self, name):
        params = self.params
        paramid = params.get(name)
        if paramid is None:
            parent = self.l_dict.parent
            while parent and parent.itype != D_DICT:
                parent = parent.parent
            if not parent:  # recursion always hits this eventually
                raise KeyError("missing parameter {}".format(name))
            paramid = parent.params[name]  # recurse through ancestor dicts
        return paramid

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def __bool__(self):
        return bool(self.params)

    def __len__(self):
        return len(self.params)

    def __iter__(self):
        return iter(self.params)

    def items(self):
        layout = self.l_dict.layout
        params = self.params
        def _items():
            for name, pid in params.items():
                yield name, layout.l_item(pid)
        return _items()

    def __contains__(self, name):
        return name in self.params

    def __call__(self, name, type_or_value, align=None):
        """assign parameter value"""
        if not isinstance(name, basestring):
            raise TypeError("parameter name must be a text string")
        l_dict = self.l_dict
        layout = l_dict.layout
        dictid = l_dict.itemid
        _dict = layout[dictid]
        if isinstance(type_or_value, Integral):  # create fixed parameter
            paramid = layout.add_param(dictid, name, None, type_or_value)
        else:
            typeid, value = _dict._get_typeid(type_or_value, layout), None
            tid = typeid
            while tid > 0:  # check for typedef to scalar primitive
                item = layout[tid]
                members = None if item.itype != D_TYPE else item.members
                if not isinstance(members, Integral):
                    raise TypeError("parameter {} datatype cannot be compound"
                                    .format(name))
                item = layout[members]
                tid = item.typeid
                if item.shape or item.filt:
                    raise TypeError("parameter {} datatype must be scalar"
                                    .format(name))
            if tid > -1 or tid < -50 or (-1 - tid)%5 > 1:
                raise TypeError("parameter {} datatype must be integer"
                                .format(name))
            paramid = layout.add_param(dictid, name, typeid, align)
        params = _dict.params
        if params is None:
            self.params = _dict.params = params = {}
        params[name] = paramid  # may update previously used name
        return layout.l_item(paramid)  # return newly added LParam


class DictTypes(object):
    __slots__ = "l_dict", "types"  # parent LDict

    def __init__(self, l_dict):
        self.l_dict = l_dict
        layout = l_dict.layout
        types = layout[l_dict.itemid].types
        self.types = {} if types is None else types

    def __getitem__(self, name):
        types = self.types
        typeid = types.get(name)
        if typeid is None:
            parent = self.l_dict.parent
            while parent and parent.itype != D_DICT:
                parent = parent.parent
            if not parent:  # recursion always hits this eventually
                raise KeyError("missing type {}".format(name))
            typeid = parent.types[name]  # recurse through ancestor dicts
        return typeid

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def __bool__(self):
        return bool(self.types)

    def __len__(self):
        return len(self.types)

    def __iter__(self):
        return iter(self.types)

    def items(self):
        layout = self.l_dict.layout
        types = self.types
        def _items():
            for name, tid in types.items():
                yield name, layout.l_item(tid)
        return _items()

    def __contains__(self, name):
        return name in self.types

    def __call__(self, name, datatype=Ellipsis, shape=None, align=None):
        l_dict = self.l_dict
        layout = l_dict.layout
        types = self.types
        if name is not None:
            if not isinstance(name, basestring):
                raise TypeError("type name must be a text string or None")
            if types is not None and name in types:
                raise ValueError("type name previously declared: {}"
                                 .format(name))
        typeid = layout.add_type(l_dict.itemid, name, datatype, shape, align)
        return layout.l_item(typeid)


class _Dict(object):
    __slots__ = "parent", "name", "items", "params", "types"
    itype = D_DICT

    def __init__(self, parent, name=None):
        self.parent = parent
        self.name = name
        self.items = {}
        self.params = self.types = None

    def _get_typeid(self, datatype, layout):
        if isinstance(datatype, (LPrim, LType)):
            return datatype.itemid
        if not isinstance(datatype, basestring):
            if datatype is None:
                return 0
            raise TypeError("expecting type as name, LPrim, or LType, got {}"
                            .format(datatype))
        _dict, types = self, self.types
        while True:
            if types is not None:
                typeid = types.get(datatype)
                if typeid is not None:
                    return typeid
            parent = _dict.parent
            if parent is None:  # _dict is root dict of layout
                # check for primitive type
                name = datatype
                if name[:1] not in "<>|":
                    name = "|" + name
                typeid = Layout.primid.get(name)
                if typeid is not None:
                    if name != datatype:
                        # add unprefixed primitive datatype to layout root dict
                        typeid = layout.add_prim(0, datatype, typeid)
                    return typeid
                raise KeyError("datatype {} not found in scope"
                               .format(datatype))
            _dict = layout[parent]
            while _dict.itype != D_DICT:  # skip over list containers
                _dict = layout[_dict.parent]
            types = _dict.types

    def _get_paramid(self, param, layout):
        if isinstance(param, LParam):
            return param.itemid
        if not isinstance(param, basestring):
            raise TypeError("expecting parameter as name or LParam, got {}"
                            .format(param))
        _dict, params = self, self.params
        while True:
            if params is not None:
                paramid = params.get(param)
                if paramid is not None:
                    return paramid
            parent = _dict.parent
            if parent is None:  # _dict is root dict of layout
                raise KeyError("parameter {} not found in scope".format(param))
            _dict = layout[parent]
            while _dict.itype != D_DICT:  # skip over list containers
                _dict = layout[_dict.parent]
            params = _dict.params


class LList(LItem):
    __slots__ = ()
    itype = D_LIST

    def __getitem__(self, index):
        layout = self.layout
        itemid = layout[self.itemid].items[index]
        if isinstance(itemid, list):
            return [layout.l_item(i) for i in itemid]
        return layout.l_item(itemid)

    def __len__(self):
        layout = self.layout
        return len(layout[self.itemid].items)

    def __iter__(self):
        layout = self.layout
        items = layout[self.itemid].items
        def _items():
            for iid in items:
                yield layout.l_item(iid)
        return _items()

    # No extend method for LList.
    def append(self, datatype, *args):
        if isinstance(datatype, LData):
            # datatype is template for datatype and shape
            args = (datatype.shape,) + args  # optional args is align
            datatype = datatype.datatype
        layout, selfid = self.layout, self.itemid
        selfid.items.append(layout.add_item(selfid, None, datatype, *args))

    def __iadd__(self, rop):
        if not isinstance(rop, tuple):
            rop = (rop,)
        self.append(*rop)

    def __add__(self, rop):
        self += rop
        return self[-1]

    def getdict(self, index):
        item = self[index]
        if item.itype != D_DICT:
            raise TypeError("list item {} is not a dict".format(index))
        return item

    def getlist(self, index):
        item = self[index]
        if item.itype != D_LIST:
            raise TypeError("list item {} is not a list".format(index))
        return item


class _List(_Item):
    __slots__ = "parent", "name", "items"
    itype = D_LIST

    def __init__(self, parent, name=None):
        self.parent = parent
        self.name = name
        self.items = []


class LParam(LItem):
    __slots__ = ()
    itype = D_PARAM

    @property
    def datatype(self):
        layout = self.layout
        typeid = layout[self.itemid].typeid
        if typeid is None:
            return None
        elif typeid < 0:
            return Layout.prim[-typeid]
        else:
            return layout.l_item(typeid) if typeid else None

    @property
    def align(self):
        layout = self.layout
        item = layout[self.itemid]
        if item.typeid is None:
            return None
        return item.align  # int or Address

    @property
    def address(self):
        align = self.align
        if align is None:
            return None
        try:
            return align.address
        except AttributeError:
            return -1  # not specified (initially unallocated or NULL)

    @property
    def alignment(self):
        """alignment of dynamic parameter or None if address specified"""
        layout = self.layout
        item = layout[self.itemid]
        if item.typeid is None:
            return None
        align = item.align
        if align:
            return align if align > 0 else None
        # Alignment is determined by datatype.
        typeid = layout[self.itemid].typeid
        if typeid == 0:
            return None  # this is {} (None) object which has no alignment
        elif typeid < 0:
            return Layout.prim[-typeid].size
        return layout.l_item(typeid).align

    @property
    def value(self):
        """value of fixed parameter or None for dynamic parameter"""
        layout = self.layout
        item = layout[self.itemid]
        return item.pid if item.typeid is None else None

    @property
    def size(self):
        """byte size of data array item or None if address specified"""
        layout = self.layout
        item = layout[self.itemid]
        if item.typeid is None:
            return 0
        typeid = layout[self.itemid].typeid
        if typeid == 0:
            return 0  # this is {} (None) object which has no size
        elif typeid < 0:
            return Layout.prim[-typeid].size
        return layout.l_item(typeid).size

    def __add__(self, rop):
        if not isinstance(rop, Integral):
            raise TypeError("parameter reference offset must be an integer")
        if rop < -31 or rop > 31:
            raise ValueError("parameter reference offset too large (>31)")
        return ParamRef(self, rop)

    def __sub__(self, rop):
        return self + (-rop)


class ParamRef(object):
    __slots__ = "l_param", "offset"

    def __init__(self, l_param, offset=0):
        self.l_param = l_param
        self.offset = offset

    @property
    def value(self):
        """value of fixed parameter or None for dynamic parameter"""
        value = self.l_param.value
        if value is None:
            return None
        if value <= 0:
            return value
        value += self.offset
        return value if value > 0 else 0


class _Param(object):
    __slots__ = "parent", "name", "pid", "typeid", "align"
    itype = D_PARAM

    def __init__(self, parent, name, pid, typeid=None, align=None):
        if align and align > 0 and (align & (align-1)):
            raise ValueError("illegal alignment {}, must be power of two"
                             .format(align))
        self.parent = parent
        self.name = name
        self.pid = pid  # value if typeid is None
        self.typeid = typeid  # fixed if None, else dynamic
        self.align = align


class LType(LItem):
    __slots__ = ()
    itype = D_TYPE

    def close(self):
        layout = self.layout
        item = layout[self.itemid]
        align = item.align
        if align >= 0:
            raise TypeError("attempt to close LType that is not open")
        item.align = -align  # align >= 0 marks closed compound

    @property
    def _check_closed(self):
        layout = self.layout
        item = layout[self.itemid]
        if item.align < 0:
            raise TypeError("__setitem__ is only legal method for open LType")
        return layout, item

    @property
    def typedef(self):
        layout, item = self._check_closed
        membs = item.members
        return layout.l_item(membs) if isinstance(membs, Integral) else None

    def __getitem__(self, name):
        layout, item = self._check_closed
        members = item.members
        if isinstance(members, Integral):
            if name == 0:
                return layout.l_item(members)
            else:
                raise KeyError("only legal key for typedef is integer 0")
        return layout.l_item(members[name])

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def __bool__(self):
        layout, item = self._check_closed
        members = item.members
        return True if isinstance(members, Integral) else bool(members)

    def __len__(self):
        layout, item = self._check_closed
        members = item.members
        return 1 if isinstance(members, Integral) else len(members)

    def __iter__(self):
        layout, item = self._check_closed
        members = item.members
        if isinstance(members, Integral):
            return iter((0,))
        else:
            return iter(members)

    def items(self):
        layout, item = self._check_closed
        members = item.members
        if isinstance(members, Integral):
            return iter(((0, layout.l_item(members)),))
        def _items():
            for name, iid in members.items():
                yield name, layout.l_item(iid)
        return _items()

    def __contains__(self, name):
        layout, item = self._check_closed
        members = item.members
        if isinstance(members, Integral):
            return name in (0,)
        return name in members

    def __setitem__(self, name, value):
        layout, itemid = self.layout, self.itemid
        item = layout[itemid]
        align = -item.align  # negative of current alignment is open marker
        if item.align <= 0:
            raise TypeError("__setitem__ is illegal method for closed LType")
        if not isinstance(name, basestring):
            raise TypeError("item name must be a text string")
        if not isinstance(value, tuple):
            value = (value,)
        layout.add_item(itemid, name, *value)
        # remains to compute alignment and size
        # While compound is open, size is byte after end of previous member
        # and align is negative of maximum member alignment so far.
        member = layout.l_item(-1)
        malign = member.align
        if malign > align:
            align = malign
        item.align = -align
        # Is size unnnecessary?  Really only need it for stream interface.
        size = item.size
        if size is not None:
            msize = member.size
            if msize is not None:
                rem = size & (malign-1)
                if rem:
                    size += malign - rem
                item.size = size + msize
            else:
                item.size = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class _Type(object):
    __slots__ = "parent", "name", "members", "size", "align"
    itype = D_TYPE

    def __init__(self, parent, name, members):
        self.parent = parent
        self.name = name
        self.members = members
        self.size = 0
        self.align = -1  # align < 0 marks open compound


class Address(int):
    __slots__ = ()

    def __new__(cls, address):
        if address < -1:  # address -1 means "not allocated" or NULL
            raise ValueError("Address cannot be less than -1")
        return super(Address, cls).__new__(cls, -2 - address)

    @property
    def address(self):
        return -2 - self
