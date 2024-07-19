/* Dudley grammar */

%union{
  char *str;
  long long num;
}

%start layout

%token<str> SYMBOL
%token<num> INTEGER
%token EQ CEQ EEQ PEQ SLASH ELLIPSIS DOTDOT DOT LBRACK RBRACK COMMA AT PCNT
/*     =  :=  ==  +=  /     ...      ..     .   [      ]      ,     @  %   */
%token LCURLY RCURLY BCURLY QUEST
/*     {      }      !{     ?    */
%token<num> PLUSSES MINUSES
/*          +       -      */
%token<str> PRIMTYPE

%%

layout:
  layout statement
|
;

statement:
  SYMBOL EQ variable
| SYMBOL EQ list
| SYMBOL SLASH
| SYMBOL PEQ list
| DOTDOT
| SLASH
| SYMBOL EEQ atype shape alignment
| SYMBOL address_list
| INTEGER EQ variable
| BCURLY members RCURLY
| error
;

variable: atype shape location
;

parameter:
  INTEGER
| basetype location
;

append_items:
  PEQ variable
|
;

basetype:
  SYMBOL
| PRIMTYPE
;

atype:
  basetype
| LCURLY members RCURLY
| LBRACK items RBRACK
;

shape:
  LBRACK dimensions RBRACK
|
;

location:
  address
| alignment
; 

address:
  AT INTEGER
| AT DOT
;

alignment:
  PCNT INTEGER
|
;

ushapedef: LBRACK ELLIPSIS
;

ushape:
  ushapedef RBRACK
| ushapedef COMMA dimensions RBRACK
;

uaddress:
  address_list
|
;

address_list:
  address
| address_list address
;

dimension:
  INTEGER
| symbolq
| symbolq PLUSSES
| symbolq MINUSES
;

symbolq:
  SYMBOL
| SYMBOL QUEST
;

dimensions:
  dimensions COMMA dimension
| dimension
;

items:
  variable
| items COMMA variable
| error
|
;

member:
  SYMBOL EQ variable
| SYMBOL CEQ parameter
| EQ variable
| error
;

members:
  members member
|
;
