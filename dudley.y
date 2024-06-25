/* Dudley grammar */

%union{
  char *str;
  long long num;
}

%start layout

%token<str> SYMBOL
%token<num> INTEGER
%token CEQ EEQ EQB SEQ SLASHB BAT DOTDOT QCURLY ATEQ QSLASH
/*     :=  ==  =[  *=  /[     !@  ..     ?{     @=   ?/    */
%token<num> PLUSSES MINUSES
/*           +       -      */
%token EQ LPAREN RPAREN COMMA SLASH STAR DOT AT PCNT RBRACK
/*     =  (      )      ,     /     *    .   @  %    ]     */
%token LCURLY RCURLY
/*     {      }     */
%token<str> PRIMTYPE
%token<str> SPECIAL

%%

layout:
  layout statement
|
;

statement:
  group_item
| paramdef parameter
| typedef type shape alignment
| uarraydef type ushape uaddress
| SYMBOL address_list
| SYMBOL QSLASH
| rootdef root_params RCURLY shape location
| pointee type shape location
| BAT INTEGER
| SPECIAL
;

group_item:
  arraydef type shape location
| SYMBOL SLASH
| listdef list_items RBRACK
| DOTDOT
| SLASH
| error
;

paramdef: SYMBOL CEQ
;

arraydef: SYMBOL EQ
;

typedef: SYMBOL EEQ
;

listdef: SYMBOL EQB
;

uarraydef: SYMBOL SEQ
;

rootdef: SYMBOL QCURLY
;

pointee: INTEGER EQ
;

parameter:
  INTEGER
| basetype location
;

basetype:
  SYMBOL
| PRIMTYPE
;

type:
  basetype
| struct members RCURLY
;

struct: LCURLY
;

shape:
  shapedef dimensions RPAREN
|
;

shapedef: LPAREN
;

dimension:
  INTEGER
| SYMBOL
| SYMBOL PLUSSES
| SYMBOL MINUSES
;

dimensions:
  dimensions COMMA dimension
| dimension
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

ushape:
  shapedef STAR RPAREN
| shapedef STAR COMMA dimensions RPAREN
;

uaddress:
  address_list
|
;

address_list:
  address
| address_list address
;

list_item:
  anonarray type shape location
| anonlist list_items RBRACK
| anongroup group_items RBRACK
| error
;

list_items:
  list_items list_item
|
;

anonarray: EQ
;

anonlist: EQB
;

anongroup: SLASHB
;

group_items:
  group_items group_item
|
;

member:
  arraydef type shape location
| paramdef parameter
| anonarray type shape location
| error
;

members:
  members member
| member
;

root_params:
  root_params root_param
| root_param
;

root_param:
  anonarray basetype location
| anonloc basetype location
| paramdef parameter
| error
;

anonloc: ATEQ
;
