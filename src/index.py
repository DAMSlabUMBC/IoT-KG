# This is the file to execute for analysis

"""
Reads scraped product records from data/html_dumps one file at a time,
classifies each product as IoT or not, extracts IoT entities from the IoT
products, forms relationship triples from those entities, and writes the
triples to data/triplets.

Each output line is a JSON object containing the triple plus the html dump
record it was made from (which carries the product URL) as metadata.
"""

import os
import json
import glob
import datetime

from src.analysis import IoTClassification, EntityAnalysis, RelationshipAnalysis

HTML_DUMPS_DIR = "data/html_dumps"
OUTPUT_DIR = "data/triplets"


def load_products(path):
    """Load the product records from a single JSONL dump file."""
    products = []
    with open(path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                products.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Skipping malformed line {line_number} in {path}: {e}")
    return products


def main():
    dump_files = glob.glob(os.path.join(HTML_DUMPS_DIR, "**", "*.jsonl"), recursive=True)
    print(f"Found {len(dump_files)} dump files in {HTML_DUMPS_DIR}")

    iot_classification = IoTClassification()
    entity_analysis = EntityAnalysis()
    relationship_analysis = RelationshipAnalysis()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = f"{OUTPUT_DIR}/{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jsonl"

    written = 0

    with open(output_path, "w", encoding="utf-8") as out:
        for dump_file in dump_files[:1]:
            print(f"Processing {dump_file}")

            for product in load_products(dump_file):
                title = product.get("title", "").strip()
                if not title:
                    continue

                print("Product Name: ", title)

                try:
                    classification = iot_classification.classify(title)
                    print("Classification: ", classification)
                    if classification.strip() != "IOT":
                        continue

                    # Keep the prompt focused on the descriptive fields; the raw
                    # Amazon URLs are thousands of characters of tracking tokens.
                    entities = entity_analysis.analyze({
                        "product_name": title,
                        "about_item": product.get("features", ""),
                    })
                    print("Entities: ", entities)
                    if not entities or not entities.get("entities"):
                        continue

                    relationships = relationship_analysis.analyze(entities)
                    print("Relationships: ", relationships)
                    if not relationships or not relationships.get("triples"):
                        continue
                except Exception as e:
                    print(f"Analysis failed for '{title}': {e}")
                    continue

                for triple in relationships["triples"]:
                    # The model does not always respect the schema, so treat
                    # each triple as untrusted and skip malformed ones.
                    try:
                        record = {
                            "triple": [
                                [triple["subject"]["type"], triple["subject"]["value"]],
                                triple["predicate"],
                                [triple["object"]["type"], triple["object"]["value"]],
                            ],
                            "metadata": product,
                        }
                    except (KeyError, TypeError) as e:
                        print(f"Skipping malformed triple {triple}: {e}")
                        continue
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    written += 1

    print(f"Wrote {written} triples to {output_path}")


if __name__ == "__main__":
    main()