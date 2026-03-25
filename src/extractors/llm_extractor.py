"""
LLM-based semantic triple extractor for Amazon product pages.

Uses a local Ollama model (default: gemma3:27b) to extract knowledge triples
from product page text content. Follows the same ChatOllama + structured output
pattern used throughout the project (see src/analysis/entity_analysis.py).
"""

from typing import List

from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from typing_extensions import TypedDict

from src.types.triple import Triple, TripleNode

# All predicates the LLM should preferentially use, aligned with the ontology
AVAILABLE_PREDICATES = [
    "manufacturedBy",
    "compatibleWith",
    "hasSensor",
    "performs",
    "hasASIN",
    "hasCategory",
    "hasConnectivity",
    "hasInterface",
    "hasModelNumber",
    "madeIn",
    "hasBestSellerRank",
    "hasRating",
    "hasWeight",
    "hasDimensions",
    "hasColor",
    "hasMaterial",
    "hasVoltage",
    "hasWattage",
    "hasSeries",
    "hasBattery",
    "firstAvailable",
    "hasFeature",
    "hasProperty",
    "hasPrice",
    "hasSize",
    "hasDataTransferRate",
    "hasProcessor",
    "hasStorage",
    "hasPowerSource",
    "hasFormFactor",
]

PROMPT_TEMPLATE = """\
You are an expert knowledge graph builder for IoT and electronic products.
Extract ALL factual knowledge triples from the Amazon product page content below.

A triple is (subject, predicate, object):
- subject: the main product or an entity related to it
- predicate: the relationship type (use camelCase from the preferred list when possible)
- object: the related entity or attribute value

Node types (use for subject_type and object_type):
- device        : IoT or electronic devices (the main product)
- manufacturer  : companies or brands that make products
- sensor        : sensors or detectors (GPS, accelerometer, etc.)
- process       : functions or capabilities the device performs
- application   : software, apps, or platforms
- category      : product categories
- identifier    : ASINs, model numbers, part numbers
- property      : technical specs, dimensions, weights, prices, dates, ratings

Preferred predicates (use these when they fit; use hasProperty as fallback):
{predicates}

Rules:
- Extract EVERY fact you can find, including technical specs, compatibility info,
  physical properties, identifiers, and categories.
- Use the product title as the subject value for facts about the main product.
- For multi-value fields (e.g. "Windows, Mac, Linux"), create one triple per value.
- Do not hallucinate — only extract facts present in the content.

Product Page Content:
{content}
"""


class TripleItem(TypedDict):
    subject: str
    subject_type: str
    predicate: str
    object: str
    object_type: str


class TripleListOutput(TypedDict):
    triples: List[TripleItem]


class LLMTripleExtractor:
    """
    Extracts knowledge triples from product page text using a local LLM.

    Args:
        model: Ollama model name (default: gemma3:27b for best accuracy).
    """

    def __init__(self, model: str = "gemma3:4b") -> None:
        self.llm = ChatOllama(model=model)
        self.prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)

    def extract(self, product_data: dict[str, str]) -> list[Triple]:
        """
        Extract triples from a product_data dict of section_name → text.
        Matches the format produced by AmazonTemplateExtractor.scraped_data.
        """
        content = self._format_content(product_data)
        predicates_str = "\n".join(f"- {p}" for p in AVAILABLE_PREDICATES)

        filled_prompt = self.prompt.format(
            predicates=predicates_str,
            content=content,
        )

        structured_llm = self.llm.with_structured_output(
            TripleListOutput, method="json_schema"
        )
        response: TripleListOutput = structured_llm.invoke(filled_prompt)

        triples = []
        for item in response.get("triples", []):
            try:
                triples.append(
                    Triple(
                        subject=TripleNode(
                            node_type=item.get("subject_type", "device"),
                            value=item["subject"],
                        ),
                        predicate=item["predicate"],
                        object=TripleNode(
                            node_type=item.get("object_type", "property"),
                            value=item["object"],
                        ),
                    )
                )
            except (KeyError, TypeError):
                pass
        return triples

    def _format_content(self, product_data: dict[str, str]) -> str:
        """Format the section dict into readable text for the prompt."""
        parts = []
        for key, value in product_data.items():
            if value and isinstance(value, str):
                label = key.replace("_", " ").title()
                parts.append(f"[{label}]\n{value}")
        return "\n\n".join(parts)
