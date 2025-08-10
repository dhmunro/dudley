/* Dudley grammar
  27 terminals
  23 non-terminals
  66 rules
  101 states

  Does not include grammar for attribute comments (or document comments).
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
%token LT GT LARROW RARROW LPAREN RPAREN AMP
/*     <  >    <-     ->     (      )     & */
%token<num> PLUSSES MINUSES
/*             +       -   */

%%

layout:
  dict_items
| preamble dict_items
| preamble
|
;

dict_items:
  dict_item
| dict_items dict_item
;

dict_item:
  data_param
| SYMBOL SLASH
| SYMBOL list_def
| SYMBOL struct_def
| SYMBOL list_extend
| SLASH
| DOTDOT
| AMP data_item
| error
;

data_param:
  SYMBOL EQ data_item
| SYMBOL COLON INTEGER
| SYMBOL COLON PRIMTYPE placement
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
;

struct_items:
  PCNT INTEGER struct_item
| struct_items struct_item
|
;

struct_item:
  data_param
| error
;

order:
  LT
| GT
;

preamble:
  order
| order LCURLY template_params RCURLY
| LCURLY template_params RCURLY
;

template_params:
  SYMBOL COLON PRIMTYPE
| template_params SYMBOL COLON PRIMTYPE
| error
;

filter:
  filterop SYMBOL
| filterop SYMBOL LPAREN filterarg RPAREN
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
