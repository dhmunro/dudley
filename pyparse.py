"""Parse a Dudley layout from a file, stream, or str
"""
from __future__ import absolute_import

import sys
from collections import OrderedDict
from weakref import proxy
from io import StringIO

PY2 = sys.version_info < (3,)
if PY2:
    dict = OrderedDict

# import ast    ast.literal_eval(text_in_quotes)  repr is inverse
# JSON.parse, JSON.stringify in javascript
from ast import literal_eval


class DLayout(object):
    def __init__(self, filename=None, stream=None, text=None, ignore=0):
        self.filename = filename
        self.root = DGroup()
        self.types = {}  # types which have been used or explicitly declared
        self.default_order = "|"  # initialliy just native order
        self.ignore = 0  # 1 bit ignore attributes, 2 bit ignore doc comments
        if filename is not None:
            with open(filename) as stream:
                self.parse(stream)
        else:
            if text is not None:
                if PY2:
                    if isinstance(text, str):
                        try:
                            text = text.decode("utf-8")
                        except UnicodeDecodeError:
                            text = text.decode("latin1")
                stream = StringIO(text)
            self.parse(stream)

    @property
    def me(self):  # so a proxy can get back a strong reference
        return self
    # Note on proxy references: proxy.any_bound_method.__self__ to get
    # strong reference, but here provide a "me" property explicitly.
    # This is not usually needed, except for introspection like isinstance.

    primitives = set("f2", "f4", "f8", "i1", "i2", "i4", "i8",
                     "u1", "u2", "u4", "u8", "S1", "U1", "U2", "U4",
                     "b1", "c2", "c4", "c8")

    def get_type(self, name):
        dudtype = self.types.get(name)
        if dudtype is not None:
            return dudtype  # already seen this type
        order = name[0]
        if order in "><|":
            name = name[1:]
        else:
            order = ""
        if name in self.primitives:
            dudtype = DType(self, (order or "|") + name)
            self.types[order+name] = dudtype
        elif order:
            raise ValueError("illegal type name {}".format(order+name))
        return dudtype

    def parse(self, stream):
        tokens = DTokenizer(stream, self.ignore)
        default_order = None  # default byte order will come from binary file
        if tokens.peek()[0] in ("<", ">"):  # e.g.- netCDF always >
            self.default_order = tokens.next()[0]
        self.summary = None
        root = DDict()
        if tokens.peek() == ("{",):
            # Summary block, if present, is both a struct datatype and the
            # leading items in the root dict for the layout.
            summary = DType(self)
            summary.parse(tokens)  # parses everthing in {} as struct type
            root.update(summary)  # summary items also begin the root group
            self.summary = summary
        root.parse(layout, tokens)

    def describe(self, stream, prefix=""):
        if self.default_order:
            stream.write(prefix + self.default_order + "\n")
        if self.summary:
            self.summary.describe(stream, prefix)
        root.describe(stream, prefix)

    def syntax_error(mesg):
        pass


class DDict(dict):
    isdict = True
    islist = isdata = istype = isparam = False

    def __init__(self, parent):
        self.parent = proxy(parent)
        self.doc = self.attrs = None

    @property
    def me(self):  # so a proxy can get back a strong reference
        return self

    @property
    def layout(self):
        parent = self.parent
        return parent.layout if hasattr(parent, "parent") else parent.me

    def parse(self, layout, tokens):
        amtype = self.istype
        while True:
            token = tokens.next()
            if token[0] == "symbol":
                name = token[1]
                token = tokens.peek()
                if token == ("=",):
                    tokens.next()
                    self[name] = value = DData(self)
                    value.parse(layout, tokens)
                elif token == (":",):
                    tokens.next()
                    token = tokens.peek()
                    if token[0] == "int":
                        tokens.next()
                        value = token[1]
                    else:
                        value = DData(self)
                        value.parse(layout, tokens)
                        attrs = value.attrs
                        if attrs.shape or attrs.stype.kind != "i":
                            layout.syntax_error(
                                "syntax error parameter {} not a scalar int"
                                "".format(name))
                    # how to store parameters?
                elif token == ("/",):  # declare or continue dict
                    tokens.next()
                    value = self.get(name)
                    if value is None:
                        value = DDict(self)
                        self[name] = value
                    elif not isinstance(value, DDict):
                        layout.syntax_error(
                            "syntax error expecting {} to be a dict"
                            "".format(name))
                    value.parse(layout, tokens)
                elif token == ("[",):  # declare or continue list
                    value = self.get(name)
                    if value is None:
                        value = DList(self)
                        self[name] = value
                    elif not isinstance(value, DList):
                        layout.syntax_error(
                            "syntax error expecting {} to be a list"
                            "".format(name))
                    value.parse(layout, tokens)
                elif token == ("{",):  # declare type, always at global level
                    value = DType(layout, name)
                    value.parse(layout, tokens)
                elif token in (("-",), ("eof",)):
                    return  # EOF
                else:
                    layout.syntax_error(
                        "syntax error declaring {}".format(name))
            elif token == ("/",):
                layout.root.parse(layout, tokens)  # continue parsing root
            elif token == ("..",):
                parser = self.parent.parse
                if isinstance(parser.__self__, DDict):
                    parser(layout, tokens)  # back to parent
                else:
                    layout.syntax_error("syntax error parent is not dict")
            elif token == (",",):
                parser = self.parent.parse
                if isinstance(parser.__self__, DList):
                    parser(layout, tokens)  # back to parent
                else:
                    layout.syntax_error("syntax error group parent is not list")
            else:
                layout.syntax_error("syntax error expecting name to declare")

    def describe(self, stream, prefix=""):
        pass


class DType(DDict):
    istype = True
    islist = isdata = isdict = isparam = False

    def __init__(self, layout, primitive=name):
        if hasattr(layout, "parent"):
            raise TypeError("parent of DType must be a DLayout instance")
        super(DType, self).__init__(layout)


class DList(list):
    islist = True
    isdict = isdata = istype = isparam = False

    def __init__(self, parent, name):
        self.parent = proxy(parent)
        self.doc = self.attrs = None

    @property
    def me(self):  # so a proxy can get back a strong reference
        return self

    @property
    def layout(self):
        parent = self.parent
        return parent.layout if hasattr(parent, "parent") else parent.me

    def parse(self, layout, tokens):
        pass

    def describe(self, stream, prefix=""):
        pass


class DData(object):
    isdata = True
    islist = isdict = istype = isparam = False

    def __init__(self, parent):
        self.parent = proxy(parent)
        self.doc = self.attrs = None

    @property
    def layout(self):
        parent = self.parent
        return parent.layout if hasattr(parent, "parent") else parent.me

    def parse(self, layout, tokens):
        pass

    def describe(self, stream, prefix=""):
        pass


class DParam(DData):
    isparam = True
    islist = isdata = isdict = istype = False


#    tokens (terminals of grammar):
# symbol
# quoted   (symbol if attribute name, otherwise text value)
# fixed    (value is int)
# floating (value is float)
# = : [ ] , + - * / .. { } < > | @ % #  (value is character as str)
re_symbol = re.compile(r"[a-zA-Z_]\w*")
re_quoted = re.compile(r'(?:"(?:\\.|[^"\\])*"'
                       r"|(?:'(?:\\.|[^'\\])*')")
re_fixed = re.compile(r"[+-]?([1-9]\d*|0x[[a-fA-F0-9]+|0o[0-7]+|0b[01]+|0+)")
re_floating = re.compile(r"[+-]?(?:\d+\.\d*|\.\d+"
                         r"|(?:\d+|\d+\.\d*|\.\d+)[eE][+-]?\d+)")
re_punctuation = re.compile(r"(?:[][}{=:,+\-*@%><|]|\.\.)")
re_comment = re.compile(r"#.*$", re.M)
re_spaces = re.compile(r"\s+")


class DTokenizer(object):
    def __init__(self, stream, ignore=0):
        self.stream = stream
        self.line = stream.readline()  # read first line
        self.nline = 1
        self.pos = 0  # first unconsumed character of line
        self.ignore = ignore
        self.lookahead = None
        self.docs = self.attribs = self.errors = None

    def next(self):
        token = self.lookahead
        if token:
            self.lookahead = None
            return token
        line, pos = self._skip_spaces_and_comments()
        # Note that attribute and document comments, as well as
        # errors while parsing attribute comments, are stored in self.
        # These are cumulative until pop_docs_attribs_errors() called.
        if not line:
            return "eof",
        match = re_symbol.match(line, pos)
        if match:
            self.pos = match.end()
            return "symbol", match.group()
        match = re_punctuation.match(line, pos)
        if match:
            self.pos = match.end()
            return match.group(),
        match = re_fixed.match(line, pos)
        if match:
            self.pos = match.end()
            return "int", int(match.group(), 0)
        match = re_quoted.match(line, pos)
        if match:
            self.pos = match.end()
            return "symbol", literal_eval(match.group())
        # cannot find a legal token
        self.pos = pos + 1
        return "error", pos

    def peek(self):
        token = self.next()
        self.lookahead = token
        return token

    def pop_docs_attribs_errors(self):
        docs, attribs = self.docs, self.attribs
        self.docs = self.attribs = self.errors = None
        return docs, attribs, errors

    def _skip_spaces_and_comments(self):
        line, pos, ignore = self.line, self.pos, self.ignore
        errors = None
        while True:
            match = re_spaces.match(line, pos)
            if match:
                pos = match.end()
            match = re_comment.match(line, pos)
            if match:
                c = match.group()
                if c.startswith("#:") and not ignore & 1:
                    attribs, dpos, errmsg = self._acomment(c[2:].rstrip())
                    if errmsg is not None:
                        err = self.line, self.nline, pos+2+dpos, errmsg
                        if errors is None:
                            errors = [err]
                        else:
                            errors.append(err)
                    self.attribs.update(attribs)
                if c.startswith("##") and not ignore & 2:
                    docs = self.docs
                    if docs:
                        docs.append(c[2:].rstrip())
                    else:
                        self.docs = [c[2:].rstrip()]
            elif pos < len(line):
                self.errors = errors
                return line, pos  # pos at a token on this line
            self.line = stream.readline()
            self.nline += 1
            if not line:
                self.errors = errors
                return line, pos  # EOF because line is ""

    def _acomment(self, string):
        # Parse attribute comments on a single line.  A single attribute
        # definition may not span multiple lines, and within a single line
        # the definitions must be comma separated.
        attribs = {}
        pos = 0
        posmax = len(string)
        skip_spaces = self._skip_spaces
        get_constant = self._get_constant
        while True:
            pos = skip_spaces(string, pos)
            if pos >= posmax:
                return attribs, None, None
            name, pos = self.get_name(string, pos)
            if name is None:
                return attribs, pos, "expecting attribute name"
            pos = skip_spaces(string, pos)
            if pos < posmax and string[pos] not in "=,":
                return attribs, pos, "expecting attribute name="
            if pos >= posmax or string[pos] == ",":
                attribs[name] = True  # only way to get boolean attribute value
                if pos >= posmax:
                    return attribs, None, None
                pos += 1
                continue
            pos = skip_spaces(string, pos+1)  # skip past = sign
            if pos < posmax and string[pos] == "[":
                pos = skip_spaces(string, pos+1)
                value, pos, expect = get_constant(string, pos)
                if value is None:
                    return attribs, pos, expect
                value = [value]
                while True:
                    pos = skip_spaces(string, pos)
                    if pos < posmax:
                        if string[pos] == "]":
                            attribs[name] = array(value)
                            pos += 1
                            break
                        if string[pos] != ",":
                            return (attribs. pos,
                                    "missing , in attribute name=[v1,...]")
                        pos = skip_spaces(string, pos)
                        v, pos, expect = get_constant(string, pos, expect)
                        if v is None:
                            return attribs, pos, expect
                        value.append(v)
            else:
                pos = skip_spaces(string, pos+1)
                value, pos, expect = get_constant(string, pos)
                if value is None:
                    return attribs, pos, expect
                attribs[name] = value
            pos = skip_spaces(string, pos)
            if pos >= posmax:
                return attribs, None, None
            if string[pos] != ",":
                "expected , between attributes in attribute list"
            pos += 1

    def _skip_spaces(string, pos):
        match = re_spaces.match(string, pos)
        return match.end() if match else pos

    def _get_name(self, string, pos=0):
        name = None
        match = re_symbol.match(string, pos)
        if match:
            pos = match.end()
            name = match.group()
        else:
            match = re_quoted.match(string, pos)
            if match:
                pos = match.end()
                name = literal_eval(match.group())
        return name, pos

    def _get_constant(string, pos, expect=None):
        if expect:
            expect = [expect==1, expect==2, expect==3]
        else:
            expect = [True, True, True]
        match = expect[0] and re_fixed.match(string, pos)
        if match:
            return int(match.group(), 0), match.end(), 1
        match = expect[1] and re_quoted.match(string, pos)
        if match:
            return literal_eval(match.group()), match.end(), 2
        match = expect[2] and re_floating.match(string, pos)
        if match:
            return float(match.group()), match.end(), 3
        if all(expect):
            return None, pos, "expecting fixed, quoted, or float attrib value"
        else:
            return None, pos, "attribute array elements not all same type"
