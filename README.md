# The Dudley Layout Language

Dudley is a data description language which has roughly the same scope
as HDF5 or PDB metadata, plus some features of XDR.  Dudley code is a
text file or stream (using any newline convention) that describes the
layout of data in a file, which may also contain parameter values
describing multidimensional array shapes.  A complete "program" in the
Dudley language is called a "layout".  A Dudley layout file has the
preferred name extension ".dud".

While a Dudley layout can precisely describe the data layout of a
particular binary file, like HDF5 or PDB metadata, Dudley can also
describe a parametrized layout which can apply to a wide range of
individual binary files having the same variables but different array
shapes.  This extended capability is similar to XDR.  However, unlike
XDR, Dudley is designed to be able to specify the precise address of
data in a file without streaming through the entire file.

There are at least three distinct use cases for Dudley:

1. The layout explicitly defines the addresses of every item in a
   single specific file.  This is what PDB and HDF5 metadata is
   designed to do.  The description may contain parameters defined as
   fixed values in the layout, but these are a form of documentation
   like named dimension lengths in netCDF.

2. The layout is intended to describe many different data streams, but
   the consumer will always read the entire data stream in serial
   order.  The data stream may contain parameters describing dimension
   lengths of objects later in the stream, so one layout may describe
   streams with different sized arrays.  This is what XDR is designed
   to do, which is similar to the Python pickle protocol.  Potentially
   it is useful for files as well, when the consumer will always read
   the entire file sequentially.

3. The layout is intended to describe many different files, and the
   consumer is expected to read only random parts of the file.  This
   can be made reasonably efficient if the parameters are all
   collected at the beginning of the file, so the reader can compute
   the actual addresses of everything in the file from the information
   in a small block at its beginning.  In this case, the Dudley layout
   is a template for many files, a capability which none of our
   existing tools has.


## Namespaces

Dudley keeps three separate namespaces for data types, parameters, and
variables.  The grammar completely determines the context of all
symbolic names.  In the following description, a type name will be
called simply "type", a parameter name simply "param", and a variable
name simply "var".  (Struct member names and variable names are
treated in exactly the same way, so "var" may also represent a struct
member.)  There is only one global type namespace for the entire file,
but every struct data type and group (dict) has its own parameter and
variable namespaces.  In the case of groups, the parameter namespaces
of the parent groups will be searched in reverse order, so the
parameter namespace is hierarchical in this sense.

Symbols in the Dudley language must be legal variable names in C or
Python, that is begin with A-Za-z_ and continue with either those
characters or digits 0-9.  However, there are no reserved words in
Dudley; you are free to use whatever names you please.  The grammar of
Dudley is defined entirely by punctuation characters.


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
understand their meaning anyway.  You should not store information
necessary to disambiguate variable meaning as attributes (let alone
required as actual variable data for processing); this omission is
intended to encourage you to store any such information as actual
named variables in your files.


## Primitive data types

Predefined primitive data types are based on numpy array interface:

    Signed integers:   i1, i2, i4, i8  (suffix is number of bytes)
    Unsigned integers: u1, u2, u4, u8
    Floating point:    f2, f4, f8  (IEEE 754 16, 32, 64 bit formats)
    Complex floats:    c4, c8, c16
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
    S1, U1 -> same data treatment as u1
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
with |.  The unprefixed primitive type name is implicitly defined only
upon its first use in a declaration if you haven't defined it
previously.  The actual primitive name has the | prefix and is
therefore not a legal Dudley symbol in any other context.


## Parameters

Parameters are integer values which can be used to declare array
shapes.  They can either be defined in the Dudley layout (like netCDF
metadata) or read from the file itself.  The Dudley syntax for these
two cases are, respectively:

    param := integer
    param := type @ address

In the second form of the parameter declaration, the data type must be
an integer (signed or unsigned) primitive data type.  The parameter
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
group (python dict) of named variables.  You declare a data variable
with:

    var = type(shape) @ address

Data variables can have any type (predefined primitive or compound),
and optionally include a (shape) - a list of array dimensions if
present.  As for a parameter declaration, the @ address clause is
optional, with the default again being the next address after the
previous read or free-standing !@ address directive.

You declare a list variable with:

    var = [
      = type(shape) @ address  # first item of list is data variable
      = type(shape) @ address  # second item of list is data variable
      = [  # third item of list is a sublist
        = type(shape) @ address
        = type(shape) @ address
      ]
      ----- and so on -----
    ]

containing zero or more anonymous variable declarations in its body.
Unlike a data variable, you can "reopen" a list variable by repeating
the list declaration sequence with the same var name at any later
point in the Dudley layout to append more items (anonymous variable
declarations) to the list.  You can also add anonymous group
declarations as elements of a list variable, but first we show how to
define a named group variable (essentially a python dict):

    var /
      param := type(shape) @ address  # parameter(s) here and in children
      param := type(shape) @ address
      var = type(shape) @ address  # declare a member variable
      var = type(shape) @ address
      var /  # declare a subgroup (child group)
        param := type(shape) @ address
        var = type(shape) @ address
      ..  # double dot pops back to parent group
      var = [  # declare a list
        = type(shape) @ address
      ]
      ----- and so on -----
    /  # optionally return all the way to root level

Like a list, you can return to a group and continue to append more named
variables to it whever you like.  In particular, notice that

    /var/var/var/  # acts like cd to a fully specified path name

and

    /var/var/var = type(shape) @ address  # declare variable with full path

(The latter also leaves the parent group of the data variable as the
current group.)

Defining an anoymous group as a list item follows a similar pattern,
except that the "root level" of any such group is its containing list
variable.  It is impossible to append more items to an anonymous group
after its initial declaration:

    var = [
      = type(shape) @ address
      = type(shape) @ address
      /  # third item of list is a group of named parameters and variables
        param := type(shape) @ address
        var = type(shape) @ address
        ----- and so on -----
        ..  # or / to pop all the way out of a nested group declaration
    ]

Note the difference between a list and an array: a single address
determines the location of all elements of an array, but the items of
a list may have unrelated addresses.


## Dimension lists

The format of a (shape) list in a data variable declaration is

    (dim1, dim2, ...)

The dimensions are always listed from slowest to fastest varying, so
that (3, 2) means three pairs, not two triples.  This is "C order" or
"row major order".  You would build a shape (3, 2) array like this:
[[a, b], [c, d], [e, f]], and the elements in this notation appear in
the same order they are stored in memory.

Each dimension length may be either an integer value or a parameter
name.  The parameter name must have been previously declared in either
the current group or one of its ancestors.

Additionally, a parameter name may have a + or - suffix to indicate
one larger or one smaller than the parameter value.

If any dimension length is zero, the variable has no data, takes no
space, and does not advance the current address.

If any dimension length is negative, it is removed from the dimension
list, reducing the number of dimensions of the array.  This happens
before any + or - increment or decrement suffix is computed.


## Data types and typedefs

You can define named compound data types similar to C structs.  There
is not a huge distinction between groups and struct types; a struct is
more or less a template for a group.  However, for modest member
counts at least, a group is intended to be mapped to a Python dict,
while a struct is intended to be mapped to a numpy structured dtype
(or C struct).  The Dudley syntax is:

    type == {
      param := type @ offset  # param := integer also legal
      var = type(shape) @ offset
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

    type == type(shape)

Struct data types need not be explicitly named.  Anywhere "type"
appears in the Dudley grammar, it can be either a (possibly prefixed)
primitive data type, a symbol which has been previously defined
as a data type in an == statement, or a struct declaration in { }
brackets.

As a special case, if there is only a single member (variable
declaration) in the struct, you may omit the variable name, like the
anonymous variable declarations in a list.  In this case, an instance
of the type should be presented as if it were an instance of the
anonymous member.  This syntax is a way to get the effect of counted
arrays, in which the length of the array is written at the address of
the instance:

    string == {
      count := u4
      = S1(count)  # single anonymous member
    }
    text = string

declares a variable "text" created from an array of ASCII characters,
written to the file as a 4 byte integer count followed by that many
characters.  Reading it back produces a result indistinguishable from

    text = S1(count)

if count were defined as some fixed value.  This is a popular
construct in many existing file and stream formats (present in both
XDR and HDF5 for example).  However, it should be avoided because the
length of the data cannot be computed without reading the file at the
address of the data itself, making it necessary to provide explicit
addresses in the Dudley layout after every instance of such a
parametrized type (unless you are using Dudley as just a stream
decoder like XDR).


## Pointer data

Pointers automatically require listing explicit addresses in the
Dudley layout, making the description specific to a single file.  Each
pointee must be declared like this:

    integer = type(shape) @ address

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


## Additional constructs

Dudley needs a way to write or read the default byte order as part of
the file, unless it is describing a file in a non-native format like
PDB or HDF (in which case all of the declarations would have explicit
< or > prefixes).  A special parameter-like declaration handles this

    !DUDLEY := S1(8) @ address  # signature and byte order mark

The Dudley file has one of two eight byte hex signatures: [89, 44, 75,
44, 0d, 0a, 1a, 0a] or [89, 64, 95, 64, 0d, 0a, 1a, 0a].  Note that
[44, 75, 44] is "DUD" if the default byte order is big endian >, while
[64, 95, 64] is "dud" means the default byte order is little endian <.
This sequence is stolen from HDF5, which stole it from PNG.  It
detects common file transfer mishandling errors.

- Use %alignment for alignments in contexts similar to @address?
- Should !DUDLEY := 0 or 1 specify default little or big endian?


## Separate parameter streams

The

    !TEMPLATE

directive indicates that this file is intended to be a layout
template.  The parser can check that all data addresses are computable
from the parameters, and that furthermore all parameters are grouped
at the beginning of the file.  Note that the !DUDLEY file signature is
an important parameter if you want to support families with members of
both endianness.


## Parallel processing support

Dudley has a mechanism to support a family of files each written by
one "ionode" which owns only a subset of "blocks" comprising some
global data set.  The number of such blocks may vary from one ionode
to the next (presumably as a side effect of balancing the load among
processors).  A single "index file" holds all of the parameters for
all of the blocks, in order to enable the full data set to be read by
a different number of processors with a different partitioning of the
blocks among them.

The Dudley layout for the whole family describes
the index file layout in the usual manner, but contains one or more
"ionode" types declared with a special "?=" statement to be a one
dimensional array.  The single dimension corresponds to the number of
"blocks" in the global data set:

    nblocks := u4  # or u8 or any integer data type
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
      var = type(shape)
      var = type(shape)
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
layout file would serve as a very concise description of of the
meaning of everything the code uses to run.  Similarly, each standard
post processing file family could be described by its single Dudley
layout.  Furthermore, by editing such a standard file it would be easy
to derive new layouts containing custom data.


## Notes on Dudley grammar

1. Terminal tokens in the grammar are:
   -  [A-Za-z_][A-Za-z_0-9]*   (symbols)
   -  (0x)?[0-9]+   (integers)
   -  < | > = := == ?= @= ( , + - ) { } [ ] / .. @ ! # #: % " '
   -  [\x0d\x0a]  (newlines, either LF, CRLF or CR)
   -  whitespace  (space, tab, vertical tab, form feed)
   - (" ' reserved for use declaring variable names with illegal characters)
   - (% reserved for use in alignment declarations)

2. Newlines are distinguished from other whitespace only to determine
   the end of a comment introduced by # or #:.  Any whitespace, including
   newlines, is otherwise optional unless needed to delimit other tokens.
