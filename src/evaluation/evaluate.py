"""
Main evaluation script: Template-based vs LLM-based triple extraction.

Runs both extractors on an Amazon product URL, compares results, prints a
detailed report, and saves JSON output to data/evaluation/.

Usage:
    uv run -m src.evaluation.evaluate [url] [model]

    url   : Amazon product page URL (default: HiLetgo FT232RL adapter)
    model : Ollama model name for LLM extraction (default: gemma3:27b)
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from src.evaluation.metrics import EvaluationMetrics, FalsePositive, compute_metrics
from src.extractors.amazon.template_extractor import AmazonTemplateExtractor
from src.extractors.llm_extractor import LLMTripleExtractor
from src.types.triple import Triple

DEFAULT_URL = (
    "https://www.amazon.com/Google-Nest-Thermostat-Smart-Programmable/dp/B08HRPDYTP/ref=sr_1_1_mod_primary_new?dib=eyJ2IjoiMSJ9.kZzJqvpPmPNLiR4HPY2y6hqqx0ux1t85tNWIvZmOG9n04Oc9iUJwLTSp6uJ4Wt2VML7YKKHTJGBZ1G4UMpgEHNVR6iUyZDo3yga859nBct0vRC0tUpc3SI0OZpIzkyBubAIcs2njbGjB073TCVOrhmytcIi1TXTrK1IKWrNpuIi7uRHKh_kKvX2HJbPvaWJvXHynEby6jkt2pdU-LdKmjlATArPovCPKCFtcoFjNFBZ1Ba5XZjFhH9W38P0isGJ5d_ZfIgSRQANk5f-jm6dhsZaLLMLbuH6IuJGHC-GgUSo.izNe6MdX3tnEgnS7tLm7lk_HBMLcFmJlNxXgWENpGlA&dib_tag=se&keywords=google+nest&qid=1772170656&s=amazon-devices&sbo=RZvfv%2F%2FHxDF%2BO5021pAnSA%3D%3D&sr=1-1"
)
DEFAULT_MODEL = "gemma3:4b"
OUTPUT_DIR = Path("data/evaluation")

WIDTH = 80


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _fmt(t: Triple) -> str:
    return (
        f'({t.subject.node_type}, "{t.subject.value}")'
        f" -[{t.predicate}]->"
        f' ({t.object.node_type}, "{t.object.value}")'
    )


def _section(title: str, count: int | None = None) -> None:
    label = f"  {title}"
    if count is not None:
        label += f"  [{count}]"
    print("=" * WIDTH)
    print(label)
    print("=" * WIDTH)


def print_report(
    url: str,
    template_triples: list[Triple],
    llm_triples: list[Triple],
    metrics: EvaluationMetrics,
) -> None:
    print()
    print("=" * WIDTH)
    print("  Amazon Triple Extraction: Template vs LLM")
    print("=" * WIDTH)
    print(f"\n  URL: {url}\n")

    _section("Template Triples  (Ground Truth)", len(template_triples))
    for i, t in enumerate(template_triples, 1):
        print(f"  {i:3}. {_fmt(t)}")

    print()
    _section("LLM Triples", len(llm_triples))
    for i, t in enumerate(llm_triples, 1):
        print(f"  {i:3}. {_fmt(t)}")

    print()
    _section("Evaluation Metrics")
    print(f"  True Positives  (LLM correct):      {metrics.true_positives}")
    print(f"  False Positives (LLM hallucinated):  {metrics.false_positives}")
    print(f"  False Negatives (LLM missed):        {metrics.false_negatives}")
    print()
    print(f"  Precision : {metrics.precision:.3f}  ({metrics.true_positives}/{metrics.true_positives + metrics.false_positives})")
    print(f"  Recall    : {metrics.recall:.3f}  ({metrics.true_positives}/{metrics.true_positives + metrics.false_negatives})")
    print(f"  F1 Score  : {metrics.f1:.3f}")

    if metrics.matched_pairs:
        print()
        _section("Matched Triples", len(metrics.matched_pairs))
        for templ, llm in metrics.matched_pairs:
            print(f"  ✓ [{templ.predicate}]  {_fmt(templ)}")

    if metrics.missed:
        print()
        _section("Missed by LLM  (False Negatives)", len(metrics.missed))
        for t in metrics.missed:
            print(f"  ✗ {_fmt(t)}")

    if metrics.extra:
        print()
        _section("LLM-only Triples  (Needs Human Review)", len(metrics.extra))
        print("  Label each as 'hallucination' or 'valid_extra' in the JSON output.")
        print()
        for fp in metrics.extra:
            print(f"  ? {_fmt(fp.triple)}")

    print()


# ---------------------------------------------------------------------------
# JSON serialisation
# ---------------------------------------------------------------------------


def _triple_to_dict(t: Triple) -> dict:
    return {
        "subject": {"node_type": t.subject.node_type, "value": t.subject.value},
        "predicate": t.predicate,
        "object": {"node_type": t.object.node_type, "value": t.object.value},
    }


def save_results(
    url: str,
    template_triples: list[Triple],
    llm_triples: list[Triple],
    metrics: EvaluationMetrics,
    model: str,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results = {
        "url": url,
        "model": model,
        "timestamp": datetime.now().isoformat(),
        "template_triples": [_triple_to_dict(t) for t in template_triples],
        "llm_triples": [_triple_to_dict(t) for t in llm_triples],
        "matched_pairs": [
            {"template": _triple_to_dict(tmpl), "llm": _triple_to_dict(llm)}
            for tmpl, llm in metrics.matched_pairs
        ],
        "missed": [_triple_to_dict(t) for t in metrics.missed],
        "extra": [
            {"triple": _triple_to_dict(fp.triple), "review": fp.review}
            for fp in metrics.extra
        ],
        "metrics": {
            "true_positives": metrics.true_positives,
            "false_positives": metrics.false_positives,
            "false_negatives": metrics.false_negatives,
            "precision": round(metrics.precision, 4),
            "recall": round(metrics.recall, 4),
            "f1": round(metrics.f1, 4),
        },
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"  Results saved → {output_path}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def evaluate(
    url: str = DEFAULT_URL,
    model: str = DEFAULT_MODEL,
) -> EvaluationMetrics:
    """
    Run both extractors on an Amazon product URL and compare results.

    Args:
        url   : Amazon product page URL.
        model : Ollama model name used for LLM extraction.

    Returns:
        EvaluationMetrics with precision, recall, F1, and detailed match lists.
    """
    print(f"\n[1/2] Template extractor  →  {url}")
    template_extractor = AmazonTemplateExtractor()
    template_triples = template_extractor.extract(url, debug=True)
    print(f"       {len(template_triples)} triples extracted")

    print(f"\n[2/2] LLM extractor  (model: {model})")
    llm_extractor = LLMTripleExtractor(model=model)
    llm_triples = llm_extractor.extract(template_extractor.scraped_data)
    print(f"       {len(llm_triples)} triples extracted")

    metrics = compute_metrics(template_triples, llm_triples)

    print_report(url, template_triples, llm_triples, metrics)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"amazon_eval_{timestamp}.json"
    save_results(url, template_triples, llm_triples, metrics, model, output_path)

    return metrics


if __name__ == "__main__":
    # Strip stray backslashes/quotes that PowerShell can inject when escaping
    _url = sys.argv[1].strip("\\'\"") if len(sys.argv) > 1 else DEFAULT_URL
    _model = sys.argv[2].strip("\\'\"") if len(sys.argv) > 2 else DEFAULT_MODEL
    evaluate(_url, _model)
