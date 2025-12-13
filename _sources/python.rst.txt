Python API
==========

The Dudley python API has a higher level stream interface and a lower level
layout interface.  The stream interface handles saving and restoring numpy data
in individual self-describing binary files.  The layout interface handles more
formal design and construction of where and how binary data will be stored in
a file.  Thus the stream interface is what you need for concrete operations,
while the layout interface is what you need for abstract descriptions.

While the stream interface is fairly complete as far as moving data between a
binary file and a numpy environment, it lacks any way to query the type and
shape of a data array without reading it.  Familiarity with the basic structure
of the data is presumed.  When you need query operations, you need to move to
the layout interface.  For casual interactive use, often the easiest and most
convenient way to understand the contents and structure of a binary file is to
simply dump the Dudley layout for the entire file and read it.

Fundamentally, both interfaces map numpy ndarrays into a binary stream,
organized into python dict and list containers.  In order to handle numpy
record datatypes, a Dudley layout supports compound datatypes in addition to
numeric and text ndarrays.  Finally, Dudley extends numpy array shapes with
support for named parameter references as dimension lengths.  These parameters
may have dynamic values which are written into the data stream mixed with the
ndarrays.  A Dudley layout with dynamic parameters describes not just a single
binary file, but a parametrized family of files.

Stream interface
----------------

Moving data
...........

Before you can read or write binary data, you need to open a binary I/O stream
using the `dudley.openbd` function::

    from dudley import openbd
    s_root = openbd(bdfile, mode)

In this simple form `bdfile` is a filename, and `mode` is one of:

* **"r"** open read-only (the default)
* **"w"** create read-write, first delete file if present
* **"a"** open read-write, create if file not present
* **"r+"** open read-write, error if file not present
* **"w-"** create read-write, error if file present

Except for the "w" modes, if `bdfile` already exists, it must begin with a
Dudley signature, and have its Dudley layout appended to the end of the file.
If `openbd` is creating the file, it will have this format.  In other words,
Dudley acts like HDF5 or ather self-describing binary file format libraries
for this `openbd` call.

(More complex scenarios involve optional `dud` and `params` arguments to
`openbd`, which set the Dudley layout and any dynamic parameter values without
needing to read them from the file, as described later.)

The `s_root` object returned by `openbd` is the root dict of the stream, an
instance of the `SDict` container class.  `SDict` instances behave for the
most part like python dict instances, except that their keys must be text
strings, and their values are typically numpy ndarrays which are stored in
the binary file associated with the `SDict`.  For example::

    s_root["var0"] = zeros((5, 3))  # writes a 5x3 array of zeros named var0
    var0 = s_root["var0"]  # reads ndarray var0
    # SDict update, __iter__, and items methods and others work like a dict:
    s_root.update(var1=arange(5), var2=arange(5)[:, newaxis]*arange(3))
    names = list(s_root)  # get names of all items in s_root
    for name in s_root:
        print(name, s_root[name].shape)
    for name, value in s_root.items():
        print(name, value.shape)
    if "var1" in s_root:
        print("var1 is in root dict")

An `SDict` has methods beyond the standard python dict methods as well, in order
to control its attached I/O stream::

    s_root.flush()  # flush buffers and write layout at end of file
    s_root.close()  # flush and close the file (making s_root object unusable)

The `close` method is implicitly invoked by the `SDict` destructor, so if the
python object goes out of scope, the associated file will be closed.  Similarly
you can use an `SDict` like a file handle::

    with openbd("example.bd", "a") as s_root:
        s_root["var0"] = zeros((5, 3))
    # var0 either overwritten or appended to previous contents, file closed

Like a dict, an `SDict` permits you to save multiple values at once using the
`update` method.  Unlike a dict, an `SDict` has a `subset` method that allows
you to restore multiple values at once::

    var0, var2 = s_root.subset("var0", "var2")  # return value actually a dict

`SDict` instances also feature syntactic sugar beyond dict instances.  Namely,
you may use python's attribute syntax instead of its item syntax whenever the
variable name is a legal python variable name that does not conflict with any
`SDict` method names::

    s_root.var0 = value  # same as s_root["var0"] = value
    value = s_root.var0  # same as value = s_root["var0"]

This syntax is so handy in casual interactive use that there is also a hack to
work around the occasional collision of a variable name with an `SDict` method
name or a python reserved word: If the attribute name ends in underscore,
that trailing underscore is removed::

    items = s_root.items_  # same as items = s_root["items"]
    s_root.yield_ = value  # same as s_root["yield"] = value

Containers
..........

A Dudley dict may contain not only data arrays, but also sub-dict and list
containers.  `SDict` objects map to python dict objects in the obvious way,
but the Dudley `SList` object - a list container - is slightly trickier to
write because of the potential confusion between a python list and a numpy
1D array object - in fact, most numpy APIs that accept ndarray arguments will
also accept python lists or tuples (called array_like in numpy parlance).

Writing a Dudley sub-dict is straightforward.  For example to create a sub-dict
"mydict" of `s_root`, simply set it to a python dict instead of an ndarray::

    s_root.mydict = dict(var0=value0, var1=value1)

However, reading "mydict" behaves differently than reading an ndarray.  Instead
of returning the populated python dict, reading "mydict" returns the
corresponding `SDict` container::

    mydict = s_root.mydict  # mydict is an `SDict`, not a python dict
    value0 = mydict.var0  # ... etc.
    value0 = s_root.mydict.var0  # read only var0, not whole mydict

The third line of this example shows why `s_root.mydict` does not read the
entire contents of `mydict`.  If you do want to read back the entire python
dict, any `SDict` object may be invoked as a function to do so (another
enhancement to a python dict)::

    mydict = s_root.mydict()  # reads "mydict" back as a python dict
    everything = s_root()  # reads the entire bdfile into memory
    # Thus, to copy an entire file (inefficently compared to cp command):
    openbd("file2.bd", "w").update(openbd("file1.bd", "r")())

Similiarly, reading a Dudley list container does not immediately read all the
items in the list, but rather returns an `SList` instance::

    mylist = s_root.mylist  # mylist is an SList if "mylist" is a Dudley list
    value1 = mylist[1]  # reads second item in Dudley list "mylist"
    value0, value1, value2 = mylist[:3]  # reads first three items in list
    value_list = mylist[:]  # reads all items in list, like mydict()

All of the python list indexing operations work for an `SList` (just as the
dict key lookup operations work for an `SDict`).  The append and extend methods
also work, as does the len function and other python list methods::

    mylist.append(value3)
    mylist.extend([value4, value5])
    nelements = len(mylist)  # note that len(mydict) works as well
    # The += operation can be used as a shorthand for extend (and append):
    mylist += value4, value5  # same as mylist.extend([value4, value5])
    mylist += value3,  # (note trailing ,) same as mylist.append(value3)

But how do you declare that "mylist" is a Dudley list in the first place?  All
of these examples assume that `s_root.my_list` already exists, and::

    s_root.var0 = [1, 2, 3]  # same as s_root.var0 = array([1, 2, 3])

because `[1, 2, 3]`, while it is a python list, is also a numpy `array_like`
object.  The stream interface breaks this ambiguity by treating a length-2
tuple whose first element is the python list class (that is, `type([])`) to
mean that the second element is to be interpreted as a list rather than as an
array_like.  Alternatively, you can declare an empty list as just the list
class::

    s_root.mylist = list, [1, 2, 3]  # mylist is the list [1, 2, 3]
    s_root.mylist = list  # mylist is the empty list []
    s_root.mylist.extend([1, 2, 3])  # same, starting from empty list
    s_root.mylist = list, [1, (list, [-1, -2]), 3]  # recursive application

The fourth example above shows that you need to apply this rule recursively to
define nested lists.

The stream interface provides a similar special functionality if you assign a
variable using a length-2 tuple whose first element is a numpy dtype.  In this
case, the second element is a shape.  This hack enables you to declare an
array in the file without actually writing any data initially::

    s_root.var0 = dtype, shape  # declare "var0" without writing anything

You can then write the data for var0 in chunks.  The trick to do that is to
pass multiple keys to the `[]` operator::

    s_root["var0", 0:2] = part_of_var0  # partial write of var0[0:2]
    part_of_var0 = s_root["var0", 0:2]  # partial read of var0[0:2]

You use `s_dict[name]` (or `s_dict.name`) or `s_list[index]` to move down the
container tree.  To move up the container tree, both `SDict` and `SList`
objects have `parent` and `root` properties::

    s_container1 = s_container0.parent  # SDict or SList parent of container
    s_root = s_container0.root  # root SDict of the stream

Recording mode
..............

An `SDict` has modes to simplify recording the history of a data array
as it changes, perhaps during the course of a simulation.  Normally,
when you store data to an existing array, the streaming interface overwrites
the previous stored value, just as reassigning a variable in a python program
overwrites any previous value.  If instead you want to save the old value in
addition to the new value, you want the variable in the file to be an `SList`
whose elements are the values of the data array.  Since an `SList` can be
extended, this permits you to store an evolving sequence of arrays under a
single variable name::

    mydict.x = list, [x]  # store array x as the first element of an SList
    ...  # change x somehow
    mydict.x.append(x)  # append new value of x array
    ...  # change x somehow
    mydict.x.append(x)  # append new value of x array

Especially for casual interactive use, this can become tedious, as well as less
clear than you might hope for someone reading your code.  Instead, the stream
interface provides a shorthand for storing arrays as lists, with assignment
operations appending list elements::

    mydict.recording(True)  # put mydict in recording mode
    mydict.x = x  # in recording mode mydict.x becomes a 1-element SList [x]
    ...  # change x somehow
    mydict.x = x  # in recording mode same as mydict.x += x, not overwrite
    ...  # change x somehow
    mydict.x = x  # append third value of x array

Note that the first declaration of `x` must be made with `mydict` in recording
mode for this to work; once `mydict.x` is a data array, recording mode cannot
change it into an `SList` container.  In recording mode, you can
record new values for multiple variables with a single call::

    # Create SLists var0, var1, etc.:
    mydict.update(dict(var0=value0, var1=value1, ...))
    ...  # change value0, value1, etc.
    mydict.update(dict(var0=value0, var1=value1, ...))  # append values

When you reference a sub-\ `SDict`, it inherits the recording state of its
parent `SDict`, so the above update can be used to create and update an entire
tree of dicts; you don't need to append to each `SList` individually.

Recording mode works for creating and appending to lists of arrays.  `SDict`
has an independent goto mode to make it convenient to read back lists recorded
in this manner.  Each `SDict` keeps a "goto index", which is normally `None` to
indicate the `SDict` is not in goto mode.  In goto mode, any reference to a
Dudley list element acts as if the element with that index were referenced::

    mydict.goto(42)  # sets goto mode index to 42
    x = mydict.x  # same as mydict.x[42] if goto mode were off
    mydict.goto(None)  # turns off goto mode
    mydict.goto(time=t0)  # set to index where mydict.time[index] is nearest t0
    # mydict.goto is an SDict property, not just a method, which itself has
    # other useful attributes and methods:
    recording_state = mydict.goto.recording  # True or False
    goto_state = mydict.goto.goto  # current index or None
    for time in mydict.goto.time:  # "time" can be any SList variable in mydict
        ...  # Loop over all elements of mydict.time, setting goto index
        ...  #   to corresponding value on each pass.
    with mydict.goto:  # remember goto and recording states
        mydict.goto(42)  # temporarily sets goto mode index to 42
        x = mydict.x  # retrieves x[42]
    # mydict goto and recording modes restored to before with statement

With a keyword argument, you can specify an index using any list of scalar
values in `mydict` - the variable `mydict.time` is an `SList` of times in the
above example.  To work as a goto keyword, a variable must have a scalar
value, but for the iterator `mydict.goto.varname`, the values of `varname` can
be anything.

Layout interface
----------------

Dicts, lists, and data
......................

Usually, the best way to build a Dudley layout that is not associated with any
binary data file is to write a ".dud" text file, then parse it with::

    l_root = opendud(dudfile, mode)

The `dudfile` argument can be the name of a text file or a python `TextIOBase`
text stream object.  The `opendud` function parses this text according to the
Dudley language, returning an `LDict` object representing the root dict of the
layout.  Unlike an `SDict`, the `LDict` is not associated with any particular
binary data stream - you cannot use it to read or write data.  However, every
`SDict` or `SList` container has an associated `LDict` or `LList` container
which is the description of its contents in the Dudley data model.  You can
retrieve this description using the read-only `dud` property::

    l_root = s_root.dud  # get entire layout for a binary stream

Unlike the stream interface, the layout interface is not designed for casual
interactive use.  There is no syntactic sugar like mapping attribute names to
item names; there are few convenience features like recording mode.  That said,
`LDict` and `LList` containers both implement many of the methods python
programmers expect in dict or list containers::

    item = l_dict[name]
    nitems = len(l_dict)
    if name in l_dict:
        ...
    names = list(l_dict)  # all item names
    for name in l_dict:
        ...
    for name, item in l_dict.items():
        ...
    
    item = l_list[index]
    nitems = len(l_list)
    for item in l_list:
        ...

While the stream interface has no classes beyond the `SDict` and `SList`
containers, the layout interface must describe all of the different kinds
of objects in the Dudley language.  Besides dicts and lists, there are
data arrays, parameters, datatypes, and primitives, all of which are
subclasses of a generic item class.  There are a couple of helper classes as
well for things like filters.

Creating a data item in an `LDict` (or `LList`) is similar to declaring an
array without writing it in an `SDict` (or `SList`)::

    l_dict[name] = datatype, shape, align, filt  # only datatype required
    l_list += datatype, shape, align, filt
    l_list.append(datatype, shape, align, filt)  # this adds a single item

To create a dict or list container, you use the python "dict" or "list" class
(or any subclass) as if it were a datatype::

    l_dict[name] = dict  # create a sub-dict called name
    l_dict[name] = list  # create a list called name
    mydict = l_dict.getdict(name)  # create new or retrieve existing dict
    mylist = l_dict.getlist(name)

    l_list += dict  # trailing comma unnecessary, or l_list.append(dict)
    l_list += list  # trailing comma unnecessary, or l_list.append(list)
    # LList + operator behaves differently from python list:
    # item = l_list + something     is shortthand for
    # l_list += [something]; item = l_list[-1]
    mydict = l_list + dict
    mylist = l_list + list

The special Dudley syntax for duplicating previous data items in a list has an
analog in the layout interface::

    l_list += l_list[-1]  # "l_list[%0]" in a Dudley layout
    l_list += l_list[i]  # "l_list[i%0]" in a Dudley layout
    l_list += l_list[i], align  # "l_list[i%align]" in a Dudley layout

Datatypes and parameters
........................

In addition to data, dict, and list items, datatype and parameter items may be
associated with an `LDict`.  You create and access parameters using the
`params` property and datatypes using the `types` ; both of these are
themselves dict-like objects::

    param = l_dict.params[name]  # LParam parameter item for name
    datatype = l_dict.types[name]  # LType datatype item for name
    # Note: param or datatype may be in an ancestor of l_dict
    # However, when used as an iterator, only parameters or types with
    #   l_dict as their parent are iterated over:
    for param in l_dict.params:
        ...
    for datatype in l_dict.types:
        ...
    
In order to create a parameter, use one of::

    param = l_dict.params(name, value)  # create fixed parameter
    param = l_dict.params(name, datatype, align)  # create dynamic parameter
        # datatype must be integer primitive, align is optional

To reference a parameter in a shape, simply include an `LParam` object in its
shape list.  You can add or subtract a small integer value from an `LParam`
reference in order to indicate Dudley "+" or "-" suffixes.  For example::

    NZONES = l_dict.params("NZONES", "i8")
    ...
    l_dict["rho"] = "f8", (3, NZONES)  # rho is 3xNZONES array of doubles
    l_dict["x"] = "f8", (3, NZONES+1)  # x is 3x(NZONES+1) array of doubles

When you retrieve a data array with `l_dict[name]` or `l_list[index]`, you get
a `DData` object, which you can query to determine the datatype, shape, align,
and filt parameters used to create it::

    l_data = l_container[key]
    datatype, shape, align, filt = l_data
    datatype = l_data.datatype
    shape = l_data.shape
    align = l_data.align  # 1 if address specified, 0 if defaulted
    address = l_data.address  # None if alignment specified
    filt = l_data.filt

The `shape` is a tuple of dimensions, which may contain `ParamRef` objects as
well as integer dimension lengths.  A `ParamRef` has `param` and `suffix`
properties.

In order to create a typedef datatype, you can use (shape and align are
optional)::

    datatype = l_dict.types(name, datatype, shape, align)

To create a compound datatype, use a python "with" statement::

    with l_dict.types(name) as datatype:
        # Inside the block, datatype acts like a dict container.
        datatype[mname0] = datatype0, shape0, align0
        datatype[mname1] = datatype1, shape1, align1
        ...  # datatype is open and unusable as an array type inside block
    # datatype is closed and usable outside its with block

Besides `LType` objects, a `datatype` argument in an array declaration may be
a string, which can be either a (prefixed or unprefixed) primitive type name,
or a previously defined type name (in the current container or an ancestor).

Alignment and address
.....................

The optional `align` argument in array and dynamic parameter declarations can
be used to slightly adjust the byte address of the data in a file.  Primitive
datatypes have an alignment equal to their byte size (of each floating point
component in the case of complex), meaning that the byte address of that
primitive will always be a multiple of its size.  However, for any individual
data array, you can override that default alignment by specifying an `align`
argument in its declaration.  Typedef or compound datatypes have alignment
equal to the largest alignment of any member by default, but that too may be
overridden by an `align` argument for specific arrays.  An `align` value must
always be a small power of 2: 1, 2, 4, or 8.  As a special case, an `align`
value of 0 means to use the default alignment of the `datatype` of the array.

However, the Dudley language permits you to declare arrays with a specified
byte address (`@address`) instead of just an alignment adjustment (`%align`).
In the python layout interface, such an address specification is indicated by
an `align` value with a special `Address` object instead of an integer::

    l_dict["mydata"] = datatype, shape, Address(12345)

declares that the data array "mydata" begins at exactly byte address 12345 of
the file.  Such an address ignores the default datatype alignment restriction
(just as it would be ignored if you specified a non-zero `align`).

Attributes and documentation
............................

Each item in the layout may have a list of documentation lines or a dict of
attributes or both, corresponding to any documentation or attribute comments in
the Dudley layout language.  You access these using the `docs` and `attrs`
methods of any LItem (LData, LDict, LList, LParam, or LType).

To append to the list of documentation lines, use::

    l_item.docs("Text of first line of documentation.",
                "Text of second line of documenation.", ...)

To retrieve the list of documenation lines associated with an l_item, just
call the `docs` method with no arguments::

    docs = l_item.docs()  # ["line1", "line2", ...] or []

To add to the doct of attributes, use::

    l_item.attrs({"attname1": value1, "attname2": value2},
                 attname3=value3, attname4=value4)

That is, you may add new attribute either by passing the `attrs` method a dict
containing them, or by using keyword arguments directly.  To retrieve the dict
of attributes, just call the `attrs` method with no arguments::

    attrs l_item.attrs()  # {"name1": value1, "name2": value2, ...} or {}

(If the list returned by `docs` or the dict returned by `attrs` is not empty,
it is the actual mutable list or dict stored in the Layout, so be careful not
to modify it.  On the other hand, an empty list or dict returned is *not*
stored in the Layout, so modifying that temporary object will have no effect
on the Layout.)

Filters
.......

Data array declarations, except for datatype members, may include an optional
filter argument.  There are two filter classes; `CFilter` is compression
filters, while `RFilter` is reference filters::

    cfilt = CFilter(filtname, arg1, arg2, ...)  # arguments are optional
    rfilt = RFilter(filtname, arg1, arg2, ...)  # arguments are optional
    
Stream and layout
-----------------

You can open a stream without without reading the layout from the stream by
passing `opendb` a layout parameter.  This paramter may be either a layout
root dict, or another stream root dict (to use the layout associated with that
stream).  You may also optionally pass a 1D array_like list of all the dynamic
parameter values for the stream you are opening, to avoid reading them from the
file as well::

    s_root = openbd(bdfile, mode, l_root, params)
    l_dict = s_dict.dudley  # get the `LDict` associated with an `SDict`
    l_list = s_list.dudley  # get the `LList` associated with an `SList`

In this form, the `mode` argument may have a "<" or ">" prefix to indicate a
little or big endian byte order without reading the file.

You can also retrieve shape information with expanded parameter values::

    value = param.value(s_container)  # param value in stream of s_container
    shapex = s_container.shape(l_data)  # shape of l_data, params expanded
    dtype = datatype.dtype(s_container)  # expand any parameters in datqatype
