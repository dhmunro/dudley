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

  number / dict_item1 dict_item2 ... dict_itemN

  number [ list_item1, list_item2, ,,,, list_itemN ]

  number\ :subscript:`opt` address

As mentioned above, the comma `,` or `]` separating or terminating the list
declaration also terminates a dict item in the list.

In the second two cases, the leading number is the integer index of a
previous list item to be extended.  That item must have been a dict in the `/`
case, or a list in the `[` case.  Neither form appends a new item to the list,
instead modifiying an existing item.

The final case is a shortcut for duplicating a previously data item declaration
as the next item of the list.  If number is not present, the previous list item
is the default thing to duplicate.  In either case, the referenced item must be
a data array, not a dict or a list.  With an `address` of `%0`, this makes it
very easy to build a list consisting of many identically shaped arrays.

The number can be negative to refer to the current end of the list, as in
python list indexing, so that `-1` refers to the previous element, `-2` to the
element before that, and so on.  (Thus, in the final case, the default number
is `-1`.)

Type item
----------

The datatype in a **data** array declaration may simply be a name or it may be
an anonymous datatype enclosed in curly braces `{item1 ... itemN}`.  The
curly brace form is exactly the same as what may appear after the type_name
of a named type declaration dict item:

**datatype** is one of:
  type_name

  { member_name1 : data1  member_name2 : data2 ... member_nameN : dataN }

  { : data }

  {}

The second form is a compound datatype like a C struct.  The format of each
struct member is identical to a data array item in a dict, except that if an
absolute address `@address` is specified, it is interpreted as a byte address
relative to the start of any instance of this datatype.  The alignment of the
new datatype is the greatest alignment of any of its members (possibly as
overridden by a `%alignment`).

The third form, in which the type has a single anonymous member, is similar to
a C typedef, allowing you to give a name to an arbitrary array type and shape.
This form also permits you to change the alignment of a datatype, which might
occasionally be useful to change the alignment of predefined primitives.

The fourth form - an empty compound - is a special case which gives Dudley a
way to declare variables whose value is `None` in python or `null` in
javascript.  This isn't useful in Dudley layouts intended to describe
multiple files, but without it Dudley would be unable to store the state of
individual simulations or interactive sessions in those languages.  Unlike the
compound or typedef forms, `{}` does not create a separate item in the
layout, but is instead treated like a predefined primitive.

Parameter item
--------------

After the `=` sign, a parameter declaration resembles a data array declaration,
except that a fixed integer value is permitted and a shape or filter is not:

**param** is one of:
  integer_value

  integer_type_name address\ :subscript:`opt`

The first declares a fixed parameter, which takes no space in the data stream,
while the second declares a variable parameter, which takes space in the data
stream exactly as if it were a (scalar) data array with the same declaration.

The integer type name can be any `u` or `i` format primitive type.  However,
internally, the parameter value is always a signed 8-bit integer, as are all
fixed integer values in Dudley (either fixed parameter values or fixed
dimension lengths in an array shape).

Dimension lengths, hence parameters, may have any positive integer value, as
expected.  However, Dudley explicitly permits dimension length 0.  If any
dimension in an array shape is 0, the array takes no space in the data stream,
including any alignment adjustment which would otherwise occur.  This is
consistent with the numpy treatment of arrays with 0 dimensions.

Additionally, Dudley recognizes dimension length of -1 to mean that the
corresponding dimension should be removed when the array is presented to the
user.  (That is, it is treated as dimension length 1, but the uint length index
is then squeezed out of the array shape.)  Hence, Dudley internally keeps all
dimension lengths as signed integer values.

Often, two arrays will have dimension lengths which always differ by one or
two.  For example, an array of bin boundary values will always be one
element longer than a corresponding array of quantities within the bins.
To indicate such a relation, you may define only a single parameter but append
one (or more) `+` or `-` suffixes to its name when you declare an array
with one (or a few) more or less element(s).  For example, if you bin a
population by income, you might describe poll result like this::

      NBINS = i4          # number of income bins (variable)
      income: f4[NBINS+]  # boundaries of income bins
      npeople: i4[NBINS]  # number of people in each income bin

Of course, in this case you might prefer to think of there being one *more*
bin than income boundary - with a bin for all those below your smallest income
value and another for all those above your largest - in which case you would
declare `income: f4[NBINS-]` instead.  In either case, just the
relationship gives a human reader of this layout a pretty clear idea of which
way you are thinking about bins and boundaries.

Parameter and type scope
------------------------

Both parameters and named datatypes are children of a dict.  When a name
appears in any array declaration (including type declarations in `{}`),
Dudley searches all the ancestor dicts of the array being declared for a
parameter or named type matching the name.  The matching parameter or type
name declared in the nearest ancestor is the one Dudley uses.  This association
is determined as Dudley parses the layout, so only parameter or type names
declared in the layout prior to thearray being parsed can match.

In particular, a parameter in the shape of a data array member (or its type)
in a compound datatype will be bound to the nearest ancestor parameter (or
type) where the compound type was declared, *not* where any instance of that
compound type is declared.  In other words, a named datatype will not change
even if used in a scope where its member declarations would mean something
different than where it was declared.

Similarly, if a parameter name is reused within a single dict by redeclaring it,
previously declared items will still be bound to the instance of that parameter
in force when they were declared.

Predefined primitive types
--------------------------

Dudley recognizes 19 predefined primitive names:

**u1 u2 u4 u8**
  1, 2, 4, or 8 byte unsigned integers
**i1 i2 i4 i8**
  1, 2, 4, or 8 byte signed integers
**f2 f4 f8**
  2, 4, or 8 byte IEEE 754 floating point numbers
**c4 c8 c16**
  complex numbers as (re, im) pairs of f2, f4, or f8
**b1**
  1 byte boolean values (0 false, anything else true)
**S1**
  1 byte ASCII character (CP1252 or Latin1 if high order bit set)
**U1 U2 U4**
  UTF-8, UTF-16, or UTF-32 unicode character (1, 2, or 4 bytes/unit)

Any of these may be prefixed by the character `<` to indicate little-endian
byte order (least significant byte first), or `>` to indicate big-endian
byte order, or `|` to indicate indeterminate byte order.  Here, indeterminate
byte order means that the layout may describe streams written with either
byte order, and that the byte order for a specific stream instance must be
recorded separately from the layout (e.g.- in a file signature).

A prefixed primitive type name like `<i4` or `|i4` or `>i4` is the one
exception to the rule that only alphanumeric or underscore characters may
appear in unquoted names.  That is, you do not need to write `"<i4"`, but
you would need to write `"<dumb_name"`.

An unprefixed primitive type name implies a `|` indeterminate prefix.  However,
you may change that default behavior by explicitly declaring a named datatype
using an unprefixed primitive name.  For example::

    i4 {:<i4}

explicitly declares that datatype `i4` means `<i4` in any subsequent (in scope)
data declarations, rather than its implicit `|i4` meaning.  You cannot
change the meaning of a prefixed primitive type in this manner.  (The prefixed
primitive type names are the only reserved names in Dudley.)

Dudley's primitive type names generally follow the numpy array protocol.
However, note that the `|` prefix has a slightly different meaning in Dudley,
and that the meaning of byte size suffix for the text types `S` and `U` is
minimum bytes per character in Dudley, not characters per string as in numpy.
(In fact, numpy does not support UTF-8 or UTF-16 encodings in ndarrays.)

Dudley does not support quad precision floating point `f12` or `f16`, because
usually only one of those is supported by numpy owing to inconsistent
hardware support across platforms.  (Hardware support for `f2` is also limited,
even though numpy supports that on all platforms.)  The only way to describe
such data in a Dudley layout is to leave it as raw bytes, for example by
defining::

    f16 {:u1[16]}

Quoting and other details
-------------------------

A Dudley layout is encoded as UTF-8 (or ASCII).

An unquoted Dudley name (for a named data or type or a parameter in a dict,
or a parameter in an array shape, or a filter name) must be a contiguous
string of alphanumeric or underscore ASCII characters not beginning with a
digit (like legal C or python or javascript variable names).

However, any Dudley name may be an arbitrary quoted string, including the
empty string `""`.  Either single or double quotes may be used.  Dudley
recognizes only three backslash escape sequences inside the quotes,
`\\\\`, `\\"`, and `\\'`.  Note that any other escapes are unnecessary
in Dudley, since the name will not end until the closing quote.  While
arbitrary characters in names are permitted, obviously you should avoid
anything other than printing characters.

In Dudley, an integer value consists of an optional `-` or `+` sign, followed
(with no intervening whitespace) by a string of decimal digits beginning with
a non-zero digit, or a string of hexadecimal digits (each a digit or a-f)
beginning with `0x`.  Any non-digit characters (including the `x` in the hex
prefix) may be either lower or upper case.

A floating point number has the same format as in C or python or javascript,
but must include either a decimal point or an exponent field beginning with
`e` (or `E`) or both.  Again, any optional leading sign may not be separated
by any whitespace from the number.

Anonymous items
---------------

Ordinarily items in a dict or members of a compound type have names.  However,
you have already met anonymous types generated by using compound or typedef
type definitions `{...}` as the datatype in an array declaration, and the
single unnamed member `{:data}` in a typedef type.  These array declarations
are children of the parent dict or type, respectively, but have no name.
Since the only way to reference an item in a dict or group is by name, there
is no way you can later refer to these objects - the one reference to them is
generated by the context in which they were declared.

Filters, discussed more fully in a later section, create the need for two
additional kinds of anonymous items.  These both depend on the content of the
data being stored, not simmply its structure, and so they can only be present
in programmatically generated Dudley layouts.

In brief, a compression filter requires an anonymous variable parameter, whose
value is the length in bytes of the compressed data.  This parameter goes at
the stream address of the compressed data array, with the compressed data
itself immediately following.  Thus::

    data_name: datatype[shape] -> filter

appears in the stream as if it were described by::

    ANONYMOUS_LENGTH = i8  data_name: u1[ANONYMOUS_LENGTH]

The implicit anonymous length parameter appears in the global list of dynamic
parameters Dudley keeps internally, but there is no way to reference it
explicitly.

A reference filter, on the other hand, requires an anonymous data array
corresponding to every individual instance of the reference declared.  These
must actually appear in the Dudley layout.  All such anonymous reference
arrays are children of the root dict (as are the anonymous length parameters
generated by compression filters).  An automatically generated referenced
array declaration in a Dudley layout looks like this:

**referenced_data**
  : datatype shape\ :subscript:`opt` address\ :subscript:`opt`

This looks like an ordinary dict data item declaration but without a
`data_name`.  However, there are additional restrictions on the `datatype` and
`shape` of a referenced array.  Namely, it may use only named datatypes
declared in the root dict, and its shape may include only explicit integer
dimension lengths - parameter names are not permitted in referenced array
shapes.
