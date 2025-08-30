/* Dudley grammar
  23 terminals
  21 non-terminals
  57 rules
  84 states

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
%token LARROW RARROW LPAREN RPAREN
/*       <-     ->     (      )   */
%token<num> PLUSSES MINUSES
/*             +       -   */

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
  SYMBOL EQ data_item
| SYMBOL COLON INTEGER
| SYMBOL COLON PRIMTYPE placement
| SYMBOL SLASH
| SYMBOL list_def
| SYMBOL struct_def
| SYMBOL list_extend
| SLASH
| DOTDOT
| EQ data_item
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
| SYMBOL PLUSSES
| SYMBOL MINUSES
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
  LBRACK list_items RBRACK
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
| error
;

list_extend:
  address_align
| list_extend address_align
;

struct_def:
  LCURLY struct_items RCURLY
| LCURLY EQ data_item RCURLY
;

struct_items:
  struct_items struct_item
|
;

struct_item:
  data_item
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
