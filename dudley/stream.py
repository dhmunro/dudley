"""
"""
from __future__ import absolute_import

from numbers import Number, Integral
import re

from .bisonp import BisonParser, SemanticError, AbortParse


class Layout(object):
    """Dudley layout

    Attributes
    ----------
    root : Group
        root group for this layout

    types : dict
        dict of named datatypes used in this Layout
    """
    def __init__(self, address=None, default=None):
        self.address, self.default = address, default
        self.root = self.current = Group()
        self.types = dict(prefixed_primitives)

    # ------ Following section is commands implementing parser rules. ------
    def add(self, nameitem):
        name, item = nameitem
        item0 = self.current.get(name)
        if isinstance(name, tuple):  # this is list += list or addr_list
            name = name[0]
            if not isinstance(item0, List):
                raise SemanticError(
                    "{} is not an existing List for +=".format(name))
            item0 += item
        elif item is dict:
            if name is None:
                self.current = self.root
            elif name is Ellipsis:
                self.current = self.current.parent
            else:
                if item0 is None:
                    self.current[name] = g = Group(self.current)  # new subgrp
                    self.current = g
                elif isinstance(item0, Group):
                    self.current = item0  # existing subgrp
                else:
                    raise SemanticError(
                        "{} exists but is not a Group".format(name))
        elif item0 is not None:
            if item0 is not None:
                raise SemanticError(
                    "cannot redeclare existing variable {}".format(name))
        elif isinstance(item, (Datum, List, Param)):
            self.current[name] = item
        else:
            raise AbortParse("parser delivered unrecognized item to add")

    def newparam(self, basetype, location=None):
        return Param(basetype, location)

    def newarray(self, datatype, shape, location):
        # datatype must be either anonymous Struct or known type name
        if isinstance(datatype, Struct):
            datatype.resolve
        return Datum(datatype, shape, location)

    def newlist(self, item=None):
        return List(item)

    def newgroup(self):
        return Group()

    def newstruct(self):
        return Struct()

    def _check_type(self, datatype):
        if isinstance(datatype, Struct):
            types = self.types
            atype = types.get(datatype)
            if atype is None:
                native = "|" + datatype
                if native in prefixed_primitives:
                    types[datatype] = native
                else:
                    raise SemanticError(
                        "undefined datatype {}".format(datastype))

    def typedef(self, name, datatype, shape=None, align=None):
        # datatype is typename or struct
        types = self.types
        if name in types:
            raise SemanticError(
                "cannot redefine existing datatype {}".format(name))
        if not isinstance(datatype, Struct):
            # datatype must be a string
            atype = types.get(datatype)
            if atype is None:
                native = "|" + datatype
                if native in prefixed_primitives:
                    types[datatype] = native
                else:
                    raise SemanticError(
                        "undefined datatype {}".format(datatype))
        else:
            if datatype.parent:
                datatype = Struct(datatype)  # make a copy of datatype
            datatype.parent = self
        types[name] = datatype  # a str or Struct


# Datum is a leaf in the layout - an instance of an array or or scalar value.
# Datatype atype either a named type (primitive or typedef) or a Struct,
#   which may remain partially unresolved until this Datum has a parent.
class Datum(object):
    __slots__ = "parent", "params", "atype", "shape", "location"

    def __init__(self, atype, shape=None, location=None):
        self.parent = None
        self.params = None
        if not isinstance(atype, (str, Struct)):
            raise SemanticError("Datatype must be name or Struct")
        if location is None:
            self.location = None
        elif isinstance(location, Integral):
            location = int(location)
            if location < 0:  # location is an alignment
                if (-location) & (-location-1):
                    raise SemanticError("alignment must be power of two")
            self.location = location
        if shape:
            dims = []
            for d in shape:
                if isinstance(d, Integral):
                    d = int(d)
                elif not isinstance(d, Param):
                    raise SemanticError("dimension must be int or Param")
                dims.append(d)
            self.shape = tuple(dims)
        else:
            self.shape = None


# Note that a Datum may be anonymous, while a Param may not.
# Thus, when a raw parameter is inserted into its parent Group or Struct,
#       its parent and name attributes must be set.
# The address can be:
#   >= 0 if known (read, written, or specified in layout)
#   < 0 if alignment specified in layout, overrides iN alignment
#   None if unspecified
# If this layout is a template, how to recover original state
class Param(object):
    __slots__ = "parent", "name", "value", "tname", "address"
    def __init__(self, basetype, location=None):
        self.parent = self.name = None
        if isinstance(basetype, Number):
            self.value = basetype
            self.tname = self.address = None
            return
        self.value = None
        if isinstance(basetype, ArrayType):
            basetype = basetype.name
        if not _param_type.match(basetype):
            raise ValueError("parameter type must be integer primitive")
        self.tname = basetype  # used only to dump into layout file

    # Emulate param attribute of _ParamX instance
    @property
    def param(self):
        return self

    @property
    def value(self):
        v = self.param.value
        minvalue = self.minvalue
        if v > 0:
            v += self.increment
        elif v < minvalue:
            v = minvalue
        return v

    def __str__(self):
        return self.name

    def __add__(self, y):
        if not isinstance(y, Number):
            raise ValueError("can only add integer to Parameter")
        return _ParamX(self, -1, y)

    def __invert__(self):
        return _ParamX(self, 0, 0)


_param_type = re.compile(r"[<|>]?i[1248]$")


class Group(dict):  # Folder? Block?
    def __init__(self):
        self.parent = None
        self.externs = None


class List(object):  # Series? Listing? Menu? Roster?
    def __init__(self, parent=None):
        self.parent = None


class ArrayType(object):
    __slots__ = "parent", "params"
    def __init__(self, atype=None, shape=None, alignment=None):
        self.parent = None  # always a Layout
        self.params = None


class Struct(ArrayType, dict):
    __slots__ = ()
    def __init__(self, *args, **kwargs):
        # This relies on kwargs being an OrderedDict in python >= 3.7!
        # In earlier versions would need messy collections.OrderedDict.
        # Alternative using *args works for all cases.
        if args:
            if kwargs:
                raise TypeError("Struct cannot accept both *args and **kwargs")
            if len(args) % 2:
                raise ValueError("Struct needs even number of args")
            nameval = zip(args[0::2], args[1::2])
        else:
            nameval = kwargs.items()
        for name, value in nameval:
            value.install(name, self)


class Shape(tuple):
    __slots__ = "unlimited"

    def __init__(self, *dims):
        dims = list(dims)
        self.unlimited = dims and dims[0] is None
        if self.unlimited:
            dims = dims[1:]
        for i, dim in enumerate(dims):
            if isinstance(dim, Number):
                continue
            dims[i] = Dimension(dim)
        super(Shape, self).__init__(dims)

    @property
    def value(self):
        dims = []
        for dim in self:
            if not isinstance(dim, Number):
                dim = dim.value
            if dim >= 0:  # otherwise skip dimension
                dims.append(dim)
        return dims

    def __str__(self):
        dims = [str(dim) for dim in self]
        if self.unlimited:
            dims = ["*"] + dims
        return "[" + ", ".join(dims) + "]"


# TODO: Better to just keep (name/param, minval, inc) in Shape lists
# Initially name, switch to param when Var is added to parent - this
# is also when the search to find the Param happens.

# Special extended parameter type for derived dimensions
# IMAX?  or  IMAX+  or  IMAX-  or  IMAX?+  etc.
# minvalue is normally -1, but 0 for IMAX?
# Note that param attribute mimics param property of Param instance.
class _ParamX(object):
    __slots__ = "param", "minvalue", "increment"

    def __init__(self, param, minvalue, increment):
        self.param = param
        self.minvalue = minvalue
        self.increment = increment

    @property
    def value(self):
        v = self.param.value
        minvalue = self.minvalue
        if v > 0:
            v += self.increment
        elif v < minvalue:
            v = minvalue
        return v

    def __str__(self):
        text = str(self.param)
        if not self.minvalue:
            text += "?"
        increment = self.increment
        if increment > 0:
            text += "+" * increment
        elif increment < 0:
            text += "-" * (-increment)
        return text

    def __add__(self, y):
        if not isinstance(y, Integral):
            raise ValueError("can only add integer to Parameter")
        return _ParamX(self.param, self.minvalue, self.increment + y)


prefixed_primitives = {
    "|i1": True, "|i2": True, "|i4": True, "|i8": True,
    "|u1": True, "|u2": True, "|u4": True, "|u8": True,
    "|f2": True, "|f4": True, "|f8": True,
    "|c4": True, "|c8": True, "|c16": True,
    "|b1": True, "|S1": True, "|U1": True, "|U2": True, "|U4": True,
    "|p4": True, "|p8": True,
    "<i1": True, "<i2": True, "<i4": True, "<i8": True,
    "<u1": True, "<u2": True, "<u4": True, "<u8": True,
    "<f2": True, "<f4": True, "<f8": True,
    "<c4": True, "<c8": True, "<c16": True,
    "<b1": True, "<S1": True, "<U1": True, "<U2": True, "<U4": True,
    "<p4": True, "<p8": True,
    ">i1": True, ">i2": True, ">i4": True, ">i8": True,
    ">u1": True, ">u2": True, ">u4": True, ">u8": True,
    ">f2": True, ">f4": True, ">f8": True,
    ">c4": True, ">c8": True, ">c16": True,
    ">b1": True, ">S1": True, ">U1": True, ">U2": True, ">U4": True,
    ">p4": True, ">p8": True
}
