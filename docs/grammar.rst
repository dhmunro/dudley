Dudley Grammar
==============

Terminals
---------

Besides punctuation, the Dudley grammar has these terminals:

**name**:
  Any text comprising ASCII alphanumeric characters or underscores whose first
  character is not a digit.  Additionally, any quoted Unicode text excluding
  the NUL charcter is a legal name; Dudley has no keywords.  Names may be
  quoted with either single or double quotes, "**\"**" or "**`**", and escape
  sequences "**\\\"**", "**\\`**" and "**\\\\**" can be used inside quoted
  strings.  (Dudley does not recognize any other escape sequences; a quoted
  string only ends with the matching unescaped close quote.)

**integer**:
  A string of decimal digits not beginning with 0 (except for the single digit
  0), or a string or hex digits prefixed by "0x".  The digits may be prefixed
  with a "-" or "+" sign.

**primitive**:
  A three or four character shorthand name for the predefined primitive
  datatypes, similar to the numpy array protocol, consisting of one of three
  prefixes, followed by a single character indicating the kind of encoding,
  followed by one or two digits specifying the number of bytes per item.
  The prefixes are "**<**" (little endian), "**>**" (big endian), or
  "**|**" (unspecified byte order).  The characters are "u" or "i" (unsigned
  or signed integer, 1, 2, 4, or 8 bytes), "f" (IEEE754 floating point, 2, 4
  or 8 bytes), "c" (complex, 4, 8, or 16 bytes), "b" (boolean,   1 byte), "S"
  (ASCII or CP1252 or Latin1 character, 1 byte), "U" (Unicode character, 1, 2,
  or 4 bytes).

**float**:
  A floating point number recognized by C or python (including an
  optional sign prefix).  It must include a decimal point to distinguish it
  from an integer.

Container specification
------------------------

Here "?" denotes zero or one occurrence, "+" denotes one or more occurrence,
and "*" denotes zero or more occurrences.

Note that the entire layout is a **dict**, namely the root dict.

**dict**:
  dictitem*

**dictitem**:
  name "**:**" data

  name "**/**" dict

  name "**[**" list "**]**"

  name "**=**" parameter

  name struct

  "**/**"

  "**..**"

**list**:
  listitems?

**listitems**:
  listitem

  listitem "**,**" listitems

**listitem**:
  data

  integer? address

  integer? "**/**" dict

  integer? "**[**" list "**]**"

Data specification
------------------

**array**:
  datatype shape? address?
 
  struct shape? address?

**data**:
  array filter?

**parameter**:
  integer

  primitive address?

  name address?

**datatype**:
  primitive

  name

**struct**:
  "**{**" structbody "**}**"

**structbody**:
  structmember*

  "**:**" array

**structmember**:
  name "**:**" array

**shape**:
  "**[**" dimensions "**]**"

**dimensions**:
  dimension

  dimension "**,**" dimensions

**dimension**:
  integer

  name

  name "**+**"+

  name "**-**"+

**address**:
  "**@**" integer

  "**%**" integer

**filter**:
  "**->**" name arguments?

  "**<-**" name arguments?

**arguments**:  
  "**(**" arglist "**)**"

**arglist**:
  argument

  argument "**,**" arglist

**argument**:
  integer

  float

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
  attribute

  attribute attributes

**attribute**:
  name

  name "**=**" attrvalue

  name "**=**" "**[**" integers "**]**"

  name "**=**" "**[**" floats "**]**"

**attrvalue**:
  integer

  float

  string

**integers**:
  integer "**,**" integers

**floats**:
  float "**,**" floats

**string**:
  A terminal like the **name** terminal, except that it must be quoted.
