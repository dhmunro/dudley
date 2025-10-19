Special Comments
================

A comment in a Dudley layout begins with a `#` and extends to the end of the
line.  Comments, including the leading `#`, are treated like any other
whitespace.

Document comments
-----------------

However, a Dudley parser does not completely ignore all comments.  A comment
beginning with `##` is a document comment.  Dudley collects document
comments when it parses the layout, and remembers which item was being
declared at the point where each document comment appeared, so you can later
query the document comments associated with any item in the layout.  Multiple
document comment lines may be associated with a single item.

The rule for which item "is being declared" and is therefore associated with
a document comment is not quite obvious.  To document a dict or list (or
datatype) container, you can place document comments before its first item or
member.  For dict and list containers, any document comment after the
container is reopened but before the first new item is declared also apply
to the container.  Item declarations within a dict always begin with the
name of the item; any document comment after the name but before the name of
the following item will be associated with that named item.  For items in a
list, document comments for an item may appear after the comma ending the
item declaration, as long as the declaration of the next item has not yet
begun.

Note that a document comment for a list container or a named datatype may
appear after its close bracket or curly brace, as well as before its first
item or member.

Notice that, unlike document comments in many other languages, Dudley
documentation alway *follows* the item being documented; there is no way to
place the documentation for an item *before* its declaration.  The Dudley
parser is designed to require very little lookahead in general, so this rule
is consistent with the overall design goals of the parser.

Attribute comments
------------------

Document comments are completely free-form.  Dudley provides a second kind of
special comment which must conform to a (very simple) formal syntax - the
attribute comment.  Attribute comments begin with `#:`.  Dudley collects and
associates attribute comments with indivdual items in a layout in exactly the
same way as document comments.  Any item may have both, and multiline
docuemnt and attribute comments may be freely mixed (although this is probably
not good practice) - Dudley keeps them separate, so that docuemntation and
attributes for any item may be retrieved separately.

**attribute comment**
  `#:` attr1 attr2 ... attrN

That is, each attribute comment consists of any number (including zero) of
whitespace delimited attributes.  Each attribute may be one of:

**attr**
  attr_name

  attr_name = attr_value

An `attr_name` follows the same rules as any other Dudley name, namely it must
be quoted if if contains characters other than alphanumeric characters or
underscores, or if it begins with a digit.  For attributes which have a value,
the value may be one of:

**attr_value**
  integer_number

  floating_point_number

  "quoted string"

  [alist_value1, alist_value2, ... alist_valueN]

Quoted strings may use either single or double quotes, and support the same
three backslash escapes as Dudley names.

The attribute value may also be a 1D array of comma delimited values in
square brackets, the fourth form shown here.  The `alist_values` may be any
of the other three types - integers, floats, or quoted strings - but all the
values in the array must have the same type.  That is, only homogeneous 1D
arrays are permitted as attribute values.  There is no way to continue an
array attribute value into a second attribute comment - if the comment line
ends before the close square bracket, it is an error.

There is a delicate balance to be struck between what is an "attribute" of a
data item, and what is "data" in its own right.  Dudley intentionally
encourages you to take the complexity of the value into account by limiting
what it can keep as an attribute.  Notice also that attribute values are not
binary, but text representations.  Floats and integers are kept internally as
`f8` and `i8` values.
