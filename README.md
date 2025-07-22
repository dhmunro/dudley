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
contain parameters, so that a single layout may describe many
different files or data streams - a design feature more like XDR than
the self-describing file formats.  For scientific computing, this can
drastically reduce the amount of time required to parse metadata in
order to locate individual arrays of numbers in large families of
files, when you want to read back only a small fraction of what has
been written.  Perhaps even more significantly, you can design a
single Dudley layout describing every restart file a physics
simulation code can produce - only the specific parameter values
(array dimensions) need be stored in the individual files.  Since a
Dudley layout is human readable, such a restart description can also
serve as a quick reference guide for all the variables used by the
code itself.

Dudley features:

  * Very simple data model consists of multidimensional arrays and
    containers that are either groups of named members or lists of
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


## Data model

Data arrays are multidimensional arrays of numbers, boolean values, or
text characters (ASCII or Unicode).  You can specify byte order and
size in bytes of numbers, but floating point numbers are assumed to be
in one of the IEEE-754 standard formats, and integers are assumed to
be two's complement.  Dudley data types can also be compounds built
from these primitive types (numpy record dtypes or C structs).

The Dudley data model is highly compatible with the python numpy
library - and therefore scientific computing in general.  In a typical
numpy program, datasets are built up from basic variables that are
ndarrays (multidimensional arrays of numbers, strings, or structs),
aggregated using groups (name-to-variable mappings, realized as dicts
in python) and lists (index-to-anonymous-variable mappings).  These
aggregates match the JSON object and array structures.  The top level
group in a Dudley layout is analogous to the root folder in a file
system, where named members of a group can be data arrays, groups,
or lists of arrays, groups, and lists.

The netCDF-3 ("classic") format supports named array variables,
including arrays with an "unlimited" slowest dimension, which amount
to homogeneous lists of arrays.  Both HDF5 and PDB permit the same
general tree structure of named array variables (including homogeneous
lists via "unlimited" dimensions), but neither has direct support for
arbitrary lists of unnamed arrays.

It is possible to produce a Dudley layout which describes much or all
of the data in an HDF5 or PDB file - that is, you can very often use
an HDF5 or PDB file without modification as the binary stream
described by a Dudley layout.

Dudley layouts are completely transparent - you know exactly where
your data is being stored, and how much you will need to read back in
order to locate any data array you wrote.  If you will always read
back the entire stream you have written, this is not a very important
feature.  However, a modern simulation may store many terabytes of
data requiring gigabytes of HDF5 metadata, and you very likely will
later want to focus on much smaller subsets - if you need to read the
entire metadata stream in order to locate the part you want, you won't
be happy.  Dudley lets you design large data layouts that you can
access efficiently.  Since a layout is a human readable text file,
Dudley also provides a means to easily share small data sets.


## Simplified grammar

    var = dtype[shape] @address  ## documentation comment associated with var
                                 ##  continuation of document comment
                                 # single # means layout comment, completely
                                 #   ignored during parsing
                                 # The @address is optional; the next available
                                 # address is the default.
    var = dtype[shape] %align    # variant of optional @address specifying only
                                 #   alignment - align may be 1, 2, 4, 8, or 16
    var2 = dtype[shape]  ## documentation comment (optional)
                         # Variable attribute comments begin with : and have a
                         # formal grammar of comma separated name-value pairs:
                         #: attr1=avalue, attr2=avalue,
                         #: attr3=avalue
                         # The avalue can be a number, string, or [,] list.
    group/  ## document comment for group
      var = dtype[shape]  # declares group/var, address optional
      group2/
        var = dtype[shape]  # declares group/group2/var
        ..  # back to parent group level
      var2 = dtype[shape]  # declares group/var2
      group3/
        var = dtype[shape]  # declares group/group3/var
        /  # back to root group level
    group/group2/var3 = dtype[shape]  # full or partial path on one line
    list [  # create or extend list, which is a group with anonymous members
        dtype[shape],  # optionally may have @address or %align
        / var = dtype[shape]  # a list item may be an (anonymous) group
        ,  # comma ends anonymous group declaration
        [ dtype[shape]  # a list item may be a sublist
        ]  # optional *n as for outer list allowed for sublists
    ]*n  # optional *n extends list with n of these lists of items
         # n can be a number or a parameter, may be 0
    list [n]  # extends list by n more of its last item (similar to *n)

Note that list = [/var1=dtype[shape] ... varN=dtype[shape]]*n is netCDF-like
history records.

Shape is a comma delimited list of dimensions, slowest varying first
("C order").  Dimensions may be a number or a symbolic parameter.  A symbolic
parameter may have + or - suffix(es) to indicate one more or less than the
parameter value.

    param : pvalue  ##  documentation comment

Parameters belong to groups like variables, and their scope is limited to the
group in which they are defined and its descendant groups.  A parameter must
always be defined before its first use in a shape.  Parameters may also be
stored in the data stream as integer scalar variables, although their dtype
must be an integer:

    param : dtype @address  # as for variables, @address is optional

Dimensions of length 0 are legal, meaning that the array has no data and takes
no space in the data stream.  Dimensions of -1 are also legal, and mean that
the associated dimension is removed from the shape, so the number of dimensions
is one less than the declaration.

A dtype may be one of the primitive data types, with or without an explicit <
of > order specifier, or a previously declared type name (syntax described
below), or an anonymous struct declaration in curly braces:

    {
        param : pvalue  # parameters local to the struct
                        # if pvalue is a dtype, takes space in each instance
        var = dtype[shape]  # param or var may have @address or %align
                            # which are relative to each instance
        var2 = dtype[shape]
    }

Note that if the struct contains a param written as part of the struct, its
overall length in the file is unknown until the particular instance is read.
This happens for variables outside a struct declaration as well, as will be
discussed in more detail below.

Two syntaxes are available to declare a non-primitive type name:

    type { dtype }[shape] %align  # typedef form to include a shape

    type {  # struct form
        param : pvalue
        var = dtype[shape]
    }[shape] %align  # struct form also permits overall shape and alignment

Finally, the whole layout stream may optionally begin with a single summary
block, which contains the various parameters and variables required to find
the data stream and compute any variable addresses which are not explicitly
declared in the layout:

    <{  # The leading < or > default order specifier is optional.
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
signature is address zero in the layout

Furthermore, the second eight bytes of a native file are either all zero, or
the address of the layout appended to the end of the binary file, in the byte
order specified by the < or > character in the layout.

This was inspired by the PNG header.  The rationale is that non-binary FTP
file transfers will corrupt either the 0d 0a sequence or the 0a character,
while the 1a character stops terminal output on MSDOS (and maybe Windows).
Here the 8d character is chosen because it is illega as the first character
of a UTF-8 stream and it is not defined in the CP-1252 character encoding,
nor in the latin-1 encoding (it is the C1 control character RI there), and as
for the leading character of the PNG signature, any file transfer which resets
the top bit to zero will corrupt it.

=======================================

## Basic Dudley layout grammar

Arrays of floating point, integer, or character primitives comprise
the data in a Dudley layout, while groups of named members and lists
of anonymous members are the two kinds of containers for these data.
Groups and lists may each contain groups and lists in addition to
arrays, nested arbitrarily.  Thus,

    var = datatype[shape] @address

declares that an array named "var" with the given datatype and array
shape is written at the specified byte address in the data stream.
The @address may be omitted if "var" is written at the next available
address (possibly preceded by a few bytes of alignment padding, as
explained later).  The [shape] may be omitted if this array is just a
scalar instance of the datatype.  A couple of dozen datatypes are
predefined, like "<f8" meaning an 8-byte little-endian IEEE-754
floating point value, or ">i4" meaning a 4-byte big-endian twos
complement integer value.

An array shape is a comma delimited list of dimensions [dim1, dim2,
...], in order from slowest varying to fastest varying - "C order" or
"row major order".  Hence "f8[3, 2]" means three pairs of 8-byte
floats.  (You can omit the < or > order specifier to get the default
byte order for this data stream, as explained below.)

Dudley groups are analogous to the folders in a file system.  You
create a new group (or re-open and existing group) called "grp" like
this:

    grp/
      thing1 = datatype[shape]  # thing1 is in group grp
      sub/
        thing2 = datatype[shape]  # thing2 is in group grp/sub
        ..  # ".." pops back to parent group
      thing3 = datatype[shape]  # thing3 is in group grp
      sub/
        thing4 = datatype[shape]  # thing4 is in group grp/sub
        /  # "/" pops back to root group
    thing5 = datatype[shape]  # thing5 is in group / (the root)

Notice that you can comment a Dudley layout - everything from a
"#" character to end-of-line is treated as whitespace.  Apart from
comments, Dudley treats line breaks like any other whitespace.  The
line breaks and indentation in these examples is unnecessary, so

    /grp/sub/thing6=datatype[shape] thing7=datatype[shape]

declares both thing6 and thing7 to be in the /grp/sub group.

If you find yourself naming sequences of variables like x0, x1, x2,
and so on, you might want to consider using a list container simply
called "x" instead:

    x = [
      type0[shape0],  # Note that list items are comma delimited.
      type1[shape1],
      type2[shape2]
    ]

The list "x" here is a member of the current group, just as "sub"
was a member of "grp".  You can also nest list or groups within
lists:

    y = [
      [  # Nested lists have the obvious syntax with [] delimiters.
        type0[shape0]
      ],
      /  # Delimit a group inside a list using slashes /.../.
        member1 = typem[shapem]
        member2 = typem[shapem]
        member3/  # nested groups may have subgroups
          thing8 = datatype[shape]
          ..
        member4 = []  # a list (or a group) may be empty
      /,
      type2[shape2]
    ]

Just as you can add members to a group by reopening it, you can add
items to a list after its original declaration:

    x += [  # Use the += operator to extend an existing list.
      type3[shape3] @address3,  # You may always specify
      type4[shape4] @address4   # byte addresses explicitly
    ]

You may also append arrays to a list which have the same datatype and
shape as the final list element using this shorthand:

    x @address5 @address6  # appends two more type4[shape4] items

Instead of an integer byte address value like "@ 543210", you may
specify "@ ." to get the next available address.  Ordinarily, this is
the same as simply omitting the "@ address", but in the list append
shorthand, it is useful to be able to add items with a string like
"@.@.@.@.".  (The shorthand only works if the final item in the list
is an array - it is an error if the final item is a list or group.)


## Dudley datatypes

You can name a datatype using the == operator:

    mytype == datatype[shape] %alignment

The name "mytype" applies to the entire layout; type names in Dudley
have a global namespace, distinct from the namespace of any group
(including the root group).  Once defined, you can use "mytype" as the
datatype of any array.  There is no way to change the definition of
"mytype" once it has been defined.

The "%alignment" and "[shape]" may be omitted.  If specified, the
slignment must be a small power of two; it means that mytype byte
addresses in the data stream will always fall at multiples of
alignment, by adding a few undefined padding bytes if necessary.  By
default, the primitive datatypes are all aligned to multiples of their
size (e.g.- no alignment for i1, i2 on 2-byte boundaries, i8 on 8-byte
boundaries, and so on).  If not specified, the alignment of mytype
will be the same as datatype.

You may also specify "%alignment" for individual instances of arrays
instead of "@address" in order to override the default alignment for
that particular instance of the array datatype.

Dudley implicity defines unprefixed primitive types as their
|-prefixed form at first use, so if you declare a variable as "i8",
"i8" implicitly becomes "|i8" everywhere else in the layout.  Before
the first use, you can explicity define the unprefixed primitive
names.  For example, for old 32-bit Intel machines, an i8 was
little-endian and 4-byte aligned:

    i8 = <i8 %4

But the main reason for the == syntax is to define compound data
types, analogous to C structs or numpy record dtypes.  Perhaps

    Vector3 == {
      x = f8
      y = f8
      z = f8
    }
    r = Vector3[3, 2]  # Declare a 3x2 array of Vector3 instances.

The syntax inside of the struct {} delimiters is the same as for array
declarations in any group.  If present in a struct declaration, any
"@address" means the byte offset relative to the start of the struct
instance; you can also use "%alignment" to force a non-default
alignment for any individual struct member.

By default, the alignment of the whole struct equals the maximum of
any of its members.

You may define an anonymous struct type using the {} syntax for the
datatype in any array declaration:

    r = {x=f8 y=f8 z=f8}[3, 2]

Unlike a group, you can have an array of anonymous struct instances,
like r in this example.  Unlike an anonymous struct instance, a group
may have list members.  Note that a struct instance can have members
which are anonymous struct instances, so the possibility of list
members is the only real extra feature of a group.  Also, you can
always append new members to a group, while a struct instance is
permanently confined to the members declared in the curly braces.


## Parameters

So far, a Dudley layout has the same scope as HDF5 or PDB metadata:
You can describe the location of every array written into a particular
binary file.

While you occasionally have many files with identical structure, in
scientific computing you very often encounter many files with the same
structure except for the array dimensions.  Or perhaps the simulation
ran in parallel on a large number of processors, each owning a block
of the problem with slightly varying sizes, and each writing one
member of a family of output files.

In order to describe this kind of a family of binary files by a single
layout, Dudley introduces the concept of *parameters*.  A Dudley
parameter is a symbolic dimension length which can be used in any
array shape (even in named type declarations).  Each symbol may have a
fixed value (like a named dimension in netCDF format), or its value
may be written into the data stream like a scalar (unshaped array)
value.  The latter case is the interesting one: each data file
contains just a few values - array dimensions - which determine the
precise location of all the arrays described in the layout.

    IMAX := 5  # fixed value parameter
    JMAX := i4 @address  # parameter written into data stream
    var = datatype[IMAX, JMAX, 3]  # use parameters in shapes

As for a data array, the "@address" in a parameter declaration may be
omitted.  A parameter must be a scalar of integer type (i1, i2, i4, or
i8, possibly with an order prefix).  Like data arrays, parameters may
be members of any group, but parameters have a separate namespace from
the array, list, or subgroup members.  Parameter declarations may also
appear in a struct, so that values stored in the struct instance may
be used as dimensions for subsequent arrays in the struct.

Since parameters are associated with groups or struct instances, they
will shadow another parameter of the same name that is defined higher
in the group hierarchy.  The instance of a parameter which applies to
a particular array shape is always determined when the struct
*instance* is declared.

    IMAX := i8
    var1 = f8[IMAX]  # var1 uses the root IMAX
    DemoType == {
      JMAX := i4
      mem1 = f4[IMAX]  # IMAX depends on where DemoType used
      mem2 = f4[JMAX]  # JMAX always the JMAX in this instance
    }
    grp/
      IMAX := i4  
      var2 = f8[IMAX]  # the /grp IMAX
      var3 = DemoType  # var3.mem1 uses the /grp IMAX
      ..
    var4 = f8[IMAX]  # the root IMAX, same as var1
    var5 = DemoType[3]  # var5[i].mem1 uses the root IMAX

That is, a named struct with any parametrized shapes not declared in
that struct (or an ancestor struct) inherits that external parameter
from the group (or ancestor group) where it is used to declare an
instance.  Thus, while a named type has global scope, it may be
parametrized in the same sense as an entire layout is parametrized - a
named struct with external parameters represents a whole family of
different specific structs.

Parameters serve as a simple form of documentation for how arrays in
the file are related - when two arrays share a dimension parameter,
you can be sure that those dimensions represent the same extent in the
physical model - they aren't simply accidentally equal.  Often arrays
of slightly different length are related in this manner - most
commonly, when one array represents zone boundaries, and another
represents values in each zone.  In that case, the number of
boundaries is always one greater than the number of zones.  Dudley
provides a syntax for expressing this relationship using a + or -
suffix after a parameter name:

    boundary_value = f8[IMAX]
    zonal_value = f8[IMAX-]  # has IMAX-1 elements

You can use IMAX+ for dimension length IMAX+1, IMAX-- for IMAX-2, and
so on.

Dudley permits an array dimension to be 0, which naturally means that
no data is stored, nor any space taken by the array in the data
stream.  When combined with parameters stored in the data stream, this
provides a mechanism for conditionally including arrays in a
parametrized layout, so that some files in the family described by the
layout contain the array while others do not.  Thus,

    pbins = f8[NGROUP, IMAX, JMAX]

might be radiation intensity in each zone for a radhydro code, where
NGROUP is a number of photon energies, while IMAX and JMAX are spatial
dimensions.  In problems with no radiation, by setting NGROUP=0, the
pbins array will not be present in the file, just as it is not defined
for such a simulation.

As a special case, if a parameter like NGROUP is zero, then any +-
suffixes are ignored, so if the photon group energy boundary array
is declared as

    gb = f8[NGROUP+]  # NGROUP+1 phton energy boundaries

then when NGROUP=0, gb also does not exist - gb is *not* an f8[1]
array, it is also f8[0].  That is, any array which mentions NGROUP
in its shape is omitted if NGROUP=0.

There are also situations in which you want a single layout to
describe an array which may have different dimensionality in some
files than in others.  For example, a hydrocode might handle both
2D and 1D simulations.  For a 2D simulation, the fluid velocity
might be:

    u = f8[IMAX, JMAX]  # x velocity component at IMAXxJMAX places
    v = f8[IMAX, JMAX]  # y velocity component at IMAXxJMAX places

You could get the correct number of velocities for a 1D simulation
by setting JMAX=1, but you really want u to be f8[IMAX] for a 1D
simulation.  Dudley lets you do this by interpreting a parameter
value of -1 to mean that this index is to be removed.  That is,
Dudley treats f8[IMAX, -1] as if it were f8[IMAX].

However, when you set JMAX=-1 to indicate a 1D simulation, you also
want the v array to be completely omitted.  That is, you want
v to become an f8[IMAX, 0] when JMAX=-1.  To get that behavior, a
parameter value of -1 being treated the same as parameter value 0,
use a ? suffix after the parameter name in the shape list:

    v = f8[IMAX, JMAX?]  # no y velocity component if JMAX=-1

If you need this special behavior for a dimension with a +- suffix,
the ? suffix must precede any + or -.  Like JMAX=0, JMAX=-1 removes
the dimension (or omits the variable entirely) before any + or -
increments, so any +- suffix is ignored in both those cases.

Instead of needing to parse a potentially large amount of nearly
identical metadata in order to determine what's in each file, an
interpreter needs to read only a few bytes of the file to be able to
reconstruct everything from a single parametrized layout.  Even if the
machine parsing cost is negligible, the advantage in human readability
and usefulness of the Dudley layout can be huge.  For example, you can
share a couple of dozen analysis results consisting of a few arrays
each with a colleague by simply sending a single Dudley layout along
with the binary file for each result.  The layout gives you a natural
framework for explaining the meaning of each array.


## Document comments

A comment beginning with #: is a document comment which describes the
meaning of the type, parameter, or variable defined on this line, or
on the previous line if the #: is the first non whitespace token on
the line.  If the previous line already had a document comment, this
line is a continuation of that document string.

    # An ordinary comment does not document a particular variable.
    pres = f8[IMAX, JMAX]  #: pressure (kPa) at ground level
    temp = f8[IMAX, JMAX]  #: temperature (C) at ground level
                           #: (measured in shade)

The intent is for document comments to replace data attributes in HDF5
and other formats.  If you need compact attributes that can be reduced
to just a number, you can extend the Dudley syntax to support that (by
parsing document comments), but such extensions are beyond the scope
of this basic language definition, since they have no effect on how or
where your data is stored, and any consumer of your data will need to
understand their meaning anyway.

The omission of data attributes is intended to encourage you to either
store any such information as actual named variables in your files (if
dynamic and really part of your data) or as a document comment (if
unchanging and a mere hint to the nature of the variable beyond its
data type).  Note, however, that you may be able to distinguish point
versus zone centered arrays using +- dimension suffixes.


## Primitive data types

Predefined primitive data types are based on numpy array interface:

    Signed integers:   i1, i2, i4, i8  (suffix is number of bytes)
    Unsigned integers: u1, u2, u4, u8
    Floating point:    f2, f4, f8  (IEEE 754 16, 32, 64 bit formats)
    Complex floats:    c4, c8, c16
    Boolean:           b1
    ASCII:             S1
    Unicode:           U1, U2, U4  (UTF-8, UCS-2, and UCS4)
    Pointer:           p4, p8  (extension to numpy array interface)

Unlike the numpy array interface, the S and U types do not have the
(maximum) number of characters as the count suffix - that count is
instead the fastest varying array index and variables with these types
must always be declared with at least one dimension.  Also, here the
suffix indicates which Unicode encoding, while in the numpy array
interface U always means UCS-4, or U4 here.  To convert S1 to Unicode,
best practice is to assume cp1252, falling back to latin1 if any of
the missing code points in cp1252 actually occurs in the text.  (This
is more or less the W3 recommendation for how to handle html documents
when the character set is not explicitly specified.)

These primitive types map to the following C primitive types on all
modern machines and compilers:

    i1 -> char, i2 -> short, i4 -> int, i8 -> long long
    u1, u2, u4, u8 -> unsigned versions of i1, i2, i4, i8
    f4 -> float, f8 -> double (f2 not supported in ANSI C)
    c4, c8, c16 -> (real, imaginary) pair of f2, f4, f8
    b1, S1, U1 -> same data treatment as u1
    U2, U4 -> same data treatment u2, u4
    p4, p8 -> same data treatment as u4, u8, meaning similar to void*

Note that the long data type is i8 on all 64-bit UNIX platforms (and
MacOS), but long is i4 on all Windows platforms, 64-bit or 32-bit.


## Pointer data

Pointers automatically require listing explicit addresses in the
Dudley layout, making the description specific to a single file.  In
other words, pointers are incompatible with using Dudley to create a
template describing multiple files, or with Dudley's parallel
processing support.  Each pointee must be declared like this:

    integer = type[shape] @ address

That is, a pointee is a variable whose name is a 4 or eight byte
unsigned integer value, depending on whether it was declared as a p4
or a p8.  The integer is the value written to the file, which must be
unique among all the pointees in the file.  (You could use the
in-memory pointer value, but you'd have to be careful not to free and
reallocate memory at the same address for a subsequent pointee.)  The
values 0 and (unsigned) -1 are reserved to represent the NULL pointer,
and must not appear as the integer in any pointee declaration.

Pointee declarations always have global scope like named types; they
will never be members of any group other than the root of the whole
file.


## Additional constructs

As a special case, if there is only a single member (variable
declaration) in the struct, you may omit the member (variable) name,
like the anonymous variable declarations in a list.  In this case, an
instance of the type should be presented as if it were an instance of
the anonymous member.  This syntax is a way to get the effect of
counted arrays, in which the length of the array is written at the
address of the instance:

    string == {
      COUNT := i4
      = S1[COUNT]  # single anonymous member
    }
    text = string

declares a variable "text" created from an array of ASCII characters,
written to the file as a 4 byte integer COUNT followed by that many
characters.  Reading it back produces a result indistinguishable from

    text = S1[COUNT]

if COUNT were defined as some fixed value.  This is a popular
construct in many existing file and stream formats (supported by both
XDR and HDF5 for example).  However, you should avoid it because the
length of the data cannot be computed without reading the file at the
address of the data itself, making it necessary to provide explicit
addresses in the Dudley layout after every instance of such a
parametrized type.  Of course, if you are using Dudley as just a
stream decoder like XDR, or if you are willing for the layout to
specify "@ address" for every variable in the file like HDF5, then
this warning is irrelevant.  For Dudley template layouts, however,
structs with parameters embedded in each instance are a non-starter.

Dudley needs a way to write or read the default byte order as part of
the file, unless all of the declarations have explicit < or >
prefixes.  A special syntax handles this:

    !DEFAULT >  # for big-endian (most significant byte first)
    !DEFAULT <  # for little-endian (least significant byte first)

You can also use the !DEFAULT statement to change the maximum default
alignment from 8 (for f8, i8, and u8 primitives) to 1, 2, or 4 bytes
as it was on some old architectures.  For example,

    !DEFAULT <4  # little-endian with 4-byte maximum default alignment

Importantly, these default settings may be written to the file like
this:

    !DEFAULT @ address  # "@ address" optional as usual

The DEFAULT value is a two bytes, e.g.- "<8" for little endian, 8-byte
max alignment, or ">2" for big endian 2-byte max alignment.  Again,
the only legal max-alignment values are 1, 2, 4, or 8, with 8 being
the default.  Any other values than those eight possiblities at that
address means the data stream has been corrupted and throw an
exception.

A Dudley layout may be appended to the data file it describes to
create a single self-describing file.  Such a file should begin with
the native Dudley signature, but this is not required.  After
appending the text of the layout file, append the additional text:

    !DUDLEY[length]<8    # little endian, 8-byte max align
    !DUDLEY[length]>8    # big endian, 8-byte max align

This <8 or >8 will be overridden by the value of the special !DEFAULT
statement elsewhere in the file - it is merely a default for data
layouts which do not include that statement.  The length is the number
of bytes of layout text, ending just before this ! character - in
other words, "!DUDLEY" is treated as end of file by the Dudley layout
parser.  Ideally, these are the last bytes of the file, but as long as
the leading ! character is within the final 4096 bytes of the file,
the appended Dudley layout will be discovered.

The preferred file extension for a file with the Dudley layout
appended is .dud, the same as a bare layout file.

Keeping the layout stream separate from the binary data stream is
encouraged, particularly in cases in which binary data will be added
over several sessions.  In that case, the layout text file should get
the .dud extension, while the binary data file can have any other
extension (say .dat).  This is also convenient when the binary data is
contained in a file of a different format, like HDF5 or netCDF or PDB.

Dudley also supports an arbitrary file signature or "magic number",
which usually would be placed at address 0 in a file.  To do this,
Dudley recognizes a second special parameter-like declaration:

    !SIGNATURE "\x89DUD\x0d\x0a\x1a\x0a" @ address

The signature can be any fixed byte string; with the optional address
that signature must appear at that address in the file.  The value
shown is the default signature for a native Dudley data file (see the
PNG format standard for the rationale).  Failure to match the expected
signature indicates the data stream has been corrupted and throws an
exception.  The Dudley signature would normally be be at address 0,
followed by a !DEFAULT at address 8.


## Parallel processing support

WORK IN PROGRESS

Dudley has a mechanism to support a family of files each written by
one "ionode" which owns only a subset of "blocks" comprising some
global data set.  The number of such blocks may vary from one ionode
to the next (presumably as a side effect of balancing the load among
processors).  A single "index file" holds all of the parameters for
all of the blocks, in order to enable the full data set to be read by
a different number of processors with a different partitioning of the
blocks among them.

The Dudley layout for the whole family describes the index file layout
in the usual manner, but contains one or more "ionode" types declared
with a special "?=" statement to be a one dimensional array.  The
single dimension corresponds to the number of "blocks" in the global
data set:

    NBLOCKS := i4  # or u8 or any integer data type
    !{
      = u4  # anonymous member is block ionode index (any integer type)
      @= u8  # optional special member is block root address
      param := type  # additional members are block parameters
      param := type
    }[NBLOCKS]  # optional "@ address" in index file

This special ionode variable definition may appear only at the top
level of the Dudley layout; it lives in the (top level) variable
namespace for the index file.

The anonymous "=" member of this special ionode variable is
required; its value is the index of the ionode owning this block.
(The association between an ionode index and the corresponding
processor or file is left to the application - note that the index
file layout is free to include other variables needed to work out the
association, such as a corresponding list of filenames.)  Within the
nblocks instances of this struct, any given ionode index may appear
multiple times (meaning it owns multiple blocks) or not at all
(meaning it owns no blocks).

The anonymous "@=" member of this special ionode variable is optional;
its value is the root address of this particular block in the file
associated with this ionode.

Parameter declarations within the special ionode variable are the
parameters describing the shape of the array data for each block in
the individual files.  Writing these parameters to the index file (and
the optional "@=" root address) allows the address of any variable in
the entire family to be computed from the data in the index file,
without needing to read anything from any of the files owned by any
individual ionode.

More than one "?=" variable may be declared, and they need not share a
common dimension length - that is, the application may contain several
different kinds of blocks.  However, any ionode index value in all the
"?=" declarations should refer to the same ionode processor and file.

Once a "?=" variable has bee defined, the Dudley layout can use the
special "?/" notion to declare the root group associated with one block
(of this ionode type if there are multiple kinds of blocks) like this:

    ionode ?/
      var = type[shape]
      var = type[shape]
      ----- and so on -----

The array shapes may use the parameters declared in the corresponding
"?=" variable declaration.  These may optionally be repeated as
parameters in the "?/" group; the application is responsible for
ensuring that any repeated parameter values written to the individual
ionode files match the corresponding values written to the index file.

Any "@ address" specifications within such an ionode group are
relative to the root address for that block, not absolute addresses in
the file (as for ordinary groups).

Notice that a Dudley layout of this sort gracefully falls back to the
case of a single file, possibly combined with the index file (at the
option of the application).  This opens the possibility of a single
Dudley layout description covering all restart dumps, serial or
parallel, for a complex radhydro code.  With document comments, such a
layout file would serve as a very concise description of the
meaning of everything required to specify the state of the code.
Similarly, each standard post processing file family could be
described by its single Dudley layout.  Furthermore, by editing such a
standard file it would be easy to derive new layouts containing custom
data.


## Python API

Although you can read a Dudley layout file to create a python object
representing that layout in a python program, sometimes it is convenient
to create that object using a python API directly.  Dudley provides a
standard API for this purpose.

The API predefines instances of the Type class corresponding to every
Dudley primitive data type, which you can use to declare data arrays:

- i1, i2, i4, i8 (signed integers)
- f2, f4, f8 (floating point numbers)
- c4, c8, c16 (complex numbers)
- b1 (boolean)
- u1, u2, u4, u8 (unsigned integers - use sparingly!)
- S1 (8-bit ASCII characters)
- U1, U2, U4 (Unicode characters)
- p4, p8 (unsigned integers used as pointers - avoid!)

These are all native byte order by default, but they have be and le
properties if you want explicitly big-endian (most significant byte
first) or little-endian (least significant byte first) byte order.
For example, f8 corresponds to the Dudley "|f8", f8.be to ">f8", and
f8.le to "<f8".

The Dudley API defines Group and List container classes - Groups hold
named variables, while Lists are sequences of anonymous variables.
Each item (variable) in a Group or a List may itself be a Group or a
List as well - that is, the you can organize your data into a very
general tree structure of Groups and Lists, with arrays as the leaf
nodes of your tree.

Suppose you want to declare a 2D array "x" of six 8 byte floats,
stored as three pairs, which is a member of a Group g::

    g = Group()  # declares a top level Group to hold "x"
    g["x"] = f8[3, 2]  # x is a 3-by-2 array of 8 byte floats

You may also wish to specify the precise address in the file where
the variable "x" is stored::

    g["x"] = f8[3, 2], address  # address is the byte address in file

Unspecified addresses are assumed to be the next available address in
the file, possibly padded by a few bytes to satisfy type alignment
constraints.  To declare a subgroup thing1 or a list thing2::

    g["thing1"] = Group()
    g["thing2"] = List()

These assignments modify the initial empty Group or List to record
that their parent Group is g.  You can retrieve the parent of any
Group or List as its parent attribute container.parent, which will be
either a Group or a List.  The List constructor accepts positional
arguments, if you wish to initialize non-empty lists.  The Group
constructor accepts (name, member) pairs as positional arguments to
initialize non-empty groups.

To append something to a List, use the += operator:

    thing2 = g["thing2"] = List()
    thing2 += f8[3, 2], address
    thing2 += ...  # can be a Group or a List as well as an array
    # Append multiple items at once like this:
    thing2 += [f8[3, 2], (f4[4, 5], address), Group(), ...]
    # Shorthand to repeat last item at several addresses:
    thing2 += addr1, addr2, addr3, ...

You can define custom array data types using the Type class.  A custom
type may be named or anonymous - an anonymous type applies to only a
single data array, while a named type can be shared by many data
arrays.  A custom data type may be simple - just a name for an array
of a previously defined type - or compound - a set of named arrays
like a C struct::

    mytype = Type(f4[2, 3])  # anonymous simple type
    mytype = Type()  # begin anonymous compound type
    mytype = Type("mytype")  # begin named compound type
    mytype["mem1"] = atype[shape1]  # declare member "mem" of compound...
    mytype["mem2"] = atype[shape2], off2  # ...with explicit offset
    mytype.close()  # explicitly close compound type
    # Alternatively, you can construct a compound directly:
    mytype = Type(("mem1", atype[shape1]),
                  ("mem2", (atype[shape2], off2)))
    root.typedef["mytype"] = mytype  # names mytype as side-effect

Any use of mytype in an array declaration closes it.  In the case
of a compound type, this means you will no longer be able to add
members.  In the case of an anonymous type, you will not be able to
use it a second time (only named data types may be shared).

If you merely wish to describe the layout of a single data file, like
HDF5 or PDB, this much of the Dudley API suffices.  In fact, neither
HDF5 nor PDB directly support the Dudley List - a sequence of
anonymous variables mapping naturally to a python list or to a
javascript array.

In order to operate as a template, potentially describing many binary
data files, Dudley adds the concept of a *parameter*.  The germ of the
idea behind Dudley parameters comes from netCDF named array
dimensions.  Many scientific datasets are identical except for the
lengths of the dimensions of arrays, so that by simply using symbolic
names for the array dimensions, you can create a single parametrized
layout covering all of the datasets.  The actual values for these
dimension parameters can be written into the datastream itself, or
into a separate datastream.  Notice that by writing many sets of
parameters into a separate stream, you can very compactly specify the
exact layout of a large number of potentially very large individual
files.  This can be extremely useful to support large families of
files produced during parallel processing.

A Dudley parameter is a signed integer, which may be stored as any of
the i-type primitives (i1, i2, i4, or i8).  A parameter always has a
name.  It may have a fixed value, or be stored in a datastream::

    IMAX = Param(IMAX=6)  # fixed value (=6) parameter IMAX
    IMAX = Param("IMAX", 6)  # same as keyword form
    IMAX = Param(IMAX=i8)  # parameter IMAX stored as i8 in stream
    IMAX = Param("IMAX", i8)  # same as keyword form

If you want to store a parameter as part of the same datastream as
your data, use the += operator on a group or compound datatype::

    g += IMAX  # IMAX parameter stored at next address in g
    g += IMAX, address  # ...or stored at specific address in file
    mytype += IMAX, offset  # can also be stored in compound instance
    # A parameter may also appear in a compound constructor list:
    mytype = Type((IMAX, offset), ...)

A parameter must be declared in this way before its use in an array
dimension.  This is true even for fixed value parameters - even though
they are not stored in any datastream and take no space.  To use a
parameter as an array dimension, just use it in a shape::

    g.xyz = f8[IMAX, 3]  # declare an IMAX-by-3 f8 array xyz

A Param object also supports addition on the right by a (small)
integer, in order to specify a dimension a few shorter or longer than
the parameter value::

    g.abc = f8[IMAX-1, 3]  # declare an (IMAX-1)-by-3 f8 array abc

Finally, a Param object supports unary minus (-IMAX), which produces
the effect of "IMAX?" in the Dudley layout language.  A parameter used
in an array dimension which is undeclared in the Group or Type
containing the array must be declared in some ancestor of that Group
or Type.


## Javascript API


## Examples

State template for a very simple 1D or 2D radhydro simulation:

    IMAX := i8    # make dimensions signed to use in expressions
    JMAX := i8    # negative to remove from dimension lists
    NGROUP := i8  # zero to make arrays take no space
    time = f8
    r = f8[JMAX?, IMAX]  # r not present if JMAX negative
    z = f8[JMAX, IMAX]  # coordinates and velocities node-centered
    u = f8[JMAX?, IMAX]
    v = f8[JMAX, IMAX]
    rho = f8[JMAX-, IMAX-]  # densities and temperatures zone-centered
    te = f8[JMAX-, IMAX-]
    unu = f8[NGROUP, JMAX-, IMAX-]  # not present if NGROUP zero
    gb = f8[NGROUP+]  # group boundaries also not present if NGROUP zero

A set of time history records for this same simulation can be structured
in many different ways:

netCDF-like, with gb a non-record variable and the rest rescord
variables:

    NREC := i8    # number of records in this file
    IMAX := i8
    JMAX := i8
    NGROUP := i8
    static = {
      gb = f8[NGROUP+]  # group boundaries do not change
    }
    record = {
      time = f8
      r = f8[JMAX?, IMAX]
      z = f8[JMAX, IMAX]
      u = f8[JMAX?, IMAX]
      v = f8[JMAX, IMAX]
      rho = f8[JMAX-, IMAX-]
      te = f8[JMAX-, IMAX-]
      unu = f8[NGROUP, JMAX-, IMAX-]
    }[NREC]

HDF5 or PDB-like, with each record variable a homogeneous list - the
list index corresponding to the UNLIMITED dimension:

    IMAX := i8
    JMAX := i8
    NGROUP := i8
    gb = f8[NGROUP+]  # group boundaries do not change
    time = f8[*]
    r = f8[*, JMAX?, IMAX]
    z = f8[*, JMAX, IMAX]
    u = f8[*, JMAX?, IMAX]
    v = f8[*, JMAX, IMAX]
    rho = f8[*, JMAX-, IMAX-]
    te = f8[*, JMAX-, IMAX-]
    unu = f8[*, NGROUP, JMAX-, IMAX-]
    # Dudley description requires each record to be explicitly
    # defined, for example with one line per record, like this:
    time@. r@. z@. u@. v@. rho@. te@. unu@.
    time@. r@. z@. u@. v@. rho@. te@. unu@.
    time@. r@. z@. u@. v@. rho@. te@. unu@.
    # ... and so on
    # Thus, this layout could not be used as a template.
