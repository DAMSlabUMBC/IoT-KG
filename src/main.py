from src.types.triple import Triple, TripleNode 
from src.validators.search import SearchValidator
from src.validators.rag import RAGValidator

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
    weight = 0.1

    print(f"\n Triple Weight: {weight}")

    if(weight < .75):
        print(f"Performing second validation method because weight is lower than 0.5: {weight}")
        ragValidator = RAGValidator() 
        ragResult = ragValidator.validate(triple="alexa privacy policy location tracking")
        print("RAG Result from main: ", ragResult)
        weight = ragResult["weight"]
        print("RAG weight from main: ", weight)
if __name__ =="__main__":
    main()