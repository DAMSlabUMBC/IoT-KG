"""
Triple comparison and evaluation metrics.

Compares template (ground truth) triples against LLM triples using strict
predicate and value matching. FPs are flagged for human review to distinguish
hallucinations from valid facts the template missed.
"""

import re
from dataclasses import dataclass, field

from src.types.triple import Triple


def normalize(s: str) -> str:
    """Lowercase and collapse whitespace for comparison."""
    return re.sub(r"\s+", " ", s.lower().strip())


def predicates_match(p1: str, p2: str) -> bool:
    """Return True if two predicates are the same (case-insensitive)."""
    return normalize(p1) == normalize(p2)


def values_match(v1: str, v2: str) -> bool:
    """Return True if two values are identical after normalization."""
    return normalize(v1) == normalize(v2)


def triples_match(t1: Triple, t2: Triple) -> bool:
    """
    Return True if two triples represent the same fact.

    Matching rules:
    - Predicates must match exactly (case-insensitive).
    - Subject and object values must match exactly (case-insensitive).
    """
    return (
        predicates_match(t1.predicate, t2.predicate)
        and values_match(t1.subject.value, t2.subject.value)
        and values_match(t1.object.value, t2.object.value)
    )


@dataclass
class FalsePositive:
    """An LLM triple not matched to any template triple, pending human review."""
    triple: Triple
    # Human review label: "hallucination" | "valid_extra" | None (unreviewed)
    review: str | None = None


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
    # LLM triples not matched to any template triple — needs human review
    extra: list[FalsePositive] = field(default_factory=list)


def compute_metrics(
    template_triples: list[Triple],
    llm_triples: list[Triple],
) -> EvaluationMetrics:
    """
    Compare LLM triples against template (ground truth) triples using strict
    exact matching.

    FP triples are wrapped in FalsePositive with review=None, indicating they
    need human annotation ("hallucination" or "valid_extra") before precision
    can be considered final.

    Returns precision, recall, F1, and detailed match/miss/extra lists.
    """
    unmatched_template = list(template_triples)
    unmatched_llm = list(llm_triples)
    matched_pairs: list[tuple[Triple, Triple]] = []

    for llm_t in list(llm_triples):
        for templ_t in unmatched_template:
            if triples_match(llm_t, templ_t):
                matched_pairs.append((templ_t, llm_t))
                unmatched_template.remove(templ_t)
                unmatched_llm.remove(llm_t)
                break

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
        extra=[FalsePositive(triple=t) for t in unmatched_llm],
    )
