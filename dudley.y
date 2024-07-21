/* Dudley grammar */

%union{
  char *str;
  long long num;
}

%start layout

%token<str> SYMBOL
%token<num> INTEGER
%token EQ CEQ EEQ PEQ SLASH DOTDOT DOT LBRACK RBRACK COMMA AT PCNT
/*     =  :=  ==  +=  /     ..     .   [      ]      ,     @  %   */
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
  group_member
| SYMBOL PEQ list
| SYMBOL address_list
| SYMBOL EEQ datatype shape alignment
| INTEGER EQ array
| BCURLY members RCURLY
;

group_member:
  SYMBOL CEQ parameter
| SYMBOL EQ array
| SYMBOL SLASH
| DOTDOT
| SLASH
| SYMBOL EQ list
| error
;

parameter:
  INTEGER
| basetype location
;

basetype:
  SYMBOL
| PRIMTYPE
;

array: datatype shape location
;

datatype:
  basetype
| LCURLY members RCURLY
;

shape:
  LBRACK dimensions RBRACK
|
;

dimensions:
  dimensions COMMA dimension
| dimension
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

list:
  LBRACK items RBRACK
;

items:
  item
| items COMMA item
|
;

item:
  array
| list
| SLASH group_members SLASH
| error
;

group_members:
  group_members group_member
|
;

address_list:
  address
| address_list address
;

members:
  members member
|
;

member:
  SYMBOL CEQ parameter
| SYMBOL EQ array
| EQ array
| error
;
