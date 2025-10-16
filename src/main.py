from src.validators.search import Triple, TripleNode, TripleValidator

# (('device','EchoDot'),'compatibleWith',('application','Alexa')) 0.5 https://www.amazon.com/Honeywell-Programmable-Thermostat-RTH2300B1038-E1/dp/B00CTSY6G0 2025-04-10 19:27:10
# (('device','EchoDot'),'manufacturedBy',('manufacturer','Amazon')) 0.5 https://www.amazon.com/Honeywell-Programmable-Thermostat-RTH2300B1038-E1/dp/B00CTSY6G0 2025-04-10 19:27:10

def main():
    triple = Triple(
        subject=TripleNode("device", "echo dot"),
        predicate="manufacturedBy",
        object=TripleNode("manufacturer", "Google")
    )
    
    validator = TripleValidator(headless=False)
    is_valid = validator.validate(triple)

    print(f"\n Triple Weight: {is_valid}")
    

if __name__ =="__main__":
    main()