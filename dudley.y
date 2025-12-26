/* Dudley grammar
  23 terminals
  22 non-terminals
  63 rules
  95 states

  Does not include mini-grammar for attribute comments (or document comments)
  - expect to handler those in lexer.
 */

%union{
  char *str;
  long long num;
  double realnum;
}

%start layout

%token<str> SYMBOL PRIMTYPE
%token<num> INTEGER
%token<realnum> FLOATING
%token EQ COLON SLASH DOTDOT LBRACK RBRACK COMMA AT PCNT LCURLY RCURLY
/*     =    :     /     ..      [      ]     ,   @   %     {      }   */
%token LARROW RARROW LPAREN RPAREN CARAT
/*       <-     ->     (      )      ^  */
%token<num> PARAMSFX
/*           + or -   */

%%

layout:
  dict_items
|
;

dict_items:
  dict_item
| dict_items dict_item
;

dict_item:
  SYMBOL COLON data_item
| SYMBOL EQ INTEGER
| SYMBOL EQ PRIMTYPE placement
| SYMBOL SLASH
| SYMBOL list_def
| SYMBOL struct_def
| SLASH
| DOTDOT
| CARAT data_item
| error
;

data_item:
  PRIMTYPE shape filter placement
| SYMBOL shape filter placement
| struct_def shape filter placement
;

shape:
  LBRACK dimensions RBRACK
|
;

dimensions:
  dimension
| dimensions COMMA dimension
;

dimension:
  INTEGER
| SYMBOL
| SYMBOL PARAMSFX
| error
;

placement:
  address_align
|
;

address_align:
  AT INTEGER
| PCNT INTEGER
;

list_def:
  LBRACK list_items list_close
;

list_close:
  RBRACK
| COMMA RBRACK
;

list_items:
  list_item
| list_items COMMA list_item
|
;

list_item:
  data_item
| list_def
| SLASH dict_items
| SLASH
| INTEGER list_def
| INTEGER SLASH dict_items
| address_align
| INTEGER address_align
| ref_items
| error
;

ref_items:
  CARAT data_item
| ref_items CARAT data_item
;

struct_def:
  LCURLY struct_items RCURLY
| LCURLY COLON data_item RCURLY
;

struct_items:
  struct_items struct_item
|
;

struct_item:
  SYMBOL COLON data_item
| error
;

filter:
  filterop SYMBOL
| filterop SYMBOL LPAREN filterargs RPAREN
|
;

filterop:
  LARROW
| RARROW
;

filterargs:
  filterarg
| filterargs COMMA filterarg
;

filterarg:
  INTEGER
| FLOATING
| error
;
