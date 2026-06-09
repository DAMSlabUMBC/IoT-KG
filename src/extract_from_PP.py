from src.analysis import IoTClassification, EntityAnalysis, TriplesAnalysis
import json
import time


if __name__ == "__main__":
    source_name = "Apple"
    url = "https://www.apple.com/legal/privacy/en-ww/"

    # gets cached scraped data from PP
    with open(f"{source_name}_parsed.json", "r", encoding="utf-8") as j:
        config = json.load(j)

    entityAnalysis = EntityAnalysis()
    triplesAnalysis = TriplesAnalysis()

    # iterates through each section
    with open(f"{source_name}_analysis.txt", "w", encoding="utf-8") as f:
        for section in config:
            text = f"{section}: {config[section]}"

            # extracts entities
            entities = entityAnalysis.analyze(text)
        
            print(f"ENTITIES: {entities}")
            if entities:
                triples = triplesAnalysis.analyze(entities, text)
                print(f"TRIPLES: {triples}")
                f.write(f"{section}\nENTITIES: {entities}\nTRIPLES: {triples}\n\n")
            else:
                print("TRIPLES: NO ENTITIES FOUND")