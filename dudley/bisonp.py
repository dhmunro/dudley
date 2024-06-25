"""Module bisonp implements a parser using Bison-generated parse tables.

This is an event-driven parser, designed as a callback accepting a stream
of successive tokens as events.  Each new token advances the state of a
generator function, which completes when the parse is complete, which
is usually when an end-of-file token is delivered.

Alternatively, you can provide a next_token function to operate the parser
in the manner of a traditional yacc-lex or bison-flex parser, so that it
performs the entire parse in a single call which repeatedly invokes your
next_token function until it returns the EOF token or the parse aborts at
an unhandled error in your grammar.

To use the parser, you need to run bison to generate the required tables,
then run then bisonx extraction utility to extract the tables in the
form required by BisonParser, creating a bisontab.py module.  The bisontab
file will contain the extracted tables, plus a skeleton for you to flesh
out with the functions that implement the rules for your grammar.  Then::

   from bisonp import BisonParser
   from bisontab import tables, rules
   parser = BisonParser(tables, rules)

At this point, you can either use parser(token) as a callback for token
events, or provide a next_token() function to perform the whole parse:

   if parser(next_token):
       parse_failed

BisonParser requires than you write your grammar in such a way that it
has no actions in the middle of its rules.  This is usually a minor
inconvenience.

For each rule in your grammar, the skeleton produced by bisonx looks like
this::

   @parser_rule
   def rule(args):
       '''lhs: rhs0 rhs1 rhs2 ...'''
       pass

The args will be a list of rhs values [value_rhs0, value_rhs1, ...].
Your rule should return the value that will be associated with the lhs
non-terminal in other rules of your grammar.  The next_token function
must return (token_number, token_value) pairs for the terminals of your
grammar.

"""


class BisonParser(object):
    # parser = BisonParser(tables, rules)
    #   then event callback when token arrives:
    # if not parser(token):
    #     parse complete, check parser.result, parser.nerrs
    # reduction rule i invokes rules(args) where args is rule RHS value list
    def __init__(self, tables, rules):
        if len(rules) != len(tables["r1"]):
            raise ValueError("rule table size does not match bison tables")
        self.tables = tables
        self.rules = rules
        self(None)

    def parse(self, next_token):
        token = None
        while self(token):
            token = next_token()
        return self.result

    # BisonParser instance is a callback function for token stream
    # Call with token == None to reset.
    def __call__(self, token):
        if token is None:
            self.iterator = iter(self._call())
            next(self.iterator)  # cannot accept a token before first yield
        return self.iterator.send(token)

    def _call(self):
        pact, defact, table, check, pgoto, defgoto, r1, r2, final = [
            self.tables[nm] for nm in ["pact", "defact", "table", "check",
                                       "pgoto", "defgoto", "r1", "r2", "final"]]
        parse_rules = self.rules
        default_pact = min(pact)
        last = len(yytable) - 1
        default_pact = min(yypact)  # take default action (-41)
        ntokens = max(yyr1) - yynnts + 1  # terminals of the grammar (31)
        # tokens have EOF, error, UNDEF prepended as 0, 1, 2
        eof_token, err_token, undef_token = 0, 1, 2

        state = 0  # 0 is initial state
        nerrs = errstatus = 0
        stack = [(state, None)]
        lookahead = None
        result = None

        while state != final:
            i = pact[state]
            if i == default_pact:
                rule = defact[state]
            else:
                if lookahead is None:
                    # At this point, need new token to progress.
                    lookahead = yield True
                i += lookahead
                if i >= 0 and i <= last and check[i] == lookahead:
                    j = table[i]  # >0 state for shift, <0 -rule for reduce
                    if j > 0:
                        state = j  # table entry is new state
                        if errorstatus:
                            errorstatus -= 1
                        # ---------- shift lookahead token ------------
                        stack.append((state, token.m.value))
                        lookahead = None
                        continue
                    rule = -j  # table entry is minus reduction rule
            if rule:
                # ----------- reduce according to rule --------------
                nargs, n = r2[rule], len(stack)
                value = parser_rule[rule](
                    [stack[k][1] for k in range(n-nargs:n)])
                del stack[-nargs:]
                state, _ = stack[-1]
                # non-default gotos for this reduction also stored in table
                lhs = r1[rule] - ntokens
                i = state + pgoto[lhs]
                if i >= 0 and i <= last and check[i] == state:
                    state = table[state]
                else:
                    state = defgoto[lhs]
                    stack.append((state, value))
            else:
                # ----------- syntax error -------------
                if not errstatus:
                    nerrs += 1
                elif errstatus == 3:
                    if lookahead == eof_token:
                        break  # abort if at EOF
                    lookahead = None  # failed to reuse lookahead token
                errstatus = 3  # resume parse after shifting 3 tokens
                j = 0
                while j <= 0:
                    i = pact[state]
                    if i != default_pact:
                        i += err_token
                        if i >= 0 and i <= last and check[i] == err_token:
                            j = table[i]
                            continue
                    if not stack:
                        break
                    state, _ = stack.pop()  # pop until state handles error
                else:
                    # found state that shifts err_token, push it
                    state = j
                    stack.append((state, None))  # value None okay??
                    continue
                break  # no state shifts err_token, abort

        else:
            # ------------ accept successful parse -------------
            result = 0
        # abort unsuccessful parse
        if result is None:
            result = 1
        self.result = result
        self.nerrs = nerrs
        self(None)  # automatic reset if parse is finished
        yield False
