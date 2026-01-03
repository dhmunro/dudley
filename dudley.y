/* Dudley grammar
  24 terminals
  32 non-terminals
  85 rules
  144 states

  Does not include mini-grammar for attribute comments (or document comments)
  - expect to handler those in lexer.
 */

%union{
  char *str;
  long long num;
  double realnum;
}

%start layout

%token<str> SYMBOL PRIMITIVE QUOTED
%token<num> INTEGER
%token<realnum> FLOAT
%token EQ COLON SLASH DOTDOT LSQUARE RSQUARE COMMA AT PCNT LCURLY RCURLY
/*     =    :     /     ..      [       ]      ,   @   %     {      }   */
%token LARROW RARROW LPAREN RPAREN AMPERSAND
/*       <-     ->     (      )        &    */
%token<num> PARAMSFX
/*           + or -   */

%%

layout
: dict_body
;

dict_body
: dict_body dict_element
|
| error
;

dict_element
: name named_item
| DOTDOT
| SLASH
| AMPERSAND ref_item
;

name
: SYMBOL
| QUOTED
;

named_item
: name COLON data_item
| name SLASH
| name LSQUARE RSQUARE
| name LSQUARE list_body list_close
| name LCURLY RCURLY
| name LCURLY struct_body RCURLY
| name EQ param_item
;

data_item
: datatype shape filter placement
;

list_body
: list_element
| list_body COMMA list_element
| error
;

list_close
: RSQUARE
| COMMA RSQUARE
;

struct_body
: COLON datatype shape rfilter placement
| struct_members
| error
;

struct_members
: struct_member
| struct_members struct_member
;

struct_member
: name COLON datatype shape placement
;

param_item
: INTEGER
| datatype placement
;

datatype
: PRIMITIVE
| name
| LCURLY RCURLY
| LCURLY struct_body RCURLY
;

shape
: LPAREN dimensions RPAREN
|
;

dimensions
: dimension
| dimensions COMMA dimension
;

dimension
: INTEGER
| name
| name PARAMSFX
;

placement
: address_align
|
;

address_align
: AT INTEGER
| PCNT INTEGER
;

list_element
: data_item
| LSQUARE RSQUARE
| LSQUARE list_body list_close
| INTEGER LSQUARE RSQUARE
| INTEGER LSQUARE list_body list_close
| SLASH dict_body
| INTEGER SLASH dict_body
| address_align
| INTEGER address_align
| ref_items
;

rfilter
: LARROW name
| LARROW name LPAREN filt_args RPAREN
|
;

filter
: RARROW name
| RARROW name LPAREN filt_args RPAREN
| rfilter
;

filt_args
: filt_arg
| filt_args COMMA filt_arg
;

filt_arg
: INTEGER
| FLOAT
| QUOTED
;

ref_items
: AMPERSAND data_item
| ref_items AMPERSAND data_item
;

ref_item
: ref_datatype ref_shape placement
| INTEGER ref_item

ref_datatype
: PRIMITIVE
| name
| LCURLY RCURLY
| LCURLY ref_struct_body RCURLY
;

ref_shape
: LPAREN ref_dimensions RPAREN
|
;

ref_dimensions
: INTEGER
| dimensions COMMA INTEGER
;

ref_struct_body
: COLON ref_datatype ref_shape rfilter placement
| ref_struct_members
| error
;

ref_struct_members
: ref_struct_member
| ref_struct_members ref_struct_member
;

ref_struct_member
: name COLON ref_datatype ref_shape placement
;
