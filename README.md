# The Dudley Layout Language

Dudley is a data description language, that is, a way to specify
exactly where and how binary data is stored in a file or byte stream -
the *layout* of the data.  Dudley is inspired by XDR
(https://www.rfc-editor.org/info/rfc4506) and netCDF (particularly
"classic" netCDF-3, https://www.unidata.ucar.edu/software/netcdf).
Used as metadata for a single data stream, Dudley has roughly the same
scope as HDF5 (https://portal.hdfgroup.org/documentation) or PDB (see
https://silo.readthedocs.io/files.html).

However, unlike netCDF, HDF5, or PDB metadata, a Dudley layout may
contain parameters stored in the stream, so that a single layout may describe
many different files or data streams - a design feature more like XDR than
the self-describing file formats.  For scientific computing, this can
drastically reduce the amount of time required to parse metadata in
order to locate individual arrays of numbers in large families of
files, when you want to read back only a small fraction of what has
been written.

Perhaps even more significantly, you can design a single Dudley layout
describing every restart file a physics simulation code can produce -
the layout describes all of the variables required to specify the state of
the simulation.  Since a Dudley layout is human-readable, comments in the
layout can document the meaning of every variable in the problem state,
making it a quick reference guide for code users as well as developers.
Often, thinking about how to store a problem state most concisely and
efficiently feeds back and improves code data structure designs.

Dudley features:

  * Very simple data model consists of multidimensional arrays and
    containers that are either dicts of named members or lists of
    anonymous members (like JSON objects and arrays).
  * Human readable layout description encourages you to think
    carefully about how you store your data.  By adding comments
    a layout file you can document your data.
  * Libraries are very lightweight compared to HDF5 or PDB.
  * Fully compatible with numpy/scipy.
  * Array dimensions can be parameters stored in the data stream
    so that a single layout can describe many different datasets.
    You can easily design and describe small datasets to exchange
    information with collaborators.
  * Support for data compression and arrays of references to data or
    containers.


## Data model overview

Data arrays are multidimensional arrays of numbers, boolean values, or
text characters (ASCII or Unicode).  You can specify byte order and
size in bytes of numbers, but floating point numbers are assumed to be
in one of the IEEE-754 standard formats, and integers are assumed to
be two's complement.  Dudley data types can also be compounds built
from these primitive types, like numpy record dtypes or C structs.

Data arrays may be collected in two types of containers: dicts map variable
names to data arrays or containers, while lists are sequences of anonymous
data arrays or containers.  The analogy with python dicts and lists is as
close as possible, except Dudley dicts can only have text keys, which
often map to variable names in simulation or processing codes that wrote the
data.  This dict-list pair of containers is also very close to JSON object and
array containers.

It is possible to create a Dudley layout describing all or most of the
contents of binary files written in many other formats, such as netCDF, HDF,
or PDB.

Dudley also supports two features beyond the simple array-dict-list model
described above: First, you can specify that a data array is to be compressed
in the data stream rather than stored as it is in memory.  Dudley recognizes
gzip, zfp, png, and jpeg compression if you have installed the corresponding
open source libraries - png (lossless) and jpeg (lossy) are restricted to 2D
image arrays, while gzip (lossless) and zfp (lossy) can be applied to more
general data arrays.  Second, you can store an array of references to other
data or container objects, as long as you are careful to avoid circular
references.  Unlike the basic array-dict-list model, compressed and reference
objects will only be readable by Dudley.  However, Dudley does allow you to
design and use your own custom compression or reference encoding scheme.


## Basic Dudley grammar

A Dudley layout is a human readable text format.  If the layout is in its own
file, the recommended file extension is ".dud".  A layout may also be appended
to the binary data it describes, in which case the recommended file extension
is ".bdud".  (Binary data described by a separate ".dud" file should be ".bd".)
The preferred Dudley character encoding is UTF-8, although CP-1252 or Latin-1
encodings may be discovered if assuming UTF-8 produces errors.  (All of these
are supersets of 7-bit ASCII.)

A data array is a data type - `dtype` - with an optional list of dimensions -
`[shape]` - and an optional byte address in the file - address:

    dtype[shape] @address
    dtype[shape] %align

The `[shape]` should be omitted for a scalar instance of `dtype`.  The
`@address` can be omitted if the data is at the next available address in the
stream.  Instead of `@address`, you may instead specify `%align`, which
advances the next avaialbel address to the next multiple of `align`, which must
be a power of 2.  Additionally, each `dtype` has a default alignment, so that
unless overidden by and explicit `%align` or `@address`, it will assume its
deafult alignment when determining the next available address.  The default
alignment for all the primitive data types is their size, except the complex
`c16` primitive, which has a default alignment of 8.

A dtype may be one of three things: a primitive type name, a previously
defined named data type, or an anonymous compound data type enclosed in `{}`.
The primitve data types are integers (signed or unsigned), floating point
(assumed IEEE-754), complex numbers, boolean values, or text characters (ASCII,
UTF-8, URF-16, or UTF-32).  These are specified by a single character "i", "u",
"f", "c", "b", "S", "U", which mostly follow the numpy dtype conventions
(except for the text types "S" and "U"), followed by the number of bytes in
a single primitive value:

    i1  i2  i4  i8    u1  u2  u4  u8
    f2  f4  f8    c4  c8  c16    b1
    S1    U1  U2  U4

These primitive names (and only these primitive names) may optionally have a
prefix "<" to indicate little endian (least significant first) byte order or
">" to indicate big endian (most significant first) byte order.  The "|" prefix
is also recognized to mean the native byte order of the machine interpreting
the binary data, which is initially the default behavior in the absence of any
explicit order prefix.  Any order specifier is the byte order in the stream;
the native byte order is always the assumed order for data values in memory.

The first non-comment character in the Dudley layout file may optionally be the
"<" or ">" byte order prefix to specify that the default byte order for every
primitive in the layout is "<" or ">" rather than "|".  The default byte order
for the layout may also be written into the binary file being described.  Thi
is the usual choice, so that the Dudley layout describes files written on
machines of either endianness.

A dict, such as the root dict for the whole layout, is a collectionj of named
items, each of which can be a data array, a dict, or a list.  Additionally, a
dict may contain items of a fourth type - parameters - which are a special form
of data restricted to scalar integer values that can be used as array
dimensions.  To declare these, you begin with a name, followed by one the
characters "=", "/", "[", or ":", which, respectively, declare a data array,
a dict, a list, or a parameter:

    data_name = dtype[shape] @address
    dict_name/
      data_name2 = dtype2[shape2]
      data_name3 = dtype3[shape3]
      ..
    data_name4 = dtype4[shape4] @address4
    list_name [
        dtype5[shape5],
        dtype6[shape6] @address6,
        dtype7[shape7]
    ]
    param_name: 42
    param_name2: i8 @address2

Dudley has no reserved keywords, so any character string is legal for any
name.  The only exception is that dtype names must not begin with "<", ">",
or "|".  However, if a name does not begin with an alphabetic character or
underscore "_", and contains any character not alphanumeric or underscore,
then it must be quoted, either in "..." or '...'.  Backslash escape sequences
are recognized inside quoted names.  For example,

    "dash-name" = i8

is a legal variable declaration in Dudley.

Note that after a dict delaration, subsequent array declarations all belong to
that subgroup, until the special token "..", when the name of the next item in
in the dict was expected, pops the layout back to the parent dict.

Also note that while there is no punctuation between item declarations in a
dict, the items in a list are comma separated.  An item in a list may be a
sub-list in the obvious way by enclosing it in `[...]` brackets.  Less
obviously, a dict may be an item in a list by making the first character of
the item a "/", followed by anything declaration that can go in a dict.  Where
the name of a new item in the list is expected, a "," or a "]" ends the
sub-dict, and resumes declaring the next list item, or finishes the list.
(This is why dict items cannot be comma separated.)  Unlike sub-dicts or
sub-lists of a dict, Dudley has no way to extend sub-lists or sub-dicts of a
list.

    list_name [[dtype[shape], ...], ...,
               /var_name[shape]
                var2_name[shape2]
               ,
               dtype[shape], ...]

The special token, "/", is also recognized when the name of the next item
in a dict is expected.  This pops out of all sub-dicts back to the root dict
(so you don't need a sequence of consecutive ".." to pop out of several levels
of sub-dicts).  Since Dudley ignores whitespace, including newlines (except as
a comment termination), recognizing "/" means you may always use a full path
name when declaring variables:

    /dict_name/data_name8 = dtype8[shape8]

To break this down, "/" pops back to the root dict, "dict_name/" descends into
the "dict_name" sub-dict, and "data_name8 = ..." appends a new item to
"dict_name".  Notice that if "dict_name" already exists, then "dict_name/" is
legal and begins appending more items to the dict.  Similarly, lists may be
extended simply by declaring more items:

    /list_name = [dtype9[shape9], dtype10[shape10]]

In contrast, attempting to redeclare a data array or a parameter is an error,
so "data_name = ..." would be an error.

Ordinarily, Dudley ignores whitespace, including newlines, except when
it is necessary to separate tokens.  (E.g.- "a=f8 b=i4".).  The one exception
is that Dudley treats all the characters from a "#" to the next newline as
if they were just a single newline.  In other words, "#" is the comment
character for Dudley layouts.

However, Dudley does recognize two special kinds of comments: Documentation
comments begin with "##", while attribute comments begin with "#:".  Dudley
can optionally remember document and/or attribute comments when it parses a
layout, and associate them with the array or container definition where they
appeared:

    # This is a layout comment, completely ignored, ...
    IMAX: i8  JMAX: i8  # ...as is this.
    temperature = f8[IMAX, JMAX]  ## (C) ground level air temperature in zones
      ## Document comments can be continued on multiple lines;
      ## all three of these lines refer to the data array "temperature".
      #: units="C", centering=[1,1]
      # The previous line defines "units" and "centering" attributes for
      # "temperature" (unnecessary, given the first documentation line?).
      # Attribute values may be numeric or quoted string constants, or 1D
      # homogeneous arrays of numbers or strings.  Multiple attribute comment
      # lines, like multiple document comment lines, are permitted.
    /  ## This document comment applies to the whole file.
    mygroup/  ## This document comment applies to the dict "mygroup".
      mylist[  ## This document comment applies to the list "mylist".
        f4[20]  ## This document comment applies to mylist[0].
      ]  ## This docuemnt comment again applies to "mylist" itself.


## Parameters and array shapes

Shape is a comma delimited list of dimensions, slowest varying first
("C order").  Each dimension may be a number or a symbolic parameter.  A
parameter may have + or - suffix(es) to indicate one more or less than the
parameter value.

Dimensions of length 0 are legal, meaning that the array has no data and takes
no space in the data stream.  Dimensions of -1 are also legal, and mean that
the associated dimension is removed from the shape, so the number of dimensions
is one less than the declaration.  For example, declare a variable with a
leading dimension with the parameter IF_EXISTS as its leading dimension:

    IF_EXISTS : i1
    varname = f8[IF_EXISTS, 3, 5]

Then by writing IF_EXISTS = 0, varname will not be written (will take no space
in the data stream), while by writing IF_EXISTS = -1, varname will be a 3x5
array of double precision floats.  This gives you a convenient means for
omitting a variable from some files described by a layout, while including it
in others.

A parameter declaration must precede its use in any shape.  A parameter may
be used in any descendant of the dict (or struct instance) in which it is
declared; it will shadow (supersede) any parameter of the same name declared
in an ancestor.  However, in the case of a parameter used for a shape inside
a named type declaration, it is the parameter value in scope for the
*instance* of that type which applies, not the value when the *type* was
declared (see below).


## Compound and named data types

A dtype may be one of the primitive data types, with or without an explicit <
of > order specifier, or a previously declared type name (syntax described
below), or an anonymous struct declaration in curly braces:

    { %align  # Optional alignment before first member applies to whole dtype.
        param : pvalue  # A parameter local to the struct instance.
                        # If pvalue is a dtype, takes space in each instance.
        var = dtype[shape]  # param or var may have @address or %align
                            # which are relative to each instance
        var2 = dtype[shape]
    }

Note that if the struct contains a param written as part of the struct, its
overall length in the file is unknown until the particular instance is read.
This happens for variables outside a struct declaration as well, as will be
discussed in more detail below.  You can declare custom type names like this:

    type_name {
        param : pvalue  # parameters local to the struct
                        # if pvalue is a dtype, takes space in each instance
        var = dtype[shape]  # param or var may have @address or %align
                            # which are relative to each instance
        var2 = dtype[shape]
    }

If the type contains only a single non-param member with the name "" (that is,
the empty string), then the dtype is a typedef, presented to users without
requiring any member qualification like var.member; simply var acts like the
single member.  For example:

    mesh_data {"" = f8[IMAX, JMAX]}
    x = mesh_data
    y = mesh_data
    phot = mesh_data[NGROUP]  # same as phot = f8[NGROUP, IMAX, JMAX]

Since IMAX and JMAX are not stored in the mesh_data, their value is determined
by whatever IMAX and JMAX parameters are in scope when the mesh_data dtype is
used.  Hence, mesh_data arrays may have different shapes for variables in
different dicts in a single stream (layout).

However, "mesh_data", and any other type name always has global scope; it is
illegal to define a single type name more than once in a layout; no matter
which dict it is declared in, a named type always applies to the whole file.

It is legal to redefine unprefixed primitive data types before their first use
if you want to specify a non-default alignment (the default alignment always
is the size of the primitive) or a specific byte order:

    i8 {%4 ""=|i8}  # i8 will have default alignment 4 instead of 8


## Special syntax for extending lists

In order to simplify describing HDF and PDB files containing arrays with
"unlimited" dimension, Dudley has an abbreviated syntax for extending list
variables.

    density [f8[IMAX,JMAX]]  # declares a list with a single item
    ... other declarations ...
    density@address  # Append an element to density of the same dtype[shape]
      # its last element, starting at the specified address.
    density%0  # Append an element to density at the next available address
      # (The special alignment value 0 is a no-op - use whatever alignment
      #  would apply to this data.)
    density %0 %0 %0  # Append three more elements to density.
      # A sequence of any number of @address or %align values are accepted.
    density[f8[42]]  # Since density is an ordinary list, extend as usual.
    density %0  # Appends a f8[42] element here.

    # This whole sequence is equivalent to:
    density[
        f8[IMAX, JMAX],
        f8[IMAX, JMAX]@address,
        f8[IMAX, JMAX],
        f8[IMAX, JMAX], f8[IMAX, JMAX], f8[IMAX, JMAX],
        f8[42],
        f8[42]
    ]


## Summary block

Optionally, before any other declarations, the layout stream may begin with a
single summary block in curly braces, which contains the various parameters and
variables required to find the data stream and compute any variable addresses
which are not explicitly declared in the layout:

    {
        param1 : pvalue  ##  documentation comment
        param2 : pvalue
        time : f8  # time is a typical example of a variable summary value
    }

This summary block is a part of the layout, as if the {} were not present.
However, it may be used as a struct datatype in a separate summary data stream
describing a family of files using this layout, so that someone reading this
summary datastream will be able to compute the exact location of any variable
in the whole family - which file as well as what address within the file -
from the data in the summary stream alone.  Thus, when a layout begins with a
summary block, it should contain no explicit @address specifiers (except perhaps
in struct definitions) nor any indeterminate length struct instances.  In
other words, a layout which begins with a summary block can serve as a
template for a family or indeed a whole category of files.


## File signatures

The recommended extension for a Dudley layout is .dud, and for binary files
natively describe for such a layout .bd (for "binary data").  However, the
Dudley layout may also be appended to the end of the binary file to produce
a single self-describing file.  Of course, a Dudley layout may also be
generated for a non-native binary file such as an HDF or PDB file, in which
case the separate layout .dud file is recommended.

A native Dudley binary file begins with one of two eight byte signatures:

    8d < B D 0d 0a 1a 0a   (8d 3c 42 44 0d 0a 1a 0a)
    8d > B D 0d 0a 1a 0a   (8d 3e 42 44 0d 0a 1a 0a)

The < variant makes the default byte order little endian (least significant
byte first) while the > variant make the default byte order big endian.  This
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
Here the 8d character is chosen because it is illegal as the first character
of a UTF-8 stream and it is not defined in the CP-1252 character encoding,
nor in the latin-1 encoding (it is the C1 control character RI there), and as
for the leading character of the PNG signature, any file transfer which resets
the top bit to zero will corrupt it.


## Filters

At least two common problems in data storage fall outside the scope of the
Dudley layout described so far:

The first is data compression.  Your data might intially be describable as
an array of `dtype[shape]`, but you would like to compress it somehow so that it
takes less space in your data stream.  Dudley supports compressed data with
the extended syntax:

    var = dtype[shape] -> filter_name @address

The @address (or %align) is optional as usual; it represents the address at
which the compressed data stream is written.  The `dtype[shape]` represents the
object to be compressed, and which is expected to be decompressed when read
back.  The filter must write some kind of preamble that enables it to read
back the compressed data (at least how many bytes).  Like a struct dtype which
has shape parameters in each instance, the size of the variable is unknown by
the layout, so either the layout can only be accessed sequentially, or any
subsequent variable needs an explicit @address.  Dudley recognizes filter_name
values "gzip", "zfp", "png", and "jpeg" natively, and allows you to register
custom filters.

The second problem is references to variables written elsewhere in the stream.
In this case, the form of reference variable stored in the data stream is known,
but the particular variable referenced (its dtype and shape) is unknown.  Dudley
supports references with the extended syntax

    var = dtype[shape] <- filter_name @address

Here, the dtype and shape describe the form of the stored reference, while the
filter_name takes this value and returns the variable in the layout which it
references.  The exact mechanism will differ among different underlying file
formats.  Native Dudley files define a reference filter called "ref", which
you use like this:

    var = i8[shape] <- ref

To recap the two kinds of filters: the compression-like filters -> store
a compressed version of the specified `dtype[shape]` as a string of bytes
meaningful only to the filter.  The reference-like filters <- store an array
of the specified `dtype[shape]`, which the filter somehow interprets as
references to variables described elsewhere in the layout.


## Examples

State template for a very simple 1D or 2D radhydro simulation:

    {
      IMAX := i8    ## leading dimension of mesh arrays
      JMAX := i8    ## second dimension of mesh arrays
      NGROUP := i8  ## number of photon energy groups
      time = f8     ## (ns) simulation time
    }  # summary completely specifies any file described by this layout
    r = f8[JMAX, IMAX]  ## (um) radial node coordinates
    z = f8[JMAX, IMAX]  ## (um) axial node coordinates
    u = f8[JMAX, IMAX]  ## (um/ns) radial node velocity component
    v = f8[JMAX, IMAX]  ## (um/ns) axial node velocity component
    rho = f8[JMAX-, IMAX-]  ## (g/cc) zonal mass density
    te = f8[JMAX-, IMAX-]   ## (eV) zonal temperature
    gb = f8[NGROUP+]  ## (eV) group boundaries (also no data if NGROUP zero)
    unu = f8[NGROUP, JMAX-, IMAX-]  ## (GJ/cc/eV) zonal radiation density

A set of time history records for this same simulation can be structured
in many different ways:

netCDF-like, with gb a non-record variable and the rest rescord
variables:

    {
      NREC := i8    # number of records in this file
      IMAX := i8
      JMAX := i8
      NGROUP := i8
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

HDF5 or PDB-like, with each record variable a homogeneous list - the
list index corresponding to the UNLIMITED dimension:

    IMAX := i8
    JMAX := i8
    NGROUP := i8
    gb = f8[NGROUP+]  # group boundaries do not change
    time = [f8]
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
    # Thus, this layout could not be used as a template.
