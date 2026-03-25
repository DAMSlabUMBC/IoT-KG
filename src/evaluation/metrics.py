"""
Triple comparison and evaluation metrics.

Provides fuzzy matching between template (ground truth) triples and LLM triples,
then computes precision, recall, and F1.
"""

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from src.types.triple import Triple

# Aliases for predicates the LLM may freely invent, mapped to canonical names
PREDICATE_ALIASES: dict[str, set[str]] = {
    "manufacturedBy": {
        "manufactured by", "made by", "brand", "manufacturer", "produced by",
        "created by", "sold by",
    },
    "compatibleWith": {
        "compatible with", "works with", "supports", "supported by",
        "operating system", "runs on", "designed for",
    },
    "hasSensor": {"has sensor", "contains sensor", "sensor", "equipped with sensor"},
    "performs": {
        "performs", "can", "capability", "function", "features", "does",
        "has capability", "has function",
    },
    "hasASIN": {"asin", "amazon id", "amazon identifier", "amazon standard identification number"},
    "hasCategory": {"category", "belongs to", "categorized as", "product category"},
    "hasConnectivity": {
        "connectivity", "connection", "wireless technology", "wireless",
        "connects via", "uses connectivity",
    },
    "hasInterface": {"interface", "has interface", "connector type", "port type"},
    "hasModelNumber": {
        "model", "model number", "part number", "item model number",
        "model name", "product model",
    },
    "madeIn": {"country of origin", "made in", "manufactured in", "origin"},
    "hasRating": {"rating", "customer review", "star rating", "review score"},
    "hasPrice": {"price", "cost", "selling price", "retail price", "priced at"},
    "hasFeature": {"feature", "includes", "has feature", "specification", "detail"},
    "hasWeight": {"weight", "item weight", "weighs"},
    "hasDimensions": {"dimensions", "size dimensions", "product dimensions", "measures"},
    "hasColor": {"color", "colour", "available in color"},
    "hasVoltage": {"voltage", "operating voltage"},
    "hasWattage": {"wattage", "power consumption", "watts"},
    "hasBattery": {"battery", "number of batteries", "battery type"},
    "firstAvailable": {"date first available", "release date", "first available", "launched"},
    "hasBestSellerRank": {"best sellers rank", "bestseller rank", "sales rank"},
    "hasProperty": {"property", "has", "attribute"},
}

# Flattened alias lookup: alias_text → canonical predicate
_ALIAS_TO_CANONICAL: dict[str, str] = {}
for _canonical, _aliases in PREDICATE_ALIASES.items():
    for _alias in _aliases:
        _ALIAS_TO_CANONICAL[_alias] = _canonical


def normalize(s: str) -> str:
    """Lowercase, collapse whitespace, remove punctuation for comparison."""
    s = s.lower().strip()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def similarity(a: str, b: str) -> float:
    """String similarity ratio in [0, 1] using SequenceMatcher."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def normalize_predicate(pred: str) -> str:
    """Map a free-text predicate to its canonical camelCase form if known."""
    normed = normalize(pred)
    # Direct canonical match
    for canonical in PREDICATE_ALIASES:
        if normed == normalize(canonical):
            return canonical
    # Alias match
    if normed in _ALIAS_TO_CANONICAL:
        return _ALIAS_TO_CANONICAL[normed]
    return pred


def predicates_match(p1: str, p2: str) -> bool:
    """Return True if two predicates refer to the same relationship."""
    return normalize_predicate(p1) == normalize_predicate(p2)


def triples_match(t1: Triple, t2: Triple, threshold: float = 0.8) -> bool:
    """
    Return True if two triples represent the same fact.

    Matching rules:
    - Predicates must be equivalent (exact or alias match).
    - Subject values: similarity >= threshold OR one contains the other.
    - Object values: same as subjects.
    """
    if not predicates_match(t1.predicate, t2.predicate):
        return False

    def values_match(v1: str, v2: str) -> bool:
        n1, n2 = normalize(v1), normalize(v2)
        return (
            similarity(v1, v2) >= threshold
            or n1 in n2
            or n2 in n1
        )

    return values_match(t1.subject.value, t2.subject.value) and values_match(
        t1.object.value, t2.object.value
    )


@dataclass
class EvaluationMetrics:
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float
    # Matched pairs: (template_triple, llm_triple)
    matched_pairs: list[tuple[Triple, Triple]] = field(default_factory=list)
    # Template triples the LLM missed
    missed: list[Triple] = field(default_factory=list)
    # LLM triples not matched to any template triple
    extra: list[Triple] = field(default_factory=list)


def compute_metrics(
    template_triples: list[Triple],
    llm_triples: list[Triple],
    threshold: float = 0.8,
) -> EvaluationMetrics:
    """
    Compare LLM triples against template (ground truth) triples.

    Uses greedy matching: for each LLM triple, finds the unmatched template
    triple with the highest object similarity (if above threshold).

    Returns precision, recall, F1, and detailed match/miss/extra lists.
    """
    unmatched_template = list(template_triples)
    unmatched_llm = list(llm_triples)
    matched_pairs: list[tuple[Triple, Triple]] = []

    for llm_t in list(llm_triples):
        best_templ: Triple | None = None
        best_sim = -1.0

        for templ_t in unmatched_template:
            if triples_match(llm_t, templ_t, threshold):
                obj_sim = similarity(llm_t.object.value, templ_t.object.value)
                if obj_sim > best_sim:
                    best_sim = obj_sim
                    best_templ = templ_t

        if best_templ is not None:
            matched_pairs.append((best_templ, llm_t))
            unmatched_template.remove(best_templ)
            unmatched_llm.remove(llm_t)

    tp = len(matched_pairs)
    fp = len(unmatched_llm)
    fn = len(unmatched_template)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return EvaluationMetrics(
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        precision=precision,
        recall=recall,
        f1=f1,
        matched_pairs=matched_pairs,
        missed=unmatched_template,
        extra=unmatched_llm,
    )
