"""Dudley layout language parser."""
from __future__ import absolute_imports

from io import TextIOBase

from .layout import (Layout, Address,
                     D_PRIM, D_DATA, D_PARAM, D_DICT, D_LIST, D_TYPE)
from .filter import CFilter, RFilter

__all__ = "opendud"


def opendud(dudfile=None, mode=None):
    """Parse a Dudley layout, returning the root LDict.

    Parameters
    ----------
    dudfile : str or TextIOBase, optional
        is a UTF-8 (or ASCII) text file name or previously opened text stream
        Note that if `dudfile` is an already open text stream, its encoding
        need not be UTF-8.  If `dudfile` is None (default), new empty layout
        is not associated with any stream.

    mode : str, optional
        "r" (default) to open read-only, "a" to open for appending (creating
        the file if not present), "r+" to open for appending (error if the
        file not present), "w" to create the file (overwriting existing file),
        "x" to create the file (error if file is present)

    Returns
    -------
    l_root : LDict
        the root LDict of the layout specified by `dudfile`
    """
    if not isinstance(dudfile, TextIOBase):
        if mode is None:
            mode = "r"
        elif "b" in mode:
            raise ValueError("cannot open Dudley description in binary mode")
        dudfile = open(dudfile, mode)
    flags = 0
    if dudfile is not None:
        if dudfile.readable():
            flags = 1
        if dudfile.writable():
            flags += 2
    layout = Layout()
    l_root = layout.l_item(0)
    if flags & 1:
        Parser(l_root).parse(dudfile)
        if parser.errs:
            raise RuntimeError("{} errors parsing Dudley description"
                               .format(len(parser.errs)))
    return l_root


class Parser(object):
    """Dudley parser automaton, state advances on each input line."""
    def __init__(self, l_root):
        self.container = l_root  # current container
        self.docs = self.atts = self.errs = None
        self.tokens = None  # iterator created by tokenize()

    def tokenize(self, dudfile):
        """Split input stream into tokens, with mini-parser for comments."""
        qclose = attribs = attstack = None
        nline = 0
        for line in dudfile:
            nline += 1
            pos = 0
            if qclose:  # looking for end of multi-line quoted string
                match = close_quote.match(line)
                if not match:
                    value += line  # entire line is inside this quote
                    continue
                else:  # quote ends on this line
                    pos = match.end()  # after close quote
                    value += line[:pos-1]  # omit close quote
                    # replace \', \", \\ escapes within the string
                    value = _q_sub.sub("\\",
                                       _q2sub.sub('"', _q1sub.sub("'", value)))
                    qclose = None
                    if attribs is not None:
                        # Instead of yielding a token, parse attribute comment
                        self.parse_att(attribs, attstack,
                                       nline, 0, QUOTED, value)
                    else:
                        yield token, value

            pos = _white.match(line, pos).end()  # skip whitespace
            length = len(line)
            while pos < length:
                start = pos
                match = _token_patterns.match(line, pos)
                token = match.lastindex
                pos = match.end()
                if token == QUOTED:
                    qclose = _q1close if match.group() == "'" else _q2close
                    match = close_quote.match(line)
                    if not match:
                        value = line[start+1:]  # omit open quote
                        break  # quote continues to next line
                    pos = match.end()
                    value = line[start+1:pos-1]  # omit open and close quotes
                elif token == PARAMSFX:  # +++ or --- parameter suffix
                    value = pos - start
                    if line[start] == "-":
                        value = -value
                elif token == INTEGER:
                    value = line[start:pos]
                    # Discard leading zeros
                    if len(value) > 1 and value[1] not in "xX":
                        value = value.lstrip("0") or "0"
                    value = int(value)
                elif token == FLOAT:
                    value = float(line[start:pos])
                elif token == COMMENT and attribs is None:
                    special = line[start+1] if start+1 < pos else None
                    if special == "#":
                        docs = self.docs
                        if docs is None:
                            self.docs = [line[start+2:]]
                        else:
                            docs.append(line[start+2:])
                        # pos == length here
                    elif special == ":":
                        attribs = {}
                        attstack = []
                        # Reduce pos to only skip #: and whitespace.
                        pos = _white.match(line, start+2).end()
                    continue
                else:
                    value = line[start:pos]
                pos = _white.match(line, pos).end()  # skip whitespace
                if attribs is not None:
                    # Instead of yielding a token, parse attribute comment
                    self.parse_att(attribs, attstack,
                                   nline, start, token, value)
                    continue
                yield token, value

            if qclose is None and attribs is not None:
                # This is the end of attribute comment line.
                if attstack:
                    if len(attstack) == 1:
                        # final attribute name has no value
                        attribs[attstack[0]] = None
                    else:
                        self.parse_error(line, pos,
                                         "incomplete attribute value")
                if attribs:
                    atts = self.atts
                    if atts is None:
                        self.atts = attribs
                    else:
                        atts.update(attribs)
                attribs = attstack = None

        if qclose:
            self.parse_error(line, pos,
                             "file ends with with unclosed quoted name")
        # StopIteration handled in next_token() method.

    def parse_att(attribs, attstack, nline, start, token, value):
        """Parse next token in attribute comment line."""
        n = len(attstack)
        if n <= 1:  # looking for an attribute name
            if token in (TOKEN, SYMBOL):
                if n:
                    attribs[attstack[0]] = None  # first name has no value
                    del attstack[0:]  # clear stack
                attstack.append(value)
            elif n == 1 and token == EQUALS:
                attstack.append(value)
            else:
                self.parse_error(line, start, "expecting attribute name or =")
                del attstack[0:]  # clear attribute stack
        elif n == 2:  # looking for attribute value
            if token in (QUOTED, INTEGER, FLOAT):
                attribs[attstack[0]] = value
                del attstack[0:]  # clear stack
            elif token == LSQUARE:
                attstack.append(LSQUARE)
            else:
                self.parse_error(line, start, "expecting attribute value")
        else:
            atype = attstack[2]
            if atype & 0x100:  # looking for comma or close bracket
                if token == RSQUARE:
                    attribs[attstack[0]] = array(attstack[3:])
                    del attstack[0:]  # clear stack
                elif token == COMMA:
                    attstack[2] &= 0xff
                else:
                    self.parse_error(line, start,
                                     "expecting , or ] in array attribute")
                    del attstack[0:]  # clear stack
            elif token in (INTEGER, FLOAT):
                if atype == LSQUARE:
                    attstack[2] = token
                elif atype != token:
                    self.parse_error(line, start,
                                     "attribute array values "
                                     "must be all int or all float")
                    del attstack[0:]  # clear stack
                else:
                    attstack.append(value)
                attstack[2] |= 0x100  # look for comma next
            else:
                self.parse_error(line, start, "illegal attribute array value")
                del attstack[0:]  # clear stack

    def parse_error(line, column, msg):
        """Append an error to the Parser errs log."""
        errs = self.errs
        if errs is None:
            self.errs = [(line, column, msg)]
        else:
            errs.append((line, column, msg))

    def next_token(self):
        """Deliver the next token or put back token)."""
        token = self.lookahead
        if token:
            self.lookahead = None
        else:
            tokens = self.tokens
            if tokens is None:
                return EOF, None
            try:
                token = next(tokens)
            except StopIteration:
                token = EOF, None
                self.tokens = None  # discard exhausted token stream
        return token

    def put_back_token(self, token, value):
        """Put back a token so it will be delivered next."""
        self.lookahead = token, value

    def parse(self, dudfile):
        """Parse dudfile according to Dudley data description language."""
        self.tokens = self.tokenize(dudfile)
        self.dict_()

    def dict_(self):
        """Parse items in dict on top of container stack"""
        while True:
            # get next dictitem
            token, value = self.next_token()
            if token in (SYMBOL, QUOTED):
                # named item in this dict
                name = value
                token, value = self.next_token()
                if token == COLON:
                    self.data_(name)
                elif token == EQUALS:
                    self.param_(name)
                elif token == SLASH:
                    try:
                        self.container = self.container.getdict(name)
                    except TypeError:
                        continue  # how to recover??
                elif token == LSQUARE:
                    try:
                        self.container = self.container.getlist(name)
                    except TypeError:
                        continue  # how to recover??
                    self.list_(name)
                elif token == LCURLY:
                    self.type_(name)
                else:
                    # error
                    pass
            elif token == DOTDOT:
                # pop to parent if parent is dict, else no-op
                parent = self.container.parent
                if parent and parent.itype == D_DICT:
                    self.container = parent
            elif token == SLASH:
                # pop to root or first dict whose parent is a list
                self.container = self.container.root
            elif token == COLON:
                # this is anonymous reference, goes in root dict
                self.data_(Ellipsis)
            else:
                if token == EOF:
                    # not an error if this is not in a list
                    if not self.container.root.parent:
                        return
                # error
                pass

    def list_(self, name):
        """Parse items in list on top of container stack"""

    def data_(self, name):
        """data item in LDict or LList"""
        parent, name, datatype, shape, align = self.array_(name)
        filt = fargs = None
        token, value = self.peek_token()
        cfilter = token == RARROW
        if cfilter or token == LARROW:
            self.next_token()
            token, value = self.next_token()
            if token in (SYMBOL, QUOTED):
                filt = value
                token, value = self.peek_token()
                if token == LPAREN:
                    self.next_token()
                    fargs = []
                    while True:
                        token, value = self.next_token()
                        if token in (RPAREN, EOF):
                            break
                        if token in (INTEGER, FLOAT):
                            fargs.append(value)
                        else:
                            pass
                    if token == EOF:
                        pass
            fconstruct = CFilter if cfilter else RFilter
            filt = fconstruct(filt, *fargs)
        # datatype, shape, align, filt(fargs)
        parent.layout.add_item(parent, name, datatype, shape, align, filt)

    def array_(self, name):
        """get array properties"""
        if name is Ellipsis:  # this is anonymous reference
            parent = self.containers[0]  # root LDict is parent
            name = None
        else:
            parent = self.containers[-1]
        token, value = self.next_token()
        if token == PRIMITIVE:
            datatype = value
        elif token in (SYMBOL, QUOTED):
            pass
        elif token == LCURLY:
            datatype = self.type_()
        else:
            self.parse_error()

    def type_(self, name):
        """declare a typedef or compound datattype"""
        parent = self.containers[-1]
        while parent.itype != D_DICT:
            parent = parent.parent  # find first LDict parent
        token, value = self.next_token()
        if token == RCURLY:  # NoneType
            datatype = None
        elif token == COLON:  # typedef with single anonymous member
            pass
        return datatype

# Pattern for skipping whitespace:
_white = re.compile(r"\s*", re.A)
# Patterns for close single and close double quote:
_q1close = re.compile(r"(?:\\.|[^'\\])+'")
_q2close = re.compile(r'(?:\\.|[^"\\])+"')
# Patterns for escape substitutions:
_q1sub = re.compile(r"\\'")
_q2sub = re.compile(r'\\"')
_q_sub = re.compile(r'\\\\')

_token_patterns = [
    # Multicharacter patterns first, float before integer
    r"[A-Za-z_][0-9A-Za-z_]*",  # 1 SYMBOL
    r'"|' + r"'",  # 2 QUOTED
    r"[<>|](?:[iu][1248]|f[248]|c(?:4|8|16)|S1|U[124]|b1)",  # 3 PRIMITIVE
    r"[\-+]?(?:\d*\.\d+|\d+\.\d*)(?:[eE][\-+]?\d+)?",  # 4 FLOAT
    r"[\-+]?(?:0x[0-9aA-Fa-f]+|\d+)",  # 5 INTEGER (but permits leading zeros)
    r"\.\.",  # 6 DOTDOT
    r"-\>",  # 7 RARROW
    r"\<-",  # 8 LARROW
    r"(?:-+|\++)",  # 9 PARAMSFX
    r":",  # 10 COLON
    r"/",  # 11 SLASH
    r"\[",  # 12 LSQUARE
    r"\]",  # 13 RSQUARE
    r"=",  # 14 EQUALS
    r",",  # 15 COMMA
    r"\{",  # 16 LCURLY
    r"\}",  # 17 RCURLY
    r"@",  # 18 AT
    r"%",  # 19 PERCENT
    r"\(",  # 20 LPAREN
    r"\)",  # 21 RPAREN
    r"\^",  # 22 CARAT
    r"#.*",  # 23 COMMENT
    r"\S"  # 24 UNKNOWN
]
_token_patterns = re.compile("(" + ")|(".join(_token_patterns) + ")", re.A)
SYMBOL, QUOTED, PRIMITIVE, FLOAT, INTEGER = 1, 2, 3, 4, 5
DOTDOT, RARROW, LARROW, PARAMSFX, COLON, SLASH = 6, 7, 8, 9, 10, 11
LSQUARE, RSQUARE, EQUALS, COMMA, LCURLY, RCURLY = 12, 13, 14, 15, 16, 17
AT, PERCENT, LPARENT, RPAREN, CARAT, COMMENT = 18, 19, 20, 21, 22, 23
UNKNOWN, EOF = 24, 25
# Note that COMMENT is never returned as a token.
# UNKNOWN captures any single character not caught by any other pattern
