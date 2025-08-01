/* Dudley grammar */

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
%token LT GT PIPE LARROW RARROW LPAREN RPAREN
/*     <  >   |     <-     ->     (      )   */
%token<num> PLUSSES MINUSES
/*             +       -   */

%%

layout:
  dict_items
| preamble dict_items
| preamble
|
;

order:
  LT
| GT
| PIPE
;

preamble:
  order
| order struct_def
| struct_def
;

primitive:
  order PRIMTYPE
| PRIMTYPE
;

data_or_param:
  SYMBOL EQ data_item
| SYMBOL COLON INTEGER
| SYMBOL COLON primitive
;

at_or_pcnt:
  AT INTEGER
| PCNT INTEGER
;

placement:
  at_or_pcnt
|
;

dict_item:
  data_or_param
| SYMBOL SLASH
| SYMBOL list_def
| SYMBOL struct_def
| SYMBOL at_or_pcnt
| SLASH
| DOTDOT
| error
;

dict_items:
  dict_item
| dict_items dict_item
;

data_item:
  primitive shape filter placement
| SYMBOL shape filter placement
| struct_def shape filter placement
;

dimension:
  INTEGER
| SYMBOL
| SYMBOL PLUSSES
| SYMBOL MINUSES
;

dimensions:
  dimension
| dimensions COMMA dimension
| error
;

shape:
  LBRACK dimensions RBRACK
|
;

filterop:
  LARROW
| RARROW
;

filterarg:
  INTEGER
| FLOATING
| error
;

filter:
  filterop SYMBOL
| filterop SYMBOL LPAREN filterarg RPAREN
|
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

struct_def:
  LCURLY struct_items RCURLY
;

struct_items:
  struct_item
| PCNT INTEGER struct_item
| struct_items struct_item
;

struct_item:
  data_or_param
| error
;
