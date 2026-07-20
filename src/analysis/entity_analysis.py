from typing_extensions import List, TypedDict

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

class Entities(TypedDict):
    entities: List[str]


class EntityAnalysis:
    def __init__(self):
        self.llm = ChatOllama(model="gemma3:27b")
        # TODO: Decide if we need to define an ontology here in this prompt
        self.prompt = PromptTemplate.from_template(
            """
                You are an expert at identify and classifying Internet of Things (IoT) related
                entities. You will be given a JSON and your job is to extract IoT-related 
                entities from it.

                Example:

                Input:
                {{
                    "product_name": "Amazon Echo Dot, With Alexa, Charcoal.",
                    "manufacturer": "Amazon",
                    "about_item": "Smart speaker with Alexa voice control for smart home automation."
                }}

                Output:
                ["Amazon", "Alexa", "Amazon Echo Dot", "Speaker", "voice assistant", "smart home"]

                Given JSON: {content}
            """
        )
    
    def analyze(self, content):
        prompt = self.prompt.format(content=content)
        structured_llm = self.llm.with_structured_output(Entities, method="json_schema")
        response = structured_llm.invoke(prompt)
        return response
