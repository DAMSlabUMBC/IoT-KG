"""
Prequisites for this file:
We are assuming you have done the following:
- scrape_product_urls_to_disk.py to scrape product urls to disk
- performed entity, classification, and relationshiop analysis on the scraped
product to get triplets in the form of (subject, predicate, object). This should
be stored in a folder data/triplets.

Reads the triplets JSONL produced by src/index.py, validates each triple
(search first, RAG if the search weight is weak, judge if RAG is not highly
confident), and writes each record back out to data/validated_triplets with a
"weight" field added, preserving the triple's metadata (source url, html dump).
"""

from src.types.triple import Triple
from src.validators.search import SearchValidator
from src.validators.rag import RAGValidator
from src.validators.judge import JudgeValidator

import os
import json
import datetime

INPUT_FILE = "data/triplets/test.jsonl"
OUTPUT_DIR = "data/validated_triplets"


def main():
    records = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Skipping malformed line {line_number}: {e}")
    print(f"Loaded {len(records)} triplets from {INPUT_FILE}")

    search_validator = SearchValidator(headless=False)
    rag_validator = RAGValidator()
    judge_validator = JudgeValidator()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = f"{OUTPUT_DIR}/{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jsonl"

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for record in records:
                # One bad triple (dead page, rate limit, malformed LLM output)
                # must not abort the rest of a multi-hour run.
                try:
                    subject, predicate, obj = record["triple"]
                    subject, obj = tuple(subject), tuple(obj)

                    triple = Triple.from_tuple((subject, predicate, obj))
                    validation_method = "search"
                    weight = search_validator.validate(triple)

                    if weight < 0.75:
                        print(f"Performing second validation method because weight is lower than 0.75: {weight}")
                        validation_method = "rag"
                        rag_result = rag_validator.validate(str((subject, predicate, obj)))
                        weight = 1.0 if rag_result["truthfulness"] else 0.0

                        if rag_result["confidence"] != "High Confidence":
                            print(f"Performing third validation method because RAG confidence is: {rag_result['confidence']}")
                            validation_method = "judge"
                            report = judge_validator.evaluate(str((subject, predicate, obj)))
                            votes = [r["proposal"]["truthfulness"] for r in report["rounds"]]
                            weight = round(sum(votes) / len(votes), 2)
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    print(f"Validation failed for {record.get('triple')}: {e}")
                    continue

                record["weight"] = weight
                record.setdefault("metadata", {})["validation_method"] = validation_method
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    finally:
        search_validator.close()

    print(f"Validated triplets written to {output_path}")


if __name__ == "__main__":
    main()
