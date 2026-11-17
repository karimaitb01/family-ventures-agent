"""Calculatrice sûre pour l'agent : l'IA ne calcule jamais de tête (elle se trompe sur les puissances)."""

import ast
import operator

OPERATIONS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
              ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos}


def calculer(expression: str) -> float:
    """Évalue + - * / ** et parenthèses sur des nombres, rien d'autre (pas de noms, pas d'appels)."""
    def valeur(noeud):
        if isinstance(noeud, ast.Constant) and isinstance(noeud.value, (int, float)):
            return noeud.value
        if isinstance(noeud, ast.BinOp) and type(noeud.op) in OPERATIONS:
            gauche, droite = valeur(noeud.left), valeur(noeud.right)
            if isinstance(noeud.op, ast.Pow) and abs(droite) > 100:
                raise ValueError("exposant trop grand")
            return OPERATIONS[type(noeud.op)](gauche, droite)
        if isinstance(noeud, ast.UnaryOp) and type(noeud.op) in OPERATIONS:
            return OPERATIONS[type(noeud.op)](valeur(noeud.operand))
        raise ValueError("seuls les nombres, + - * / ** et les parenthèses sont acceptés")
    try:
        return float(valeur(ast.parse(expression.replace(",", ".").replace(" ", ""), mode="eval").body))
    except (SyntaxError, ZeroDivisionError) as erreur:
        raise ValueError(f"expression invalide ({erreur.__class__.__name__})") from None
