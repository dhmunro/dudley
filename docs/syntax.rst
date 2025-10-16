Dudley Syntax
=============

Dudley is designed to be easily parsable.  It has no keywords and requires
whitespace only where necessary to separate tokens.  Newline characters
terminate comments (opened by a `#` character), but are otherwise treated like
any other whitespace.  Each token is a name (possibly in quotes), a number
(possibly signed), or punctuation.

Fundamentally, a Dudley layout is a sequence of items.  Each item can be one of
five different things:

**data**
  an n-dimensional array of numbers or (fixed length) text strings

**dict**
  a collection of named items (any of the five kinds)

**list**
  a sequence of anonymous data, dict, or list items

**datatype**
  the type of each element of a data array, may be:

  * primitive, one of 19 predefined types (int, float, ASCII, or unicode)
  * compound, a sequence of named data arrays (C struct or numpy record dtype)
  * typedef, a single anonymous data array

**parameter**
  a named integer value that can be used as a data array dimension length,
  may be:

  * fixed value, set in the layout
  * variable value, stored as a scalar integer value in the binary stream

Only data and variable parameters occupy space in the binary stream the
layout describes.

The first item (item 0) of every layout is its implicitly defined root dict.
Every other item in the layout has a parent container, except for the
predefined primitive datatypes.  (These primitives are the only thing shared
among all layouts, and indeed among all binary streams Dudley can describe.)

Data item
---------

A data array is the most complicated item.  It may consist of as little as
a datatype to declare a simple scalar value, but optionally a shape, an
address, and a filter (in that order) may follow the datatype:

.. https://stackoverflow.com/questions/11984652/bold-italic-in-restructuredtext

**data**:
  datatype shape\ :subscript:`opt` address\ :subscript:`opt`
  filter\ :subscript:`opt`

A **shape** is a comma delimited list of dimensions enclosed in square
brackets `[dim1, ..., dimN]`.  Each dimension in the shape may be either an
integer value or a parameter name.  (The parameter name may optionally have
`+` or `-` suffixes as will be descibed later.)

In Dudley, the first dimension varies slowest,
the last dimension varies fastest, and there is intentionally no way to
specify reversed array index order.  This is the default ordering in numpy
(and arguably in C) but opposite to the index ordering in a FORTRAN array.
To be clear, shape `[3, 2]` in Dudley means three pairs, *not* two triples.
Each dimension in the shape may be either an integer value or a parameter
name.  (The parameter name may optionally have `+` or `-` suffixes as will be
descibed below.)

An **address** is either an absolute byte address in the binary stream, or
an alignment to specify that a few undefined padding bytes will be added to
bring the absolute address up to some even multiple of two (the value of the
alignment).  An address is `@number` in the layout, while an alignment is
`%number`.  As a special case, `%0` is a no-op, that is, the same as no
explicit address specification, which is useful in peculiar situations.

If no address field (or `%0`) is specified, the data array is located immediately
after the previous (data or variable parameter) item in the layout, possibly
adjusted by the default alignment for its datatype.  An address can be any
non-negative integer, while an alignment must be a (small) power of two (or 0).
Either kind of address field overrides the automatic placement after the
previous item.  The very first item in the layout goes at address 0 in the
stream, but the entire stream may be offset from byte 0 of the file it is in.
(For example, the offset is 16 bytes for binary files which begin with a native
Dudley file signature.)

A **filter** begins with either `-&gt;` or `&lt;-`, followed by a
name (e.g.- `gzip`) and an optional comma delimited argument list in
parentheses `(arg1, ..., argN)`, where each argument is either a number (int
or float) or a quoted string.  Filters indicate compressed data (`-&gt;`) or
references to other items (`&lt;-`).

Any filter prevents a layout from describing more than one binary file
or stream.  Lossless compression doesn't work very well for most binary data
(since low order bits of floats are already random), while references can and
should be avoided when you are designing the layout of stored data.  Although
you should avoid them, filters will be described in detail elsewhere.

Dict item
---------

A dict is a sequence of named items with no delimiters between them other than
whitespace.  The item name always comes first, followed by a punctuation
character that determines which if the five kinds of items is being declared:

**dict** item is one of:
  data_name : data

  dict_name / dict

  list_name [item1, ..., itemN]

  type_name {item1 ... itemN}

  param_name = param

  `..`

  `/`

The last two possibilities are actually not dict items; `..` opens the
parent dict (a no-op if the current dict is root), while `/` opens the root
dict.  Subsequent dict item declarations go into that newly opened dict.
(A comma `,` also closes the current dict, but that case is discussed in the
section on list items below.)

If the parent container of the current dict is a list rather than a dict, then
it counts as the root of a separate tree for the purposes of `..` and `/`.

Although all of the dict items have names, Dudley dicts keep three separate
name spaces: The main one for data, dict, and list items, a second one for type
items, and a third for parameters.  That is a data array, a datatype, and a
parameter may all have the same name - though obviously this will confuse a
human reader, even though their distinct usage is clear to the Dudley parser.

The different kinds of items also behave differently when their name is
reused.  Attempting to reuse a data item name in a single dict is always an
error.  Similarly, reusing a type item name is always an error.

However, if a sub-dict name was already used and was a sub-dict, then
that original sub-dict is reopened and subsequent item declarations go there.
Similarly, if a list name was already used and was a list, then the original
list is reopened and extended by the items in brackets `[]`.  Thus, dicts and
lists may be extended - their item declarations need not appear in order in
the layout.

Parameter names also may be reused.  Parameters resemble variables in a
block of code, except that defining a new value does not clobber the original
value, but always creates a new item in the layout.  After the redeclaration,
there is no way to get back to the previous parameter item for subsequent
array shape declarations, but any previously declared array shapes still refer
to the original parameter item.  (In the Dudley program APIs, this limitation
is enforced, even though it is only required by the layout syntax.)

Note that these rules allow you to declare new items in any dict (under the
same root) by specifying the full "path name" of the new item, e.g.::

    /dict0_name/dict1_name/dict2_name/data_name = data

However, note that dict2_name remains the current dict after such a declaration.
Furthermore, the `..` "up to parent" syntax in Dudley does *not* work the way
you might expect from the UNIX file system analogy::

    /dict0_name/dict1_name/dict2_name/data_name .. ..

is how you get from `div2_name` back to `dict0_name` in a Dudley layout - no
slashes!

List item
---------

A list is a comma delimited list of zero or more data, dict, or list items in
square brackets `[]`.

**list** item is one of:
  data

  / dict_item1 dict_item2 ... dict_itemN

  [ list_item1, list_item2, ,,,, list_itemN ]

  number

  address

As mentioned above, the comma `,` or `]` separating or terminating the list
declaration also terminates a dict item in the list.

The final two possibilities, an item which is a number (signed integer) or an
address, then all the items in the `[]` must be numbers or addresses, that is,
either `[number1, ..., numberN]` or `[address1, ..., addressN]`.  These
two special syntaxes have very different meanings.

The case of a number provides a mechanism for reopening a list item which is
itself a dict or a list.  The number is the 0-origin index into the list, and
`[number1, ..., numberN][items]` is a shorthand for
`[number1][...][numberN][items]`, which is also equivalent to
`[number1][[number2][...[[numberN]][items]...]]` - in other words a way to
extend nested lists.  As in python, a list index may be negative to refer to
the items near the end of the list, so `-1` means item `N-1`, item `-2` means
item `N-1`, and so on, if there are `N` items in the existing list.  If the
referenced item is a sub-list, then the character after the `[number]` must
be a `[`, while if it is a sub-dict, the next character must be a `/`.  In the
latter case.


==========================================================

Layout basics
-------------

Data arrays are multidimensional arrays of numbers, boolean values, or
text characters (ASCII or Unicode).  You can specify byte size and
order of numbers, but floating point numbers are assumed to be
in one of the IEEE-754 standard formats, and integers are assumed to
be two's complement.  Dudley data types can also be compounds built
from these primitive types, like numpy record dtypes or C structs.

You specify a numeric data type as a letter indicating the type, followed by a
digit (or two digits) representing the byte size, so `i4` is a 4-byte signed
integer, `u2` is a 2-byte unsigned integer, and `f8` is an 8-byte floating
point number.  Dudley recognizes a total of 19 primitive data types::

    i1 i2 i4 i8   signed integers
    u1 u2 u4 u8   unsigned integers
    b1            boolean (==0 for false, !=0 for true)
       f2 f4 f8   floating point numbers
       c4 c8 c16  complex numbers as (re, im) pairs of floats
    S1            CP1252 or Latin1 or ASCII characters
       U1 U2 U4   UTF8, UTF16, or UTF32 Unicode characters

Any of these 19 types may optionally be prefixed by `<` or `>` to indicate
little-endian (least significant byte first) or big-endian (most significant
byte first) byte order, respectively, or by `|` to indicate that the byte order
is not specified in the layout (it may be specified in the byte stream itself,
for example).  Hence `<f8` is a little-endian 8-byte IEEE-754 floating point
number.  (By default, a primitive data type prefixed by `|` is the same as the
unprefixed type, but you can change that as detailed below.)

Note that the numeric type names follow the numpy array interface protocol, but
the Dudley character data types (`S` and `U`) do not.  In Dudley, the digit
suffix refers to the (minimum) size of a single character, so that in Dudley,
the length of a text string is the (fastest varying) dimension length in the
shape - a string of text must have a shape.  (Note that the dimension length
is not necessarily the character count for `U1` and `U2`.)

You specify a multi-dimensional array in a Dudley layout as::

    dtype shape filter address

Only the `dtype` is required; the other three fields are optional.  If no shape
is specified, the "array" is just a scalar value of the given `dtype`.  The
filter is only required if you want the array to be compressed in the stream,
and should be avoided unless you have a real need - after all, the binary
number formats are already much smaller than a text representation, and
floating point numbers usually do not compress very well.

The optional address is the byte address of the beginning of the array in the
data stream; if not provided, it will be computed from the sizes and addresses
of previously declared arrays.  In other words, by default a Dudley layout
serializes a group of multi-dimensional arrays of data.  Explicit addresses,
while supported, generally restrict a Dudley layout to apply to only a single
file, like HDF5 or PDB metadata, as described more fully below.

If present, the shape is a comma delimited list of dimension lengths in square
brackets::

    f8[3, 2]  # a 3x2 array of six 8-byte floating point numbers

Always list the slowest varying dimension first (Dudley arrays are
row-major), so that `x[3, 2]` in Dudley is like `x[3][2]` in C - namely
three pairs (**not** two triples).  This is also the default order of array
shapes in numpy.  Since Dudley is merely a data description language, you
never refer to individual array elements in a layout, so this dimension order
only relates to how correct readers must interpret Dudley array declarations.

Data arrays may be collected in two types of containers: dicts and lists.  The
difference is that items in a dict have names, while items in a list are
anonymous.  An array in a dict usually represents the values of a variable of
the same name in some program::

    rho = f8[100, 200]  # density of cells in a 100x200 mesh, perhaps
    xy = f8[101, 201, 2]  # coordinates of the cell corners, perhaps

The `rho` and `xy` are the names of the arrays in the dict; every Dudley layout
has a root dict as its outmost container.  The `=` sign indicates that these
names correspond to data arrays, as opposed to another container.  No other
punctuation is permitted, but a `#` begins a comment, causing the remainder of
the input line to be ignored.  Whitespace (including newlines and comments) is
optional, unless required to separate two names::

    m=i8 n=i8  # declares scalar integers m and n

whereas `m=i8n=i8` would be a syntax error.

In addition to data arrays, dicts may contain dicts and lists::

    x = f8[3, 2]        # x is a 3x2 array of 8-byte floats
    mydict/             # mydict is a dict container
      x = i4[8]         # mydict/x is an array of 8 4-byte ints
      y = f4[42]        # mydict/y is an array of 42 4-byte floats
    ..                  # return to the parent of mydict
    y = i8[4, 3]        # y is a 4x3 array of 8-byte ints
    mydict/             # reopen mydict
      subsub/           # mydict/subsub is a dict container
        a = i2[20, 50]  # mydict/subsub/a is a 20x50 array of 2-byte ints
    /                   # return to top level dict
    z = f4[6]           # z is an array of 6 4-byte floats
    mylist [            # mylist is a list
      i4[3],            # first mylist item is array of 3 4-byte ints
      f8,               # next mylist item is 8-byte float, comma delimited
      [f4, i4]          # next mylist item is a two element list
    ]                   # return to the parent of mylist
    w = i4              # w is a 4-byte int
    mylist [            # reopen mylist
      i2,               # fourth mylist item is 2-byte int
      /                 # fifth mylist item is a dict consisting of...
        x = f8[5]       # ... x, an array of 5 8-byte floats
        y = i4[2]       # ... y, an array of 2 4-byte ints
      ,                 # , or ] closes the dict definition
      f4                # sixth mylist item is 4-byte float
    ]

The `..` and `/` symbols navigate the Dudley dict tree as they would for the
`cd` command in a UNIX shell.  The "top level" dict for the `/` directive is
either the root dict, or the nearest ancestor dict whose parent is a list.
Note that unlike items in a dict, the items in a list are `,` delimited.
(If dict items were comma delimited or list items were not, it would be
harder to recognize the close of a dict item in a list.)

Although you can reopen a dict or list in a dict by reusing its name, you
cannot reopen a list or a dict which is an element of a list - list items are
anonymous and Dudley provides no means to refer to previous elements of a list.


Parameters
----------

In scientific data sets, at least, many different arrays share dimensions in
common.  Indeed, the only structural difference among simulations is often
simply the dimensions of the arrays associated with physical quantities like
pressure or temperature - you might run many simulations with low resolution
arrays having small dimension lengths, more with medium resolution, and a few
with high resolution and correspondingly large dimension lengths.  The same is
true for collections of experimentally measured values.  Dudley, like netCDF,
allows you to give symbolic names to dimension lengths.  Unlike netCDF, named
dimensions in Dudley are optional, and far more importantly they may be written
as part of the data stream.  Thus, a Dudley layout may be parametrized so that
it can describe a whole collection of binary files.

Since parameters are named, syntactically you may define them anywhere you
could define a named data array.  However, parameter declarations differ from
array declarations in several ways.  There are two types of parameters: Fixed
value parameters simply have a definite integer value (like netCDF dimension
names).  Dynamic value parameters are written into the data stream like data
arrays.  The declarations look like this::

    FIXED_PARAM : 42  # dtype[FIXED_PARAM, 3] is the same as dtype[42, 3]
    DYNAM_PARAM : i4  # dtype[DYNAM_PARAM, 3] has variable leading dimension

The `:` character instead of the `=` distinguishes parameter declarations from
data array declarations in the case of a dynamic parameter.  The dtype of a
dynamic parameter must be one of the `i` or `u` integer primitive types.  A
dynamic parameter may not have a shape (Dudley parameters are scalar integer
values) nor a filter (why compress a scalar integer?), but it may have an
explicit address like a data array declaration.

The parameter declaration must precede its first use in a data array shape in
the layout.  A parameter name can be used in any data array shape for an array
declared in the dict where the parameter is declared, or in any descendant
container, but not outside that subtree.  A parameter declaration will shadow
any parameter of the same name declared in an ancestor dict.  Best practice is
to declare all parameters at the beginning of a dict, but Dudley does not
require this placement.

Although parameters, like named data arrays, belong to a dict, they occupy a
separate name space.  In other words, a parameter name may be the same as an
array name without confusion, although again this is bad practice since that
makes the layout harder for a human reader to understand.

As an example, consider a simple statistical experiment consisting of some
number of runs, each of which involves many trials, where in each trial several
values are measured, say `x`, `y`, and `z`.  The results could be collected
in a Dudley dict like this::

    results/
      NRUNS: i4
      NTRIALS: i4
      x = f4[NRUNS, NTRIALS]
      y = f4[NRUNS, NTRIALS]
      z = f4[NRUNS, NTRIALS]

If `NRUNS` and `NTRIALS` were fixed parameters, this Dudley dict would only
describe a specific experiment, but by storing `NRUNS` and `NTRIALS` in the
data stream, one description can apply to many different streams - perhaps one
file for each student in a class.

Unlike named data arrays, parameter names may be reused within a single dict.
That is, in addition to shadowing parameters of the same name in an ancestor
dict, a parameter may shadow a previously declared parameter of the same name
in its own dict.  Thus, parameters behave like a variable in a function in
a C or Python function - their value may change as the function executes.  The
primary reason for this is to prevent having to invent many different parameter
names to describe streams that have counted arrays::

    COUNT: i4  # could also be a fixed integer value
    x = f4[COUNT]  # dimension of x written into stream before x
    COUNT: i4
    y = f4[COUNT]  # dimension of y written into stream before y
    z = f4[COUNT]  # dimension of z same as y, but may differ from x

Effectively, a dynamic parameter is storing part of the metadata describing the
stream in the stream itself.  This mixing of data and metadata can rapidly get
out of hand, so Dudley deliberately limits metadata to this single case of
scalar parameter values as array dimensions.  This limitation of Dudley in no
way prevents you from inventing your own schemes for storing what amounts to
metadata mixed into your data.  For example, a data structure as simple as a
doubly linked list does not directly map to a Dudley layout, because dict and
list containers are restricted to be a simple tree.  However, it is easy to
store arrays of integers which you will interpret as indices into Dudley lists
or arrays in order to reconstruct more complex data structures.  These extra
integer arrays amount to metadata describing your structure, even though
Dudley itself does not "understand" how you will interpret what is stored.

Often, two arrays will have lengths that, while both variable, always differ
by one or two elements.  For example, in a simple quadrilateral mesh, vertex
centered arrays have one more value along each dimension than zone centered
arrays.  For one dimensional arrays, there is always one more bin boundary than
bin, no matter how the number of bins may vary.  To avoid having to declare
two different parameters whose values always differ by one, you can declare
a dimension length as a parameter name followed by a `+` or `-` suffix::

    NGAPS: i4
    gaps = f8[NGAPS]
    pickets = f8[NGAPS+]  # a fence always has one more picket than gap

You can use multiple `+` or `-` suffixes, so `NGAPS++` would be two more than
`NGAPS`, and so on.

Finally, Dudley recognizes two special dimension lengths: First, a dimension
may have zero length.  If any array dimension is zero, the array has no data
and takes no space in the file.  More obscurely, Dudley treats a dimension
"length" of `-1` to mean that the dimension should be removed from the shape.
In other words, the size of the array is the same as if the dimension had been
`+1`, but that unit length dimension is to be squeezed out of the shape.  You
can use this special value to create optional arrays in your stream::

    HAS_FEATURE: i1  # -1 for true, 0 for false
    x = f8[HAS_FEATURE, 3, 3]  # x[3, 3] if HAS_FEATURE=-1, else no data

Any `+` or `-` suffix is ignored if the parameter value is either 0 or -1.


Compound and named data types
-----------------------------

In addition to a (possibly prefixed) primitive type name, the `dtype`` in any
array declaration may also be a compound datatype enclosed in curly braces::

    position = {  # the dtype for position is the compound in {}
      lon = f4
      lat = f4
      elev = f4
    }[NLON, NLAT]  # each element of the position array is three f4s

In other words, the body of the compound type, or struct, has the same syntax
as the body of a dict, except that a compound type member cannot be a dict or
a list.  (But a member of a compound type can have members which themselves
have compound types.)  Each member of the compound type may have the optional
shape, filter, or address fields, although the address within a compound type
represents the address relative to the beginning of each instance of the type,
rather than relative to the start of the stream as it would mean in a dict.

This example used an anonymous compound data type.  You can also give the
compound data type a name, so that you can use for other array declarations::

    GeoLocation {  # declare GeoLocation to be a dtype
      lon = f4   # The members of this dtype are all scalar values,
      lat = f4   #   but dtype members may have shapes,
      elev = f4  #   including parametrized shapes.
    }
    position = GeoLocation[NLON, NLAT]  # same position array as before
    place = GeoLocation  # a scalar instance of GeoLocation
    paths = [  # a list of GeoLocation arrays
      GeoLocation[75],
      GeoLocation[200]
    ]

A member of a compound type may have an address field, but any addresses are
relative to the beginning of the instance of the type rather than absolute
addresses in the stream.

Like a parameter declaration, a data type declaration may appear only when
the current container is a dict.  The point of parameters and custom data types
is to give the value or type a name, which is the job of a dict, not a list.
However, a bit inconsistently, each dict keeps three separate name spaces:
one for data types, one for parameters, and the third for data arrays and
their containers.  The scope for a data type name is the same as for a
parameter - you may use it in any descendant dict or list as well as in the
dict where it was declared.  Also like parameters, data types must be declared
before their first use.

A compound data type may have no members, which maps to the `None` object in
python or `null` in javascript.  This special case is not useful if you are
designing the layout for a stream, but if you are using Dudley to capture the
state of a scipy calculation, it is inconvenient not to be able to capture
variables whose value happens to be `None`::

    mydata = {}  # produces mydata == None when read by scipy

Dudley also provides a special syntax for a "compound" data type with a single
member, which you can use to define shaped arrays as types or define aliases
for primitive types - applications where it would be confusing and unnecessary
to invent a name for the single member::

    float { = f4}  # you may prefer  the C name "float" to the Dudley "f4"
    Mesh {=float[IMAX, JMAX]}  # "Mesh" becomes an alias for "f4[IMaX, JMAX]"
    xy = Mesh[2]  # same as xy = f4[2, IMAX, JMAX] (_not_ f4[IMAX, JMAX, 2]!)


Document and attribute comments
-------------------------------

As noted earlier, Dudley treats anything between a `#` character and the next
end-of-line as a comment, that is, as it it were whitespace.  However, the
Dudley parser can collect two special types of comments, which can be
associated with the dict or list item, or with the named struct member where
those comments appeared.

Simplest is the document comment, which begins with `##`.  This should
briefly describe the meaning of the item - perhaps its units and relationship
to other items in the layout.  Multiple lines of document comments may be
associated with an item; Dudley keeps a list of the comment lines of text
after the "##" and up to the end of the line::

    te = f8[IMAX, JMAX]  ## (eV) electron temperature
                         ## ei_coupling determines how rapidly te and ti relax

Document comments are completely free-form.  Dudley also recognizes attribute
comments beginning with `#:`, which are also associated with the item where
they appear.  Again, an item may have multiple lines of attribute comments.
Document, attribute, and ordinary ignored comments may be intermixed freely
for any item, but Dudley keeps a single list of document comment lines, and
a single dict of all the attributes defined in attribute comment lines.
The format of an attribute comment is rigidly defined::

    #: attr1_name=value1 attr2_name=value2 ...

where each attribute value can be an integer, a floating point number, a
quoted text string, or a 1D homogeneous array of any of these three types
specified as a comma delimited list enclosed in `[...]`.  The attribute names
are the keys of the attribute dict Dudley will associate with the dict or list
item or struct member where the `#:` comment appears.  As a concrete example::

    #: offsets=[0, 1, -1] units="mJ/cm2/s/ster" f_stop=5.6

As for other names in Dudley, attribute names may be quoted text; Dudley
imposes no restrictions on legal attribute names.

A few attributes of the root dict have standard meanings and formats defined
here::

    #: created = "YYYY-MM-DD HH:MM:SS+00:00" (iso) or integer unix timestamp
    #: modified = "YYYY-MM-DD HH:MM:SS+00:00" (iso) or integer unix timestamp
    #: creator = "code that wrote this file"
    #: author = "name of person responsible for this data"
    #: copyright = "date and owner"
    #: license = "short name of license covering this data"
    #: dudley = "layout filename"

.. # from datetime import datetime, timezone
   # time = datetime.now(timezone.utc).isoformat(' ', 'seconds')

As an attribute of the root dict, `dudley` means the named layout file should
be inserted into this layout here.  This would usually be the only line in a
Dudley layout that is appended to the end of a binary file, save for the other
standard attribute comments mentioned here.

Another appropriate use for attributes is partially standardized here: any
data array item may have a checksum attribute.  Most of these values should be
a quoted string of hex digits (like the output of the `sha1sum` command line
utility), but the simple crc32 checksum should be an unsigned integer value::

    x = f8[200, 500]  #: crc32 = 907394167
    y = f8[200, 500]  #: sha1 = "dccad2f69992d3478cf3c46030f7abd254189473"

The "standard" attribute name should be lower case with `-` characters removed
as in these examples.  The checksum applies to the value of the data in the
stream, which may have opposite byte order from the data presented to your
program after reading.  Dudley itself only provides hooks to compute checksums
on write or check them on read, so there is no universal list of supported
algorithms.  However, crc32 is likely the best choice for an
individual array checksum, because it is overwhelmingly likely to detect
randomly corrupted bits in your stream.  If you need cryptographic security,
you almost certainly want to checksum the entire stream rather than merely
individual arrays.


Filters
-------

Dudley supports two kinds of filters.  *Compression* filters convert an array
declared in the usual way into a (hopefully shorter) byte string::

    f8[1000, 100, 100] -> zfp  # compress 1000x100x100 array using zfp

what actually is written to the data stream is the result of compressing the
array using zfp.  The zfp filter uses a lossy compression scheme, so the
1000x100x100 array you read back will not be precisely the same as what you
wrote.  ZFP has many tuning options, but the default Dudley zfp filter
simplifies its various options to just a single optional parameter.  If you
want to pass a non-default parameter value to a filter, you write the filter
like a function call::

    f8[1000, 100, 100] -> zfp(1.e-6)  # compress with tolerance 1.e-6

Dudley implements four compression filters by default, but you can define and
register your own custom filters if you wish.  Unlike an unfiltered array, you
do not know in advance how many bytes of the stream will be occupied by the
compressed array, so using any filters at all restricts a Dudley layout to
a particualr individual byte stream.  The default filters are all
simplified versions of popular open source compressors::

    *zfp(level)* **[ZFP](https://zfp.io)** is a lossy compression library.
    The Dudley `level` parameter is the ZFP *tolerance*, which is the acceptable
    absolute error for the array values if `level>0`.  If `level<0`, then
    `-level` is the ZFP *precision*, which is roughly the number of bits of
    mantissa that will be preserved, a rough way to specify the acceptable
    relative error for array values.  Finally, `level=0` specifies the ZFP
    lossless compression option.  The default is `level=-15`, which produces
    a bit better than part per thousand relative accuracy.  Only works on
    arrays of numbers (best for floats) with up to four dimensions.
    *gzip(level)* **[zlib](https://zlib.net)** is a lossless compression library.
    The `level` parameter can be 0-9 or -1, with the same meanings as the gzip
    utility.  However, Dudley makes the default `level=9` on the assumption that
    you will usually want maximum compression.  The zlib compression is not
    really designed for binary data, but it can work well on integers and text.
    *jpeg(quality)* **[jpeg](https://jpeg.org)** is a lossy image
    compression format.  Accepts only `u1[NX, NY]` data (grayscale image),
    `u1[NX, NY, 3]` data (RGB image), or `u1[NX, NY, 4]` data (CMYK image).
    The `quality` is 0-95, with `quality=75` the default.
    *png(level)* **[png](https://libpng.org/pub/png)** is a lossless image
    compression format.  Accepts only `u?[NX, NY]` data (grayscale image),
    `u?[NX, NY, 3]` data (RGB image), where `u?` is either `u1` or `u2`.
    The `level` is 0-9, with `level=9` the default.

The second kind of filter, a *reference* filter, is completely different.
Instead of converting an array of declared type and shape to an unknown
number of bytes in the file like a compression filter, a *reference* filter
converts an array of unknown type and shape into a reference to that object
where each such reference has a known datatype (usually an integer).  This
reference is roughly equivalent to declaring a `void *` in C::

    datatype shape <- ref  # this array holds references to unknown objects

Now the objects which are referenced obviously must be declared *somewhere* in
the layout - otherwise there would be no way to read them back.  Therefore,
Dudley expects to find a sequence of special declarations of the form::

    = datatype shape filter address

These can appear anywhere a named dict item is expected, but these reference
declarations are kept outside of the dict-list container tree.  The `ref`
filter is responsible for associating these special declarations with the
item containing the `<- ref` marker.  HDF5 and PDB files each have their own
`ref` filter, but these are intended to be generated only by software
translators that produce Dudley layouts describing the HDF5 or PDB binary
files.

The HDF5 an PDB reference or pointer objects were primarily designed to support
a kind of "object store" feature that, at least at first glance, maps to the
way pointers are used in C/C++ data structures.  However, C/C++ pointers do
not map very well to scipy programs, since they objects they point to (at least
in scientific programs) are usually ndarrays, or to dict-like or list-like
objects containing them, which are first-class objects in scipy or Dudley.


Catalogs
--------

Although the Dudley file format has no direct support for creating and
accessing collections of similar files, the DUdley API does support such
collections.  Namely, Dudley defines a standard higher level stream that
includes arrays of dynamic parameter values belonging to a whole collection
of individual streams, which are embedded in a family of files.  The number
of files may equal the number of individual streams, or multiple streams may
be concatenated so that there are fewer files than streams in the collection.

The higher level catalog file is also a binary file described by its own
Dudley layout


Explicit address fields
-----------------------

Dudley supports two kinds of explict address fields for data array items in
dicts, lists, or structs: You may specify either the absolute address of the
item (in the file for dict or list items, in the instance for struct items) as
`@integer_value`, or you may specify a byte alignment for the item as
`%integer_value`.  An alignment must be a (small) power of two; if the next
available address in the stream (or instance) is not a multiple of this
alignment, it will be rounded up to such a multiple, leaving a few undefined
padding bytes in the stream.

The `@value` specifier is primarily intended for software generated Dudley
layouts, for example to describe existing HDF5 or PDB files by a separate
Dudley layout.  The items in a Dudley layout ordinarily appear in the stream
in the order they are declared in the layout, but that need no be true if the
layout has explicit address specifications.

By default, the primitive types all have an alignment equal to their size.
The alignment for a compound data type is always the largest alignment among
its members - which may individually be decreased by `%value` fields if needed.
You may also use the special single member syntax for compounds to globally
change the alignment of any unprefixed primitive type, as long as this
declaration is at the global level and precedes first use of that primitive::

    f8 { = |f8 %4 }  # change f8 alignment from 8 bytes to 4 bytes

Dudley recognizes one special case alignment field: `%0` means to place the
item according to its usual alignment as if there had been no address field at
all.  This is only useful for the special shorthand list extension syntax::

    list_name [item1, item2, itemN]
    list_name address1 address2 address3 ...

is a shorthand for duplicating the last declared element (itemN) of the list
at each of the specified addresses, so the second line is the same as::

    list_name [itemN address1, itemN address2, itemN address3, ...]

The `%0` special alignment makes it possible to use the shorthand syntax to
append a series of list items as if the new items had no explicit address
field::

    list_name%0%0%0  # same as list_name[itemN, itemN, itemN]


Dudley use cases
----------------

There are two independent distinctions that can be drawn for descriptions of
binary data: First is serial versus random access - does the description allow
you to locate and retrieve random items in the stream (assuming the stream is
seekable), or do you only learn locations of data arrays in the description
once you have read previously declared arrays?  For non-seekable streams (the
intended use of XDR), this distinction is moot, since you must read the
whole stream serially anyway.  Second is whether the description is specific
to a single data stream (like PDB or HDF metadata), or is intended to describe
any one of a family of different streams (like XDR).  Dudley layouts can
handle any of the four possible use cases implied by these two dichotomies.

First, any Dudley layout with no address specifications (or only alignment
specifications) is a reasonably compact description of a stream which you
know you will read back in exactly the same sequence as you wrote it.  (A
simulation restart dump might be an example use case.)  As long as you will
read back the file in exactly the same order you wrote it, you can use all
of the constructs Dudley provides freely, including compression or reference
filters.  If you have used
parameters written to the stream for your array dimensions, there is a good
chance that this Dudley layout can be used to describe multiple data streams.
This is the use case for XDR - a Dudley layout can also be used to describe a
serial binary data stream.

By adding explicit address specifications for every item in your dict-list
container tree, you will be able to read (or write) your file randomly, rather
than being forced to read it back serially.  The price you pay is that even
with array shape parameters written to your data stream, it is unlikely
that this kind of Dudley layout can be used to describe more than one specific
binary file.  This is the only use case supported for PDB or HDF5 files.  For
many applications, such as casually saving the state of an interactive
session, this is not an important limitation.  Once again, you can use the
full set of Dudley features, including compression and reference filters.

The new use case a Dudley layout makes possible is random access to multiple
different files described by a single layout.  This is only possible if you
avoid compression or reference filters, as
well as any explicit address specifications (apart from alignment).  In this
case, from the shape parameters, Dudley can calculate the address of every
item in the layout.  If you can design a layout meeting these criteria, you
will have a Dudley template that describes a whole collection of possible
data files, each an instance of this single layout.  Thinking deeply about
how you can structure your data to make this possible, or identifying
precisely why such a structure cannot meet your needs will teach you a great
deal about the problem you are trying to solve.


File signatures
---------------

The recommended extension for a Dudley layout is .dud, and for binary files
natively described by such a layout .bd (for "binary data").  However, the
Dudley layout may also be appended to the end of the binary file to produce
a single self-describing file.  Of course, a Dudley layout may also be
generated for a non-native binary file such as an HDF or PDB file, in which
case the separate layout .dud file is recommended.

A native Dudley binary file begins with one of two eight byte signatures::

    8d < B D 0d 0a 1a 0a   (8d 3c 42 44 0d 0a 1a 0a)
    8d > B D 0d 0a 1a 0a   (8d 3e 42 44 0d 0a 1a 0a)

The < variant makes the default byte order little endian (least significant
byte first) while the > variant makes the default byte order big endian.  This
may be overridden by an explicit > or < prefix for a summary block in the
layout itself, so that the < or > may merely indicate the byte order of the
machine writing the file rather than any contents.  The first byte following
signature is address zero in the corresponding layout.

Furthermore, the second eight bytes of a native file are either all zero, or
the address of the layout appended to the end of the binary file, in the byte
order specified by the < or > character in the first eight bytes.  This will
also become the first byte of any data appended to the file if it is
subsequently extended.

This was inspired by the PNG header.  The rationale is that non-binary FTP
file transfers will corrupt either the 0d 0a sequence or the 0a character,
while the 1a character stops terminal output on MSDOS (and maybe Windows).
The 8d character is chosen because it is illegal as the first character
of a UTF-8 stream, it is not defined in the CP-1252 character encoding,
not printable in the latin-1 encoding, and finally any file transfer which
resets the top bit to zero will corrupt it.


Examples
--------

State template for a very simple 1D or 2D radhydro simulation::

    IMAX : i8    ## leading dimension of mesh arrays
    JMAX : i8    ## second dimension of mesh arrays
    NGROUP : i8  ## number of photon energy groups (zero if no radiation)
    gb = f8[NGROUP+]    ## (eV) group boundaries (also no data if NGROUP zero)
    time = f8           ## (ns) simulation time
    r = f8[JMAX, IMAX]  ## (um) radial node coordinates
    z = f8[JMAX, IMAX]  ## (um) axial node coordinates
    u = f8[JMAX, IMAX]  ## (um/ns) radial node velocity component
    v = f8[JMAX, IMAX]  ## (um/ns) axial node velocity component
    rho = f8[JMAX-, IMAX-]  ## (g/cc) zonal mass density
    te = f8[JMAX-, IMAX-]   ## (eV) zonal temperature
    unu = f8[NGROUP, JMAX-, IMAX-]  ## (GJ/cc/eV) zonal radiation density

A set of time history records for this same simulation can be structured
in many different ways:

Here is a netCDF-like version, with gb a non-record variable and the rest
rescord variables::

    NREC : i8    # number of records in this file
    IMAX : i8
    JMAX : i8
    NGROUP : i8
    gb = f8[NGROUP+]  # group boundaries do not change
    "" = {  # empty instance name effectively puts these at root level
      time = f8
      r = f8[IMAX, JMAX]
      z = f8[IMAX, JMAX]
      u = f8[IMAX, JMAX]
      v = f8[IMAX, JMAX]
      rho = f8[IMAX-, JMAX-]
      te = f8[IMAX-, JMAX-]
      unu = f8[NGROUP, IMAX-, JMAX-]
    }[NREC]

Here is an HDF5 or PDB-like version, with each record variable a homogeneous
list - the list index corresponding to the UNLIMITED dimension.  Note that this
is no longer a general template - it applies only to files with three records::

    IMAX : i8
    JMAX : i8
    NGROUP : i8
    gb = f8[NGROUP+]  # group boundaries do not change
    time = [f8]  # All time varying arrays are presented as lists.
    r = [f8[JMAX, IMAX]]
    z = [f8[JMAX, IMAX]]
    u = [f8[JMAX, IMAX]]
    v = [f8[JMAX, IMAX]]
    rho = [f8[JMAX-, IMAX-]]
    te = [f8[JMAX-, IMAX-]]
    unu = [f8[NGROUP, JMAX-, IMAX-]]
    # Dudley description requires each record to be explicitly
    # defined, for example with one line per record, like this:
    time%0  r%0  z%0  u%0  v%0  rho%0  te%0  unu%0 
    time%0  r%0  z%0  u%0  v%0  rho%0  te%0  unu%0 
    time%0  r%0  z%0  u%0  v%0  rho%0  te%0  unu%0 
    # ... and so on
