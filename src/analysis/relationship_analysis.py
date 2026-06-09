from typing_extensions import List, TypedDict

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

class Triple(TypedDict):
    subject: str
    predicate: str
    object: str


class TriplesAnalysis:
    def __init__(self):
        self.llm = ChatOllama(model="gemma3:4b")
        self.prompt = PromptTemplate.from_template(
            """
                You are an expert at identifying relationships between IoT-related entities.
                You are given:
                1) A JSON list of entities: {entities}
                2) The text they were extracted from: {text}

                Task: produce a list of triples (subject, predicate, object)
                that describe valid relationships between the entities. Output as JSON list.

                Example:
                Entities: ["Amazon", "Alexa", "Amazon Echo Dot", "Speaker", "voice assistant", "smart home"]
                Text: "Amazon Echo Dot is a smart speaker that works with Alexa for smart home automation."

                Output:
                [
                    {"subject": "Amazon Echo Dot", "predicate": "works_with", "object": "Alexa"},
                    {"subject": "Amazon Echo Dot", "predicate": "is_a", "object": "Speaker"},
                    {"subject": "Amazon Echo Dot", "predicate": "controls", "object": "smart home"}
                ]

                Entities: {entities}
                Text: {text}
            """
        )
    
    def analyze(self, entities, text):
        prompt = self.prompt.format(entities=entities, text=text)
        structured_llm = self.llm.with_structured_output(List[Triple], method="json_schema")
        response = structured_llm.invoke(prompt)
        return response