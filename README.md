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
many different files or data streams.  This is a major design feature of XDR
not found (or not emphasized in the case of HDF) in the self-describing file
formats.  For scientific computing, sharing a common layout has the potential
to greatly reduce the amount of time required to parse metadata in
order to locate individual arrays of numbers in large families of files,
when you want to read back only a small fraction of what has been written.

Perhaps even more significantly, you can design a single Dudley layout
describing every restart file a physics simulation code can produce -
the layout describes all of the variables required to specify the state of
the simulation.  Since a Dudley layout is human-readable, comments in the
layout can document the meaning of every variable in the problem state,
making it a quick reference guide for code users as well as developers.
Often, thinking about how to store a problem state most concisely and
efficiently feeds back and improves code data structure designs.  This feature
is also useful for informal sharing of data sets among collaborators.

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
* Support for data compression.


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
or PDB.  However, unlike any of those formats, Dudley offers parametrized
array dimensions where the dimension lengths may be written as part of the data
stream.  This allows a single Dudley layout the possibility to describe many
different instances of data streams, like XDR.

Dudley also supports features beyond the simple array-dict-list model
described above in the form of filters that can be applied to data items.
Compression filters convert an array of known type and shape into a stream
of bytes whose length is stored as a prefix.  Reference filters, on the other
hand, convert data arrays whose type and shape are not described in the
original layout into integer reference numbers of known size.  This allows
Dudley to store arrays pointers to data.  (This feature is mostly included for
backward compatibility with PDB and HDF formats.)


## Data arrays

Dudley describes a multidimensional array of data by a datatype with optional
shape (that is, dimension list), an optional filter, and an optional address in
the data stream:

    datatype shape filter address

If present, the shape is a comma delimited list of dimensions.  Each dimension
may be either an integer or the name of a previously declared parameter.  For
example, if parameters IMAX and JMAX have been defined, an array of 3D velocity
vectors might be described like this:

    f8[IMAX, JMAX, 3]

Here f8 is the datatype, meaning 8 byte IEEE-754 floating point numbers.  The
dimensions are listed slowest varying to fastest varying, also called row-major
or C order, which is also the default shape ordering in numpy.  For example,
`i4[3, 2]` means three pairs (never 2 triples!) of 32-bit integers.  Dudley
intentionally does not provide any way to reverse this shape ordering.

An array datatype need not be a primitive type; you can create compound data
types like C structs or numpy records as described later, and you may define
names for types you use frequently.

IMAX and JMAX must have previously been declared as parameters, for example:

    IMAX: 7   # A parameter may have a fixed integer value,
    JMAX: i4  #   or its value may be stored in the data stream

The difference is that IMAX is part of the Dudley layout - the metadata,
while JMAX is part of the data stream itself.  When a parameter is
declared with a datatype (so it is stored in the data stream), it may have
an optional address just like a data array, but no shape or filter:

    param_name : datatype address  # general form for an in-stream parameter

The datatype is restricted to an integer (i1, i2, i4, or i8) for parameters.
Dudley will also accept unsigned integer datatypes for parameters (u1, u2, u4,
or u8), but keep in mind that Dudley implicity converts all parameter values
to i8 internally.

Often, two arrays in a layout will have array dimensions differing by one.
For example, in a hydrodynamics simulation using a quadrilaterial mesh, an
array of positions or velocities will have values at the corners of each
zone, while arrays of density or temperature will have values at the zone
center.  Hence the density array `rho` will have one fewer value along each
axis than the `x` or `y` coordinate array.  To avoid requiring two parameters
to define these arrays, Dudley recognizes one or more `+` or `-` suffixes
after a parameter name in a dimension list:

    x = f8[IPOINTS, JPOINTS]
    rho = f8[IPOINTS-, JPOINTS-]  # one fewer value on each axis

or, equivalently:

      x = f8[IZONES+, JZONES+]  # one more value on each axis
      rho = f8[IZONES, JZONES]

Similary, you can use `IZONES++` to mean two more than `IZONES`, `IZONES+++`
for three more, and so on.

Dudley assumes data will be written to the stream in the order declared in
the layout.  Unless the data array (or parameter) has an explicit address, its
address will be taken from the end of the previous array to be declared.
(The first array in the layout will go at either address 0 or, if a Dudley
file signature was found at address 0, at address 16, immediately after the
signature.)

Actually, each datatype has an alignment, which you can specify as any power
of two.  If the byte following the previous array is not a multiple of this
alignment, a few padding bytes are added so that the array address is a
multiple of its alignment.  Initially, the alignment of all the primitive data
types is their size in bytes, except for the complex types, which have the
same alignment as their floating point components.  The alignment of any
compound type defaults to the largest alignment of any of its members.

The optional address field in any array or parameter declaration may take one
of two forms:

    datatype shape filter @byte_address  # specify absolute position
    datatype shape filter %alignment     # override default datatype alignment

The `@byte_address` form overrides the default datatype alignment as well.
As a special case, `%0` is a no-op - an explicit address field which means the
same thing as omitting the address field, namely that the array will have its
default alignment.

The optional filter field will be described later.


## Primitive data types

Ultimately, the only widely portable kinds of data are numbers, either fixed or
floating point, and text strings, either as bytes or unicode.  Dudley supports
the most commonly used binary formats for these objects (at least so far in
this millenium).  Dudley primitive data type names are a subset of the numpy
array interface protocol.  The Dudley interpretation of the text types S and U
is slightly different than numpy, but otherwise these type names are all
recognized by the dtype class constructor:

    i1 i2 i4 i8            1, 2, 4, or 8 byte signed integer
    u1 u2 u4 u8            1, 2, 4, or 8 byte unsigned integer
    b1                     1 byte Boolean (0 False, anything else True)
       f2 f4 f8            2, 4, or 8 byte floating point (IEEE-754)
          c4 c8 c16        complex (re, im) from f2, f4, or f8 pairs
    S1                     ASCII or CP-1252 or Latin-1 text
    U1 U2 U4               UTF-8, UTF-16, or UTF-32 Unicode text

These type names may optionally be preceded by a single character representing
the byte order (ignored for the 1 byte types): "<" for little endian (least
significant byte first), ">" for big endian (most significant byte first), or
"|" for native order of the machine generating the data stream.  If no order
character is present, "|" is assumed (and that native order must be gotten
some other way, for example in the file signature described below).


## Dict and list containers

A Dudley dict maps names to items.  An item in a dict may be one of four
things: a data array, a parameter, a dict (that is, a sub-dict), or a list
of unnamed items, to be described later.  A Dudley layout is a tree, with
dicts and lists as the branches and data arrays as the leaves.  Every branch
or leaf in this tree has exactly one parent, which is either a dict or a list.
As you read the Dudley layout, there is always a current container, either a
dict or a list, to which you are adding items, like a current working
directory or folder in a file system.  Initially, the current container is the
root dict for the entire layout, which is created implicitly.

To add items to a dict container, do one of these:

    array_name = datatype shape filter address  # add data array
    list_name = [  # add a list container, or open an existing list
      item1,  # until the close bracket, the list is the current container
      item2,
      ...
    ]
    dict_name/  # add a dict container, or open an existing dict
      # "dict_name" becomes the current container, so any following items...
      array_name = datatype shape filter address  # ...go in "dict_name"
    ..  # return to parent (original) dict, like cd .. in a filesystem
    another_array = datatype[3, 3]  # goes in original dict

Generally, Dudley places almost no restrictions on the characters in any name,
whether a dict item name, a parameter name, or a data type name.  The only
exception is that type names other than primitives may not begin with an
order character "<", ">", or "|".  However, if you want a name which would be
an illegal variable name in python, C, or javascript (alphanumeric plus
underscore, with the first character not a digit), then you must quote it,
either with single or double quotes '...' or "...".  Backslash escape sequences
are recognized inside the quotes  For example,

    "lisp-like-variable" = f4[3]
    "Variable name with \"spaces\" and punctuation, too!" = i8

Needless to say, you should very much prefer names which are legal variable
names in python or C or javascript.

To recap, you declare items in a dict by writing the item name, followed
by "=" if the item is a data array, "[" if the item is a list container, or
"/" if the item is a dict container.  The latter acts as a "change directory"
command as well.  Notice that items in a list are comma separated, while no
punctuation (other than whitespace) separates items in a dict.

A ".." (as opposed to an item name) goes up the dict tree, just as "subdict/"
goes down.  To avoid having to keep count of how many levels you have descended,
Dudley also recognizes the character "/" when expecting the next item in a dict,
which means to go back to the top level of the current directory tree.  This
is either the root dict, or, if the current dict tree is an item of a list,
the top level dict whose parent is the list.

You have had a preview of how to add anonymous items to a list; adding data
arrays or (sub)lists looks exactly as you might expect.  However, it isn't
obvious how to add a dict to a list: If the first character in a list item is
a slash "/", followed by named dict items, that does the trick:

    list_name = [
      datatype shape filter address,  # add data array
      [  # add (sub) list
        datatype shape filter address,  # add data array to sublist
        ...
      ],
      /  # add dict
        array_name = datatype shape filter address
        dict_name/  # add dict to dict item
          array_name = datatype shape filter address
        ..  # return to previous dict level (or / for top level inside list)
        dict_name2/  # add dict to dict item
          array_name = datatype shape filter address
      ,  # comma exits any number of dict levels, resuming list items
      datatype shape filter address,  # add another data array
    ]

Within a single dict, no two items may have the same name.  For data arrays,
Dudley reports an error if you attempt to add an item with the same name.
However, for dict and list items in a dict, specifying the name of an existing
dict or list reopens the old one and appends any new items you specify to that
existing container.  (Of course, you must reopen a dict as a dict and a list
as a list, not vice-versa!)  Dudley does not provide any way to reopen a
dict or a list whose parent is a list - only containers which are named dict
items may be reopened.

As a special shorthand, you may also reopen an existing list and append a
duplicate(s) of its last element using this special syntax (assuming
the current container is a dict):

    list_name address [address2 address3 ...]

where the address(es) may be either `@byte_address` or `%alignment`.  For
example:

    list_name [f8[20], S1[12], f4[IMAX, JMAX, 3]]
    ...
    list_name %0 %0 %0  # alignment=0 means to use default alignment
    # previous line does the same thing as:
    list_name [f4[IMAX, JMAX, 3], f4[IMAX, JMAX, 3], f4[IMAX, JMAX, 3]]


## Compound and named data types

In addition to a type name, the datatype in an array declaration may also be a
compound datatype enclosed in curly braces:

    array_name = {
      member1_name = datatype1 shape1 filter1 address1
        # If @byte_address specified, it is relative to start of the instance.
      param_name : datatypeP addressP  # Instances may contain parameters...
      member2_name = datatype2[param_name]  # ... used as member dimensions.
    } shape filter address  # the {...} can describe each element of an array

In other words, the body of the compound type, or struct, has the same syntax
as the body of a dict, except that a compound type member cannot be a dict or
a list.  However, a member of a compound type can have members which themselves
have compound types.

This example used an anonymous compound data type.  You can also give a
compound data type a name like this:

    type_name {
      member1_name = datatype1 shape1 filter1 address1
      param_name : datatypeP addressP
      member2_name = datatype2[param_name]
    }

With this definition of `type_name`, the previous array declaration is simply

    array_name = type_name shape filter address

In other words, you can use `type_name` just as you would use a primitive name.

This definition of the datatype `type_name` can only appear when the current
container is a dict.  There is no way to define a named data type from within
a list or another datatype.  Although this makes it appear that the new
`type_name` can only be used within the current dict, all such type definitions
are actually at the global level, so `type_name` can be used anywhere in the
layout after the point where you define it.  The `type_name` must be unique
for the whole layout; Dudley type defintions are outside of the dict-list
container tree.

In fact, in Dudley type names and dict item names (arrays, parameters, lists,
or subdicts) have comletely separate name spaces.  Hence, Dudley allows you to
have a data array named i4, say, since in the Dudley grammar there is
never any question of whether a name refers to a type or to a dict item.
Similarly, a dict item name can be the same as a type name without any conflict.

Less obviously, you can even redefine any of the plain primitive type names
(unadorned by an explicit "<>|" order) with your own custom type, as long as
you have not previously used that undecorated primitive.  This is because
Dudley implicitly declares an undecorated primitive type at its first use,
so "i4" comes to mean "|i4" only when you first declare a variable or parameter
to have the type "i4".  Although legal, this is obviously a bad idea with one
arguable exception: You may have reason for the default alignment of a
primitive type to be different from Dudley's default of the size.

Dudley provides some special quirks to make adjustments like this.  First,
you can change the default alignment of a compound data type by placing an
aligment specifier before its first member or parameter:

    { %alignment  # This becomes the default alignment for the type as a whole.
      member1 = ...
    }

Second, if the compound type has just a single member whose name is "", the
empty string (Dudley places no restrictions on valid names!), then the type
becomes just a shorthand for the type of that single member.  This is true
even if the compound includes parameters, for example:

    mesh_type {
      IMAX: i8  JMAX: i8
      "" = f8[IMAX, JMAX]
    }
    var = mesh_type

This `var` will be presented to a user reading or writing the stream as if it
were declared "var = f8[IMAX, JMAX]", even though IMAX and JMAX values are
actually present in the stream before the array.  This comes at a steep cost,
since this mesh_type has a size unknown at the time the layout is parsed.
Types like this are similar to counted data types in XDR or HDF.  In practice,
a type declaration like:

    mesh_type {
      "" = f8[IMAX, JMAX]
    }

is much preferred, since IMAX and JMAX will now be shared across potentially
many more mesh_type instances, and `var` really behaves exactly as if it were
declared `var = f8[IMAX, JMAX]`.

Combining these two special rules, here is how you would change the default
alignment of the primitive i8 to 4 bytes:

    i8 {%4 ""=|i8}

Finally, Dudley permits a special version of the compound type declaration
to declare variables with a value of None in python or null in javascript -
just use a compound type with no members:

    var = {}  # gives None or null on read, expects None or null on write
    NoneType{}  # If you prefer, you can define a type for None, then use:
    var = NoneType  # - but there is no real advantage to this.


## Filters

Dudley supports two kinds of filters.  *Compression* filters convert an array
declared in the usual way into a (hopefully shorter) byte string:

    f8[1000, 100, 100] -> zfp  # compress 1000x100x100 array using zfp

what actually is written to the data stream is `{NBYTES:i8 ""=u1[NBYTES]}`,
which the zfp filter will decompress to the `f8[1000, 100, 100]` array of the
declaration.  The zfp filter uses a lossy compression scheme, so the
1000x100x100 array you read back will not be precisely the same as what you
wrote.  ZFP has many tuning options, but the default Dudley zfp filter
simplifies its various options to just a single optional parameter.  If you
want to pass a non-default parameter value to a filter, you write the filter
like a function call:

    f8[1000, 100, 100] -> zfp(1.e-6)  # compress with tolerance 1.e-6

Dudley implements four compression filters by default, but you can define and
register your own custom filters if you wish.  The default filters are all
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

    &datatype shape filter address

These can appear anywhere a named dict item is expected, but, like named data
types, these reference declarations are kept outside of the dict-list container
tree as a simple list in the order they appear in the layout.

Unlike everything else in the layout, these really aren't expected to be
produced by a human; instead the `ref` filter is expected to generate them
when it discovers the unknown objects when writing them, or more usually,
by a translation program which is creating the layout from a PDB or HDF file.
The reference filter is responsible for converting between the datatype in
the `<- ref` declaration and an index into this list of anonymous objects.


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
