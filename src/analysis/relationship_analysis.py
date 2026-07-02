from typing_extensions import TypedDict, List

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

class TripleNode(TypedDict):
    type: str
    value: str

class Triple(TypedDict):
    subject: TripleNode
    predicate: str
    object: TripleNode

class TriplesResponse(TypedDict):
    triples: List[Triple]
    
class RelationshipAnalysis:

    def __init__(self):
        self.llm = ChatOllama(model="gemma3:4b")
        self.prompt = PromptTemplate.from_template(
            """
            You are a data engineer specialized in constructing knowledge graphs. Given a set of extracted entities from an e-commerce 
            website generate triplets in the format:

            What is an entity
            What is a triple
            what is a type
            what is a relationshiop


            [(('type1', 'entity1'), 'relationship', ('type2', 'entity2')), ...]

            Strict Rules:
            - **Output only the list of triplets.** 
            - **Do not include explanations, summaries, or extra text.** 
            - **Do not label or describe the output.** 
            - **If no valid triplets exist, return [] exactly.**

            Entity Types:
            - These are examples only — extract more types as needed:
            device, manufacturer, application, process, sensor, category, etc.

            Relationships:
            These are examples only — generate more as needed:
            developedBy, manufacturedBy, compatibleWith, hasSensor, performs, etc.

            Triplet Schema:
            Each triplet must follow this schema:
            (('type1', 'entity1'), 'relationship', ('type2', 'entity2'))
            Triplets may involve both known and new entity types or relations, as long as they are semantically valid.

            Example Expected Output:
            [
            (('device', 'Govee Smart Light Bulbs'), 'manufacturedBy', ('manufacturer', 'Govee')),
            (('device', 'Govee Smart Light Bulbs'), 'compatibleWith', ('application', 'Alexa')),
            (('device', 'Govee Smart Light Bulbs'), 'isCategory', ('category', 'Smart Lighting')),
            (('device', 'Govee Smart Light Bulbs'), 'hasSensor', ('sensor', 'WiFi')),
            (('device', 'Govee Smart Light Bulbs'), 'includesFeature', ('feature', 'Color Control')),
            (('device', 'Govee Smart Light Bulbs'), 'supportsProtocol', ('protocol', 'Zigbee'))
            ]

            If no valid triplets exist, return: []

            Triples:
            {content}
            """
        )
    
    def analyze(self, content):
        prompt = self.prompt.format(content=content)
        structured_llm = self.llm.with_structured_output(TriplesResponse, method="json_schema")
        response: TriplesResponse = structured_llm.invoke(prompt)
        return response