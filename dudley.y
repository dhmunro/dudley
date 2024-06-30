/* Dudley grammar */

%union{
  char *str;
  long long num;
}

%start layout

%token<str> SYMBOL
%token<num> INTEGER
%token CEQ EEQ EQB SLASHC BAT DOTDOT QCURLY ATEQ QSLASH QUEST
/*     :=  ==  =[  /{     !@  ..     ?{     @=   ?/     ?    */
%token<num> PLUSSES MINUSES
/*           +       -      */
%token EQ LBRACK RBRACK COMMA SLASH STAR DOT AT PCNT
/*     =  [      ]      ,     /     *    .   @  %   */
%token LCURLY RCURLY
/*     {      }     */
%token<str> PRIMTYPE

%%

layout:
  layout statement
|
;

statement:
  group_item
| SYMBOL EEQ type shape alignment
| SYMBOL EQ type ushape uaddress
| SYMBOL address_list
| SYMBOL QSLASH
| rootdef root_params RCURLY shape location
| INTEGER EQ type shape location
| BAT INTEGER
;

group_item:
  SYMBOL EQ type shape location
| SYMBOL CEQ parameter
| SYMBOL SLASH
| listdef list_items RBRACK
| DOTDOT
| SLASH
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

type:
  basetype
| struct members RCURLY
;

rootdef: SYMBOL QCURLY
;

listdef: SYMBOL EQB
;

struct: LCURLY
;

shapedef: LBRACK
;

shape:
  shapedef dimensions RBRACK
|
;

ushapedef: LBRACK STAR
;

ushape:
  ushapedef RBRACK
| ushapedef COMMA dimensions RBRACK
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

uaddress:
  address_list
|
;

address_list:
  address
| address_list address
;

list_item:
  EQ type shape location
| anonlist list_items RBRACK
| anongroup group_items RCURLY
| error
;

list_items:
  list_items list_item
|
;

anonlist: EQB
;

anongroup: SLASHC
;

group_items:
  group_items group_item
|
;

member:
  SYMBOL EQ type shape location
| SYMBOL CEQ parameter
| EQ type shape location
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
  EQ basetype location
| ATEQ basetype location
| SYMBOL CEQ parameter
| error
;
