import ast
import operator
import re

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Compare):
        # Models sometimes answer with the whole covenant test, e.g.
        # "total_debt <= threshold". Comparing is the evaluator's job, so keep
        # only the measured side and drop the threshold.
        return _eval_node(node.left)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        value = _eval_node(node.operand)
        return -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, ast.BinOp):
        op = _BIN_OPS.get(type(node.op))
        if op is None:
            raise ValueError("Unsupported operator in formula")
        return op(_eval_node(node.left), _eval_node(node.right))
    raise ValueError("Formula must contain only numbers and arithmetic operators")


def apply_formula(formula: str, inputs: dict[str, float]) -> float:
    """
    Substitute input names into an LLM-provided expression and evaluate it.

    Only numeric arithmetic is allowed, so an unresolved name or any call,
    attribute, or comparison raises instead of executing.
    """
    expression = formula.strip()
    if not expression:
        raise ValueError("Empty formula")

    # Longest names first so a short name cannot clobber part of a longer one.
    for name in sorted(inputs, key=len, reverse=True):
        expression = re.sub(rf"\b{re.escape(name)}\b", repr(inputs[name]), expression)

    return _eval_node(ast.parse(expression, mode="eval").body)
