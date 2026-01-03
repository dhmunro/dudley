Dudley Grammar
==============

Terminals
---------

Besides punctuation, the Dudley grammar has these terminals:

**SYMBOL**:
  Any text comprising ASCII alphanumeric characters or underscores whose first
  character is not a digit.

**QUOTED**
  Any quoted Unicode text excluding the NUL character is a legal name.  Either
  single or double quotes, "**\"**" or "**`**" may be used, and escape
  sequences "**\\\"**", "**\\`**" and "**\\\\**" inside quoted strings can be
  used to get a quote or backslash into the string.  Dudley does not recognize
  any other escape sequences.  A quoted string only ends with the matching
  unescaped close quote.

**INTEGER**:
  A string of decimal digits not beginning with 0 (except for the single digit
  0), or a string of hex digits prefixed by "0x".  The digits may be prefixed
  with a "-" or "+" sign.

**PRIMITIVE**:
  A three or four character shorthand name for the predefined primitive
  datatypes, similar to the numpy array protocol, consisting of one of three
  prefixes, followed by a single character indicating the kind of encoding,
  followed by one or two digits specifying the number of bytes per item.
  The prefixes are "**<**" (little endian), "**>**" (big endian), or
  "**|**" (unspecified byte order).  The characters are "u" or "i" (unsigned
  or signed integer, 1, 2, 4, or 8 bytes), "f" (IEEE754 floating point, 2, 4
  or 8 bytes), "c" (complex, 4, 8, or 16 bytes), "b" (boolean,   1 byte), "S"
  (ASCII or CP1252 or Latin1 character, 1 byte), "U" (Unicode character, 1, 2,
  or 4 bytes).  These prefixed strings are the only reserved words in Dudley.

**FLOAT**:
  A floating point number recognized by C or python (including an
  optional sign prefix).  It must include a decimal point to distinguish it
  from an integer.

A sixth pseudo-terminal, **ERROR**, indicates an alternative whose action
attempts to resynchronize the parser after a syntax error.  Effectively,
anything matches the **ERROR** terminal up until the parser can resynchronize
and continue parsing input.

Dudley is a very simple PEG (Parsing Expression Grammar), although it does not
depend on the ordered alternative semantics that defines PEGs.
Here "?" denotes zero or one occurrence, "+" denotes one or more occurrence,
and "*" denotes zero or more occurrences.  Punctuation that is part of the
grammar is shown is double quotes.

Note that the entire layout is a **dict_body**, namely the root dict.

**dict_body**:
  dict_element*

  ERROR

**dict_element**:
  name named_item

  "**..**"

  "**/**"

  "**&**" ref_item

**name**:
  SYMBOL

  QUOTED

**named_item**:
  "**:**" data_item

  "**/**"

  "**[**" list_body? "**]**"

  "**{**" struct_body? "**}**"

  "**=**" param_item

**data_item**
  datatype shape? (cfilter | rfilter)? placement?

**list_body**:
  list_element ("**,**" list_element)* "**,**"?

  ERROR

**struct_body**:
  "**:**" datatype shape? rfilter? placement?

  (name "**:**" datatype shape? placement?)+

  ERROR

**param_item**:
  INTEGER

  datatype placement?

**datatype**:
  PRIMITIVE

  name

  "**{**" struct_body? "**}**"

**shape**:
  "**(**" dimension ("**,**" dimension)* "**)**"

**dimension**:
  INTEGER

  name PARAMSFX?

**placement**:
  "**@**" INTEGER

  "**%**" INTEGER

**list_element**:
  data_item

  INTEGER? "**[**" list_body? "**]**"

  INTEGER? "**/**" dict_body

  INTEGER? placement

  ("**&**" ref_item)+

**cfilter**:
  "**->**" name ("**(**" filt_arg ("**,**" filt_arg)* "**)**")?

**rfilter**:
  "**<-**" name ("**(**" filt_arg ("**,**" filt_arg)* "**)**")?

**filt_arg**:
  INTEGER

  FLOAT

  QUOTED

**ref_item**
  INTEGER* ref_datatype ref_shape? placement?

**ref_datatype**:
  PRIMITIVE

  name

  "**{**" refstruct_body? "**}**"

**ref_shape**:
  "**(**" INTEGER ("**,**" INTEGER)* "**)**"

**ref_struct_body**:
  "**:**" ref_datatype ref_shape? rfilter? placement?

  (name "**:**" ref_datatype ref_shape? placement?)+

  ERROR

Comments
--------

Comments begin with "**#**" and extend to the next end-of line.  They are
treated as whitespace but otherwise ignored for the purposes of building the
layout.  However, the Dudley parser records two special types of comments,
and associates their text with the item (array, dict, list, parameter, or
datatype) currently being defined.

**## document comment line**:
  The parser keeps a list of document comment lines associated with each item.

**#: attributes**:
  The parser keeps a dict of attributes associated with each item.

**attributes**:
  attribute*

**attribute**:
  name

  name "**=**" attrvalue

**attrvalue**:
  INTEGER

  FLOAT

  QUOTED

  "**[**" INTEGER ("**,**" INTEGER)* "**]**"

  "**[**" FLOAT ("**,**" FLOAT)* "**]**"
