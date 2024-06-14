/* Dudley grammar */

%start layout

%token SYMBOL INTEGER
%token CEQ EEQ EQB SLASHB BAT DOTDOT QBRACE ATEQ QSLASH PLUSSES MINUSES
/*     :=  ==  =[  /[     !@  ..     ?{     @=   ?/     +       -      */
%token SPECIAL

%%

layout:
  layout statement
|
;

statement:
  group_item
| SYMBOL CEQ parameter
| SYMBOL EEQ type shape alignment
| SYMBOL '=' type ushape uaddress
| SYMBOL address_list
| rootdef root_params '}' shape location
| SYMBOL QSLASH
| INTEGER '=' array
| BAT INTEGER
| SPECIAL
;

group_item:
  SYMBOL '=' array
| SYMBOL '/'
| namedlist list_items ']'
| DOTDOT
| '/'
| error
;

array: type shape location
;

parameter:
  INTEGER
| basetype location
;

basetype:
  SYMBOL
| '>' SYMBOL
| '<' SYMBOL
| '|' SYMBOL
;

type:
  basetype
| begintype members '}'
;

begintype: '{'
;

shape:
  '(' dimensions ')'
|
;

dimension:
  INTEGER
| SYMBOL
| SYMBOL PLUSSES
| SYMBOL MINUSES
;

dimensions:
  dimensions ',' dimension
| dimension
;

location:
  address
| alignment
; 

address:
  '@' INTEGER
| '@' '.'
;

alignment:
  '%' INTEGER
|
;

ushape:
  '(' '*' ')'
| '(' '*' ',' dimensions ')'
;

uaddress:
  address_list
|
;

address_list:
  address
| address_list address
;

namedlist: SYMBOL EQB
;

anonlist: EQB
;

list_item:
  '=' array
| anonlist list_items ']'
| SLASHB group_items ']'
| error
;

list_items:
  list_items list_item
|
;

group_items:
  group_items group_item
|
;

member:
  SYMBOL '=' array
| SYMBOL CEQ parameter
| '=' array
| error
;

members:
  members member
| member
;

rootdef: SYMBOL QBRACE
;

root_params:
  root_params root_param
| root_param
;

root_param:
  '=' basetype location
| ATEQ basetype location
| SYMBOL CEQ parameter
| error
;
