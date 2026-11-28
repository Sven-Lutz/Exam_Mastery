"""Verify only complete, supported assertions in the text that the workbook prints."""
import operator
import re
from fractions import Fraction

from .experience_proof_checks import FalseIdentity, ProofCheckError, verify

NUM = r"[+-]?\d{1,12}(?:[.,]\d{1,12})?"
ARITHMETIC = re.compile(rf"({NUM})\s*([+*/×·÷−-])\s*({NUM})\s*(=|≈)\s*({NUM})")
AREA = re.compile(rf"(?:Bei|Für) a\s*=\s*({NUM}) und b\s*=\s*({NUM}) "
                  rf"(?:beträgt die Quadratfläche|ist die Quadratfläche) ({NUM})")
BOUND = re.compile(rf"(a²|ab|ba|b²|a\s*\+\s*b|Quadratfläche)\s*(=|≈)\s*({NUM})")
OPS = {"+": operator.add, "-": operator.sub, "−": operator.sub, "*": operator.mul,
       "×": operator.mul, "·": operator.mul, "/": operator.truediv, "÷": operator.truediv}


def number(text):
    return Fraction(str(text).replace(",", "."))


def compare(expected, relation, literal):
    if relation == "≈":
        digits = len(literal.replace(",", ".").partition(".")[2])
        expected = round(expected, digits)
    if number(literal) == expected:
        return "CHECKED", str(expected)
    return "BLOCKER", f"Erwartet {expected}, angegeben {literal}"


def area_variants(unit):
    scenes = unit.get("interactions")
    for scene in scenes if isinstance(scenes, list) else []:
        if not isinstance(scene, dict) or scene.get("model_ref") != "binomial_area_partition":
            continue
        variants = scene.get("variants")
        for variant in variants if isinstance(variants, list) else []:
            if isinstance(variant, dict):
                yield scene, variant


def lengths(variant):
    values = variant.get("parameters")
    if not isinstance(values, dict) or set(values) != {"a", "b"}:
        return None
    if any(type(x) not in (int, float) or not 0.5 <= x <= 6 for x in values.values()):
        return None
    return number(values["a"]), number(values["b"])


def parameters(unit, reference):
    if (not isinstance(reference, dict) or set(reference) != {"interaction", "variant"}
            or not all(isinstance(v, str) and v for v in reference.values())):
        raise ValueError("solution_oracle benötigt interaction und variant")
    matches = [lengths(v) for scene, v in area_variants(unit)
               if scene.get("id") == reference["interaction"] and v.get("label") == reference["variant"]]
    if len(matches) != 1 or matches[0] is None:
        raise ValueError("Unbekannte, mehrdeutige oder ungültige Flächenvariante")
    return matches[0]


def check_text(text, sides, unit, task):
    text = text.removesuffix(".")
    match = AREA.fullmatch(text)
    if match:
        a, b = map(number, match.group(1, 2))
        if sides is None:
            # "Quadratfläche" alone does not establish that the side is a+b.
            skills = task.get("competency_ids")
            if not isinstance(skills, list) or not any(
                lengths(v) == (a, b) and isinstance(scene.get("competency_ids"), list)
                and any(key in scene["competency_ids"] for key in skills)
                for scene, v in area_variants(unit)
            ):
                return "UNVERIFIED", "Keine passende Flächenvariante der Aufgabenkompetenz"
        elif sides != (a, b):
            return "BLOCKER", "Seitenlängen widersprechen der gebundenen Variante"
        return compare((a + b)**2, "=", match[3])
    match = ARITHMETIC.fullmatch(text)
    if match:
        try:
            value = OPS[match[2]](number(match[1]), number(match[3]))
        except ZeroDivisionError:
            return "BLOCKER", "Division durch null"
        return compare(value, match[4], match[5])
    match = BOUND.fullmatch(text)
    if match and sides is not None:
        a, b = sides
        values = {"a²": a*a, "ab": a*b, "ba": b*a, "b²": b*b, "a+b": a+b, "Quadratfläche": (a+b)**2}
        return compare(values[re.sub(r"\s", "", match[1])], match[2], match[3])
    if text.startswith("Polynomidentität: ") and len(text) <= 500 and text.count("=") == 1:
        lhs, rhs = text.removeprefix("Polynomidentität: ").split("=")
        try:
            verify({"kind": "polynomial_identity", "lhs": lhs.strip(), "rhs": rhs.strip(),
                    "variables": sorted(set(re.findall(r"[A-Za-z]+", lhs + rhs)))})
        except FalseIdentity as exc:
            return "BLOCKER", str(exc)
        except ProofCheckError:
            pass
        else:
            return "CHECKED", "Polynomidentität über den reellen Zahlen"
    return "UNVERIFIED", "Fachliche Prüfung erforderlich"


def coverage(unit, task):
    rows = []
    sides = None
    if "solution_oracle" in task:
        try:
            sides = parameters(unit, task["solution_oracle"])
        except ValueError as exc:
            rows.append({"field": "solution_oracle", "status": "BLOCKER", "detail": str(exc)})
    fields = [(k, task.get(k)) for k in ("solution", "solution_approach")]
    steps = task.get("solution_steps")
    for i, pair in enumerate(steps if isinstance(steps, list) else []):
        if isinstance(pair, list) and len(pair) == 2:
            fields.extend((f"solution_steps[{i}][{j}]", text) for j, text in enumerate(pair))
    for field, text in fields:
        if not isinstance(text, str):
            continue
        for i, line in enumerate(text.splitlines()):
            if line.strip():
                status, detail = check_text(line.strip(), sides, unit, task)
                rows.append({"field": f"{field}:{i+1}", "status": status, "detail": detail})
    return rows
