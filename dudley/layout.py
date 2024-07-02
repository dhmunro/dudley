"""
"""

from numbers import Number, Integral
import re


class Layout(object):
    """Dudley layout

    Attributes
    ----------
    root : Group
        root group for this layout

    types : dict
        dict of named datatypes used in this Layout
    """
    def __init__(self, description, data):
        pass

    #------ Following section is commands implementing parser rules. ------
    def var(self, name, atype, shape=None, location=None):
        ushape = shape and shape[0] is None

    def shape(self, *dims):
        ushape = dims[0] is None
        if ushape:
            dims = dims[1:]
        if len(dims) == 1 and isinstance(dims[1], list):
            dims = dims[1]
        for i, dim in enumerate(dims):
            if isinstance(dim, Number):
                continue
            altmode = False
            increment = 0
            if isinstance(dim, tuple):
                altmode = len(dim) == 3
                increment = dim[-1]
                dim = dim[0]
            dims[i] = self.find_param(dim, increment, altmode)
        if ushape:
            dims = [None] + dims
        return dims

    def param(self, name, basetype, location=None):
        if isinstance(basetype, tuple):
            basetype, location = basetype

    def cd(self, name=None):
        pass

    def cdup(self, name=None):
        pass

    def open_list(self, name):
        pass

    def close_list(self):
        pass

    def atype(self, name, atype, shape=None, alignment=None):
        shape = self.shape(shape)
        if not alignment:
            alignment = None
        elif alignment > 0:
            alignment = -1

    def open_struct(self):
        pass

    def close_struct(self):
        pass

    def open_group(self):
        pass

    def close_group(self):
        pass

    def set_address(self, location):
        pass

    def var_extend(self, name, *address_list):
        if len(address_list == 1) and isinstance(address_list, list):
            address_list = address_list[0]

    def pointee(self, pointer, atype, shape=None, location=None):
        shape = self.shape(shape)

    def open_root(self, name):
        pass

    def atvar(self, basetype, location):
        pass

    def close_root(self):
        pass

    def cdroot(self, name):
        pass


class Var(object):
    __slots__ = "parent", "params", "atype", "shape", "address", "align"
    def __init__(self, atype, shape=None, location=None):
        self.parent = None
        self.params = None


# Note that a Var may be anonymous, while a Param may not.
# Thus, when a raw parameter is inserted into its parent Group or Struct,
# its parent and name attributes must be set.
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
    def __init__(self, atype=None, shape=None, alignment=None):
        self.parent = None  # always a Layout
        self.externs = None


class Struct(ArrayType):
    pass


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
