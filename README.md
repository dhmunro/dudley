# The Dudley Layout Language

Dudley is a binary data description language, that is, a tool for describing
how data is encoded in a stream of bytes.  A Dudley description, or *layout*,
specifies the contents of a binary data file, with roughly the same scope and
use cases as [HDF5](https://www.hdfgroup.org/solutions/hdf5/) and similar
self-describing binary file formats.  However, a single Dudley layout may also
describe many different files or byte streams, so it can also be used like
the [XDR standard](https://www.rfc-editor.org/rfc/rfc4506) to exchange
multiple similar data sets among programs built around a common layout.  What
makes Dudley unique is its ability to handle the combined HDF5/XDR use case:
describing a whole collection of binary files with a single layout.  This can
potentially greatly reduce the cost of locating individual data arrays in the
large collections of files produced by parallel simulations.

Like HDF5 but not XDR, Dudley is specialized for describing scientific data.
Specifically, Dudley is modeled after numpy, where n-dimensional arrays are
first class objects, typically organized using python's dict and/or list
containers.  Thus, a Dudley layout organizes data in exactly the same way as
[JASON](https://json.org), except that the elements in the container tree
are binary numpy ndarrays instead of numbers or text strings.  Of course, a
Dudley layout also maps naturally to most scipy programs.

In addition to HDF5, XDR, and JASON, Dudley attempts to encorporate the most
useful features of [netCDF-3](https://www.unidata.ucar.edu/software/netcdf)
and the less well known [PDB format](https://silo.readthedocs.io/files.html).
All of these formats were designed in the mid-1990s or earlier, when
scientific computing was very different than it is today.  The main impetus for
Dudley is to make a fresh start applying lessons learned from earlier days.

Dudley features:

* Very simple data model consists of multi-dimensional arrays belonging to
  containers that are either dicts (JASON objects) or lists (JASON arrays).
* Human readable layout description encourages you to think
  carefully about how you store your data.  By adding comments to
  a layout file you can document your data.  In other words, you can work
  directly with Dudley layouts, rather than relying on a separate library API.
* A single Dudley layout can describe many binary files or streams.  Thus,
  you can easily design and document simple formats for casual exchange of
  scientific data with collaborators.
* Fully compatible with numpy/scipy.
* Supports data compression.
* Libraries are lightweight compared to HDF5 or PDB.


## Layout basics

Data arrays are multidimensional arrays of numbers, boolean values, or
text characters (ASCII or Unicode).  You can specify byte size and
order of numbers, but floating point numbers are assumed to be
in one of the IEEE-754 standard formats, and integers are assumed to
be two's complement.  Dudley data types can also be compounds built
from these primitive types, like numpy record dtypes or C structs.

You specify a numeric data type as a letter indicating the type, followed by a
digit (or two digits) representing the byte size, so `i4` is a 4-byte signed
integer, `u2` is a 2-byte unsigned integer, and `f8` is an 8-byte floating
point number.  Dudley recognizes a total of 19 primitive data types:

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

You specify a multi-dimensional array in a Dudley layout as:

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
brackets:

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
the same name in some program:

    rho = f8[100, 200]  # density of cells in a 100x200 mesh, perhaps
    xy = f8[101, 201, 2]  # coordinates of the cell corners, perhaps

The `rho` and `xy` are the names of the arrays in the dict; every Dudley layout
has a root dict as its outmost container.  The `=` sign indicates that these
names correspond to data arrays, as opposed to another container.  No other
punctuation is permitted, but a `#` begins a comment, causing the remainder of
the input line to be ignored.  Whitespace (including newlines and comments) is
optional, unless required to separate two names:

    m=i8 n=i8  # declares scalar integers m and n

whereas `m=i8n=i8` would be a syntax error.

In addition to data arrays, dicts may contain dicts and lists:

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


## Parameters

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
arrays.  The declarations look like this:

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
require this placement.  Although parameters, like named data arrays, belong to
a dict, they occupy separate name spaces.  In other words, a parameter name may
be the same as an array name without confusion, although again this is bad
practice since that makes the layout harder for a human reader to understand.

As an example, consider a simple statistical experiment consisting of some
number of runs, each of which involves many trials, where in each trial several
values are measured, say `x`, `y`, and `z`.  The results could be collected
in a Dudley dict like this:

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


## Compound and named data types

In addition to a (possibly prefixed) primitive type name, the `dtype`` in any
array declaration may also be a compound datatype enclosed in curly braces:

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
compound data type a name, so that you can use for other array declarations:

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

A compound data type may have no members, which maps to the None object in
python or null in javascript.  This special case is not useful if you are
designing the layout for a stream, but if you are using Dudley to capture the
state of a scipy calculation, it is inconvenient not to be able to capture
variables whose value happens to be None:

    mydata = {}  # produces mydata == None when read by scipy

Dudley also provides a special syntax for a "compound" data type with a single
member, which you can use to define shaped arrays as types or define aliases
for primitive types - applications where it would be confusing and unnecessary
to invent a name for the single member:

    float { = f4}  # you may prefer  the C name "float" to the Dudley "f4"
    Mesh {=float[IMAX, JMAX]}  # "Mesh" becomes an alias for "f4[IMaX, JMAX]"
    xy = Mesh[2]  # same as xy = f4[2, IMAX, JMAX] (_not_ f4[IMAX, JMAX, 2]!)


## Filters

Dudley supports two kinds of filters.  *Compression* filters convert an array
declared in the usual way into a (hopefully shorter) byte string:

    f8[1000, 100, 100] -> zfp  # compress 1000x100x100 array using zfp

what actually is written to the data stream is the result of compressing the
array using zfp.  The zfp filter uses a lossy compression scheme, so the
1000x100x100 array you read back will not be precisely the same as what you
wrote.  ZFP has many tuning options, but the default Dudley zfp filter
simplifies its various options to just a single optional parameter.  If you
want to pass a non-default parameter value to a filter, you write the filter
like a function call:

    f8[1000, 100, 100] -> zfp(1.e-6)  # compress with tolerance 1.e-6

Dudley implements four compression filters by default, but you can define and
register your own custom filters if you wish.  Unlike an unfiltered array, you
do not know in advance how many bytes of the stream will be occupied by the
compressed array, so using any filters at all restricts a Dudley layout to
a particualr individual byte stream.  The default filters are all
simplified versions of popular open source compressors:

- *zfp(level)* **[ZFP](https://zfp.io)** is a lossy compression library.
  The Dudley `level` parameter is the ZFP *tolerance*, which is the acceptable
  absolute error for the array values if `level>0`.  If `level<0`, then
  `-level` is the ZFP *precision*, which is roughly the number of bits of
  mantissa that will be preserved, a rough way to specify the acceptable
  relative error for array values.  Finally, `level=0` specifies the ZFP
  lossless compression option.  The default is `level=-15`, which produces
  a bit better than part per thousand relative accuracy.  Only works on
  arrays of numbers (best for floats) with up to four dimensions.
- *gzip(level)* **[zlib](https://zlib.net)** is a lossless compression library.
  The `level` parameter can be 0-9 or -1, with the same meanings as the gzip
  utility.  However, Dudley makes the default `level=9` on the assumption that
  you will usually want maximum compression.  The zlib compression is not
  really designed for binary data, but it can work well on integers and text.
- *jpeg(quality)* **[jpeg](https://jpeg.org)** is a lossy image
  compression format.  Accepts only `u1[NX, NY]` data (grayscale image),
  `u1[NX, NY, 3]` data (RGB image), or `u1[NX, NY, 4]` data (CMYK image).
  The `quality` is 0-95, with `quality=75` the default.
- *png(level)* **[png](https://libpng.org/pub/png)** is a lossless image
  compression format.  Accepts only `u?[NX, NY]` data (grayscale image),
  `u?[NX, NY, 3]` data (RGB image), where `u?` is either `u1` or `u2`.
  The `level` is 0-9, with `level=9` the default.

The second kind of filter, a *reference* filter, is completely different.
Instead of converting an array of declared type and shape to an unknown
number of bytes in the file like a compression filter, a *reference* filter
converts an array of unknown type and shape into a reference to that object
where each such reference has a known datatype (usually an integer).  This
reference is roughly equivalent to declaring a `void *` in C:

    datatype shape <- ref  # this array holds references to unknown objects

Now the objects which are referenced obviously must be declared *somewhere* in
the layout - otherwise there would be no way to read them back.  Therefore,
Dudley expects to find a sequence of special declarations of the form:

    = datatype shape filter address

These can appear anywhere a named dict item is expected, but these reference
declarations are kept outside of the dict-list container tree.  The `ref`
filter is responsible for associating these special declarations with the
item containing the `<- ref` marker.  HDF5 and PDB files each have their own
`ref` filter, but these are intended to be generated only by software
translators that produce Dudley layouts describing the HDF5 or PDB binary
files.  There is no other good reason to use reference filters.


## Document and attribute comments

As implied in some of the examples, Dudley treats anything between a "#"
character and the next end-of-line as a comment, that is, as it it were
whitespace.  However, the Dudley parser can collect two special types of
comments, which can be associated with the dict or list item, or with the
named struct member where those comments appeared.

Simplest is the document comment, which begins with "##".  This should
briefly describe the meaning of the item - perhaps its units and relationship
to other items in the layout.  Multiple lines of document comments may be
associated with an item; Dudley keeps a list of the comment lines of text
after the "##" and up to the end of the line:

    te = f8[IMAX, JMAX]  ## (eV) electron temperature
                         ## ei_coupling determines how rapidly te and ti relax

Document comments are completely free-form.  Dudley also recognizes attribute
comments beginning with `#:`, which are also associated with the item where
they appear.  Again, an item may have multiple lines of attribute comments.
Document, attribute, and ordinary ignored comments may be intermixed freely
for any item, but Dudley keeps a single list of document comment lines, and
a single dict of all the attributes defined in attribute comment lines.
The format of an attribute comment is rigidly defined:

    #: attr1_name=value1 attr2_name=value2 ...

where each attribute value can be an integer, a floating point number, a
quoted text string, or a 1D homogeneous array of any of these three types
specified as a comma delimited list enclosed in `[...]`.  The attribute names
are the keys of the attribute dict Dudley will associate with the dict or list
item or struct member where the `#:` comment appears.  As a concrete example:

    #: offsets=[0, 1, -1] units="mJ/cm2/s/ster" f_stop=5.6

As for other names in Dudley, attribute names may be quoted text; Dudley
imposes no restrictions on legal attribute names.

Dudley defines meanings for a few attributes of the root dict:

    #: created = "YYYY-MM-DD HH:MM:SS+00:00" (iso) or integer unix timestamp
    #: modified = "YYYY-MM-DD HH:MM:SS+00:00" (iso) or integer unix timestamp
    #: creator = "code that wrote this file"
    #: author = "name of person responsible for this data"
    #: copyright = "date and owner"
    #: license = "short name of license covering this data"

[//]: # "from datetime import datetime, timezone"

[//]: # "time = datetime.now(timezone.utc).isoformat(' ', 'seconds'"

    #: dudley_template = filename

As an attribute of the root dict, `dudley_template` means that template
layout file should be inserted into this layout here.  As an attribute of a
struct data type, `dudley_template` means that this struct is an exact match
for the template struct in the specified template layout.  (Filename searched
for on DUDLEY_PATH if not an absolute path.)  See layout preamble section below
for more information.


## Dudley use cases

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
filters and parameters that are part of struct instances.  If you have used
parameters written to the stream for your array dimensions, there is a good
chance that this Dudley layout can be used to describe multiple data streams.
This is the use case for XDR - a Dudley layout can also be used to describe a
serial binary data stream.

By adding explicit address specifications for every item in your dict-list
container tree, you will be able to read (or write) your file randomly, rather
than being forced to read it back serially.  The price you pay is that even
with array shape parameters written to your data stream, it is unlikely
that this kind of Dudley layout can be used to describe more than one specific
binary file.  This is the only use case supported for PDB or HDF files.  For
many applications, such as casually saving the state of an interactive
session, this is not an important limitation.  Once again, you can use the
full set of Dudley features, including compression and reference filters and
parameters in struct instances.

The new use case a Dudley layout makes possible is random access to multiple
different files described by a single layout.  This is only possible if you
avoid compression or reference filters and structs containing parameters, as
well as any explicit address specifications (apart from alignment).  In this
case, from the shape parameters, Dudley can calculate the address of every
item in the layout.  If you can design a layout meeting these criteria, you
will have a Dudley template that describes a whole collection of possible
data files, each an instance of this single layout.  Thinking deeply about
how you can structure your data to make this possible, or identifying
precisely why such a structure cannot meet your needs will teach you a great
deal about the problem you are trying to solve.


## File signatures

The recommended extension for a Dudley layout is .dud, and for binary files
natively described by such a layout .bd (for "binary data").  However, the
Dudley layout may also be appended to the end of the binary file to produce
a single self-describing file.  Of course, a Dudley layout may also be
generated for a non-native binary file such as an HDF or PDB file, in which
case the separate layout .dud file is recommended.

A native Dudley binary file begins with one of two eight byte signatures:

    8d < B D 0d 0a 1a 0a   (8d 3c 42 44 0d 0a 1a 0a)
    8d > B D 0d 0a 1a 0a   (8d 3e 42 44 0d 0a 1a 0a)

The < variant makes the default byte order little endian (least significant
byte first) while the > variant makes the default byte order big endian.  This
may be overridden by an explicit > or < prefix for a summary block in the
layout itself, so that the < or > may merely indicate the byte order of the
machine writing the file rather than any contents.  The first byte of the
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


## Layout preamble

If the first non-comment character in a Dudley layout is `<` or `>`, that will
set the default byte order for all primitive types in the file, overriding
the file signature, or any other attempt to specy a default byte order.  For
example, if you are writing a Dudley layout to describe a netCDF file or an
XDR data stream, the first character of the layout should be `>`, since both
those formats always encode the data stream in big-endian or "network" order.

If the first non-comment character, or the second after a `<` or `>`, is a
`{` character beginning a struct data type that contains every parameter that
will be used in the layout, then Dudley will treat that struct as a
template type, as well as automatically writing those parameters at the
beginning of the file as if the `{...}` brackets were not present.  A file
containing such a template type is assumed to be intended as a layout
template, and Dudley will throw an error if the layout contains any explicit
addresses or any other data descriptions which are not consistent with that
use case.  A file described by such a template layout need not include any
other metadata - the parameters written at the beginning of any binary file
described by such a template layout completely determine the addresses of all
the variables in the file.

Furthermore, you can store arrays of this template type in a separate catalog
file, so that the catalog plus the template layout completely determine the
location of variables in a large collection of files covered by the catalog.
Each individual file still begins with its own parameters (duplicated in its
entry in the catalog), so it is still decipherable even if it becomes
detached from the other files in the collection.  The higher level structure of
such a catalog is flexible and not a part of Dudley itself - a Dudley template
layout is simply a hook for designing such a catalog.  (The catalog itself
is expected to have its own separate Dudley layout, but the details of the
connection between the two layouts are left to the designer.)


## Examples

State template for a very simple 1D or 2D radhydro simulation:

    {  # template type completely specifies any file described by this layout
      IMAX : i8    ## leading dimension of mesh arrays
      JMAX : i8    ## second dimension of mesh arrays
      NGROUP : i8  ## number of photon energy groups (zero if no radiation)
    }
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
rescord variables:

    {
      NREC : i8    # number of records in this file
      IMAX : i8
      JMAX : i8
      NGROUP : i8
    }
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
is no longer a template:

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
