from src.types.triple import Triple, TripleNode 
from src.validators.search import SearchValidator
from src.validators.rag import RAGValidator
from src.validators.judge import JudgeValidator

import os
import json 
import datetime

# (('device','EchoDot'),'compatibleWith',('application','Alexa')) 0.5 https://www.amazon.com/Honeywell-Programmable-Thermostat-RTH2300B1038-E1/dp/B00CTSY6G0 2025-04-10 19:27:10
# (('device','EchoDot'),'manufacturedBy',('manufacturer','Amazon')) 0.5 https://www.amazon.com/Honeywell-Programmable-Thermostat-RTH2300B1038-E1/dp/B00CTSY6G0 2025-04-10 19:27:10

def main():
    triple = Triple(
        subject=TripleNode("device", "echo dot"),
        predicate="manufacturedBy",
        object=TripleNode("manufacturer", "Google")
    )
    
    # searchValidator = SearchValidator(headless=False)
    # weight = searchValidator.validate(triple)
    # weight = 0.1

    # print(f"\n Triple Weight: {weight}")

    # if(weight < .75):
    #     print(f"Performing second validation method because weight is lower than 0.5: {weight}")
    #     ragValidator = RAGValidator() 
    #     ragResult = ragValidator.validate(triple="alexa privacy policy location tracking")
    #     print("RAG Result from main: ", ragResult)
    #     weight = ragResult["weight"]
    #     print("RAG weight from main: ", weight)

    jv = JudgeValidator()
    result = jv.evaluate("echo dot by google")

    output_dir = f"test"
    os.makedirs(output_dir, exist_ok=True)

    with open(f"{output_dir}/{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(result, indent=2))

if __name__ =="__main__":
    main()