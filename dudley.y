/* Dudley grammar */

%start layout

%token SYMBOL INTEGER EOF
%token CEQ EEQ BAT DOTDOT QEQ ATEQ QSLASH PLUSSES MINUSES
/*     :=  ==  !@  ..     ?=  @=   ?/     +       -      */

%%

parameter:
  SYMBOL CEQ value
;

type:
  SYMBOL EEQ typeref shape alignment
;

variable:
  SYMBOL declaration
;

pointee:
  INTEGER declaration
;

declaration:
  '=' typeref shape location
;

value:
  INTEGER
| pfx_symbol location
;

pfx_symbol:
  '<' SYMBOL
| '>' SYMBOL
| '|' SYMBOL
| SYMBOL
;

location:
  '@' INTEGER
| alignment
;

alignment:
  '%' INTEGER
|
;

shape:
  '(' dimensions ')'
|
;

dimensions:
  dimensions ',' dimension
| dimension
;

dimension:
  INTEGER
| SYMBOL
| SYMBOL PLUSSES
| SYMBOL MINUSES
;

typeref:
  pfx_symbol
| struct
;

struct:
  '{' membership '}'
;

membership:
  parameters declaration
| members
;

members:
  members member
| member
;

member:
  variable
| parameters variable
;

parameters:
  parameters parameter
| parameter
;

listvar:
  SYMBOL list_declaration
;

list_declaration:
  '=' '[' items ']'
;

items:
  items declaration
  items list_declaration
  items '/' listgroup
|
;

group:
  SYMBOL '/'
| group_change
;

group_change:
  '/'
| DOTDOT
;

listgroup:
  variable
| listvar
| group
;

rootdef:
  SYMBOL QEQ '{' rootparams '}' shape location
;

rootparams:
  rootparams parameter
| rootparams '=' pfx_symbol location
| rootparams ATEQ pfx_symbol location
|
;

statement:
  parameter
| type
| variable
| listvar
| group
| pointee
| BAT INTEGER
| rootdef
| SYMBOL QSLASH
;

statements:
  statements statement
|
;

layout:
  statements EOF
;
