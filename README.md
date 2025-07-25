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


## Data model

Data arrays are multidimensional arrays of numbers, boolean values, or
text characters (ASCII or Unicode).  You can specify byte order and
size in bytes of numbers, but floating point numbers are assumed to be
in one of the IEEE-754 standard formats, and integers are assumed to
be two's complement.  Dudley data types can also be compounds built
from these primitive types (like numpy record dtypes or C structs).

The Dudley data model is highly compatible with the python numpy
library - and therefore scientific computing in general.  In a typical
numpy program, datasets are built up from basic variables that are
ndarrays (multidimensional arrays of numbers, strings, or structs),
aggregated using dicts (name-to-variable mappings) and lists
(index-to-anonymous-variable mappings).  These aggregates match the JSON
object and array structures.  The top level dict in a Dudley layout is
analogous to the root folder in a file system, where named members of a
dict can be data arrays, dicts, or lists of arrays, dicts, and lists.

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
                                 # The name "var" may be in quotes, which
                                 # allows it to contain arbitrary characters.
                                 # Dudley places no limits on variable names,
                                 # although legal C, python, or javascript
                                 # variable names are strongly recommended
                                 # and need not be quoted.
    var = dtype[shape] %align    # variant of optional @address specifying only
                                 #   alignment - align may be 1, 2, 4, 8, or 16
    var2 = dtype[shape]  ## documentation comment (optional)
                         # Variable attribute comments begin with : and have a
                         # formal grammar of comma separated name-value pairs:
                         #: attr1=avalue, attr2=avalue,
                         #: attr3=avalue
                         # The avalue can be a number, string, or [,] list.

    PARAM : integer  ##  documentation comment
                     # Declares a parameter.  PARAM may be used as a dimension
                     # in the shape for subsequent variable declarations in the
                     # current dict (or dtype) or its descendants.
                     # Although the integer value is usually positive, 0 and -1
                     # have well-defined meanings.
    PARAM : i4 @address  # Parameters may also be read from or written to the
                         # data stream like ordianry variables.  However,
                         # only the integer data types i1, i2, i4, or i8 are
                         # legal dtypes, and no shape is permitted.

    group/  ## document comment for group
      var = dtype[shape]  # declares group/var, address optional
      group2/
        var = dtype[shape]  # declares group/group2/var
        ..  # back to parent group level
      var2 = dtype[shape]  # declares group/var2
      group3/
        var = dtype[shape]  # declares group/group3/var
        /  # back to root group level
    group/group2/var3 = dtype[shape]  # full or relative path on one line

    list [  # create or extend list, which is a group with anonymous members
        dtype[shape],  # optionally may have @address or %align
        / var = dtype[shape]  # a list item may be an (anonymous) group
        ,  # comma ends anonymous group declaration
        [ dtype[shape]  # a list item may be a sublist
        ]  # optional *n as for outer list allowed for sublists
    ]*n  # optional *n extends list with n of these lists of items
         # n can be a number or a parameter, may be 0
    list [n]  # extends list by n more of its last item (similar to *n)

Shape is a comma delimited list of dimensions, slowest varying first
("C order").  Dimensions may be a number or a symbolic parameter.  A symbolic
parameter may have + or - suffix(es) to indicate one more or less than the
parameter value.

Dimensions of length 0 are legal, meaning that the array has no data and takes
no space in the data stream.  Dimensions of -1 are also legal, and mean that
the associated dimension is removed from the shape, so the number of dimensions
is one less than the declaration.  For example, declare a variable with a
leading dimenension with the parameter IF_EXISTS as its leading dimension:

    IF_EXISTS : i1
    varname = f8[IF_EXISTS, 3, 5]

Then by writing IF_EXISTS = 0, varname will not be written (will take no space
in the data stream), while by writing IF_EXISTS = -1, varname will be a 3x5
array of double precision floats.  This gives you a convenient means for
omitting variables from some files described by a layout, while including it
in others.

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
discussed in more detail below.  You can declare custom type names like this:

    typename {
        param : pvalue  # parameters local to the struct
                        # if pvalue is a dtype, takes space in each instance
        var = dtype[shape]  # param or var may have @address or %align
                            # which are relative to each instance
        var2 = dtype[shape]
    } %align  # optional alignment is the default for any instances

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

However, mesh_name, and any other typename always has global scope; it is
illegal to define a single typename more than once in a layout; no matter
which dict it is decalred in, a dtype always applies to the whole file.

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

It is legal to redefine primmitive data types before their first use if you
want to specify a non-default alignment (the default alignment always is the
size of the primitive) or a specific byte order:

    i8 {""=i8}%4  # i8 will have default alignment 4 instead of 8

A Dudley layout may begin with a single < or > character, indicating that
primitive types with unspecified byte order in the layout have this order.
If present, only comments may precede this global order indicator; the
summary block, if any, must follow it.

Finally, one or more - characters followed by a newline where a dict item is
expected terminates a Dudley layout stream, the same as end-of-file.

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
order specified by the < or > character in the first eight bytes.  This will
also become the first byte of any data appended to the file if it is
subsequently extended.

This was inspired by the PNG header.  The rationale is that non-binary FTP
file transfers will corrupt either the 0d 0a sequence or the 0a character,
while the 1a character stops terminal output on MSDOS (and maybe Windows).
Here the 8d character is chosen because it is illega as the first character
of a UTF-8 stream and it is not defined in the CP-1252 character encoding,
nor in the latin-1 encoding (it is the C1 control character RI there), and as
for the leading character of the PNG signature, any file transfer which resets
the top bit to zero will corrupt it.


## Primitive data types

Predefined primitive data types are based on numpy array interface:

    Signed integers:   i1, i2, i4, i8  (suffix is number of bytes)
    Unsigned integers: u1, u2, u4, u8
    Floating point:    f2, f4, f8  (IEEE 754 16, 32, 64 bit formats)
    Complex floats:    c4, c8, c16  (f2[2], f4[2], f8[2])
    Boolean:           b1
    ASCII:             S1
    Unicode:           U1, U2, U4  (UTF-8, UCS-2, and UCS4)

Unlike the numpy ndarray interface, the S and U types do not have the
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


## Examples

State template for a very simple 1D or 2D radhydro simulation:

    {
      IMAX := i8    ## leading dimension of mesh arrays
      JMAX := i8    ## second dimension of mesh arrays
      NGROUP := i8  ## number of photon energy groups
      time = f8     ## (ns) simulation time
    }  # summary completely specifies any file described by this layout
    r = f8[JMAX, IMAX]  ## (um) radial node coordinates
    z = f8[JMAX, IMAX]  ## (um) axial node coordiantes
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
    time[1] r[1] z[1] u[1] v[1] rho[1] te[1] unu[1]
    time[1] r[1] z[1] u[1] v[1] rho[1] te[1] unu[1]
    time[1] r[1] z[1] u[1] v[1] rho[1] te[1] unu[1]
    # ... and so on
    # Thus, this layout could not be used as a template.
