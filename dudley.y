/* Dudley grammar */

%start layout

%token SYMBOL INTEGER SPECIAL
%token CEQ EEQ EQB SLASHB BAT DOTDOT QBRACE ATEQ QSLASH PLUSSES MINUSES
/*     :=  ==  =[  /[     !@  ..     ?{     @=   ?/     +       -      */

%%

layout:
  layout statement
|
;

statement:
  SYMBOL '=' type shape location
| SYMBOL EQB list_items ']'
| SYMBOL CEQ value
| SYMBOL EEQ type shape alignment
| SYMBOL '/'
| SYMBOL QBRACE root_params '}' shape location
| SYMBOL QSLASH
| '/'
| DOTDOT
| INTEGER '=' type shape location
| BAT INTEGER
| SPECIAL
| error
;

value:
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
| '{' members '}'
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
  '@' INTEGER
| '%' INTEGER
|
; 

alignment:
  '%' INTEGER
|
; 

list_item:
  '=' type shape location
| EQB list_items ']'
| SLASHB group_items ']'
| error
;

list_items:
  list_items list_item
|
;

group_item:
  SYMBOL '=' type shape location
| SYMBOL EQB list_items ']'
| SYMBOL '/'
| DOTDOT
| '/'
| error
;

group_items:
  group_items group_item
|
;

member:
  SYMBOL '=' type shape location
| SYMBOL CEQ value
| '=' type shape location
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
  '=' basetype location
| ATEQ basetype location
| SYMBOL CEQ value
| error
;
