"""
Prequisites for this file:
We are assuming you have done the following:
- scrape_product_urls_to_disk.py to scrape product urls to disk
- performed entity, classification, and relationshiop analysis on the scraped
product to get triplets in the form of (subject, predicate, object). This should
be stored in a folder data/triplets.

Reads the triplets file, validates each triple (search first, RAG if the search
weight is weak, judge if RAG is not highly confident), and writes
(subject, predicate, object, weight) lines to data/validated_triplets.
"""

from src.types.triple import Triple
from src.validators.search import SearchValidator
from src.validators.rag import RAGValidator
from src.validators.judge import JudgeValidator

import os
import ast
import datetime

INPUT_FILE = "data/triplets/triplets.txt"
OUTPUT_DIR = "data/validated_triplets"


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        triplets = [ast.literal_eval(line.strip()) for line in f if line.strip()]
    print(f"Loaded {len(triplets)} triplets from {INPUT_FILE}")

    search_validator = SearchValidator(headless=False)
    rag_validator = RAGValidator()
    judge_validator = JudgeValidator()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = f"{OUTPUT_DIR}/{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for subject, predicate, obj in triplets:
                triple = Triple.from_tuple((subject, predicate, obj))
                weight = search_validator.validate(triple)

                if weight < 0.75:
                    print(f"Performing second validation method because weight is lower than 0.75: {weight}")
                    rag_result = rag_validator.validate(str((subject, predicate, obj)))
                    weight = 1.0 if rag_result["truthfulness"] else 0.0

                    if rag_result["confidence"] != "High Confidence":
                        print(f"Performing third validation method because RAG confidence is: {rag_result['confidence']}")
                        report = judge_validator.evaluate(str((subject, predicate, obj)))
                        votes = [r["proposal"]["truthfulness"] for r in report["rounds"]]
                        weight = round(sum(votes) / len(votes), 2)

                f.write(f"{(subject, predicate, obj, weight)}\n")
    finally:
        search_validator.close()

    print(f"Validated triplets written to {output_path}")


if __name__ == "__main__":
    main()
