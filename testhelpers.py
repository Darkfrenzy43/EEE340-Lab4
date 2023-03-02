"""
Some functions and a class designed to assist in testing semantic analysis
of Nimble programs.

Author: Greg Phillips

Version: 2023-02-08

"""

from collections import defaultdict

from antlr4 import ParseTreeWalker
from errorlog import ErrorLog
from generic_parser import parse
from nimble import NimbleLexer, NimbleParser
from nimblesemantics import DefineScopesAndSymbols, InferTypesAndCheckConstraints
from symboltable import Scope


def do_semantic_analysis(source, start_rule_name, first_phase_only=False):
    """
    Runs semantic analysis on the source parse tree, then indexes
    the computed node_types by line and expression to help with testing.

    The semantic analysis is in two phases:

    - `DefineScopesAndSymbols`, then
    - `InferTypesAndCheckConstraints`

    See `nimblesemantics.py` for descriptions of the two phases.

    The second phase can be switched off using the `first_phase_only` parameter,
    where you want to test just the results of the first phase.
    """

    tree = parse(source, start_rule_name, NimbleLexer, NimbleParser)
    walker = ParseTreeWalker()

    error_log = ErrorLog()
    global_scope = Scope('$global', None, None)
    node_types = {}

    scopes_and_symbols = DefineScopesAndSymbols(error_log, global_scope, node_types)
    walker.walk(scopes_and_symbols, tree)

    if not first_phase_only:
        types_and_constraints = InferTypesAndCheckConstraints(error_log, global_scope, node_types)
        walker.walk(types_and_constraints, tree)

    indexed_types = index(node_types)
    return error_log, global_scope, indexed_types


def index(node_types):
    """ Creates the 2-level dictionary of the inferred types of each expression
    in the script. Look in API documentation for example. """
    indexed_types = defaultdict(dict)
    for ctx, inferred_type in node_types.items():
        line = ctx.start.line
        source = ctx.getText()
        indexed_types[line][source] = inferred_type
    return indexed_types


def pretty_types(indexed_types):
    """
    Returns a well-formatted string for indexed_types, as generated by
    the `index` function; useful for debugging.
    """
    output = []
    for line_number in sorted(indexed_types.keys()):
        output.append(f'line {line_number}:')
        for expr in sorted(indexed_types[line_number]):
            output.append(f'  {expr} : {indexed_types[line_number][expr]}')
    return '\n'.join(output)