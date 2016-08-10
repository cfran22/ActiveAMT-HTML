# Works in Python 2.5.	Built-in ast.literal_eval didn't come until Python 2.6.

# Credit: Gabriel Genellina
#         http://www.velocityreviews.com/forums/t698556-re-compiler-ast-helper-function-literal_eval-in-python-2-4-a.html
def literal_eval(node_or_string):
	"""
	Safely evaluate an expression node or a string containing a Python
	expression. The string or node provided may only consist of the following
	Python literal structures: strings, numbers, tuples, lists, dicts, booleans,
	and None.
	"""
	from compiler import parse
	from compiler.ast import Const, Tuple, List, Dict, Name, UnarySub, Expression
	_safe_names = {'None': None, 'True': True, 'False': False}

	if isinstance(node_or_string, basestring):
		node_or_string = parse(node_or_string, mode='eval')
	if isinstance(node_or_string, Expression):
		node_or_string = node_or_string.node # [pylint] attribute node exists : pylint:disable=E1103

	def _convert(node):
		if isinstance(node, Const) and isinstance(node.value, (basestring, int, float, long, complex)):
			return node.value
		elif isinstance(node, Tuple):
			return tuple(map(_convert, node.nodes))
		elif isinstance(node, List):
			return list(map(_convert, node.nodes))
		elif isinstance(node, Dict):
			return dict((_convert(k), _convert(v)) for k, v in node.items)
		elif isinstance(node, Name):
			if node.name in _safe_names:
				return _safe_names[node.name]
			elif isinstance(node, UnarySub):
				return -_convert(node.expr)
		raise ValueError('malformed string')

	return _convert(node_or_string)
