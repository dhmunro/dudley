# The Dudley Layout Language

Dudley is a data description language which has roughly the same scope
as HDF5 or PDB metadata, plus some features of XDR.  Dudley code is a
human readable UTF-8 text file or stream (using any newline
convention) that describes the layout of binary data in a file - exactly
where in the file each data array is written.  Python and C libraries
are provided.  Dudley features:

  * Very simple data model consists of multidimensional arrays
    aggregated into named groups and anonymous lists (like JSON
    objects and arrays).
  * Human readable layout description encourages you to think
    carefully about how you store your data.  By adding comments
    a layout file you can document your data.
  * Fully compatible with numpy/scipy.
  * Array dimensions can be parameters stored in the data stream
    so that a single layout can describe many different datasets
    (like XDR).  You can easily design and describe small datasets
    to exchange information with collaborators.

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

Both HDF5 and PDB permit the same general tree structure of named
variables, but neither has direct support for lists of unnamed arrays.
It is possible to produce a Dudley layout which describes much or all
of the data in an HDF5 or PDB file - that is, you can very often use
an HDF5 or PDB file without modification as the binary stream
described by a Dudley layout.

Dudley layouts are completely transparent - you know exactly where
your data is being stored, and how much you will need to read back in
order to locate any variable you wrote.  If you will always read back
the entire stream you have written, this is not a very important
feature.  An example would be a python pickle - there isn't any harm
in an opaque format, because you can only use it to completely restore
everything in the pickle.  However, a modern simulation may store many
terabytes of data, and you very likely will later want to focus on
much smaller subsets - if you need to read the entire stream in order
to locate the part you want, you won't be happy.  Dudley lets you
design large data layouts that you can access efficiently.  Since a
layout is a human readable text file, Dudley also provides a means to
easily share small data sets.


## Namespaces

Dudley has three kinds of named objects: data types, parameters, and
variables.  There is only one global data type namespace for the
entire file, but every struct (compound data type) and group (dict)
has its own parameter and variable namespaces.  The grammar completely
determines the context of all symbolic names.  There are no reserved
words in Dudley; you are free to use whatever names you please.
Punctuation characters completely determine the context of all names.

Symbolic names in the Dudley language must be legal variable names in
C or Python, that is begin with A-Za-z_ and continue with either those
characters or digits 0-9.  However, other languages allow other
characters, so a Dudley name may also be an arbitrary text string
enclosed in quotes (either ' or ").  You can escape quote or backslash
characters with a backslash (\\).  Such quoted names must be confined
to a single input line.

In the following description, a type name will be called simply
"type", a parameter name simply "param", and a variable name simply
"var".  Struct member names and variable names are treated in exactly
the same way, so "var" may also represent a struct member.  In the
case of groups or structs, the parameter namespaces of the parent
groups or structs will be searched in reverse order, so the parameter
namespace is hierarchical in this sense.


## Comments

The # character marks the beginning of a comment, which extends to the
end of the line.  A comment beginning with #: is a document comment
which describes the meaning of the type, parameter, or variable
defined on this line, or on the previous line if the #: is the first
non whitespace token on the line.  If the previous line already had a
document comment, this line is a continuation of that document string.

The intent is for document comments to replace data attributes in HDF5
and other formats.  If you need compact attributes that can be reduced
to just a number, you can extend the Dudley syntax to support that (by
parsing document comments), but such extensions are beyond the scope
of this basic language definition, since they have no effect on how or
where your data is stored, and any consumer of your data will need to
understand their meaning anyway.  The omission of data attributes is
intended to encourage you to store any such information as actual
named variables in your files.  (Also, for concepts like point versus
zone centered arrays, the Dudley + and - dimension suffixes can play
the role of a centering attribute.)


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
best practice is probably to assume cp1252, falling back to latin1 if
any of the missing code points in cp1252 actually occurs in the text.
(This is more or less the W3 recommendation for how to handle html
documents when the character set is not explicitly specified.)

These primitive types map to the following C primitive types on all
modern machines and compilers:

    i1 -> char, i2 -> short, i4 -> int, i8 -> long long
    u1, u2, u4, u8 -> unsigned versions of i1, i2, i4, i8
    f4 -> float, f8 -> double (f2 not supported in ANSI C)
    c4, c8, c16 -> (real, imaginary) pair of f2, f4, f8
    b1, S1, U1 -> same data treatment as u1
    U2, U4 -> same data treatment u2, u4
    p4, p8 -> same data treatment as u4, u8, meaning similar to void*

Note that the long data type is i8 on all UNIX platforms (and MacOS),
but long is i4 on all Windows platforms.  Only the C type long long is
i8 on all platforms.  Also unstated here is the assumption that all
integers are stored in twos-complement format.

Any of these primitive data types may be prefixed by < to specify little
endian byte order or > to specify big endian byte order.  They may also
be prefixed by |, which here is the same as no prefix, indicating the
file-wide byte order, which must be specified elsewhere if any variables
or parameters are declared without an explicit < or > prefix.  You cannot
use the <, >, or | prefix with any type name except these primitives.

You can redefine these type names in the file, provided the new type
definition precedes the first use of that primitive type name, and in
all future references you explicitly prefix the predefined primitive
with |.  The unprefixed primitive type name is implicitly defined (as
itself with | prepended) only upon its first use.


## Parameters

Parameters are integer values which can be used to declare array
shapes.  They can either be defined in the Dudley layout (like netCDF
metadata) or read from the file itself.  The Dudley syntax for these
two cases are, respectively:

    param := integer
    param := type @ address

In the second form of the parameter declaration, the data type must be
an integer primitive data type (i1, i2, i4, or i8).  The parameter
value will be read from the file at the specified address (byte offset
into the file).  The @ address clause is optional.  If not specified,
the address is assumed to be the next address in the file after the
previous read.

Generally, you should imagine that the data file is being read in the
order of the parameter and variable declarations in the Dudley layout.
You can also place an

    !@ address

directive on a separate line to set the address of the following
parameter or variable if you want to omit individual address
specifications for a sequence of subsequent declarations.  There
is an implied "!@ 0" at the beginning of every Dudley layout.


## Variables

A variable can be a data array, or a list of anonymous variables, or a
group (python dict) of named variables.

### Arrays

You declare an array variable with:

    var = type[shape] @ address

Array variables can have any type (predefined primitive or typedef),
and optionally include a [shape] - a list of array dimensions if
present.  As for a parameter declaration, the @ address clause is
optional, with the default again being the next address after the
previous read or free-standing !@ address directive.

### Lists

Dudley supports two kinds of list variables - heterogeneous and
homogeneous.

You declare a heterogeneous list variable with:

    var =[     # no space between = and [
      = type[shape] @ address  # first item of list is data variable
      = type[shape] @ address  # second item of list is data variable
      =[  # third item of list is a sublist
        = type[shape] @ address
        ...etc...
      ]
      ...etc...
    ]

containing zero or more anonymous variable declarations in its body.
Unlike a data variable, you can "reopen" a list variable by repeating
the list declaration sequence with the same var name at any later
point in the Dudley layout to append more items (anonymous variable
declarations) to the list.  You can also add anonymous group
declarations as elements of a heterogeneous list variable, as
described below.

You declare a homogeneous list variable with:

    var = type(*, shape) @ addresses

Every element of this list will be a type[shape] array.  Without the
explicit "@ addresses" this homogeneous list is initially empty.  The
"addresses" may be either a single address or a "@"-delimited list of
addresses to declare subsequent list items.  Each address may be
either an integer or simply ".", with "." meaning the next address in
the file or stream (equivalent to declaring a variable without
specifying any address).  You may later append list items with:

    var @ address @ address ...

A homogeneous list resembles an array, but its slowest varying index
is of indeterminate length and need not be stored contiguously in the
file.  This feature provides a simple means to describe variables
which change as a simulation evolves; it emulates the most common use
case for the UNLIMITED dimension of netCDF or HDF5 files, or a PDB
block variable.  Note that a homogeneous list may not be a struct
member nor a heterogeneous list member.

### Groups

You define a named group variable (essentially a python dict):

    var /
      param := type @ address  # parameter(s) here and in children
      var = type[shape] @ address  # declare an array variable
      var /  # declare a subgroup (child group)
        param := type @ address
        var = type[shape] @ address
        ----- and so on -----
      ..  # double dot pops back to parent group
      /  # slash pops back to root group
      var =[  # declare a list
        = type[shape] @ address
      ]
      ----- and so on -----

Like a list, you can return to a group and continue to append more named
variables to it whever you like.  In particular, notice that

    /var/var/var/  # acts like cd to a fully specified path name

and

    /var/var/var = type[shape] @ address  # declares variable with full path

(The latter also leaves the parent group of the data variable as the
current group.)

Defining an anonymous group as a list item follows a similar pattern,
except that the "root group" of any such group is the top level inside
that list item.  It is impossible to append more items to an anonymous
group after its initial declaration:

    var =[
      = type[shape] @ address
      /{  # third item of list is a group of named parameters and variables
        param := type @ address
        var = type[shape] @ address
        var =[ ... ]
        var/ ...
        ----- and so on -----
      }
      ----- and so on -----
    ]

Note that a single address determines the location of all elements of
an array, but the items of a list may have unrelated addresses.


## Array dimensions

The format of a [shape] list in a data variable declaration is

    [dim1, dim2, ...]

The dimensions are always listed from slowest to fastest varying, so
that [3, 2] means three pairs, not two triples.  This is "C order" or
"row major order".  You would build a shape [3, 2] array like this:
[[a, b], [c, d], [e, f]], and the elements in this notation appear in
the same order they are stored in memory.  (Note that FORTRAN array
indexing uses the opposite "column major" convention.  You need to
reverse your array dimension lists to use Dudley with FORTRAN or any
other column major language.  Dudley's lack of support for both
dimension order conventions is a deliberate design feature.  You need
to learn to think carefully about exactly how your data is stored to
use Dudley effectively.)

Each dimension length may be either an integer value or a parameter
name.  The parameter name must have been previously declared in either
the current group or one of its ancestors.

Additionally, a parameter name may have a + or - suffix to indicate
one larger or one smaller than the parameter value.  Multiple + or -
suffixes can be used to indicate two or more length differences.

If any dimension length is zero, the variable has no data, takes no
space, and does not advance the current address.  This happens before
computing any + or - increment or decrement suffix.

If any dimension length is negative, by default it is removed from the
dimension list, reducing the number of dimensions of the array.
Again, this happens before computing any + or - increment or decrement
suffix.

An alternative behavior for a negative dimension length is to treat
it as equivalent to zero dimension length - namely, the variable will
have no data and not advance the current address.  You trigger this
alternative treatment with a ? suffix after the parameter name (before
any + or - suffixes).

For example:

    x = f8[JMAX, IMAX]
    y = f8[JMAX?, IMAX]
    rho = f8[JMAX-, IMAX-]
    unu = f8[NGROUP, JMAX-, IMAX-]

declares x and y to be 2D arrays (IMAX consecutive f8 values repeated
JMAX times). rho to be a 2D array with one fewer item in each row and
column, and unu to be a 3D array consisting of NGROUP repeats of 2D
arrays shaped like rho.  This kind of pattern would be useful in a
simulation where x and y were 2D mesh coordinates, and rho and unu
were scalar and NGROUP array values, respectively, associated with
each zone in that mesh.  IMAX, JMAX, and NGROUP could be parameters
stored in each file describe by this layout.  Now the code may have a
mode in which it does not use the unu variable at all.  Setting NGROUP
to be 0 has the effect of removing the unu variable from the file
entirely - so you don't need a second Dudley layout to describe this
mode of operation.  Furthermore, the code may have a 1D mode in which
there is no y coordinate at all, and the JMAX dimension is missing
from all the other variables:

    x = f8[IMAX]
    rho = f8[IMAX-]
    unu = f8[NGROUP, IMAX-]

Setting JMAX to -1 will make the original layout description identical
to this 1D description, so once again, a single Dudley layout can
describe both the 2D and 1D modes of code operation.


## Data types and typedefs

You can define named compound data types similar to C structs.  There
is not a huge distinction between groups and struct types; a struct is
more or less a template for a group.  However, for modest member
counts at least, a group is intended to be mapped to a Python dict,
while a struct is intended to be mapped to a numpy structured dtype
(or C struct).  The Dudley syntax is:

    type == {
      param := type @ offset  # param := integer also legal
      var = type[shape] @ offset
      ----- and so on -----
    }

That is, a struct type consists of parameter and variable
declarations, whose addresses have become byte offsets relative to the
beginning of each struct instance (in-file).  The variables are the
struct members intended to be present in the in-memory representation
of a struct instance.  The parameters (if any) are intended to not be
present in the in-memory representation, but only in the file.
However, you might also wish to present the in-memory representation
of each instance as a Python dict, in order to implement arrays of
groups.  Any parameters should appear in the shapes of some of the
data members (variables), since their scope is limited to a single
struct instance.

One distinction between a struct type and a group is that the optional
@ delimits an offset - that is, an address relative to the beginning
of the struct instance - whereas the @ address in a group represents
an absolute disk address in the file.

You can also use the == operator to create an alias for another data
type, possibly dimensioned, analogous to a C typedef:

    type == type[shape] % alignment  # alignment optional

Struct data types need not be explicitly named.  Anywhere "type"
appears in the Dudley grammar, it can be either a (possibly prefixed)
primitive data type, a symbol which has been previously defined
as a data type in an == statement, or a struct declaration in { }
brackets.

Notice that the difference between an anonymous struct instance and a
group is simply how you want to think about your data.  For example,

    var = { memb1 = type1[shape1]
            memb2 = type2[shape2] }

could refer to exactly the same data stream as:

    var / memb1 = type1[shape1]
          memb2 = type2[shape2]

However, an API based on Dudley may present this data stream very
differently.  For example, a python API should present the first as a
numpy object with a structured array dtype, while the second would
appear as a dict.  As far as the Dudley layout goes, the major
difference is that you can append more members to the group var later
in the stream, since group members are not constrained to have
consecutive addresses, unlike struct members.

As a special case, if there is only a single member (variable
declaration) in the struct, you may omit the member (variable) name,
like the anonymous variable declarations in a list.  In this case, an
instance of the type should be presented as if it were an instance of
the anonymous member.  This syntax is a way to get the effect of
counted arrays, in which the length of the array is written at the
address of the instance:

    string == {
      count := i4
      = S1[count]  # single anonymous member
    }
    text = string

declares a variable "text" created from an array of ASCII characters,
written to the file as a 4 byte integer count followed by that many
characters.  Reading it back produces a result indistinguishable from

    text = S1[count]

if count were defined as some fixed value.  This is a popular
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

Although Dudley data types are global - there is only a single
namespace for data types - when a data type references a parameter in
an array shape, the value of that parameter is taken from the closest
group to the struct instance which declares that parameter name.
For example:

    NITEMS := i4  # global NITEMS parameter
    SomeType == { memb1 = i8
                  memb2 = f4[NITEMS] }
    var1 = SomeType[4]  # var1 SomeType uses global NITEMS
    grp1 /
        var2 = SomeType  # var2 SomeType uses global NITEMS
        NITEMS := i8   # grp1 NITEMS shadows global
        var3 = SomeType[3]  # var3 SomeType uses grp1 NITEMS
        ..
    var4 = SomeType[2]  # var4 SomeType uses global NITEMS

In other words, references to Dudley parameterized data types bind
each parameter to the closest ancestor group defining that parameter
at the time the instance of that struct was declared.  Within a data
type definition (==), any parameters referenced have no particular
binding (in fact, the parameters need not have been previously
declared).  Only when the data type is instantiated are the parameter
bindings resolved.


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

Pointee declarations always have global scope; they will never be
members of any group other than the root of the whole file.


## Parallel processing support

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

    nblocks := i4  # or u8 or any integer data type
    ionode ?= {
      = u4  # anonymous member is block ionode index (any integer type)
      @= u8  # optional special member is block root address
      param := type  # additional members are block parameters
      param := type
    }(nblocks)  # optional "@ address" in index file

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


## Additional constructs

Dudley needs a way to write or read the default byte order as part of
the file, unless all of the declarations have explicit < or >
prefixes.  A special parameter-like declaration handles this:

    !BOM := |U2 @ address  # "@ address" optional as usual

The BOM value is U+FEFF, so if the two bytes are [0xFE, 0xFF], the
native byte order is big endian, while if the bytes are [0xFF, 0xFE],
the native byte order is little endian.  Any other values at that
address means the data stream has been corrupted and throws an
exception.  Since placing a byte order mark at the beginning of a
stream may indicate the whole stream is unicode, it is unwise to put
this !BOM at address 0.  You can also define the default byte order
in the layout file itself with one of:

    !BOM := 0  # for big-endian (most significant byte first)
    !BOM := 1  # for little-endian (least significant byte first)

Dudley also supports an arbitrary file signature or "magic number",
which usually would be placed at address 0 in a file.  To do this,
Dudley recognizes a second special parameter-like declaration:

    !SIGNATURE := "\x89DUD\x0d\x0a\x1a\x0a" @ address

The signature can be any fixed byte string; with the optional address
that signature must appear at that address in the file.  The value
shown is the default signature for a native Dudley data file (see the
PNG format standard for the rationale).  Failure to match the expected
signature indicates the data stream has been corrupted and throws an
exception.  The Dudley signature would normally be be at address 0,
followed by a !BOM at address 8.

A Dudley layout may be appended to the data file it describes to
create a single self-describing file.  Such a file should begin with
the native Dudley signature, but this is not required.  After
appending the text of the layout file, append the additional text:

    !DUDLEY@address!<bom>

Here \<bom\> indicates the digit 0 if the machine writing the binary
data part of the file is big-endian, or the digit 1 if it is
little-endian.  This will be overridden by the value of the special
!BOM parameter written elsewhere in the file - it is intended as a
default for data layouts which do not include that parameter.  The
address is the first byte of the layout text, and the layout text ends
just before this ! character - in other words, "!DUDLEY" is treated as
end of file by the Dudley layout parser.  Ideally, these are the last
bytes of the file, but as long as the leading ! character is within
the final 4096 bytes of the file, the appended Dudley layout will be
discovered.

The preferred file extension for a file with the Dudley layout
appended is .dud, the same as a bare layout file.

Keeping the layout stream separate from the binary data stream is
encouraged, particularly in cases in which binary data will be added
over several sessions.  In that case, the layout text file should get
the .dud extension, while the binary data file can have any other
extension (say .dat).  This is also convenient when the binary data is
contained in a file of a different format, like HDF5 or netCDF or PDB.


## Notes on Dudley grammar

1. Terminal tokens in the grammar are:
   -  [A-Za-z_][A-Za-z_0-9]*   (symbols)
   -  (0x)?[0-9]+   (integers)
   -  < | > = == := ?= @= ( , + - ) { } [ ] / .. @ ! # #: % " '
   -  [\x0d\x0a]  (newlines, either LF, CRLF or CR)
   -  whitespace  (space, tab, vertical tab, form feed)
   - (" ' reserved for use declaring variable names with illegal characters)
   - (% reserved for use in alignment declarations)

2. Newlines are distinguished from other whitespace only to determine
   the end of a comment introduced by # or #:, or the end of a special
   additional construct like !DUDLEY.  Any whitespace, including
   newlines, is otherwise optional unless needed to delimit other tokens.


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
general structure of Groups and Lists, with arrays as the leaf nodes
of your tree.

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
Group or List as its parent attribute container.parent, which will
be either a Group or a List.

To append something to a List, use the += operator:

    thing2 = g["thing2"] = List()
    thing2 += f8[3, 2], address
    thing2 += ...  # can be a Group or a List as well as an array

You can declare the first dimension of an array to be "unlimited",
that is, declare the variable to be a homogeneous list of arrays of
the shape specified by the remaining dimensions like this::

    g["var"] = atype[..., dim1, dim2, etc], address

If address is present, it specifies only the location of the first
block of atype[dim1, dim2, etc] data.  To specify the addresses of
subsequent blocks, use::

    g["var"] += address  # or, to specify multiple blocks...
    g["var"] += address1, address2, address3, ...

You can define custom array data types using the Type class.  A custom
type may be named or anonymous - an anonymous type applies to only a
single data array, while a named type can be shared by many data
arrays.  A custom data type may be simple - just a name for an array
of a previously defined type - or compound - a set of named arrays
like a C struct::

    mytype = Type(f4[2, 3])  # anonymous simple type (not useful)
    mytype = Type("mytype", f4[2, 3])  # named simple type
    mytype = Type()  # begin anonymous compound type
    mytype = Type("mytype")  # begin named compound type
    mytype["var"] = atype[shape]  # declare member "var" of compound...
    mytype["var"] = atype[shape], offset  # ...with explicit offset

Any use of mytype in an array declaration "freezes" it.  In the case
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
    mytype += IMAX, offset

A parameter must be declared in this way before its use in an array
dimension.  This is true even for fixed value parameters - even though
they are not stored in any datastream and take no space.  To use a
parameter as an array dimension, just use it in a shape::

    g.xyz = f8[IMAX, 3]  # declare an IMAX-by-3 f8 array xyz

A Param object also supports addition on the right to a (small)
integer, in order to specify a dimension a few shorter or longer than
the parameter value::

    g.abc = f8[IMAX-1, 3]  # declare an (IMAX-1)-by-3 f8 array abc

Finally, a Param object supports unary minus (-IMAX), which produces
the effect of "IMAX?" in the Dudley layout language.  A parameter used
in an array dimension which is undeclared in the Group or Type
containing the array must be declared in some ancestor of that Group
or Type.

How to define parameter stream?  Want support for arrays or lists of
parameter sets generating an array of groups...



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
