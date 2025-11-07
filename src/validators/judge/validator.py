# https://medium.com/data-and-beyond/chains-in-langchain-part-1-040624795f91

from typing_extensions import Annotated, TypedDict, Dict, List

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel

class ProposeOutput(TypedDict):
    truthfulness: Annotated[bool, ..., "The truthfulness of a triple is determined by its factual accuracy, supported by reliable data or external evidence"]

class JudgeOutput(TypedDict):
    truthfulness: Annotated[bool, ..., "The truthfulness of a triple is determined by its factual accuracy, supported by reliable data or external evidence"]
    confidence: Annotated[str, ..., "Your level of certainty based on the strength and consistency of the evidence"]
    reasoning: Annotated[str, ..., "Concise explanation of why the triple is true or false, including factual evidence"]

class RoundReport(TypedDict):
    proposer: str
    proposal: ProposeOutput
    judges: Dict[str, JudgeOutput]

class FinalReport(TypedDict):
    triple: str
    rounds: List[RoundReport]
    
class JudgeValidator:
    def __init__(self):
        self.models: Dict[str, ChatOllama] = {
            "gemma3:4b": ChatOllama(model="gemma3:4b"),
            "qwen3:8b": ChatOllama(model="qwen3:8b"),
            "llama3.1:8b": ChatOllama(model="llama3.1:8b"),
            "mistral:7b": ChatOllama(model="mistral:7b"),
        }
        
        self.propose_prompt = PromptTemplate.from_template(
            """
            You are a Knowledge Graph Engineer specialized in evaluating the truthfulness of a triple.
            The truthfulness of a triple is determined by its factual accuracy, supported by reliable data or external evidence.

            Your task is to determine whether the given triple is true or not.

            You must provide your response strictly in the following JSON format:

            {{
                "truthfulness": true | false,
            }}

            Example:
            Input: (('device','EchoDot'),'manufacturedBy',('manufacturer','Amazon'))

            Output:
            {{
                "truthfulness": true,

            }}

            Triple: {triple}

            Answer:
            """
        )

        self.judge_prompt = PromptTemplate.from_template(
            """

            You are a Knowledge Graph Engineer specialized in evaluating the truthfulness of a triple.
            The truthfulness of a triple is determined by its factual accuracy, supported by reliable data or external evidence.

            Your task is to determine whether your peer evaluated the triple correctly.
            You are given the original triple and your peers answer.

            You must provide your response strictly in the following JSON format:

            {{
                "truthfulness": true | false,
                "confidence": "Low Confidence" | "Medium Confidence" | "High Confidence",
                "reasoning": "Concise explanation of why the triple is true or false, including factual evidence.",
            }}

            Definitions:
            - Truthfulness: Whether the triple aligns with factual, verifiable information.
            - Confidence: Your level of certainty based on the strength and consistency of the evidence.

            Example:
            Input: 
            Triple: (('device','EchoDot'),'manufacturedBy',('manufacturer','Amazon'))
            Peer truthfulness answer: false

            Output:
            {{
                "truthfulness": true,
                "confidence": "High Confidence",
                "reasoning": "The Echo Dot product listings and manufacturer pages confirm Amazon as the manufacturer.",
                "sources": [
                    "https://www.amazon.com/echo-dot/s?k=echo+dot",
                    "https://www.dell.com/en-us/shop/amazon-echo-dot-5th-generation-bluetooth-smart-speaker-alexa-supported-charcoal/apd/ac313554/home-automation"
                ]
            }}

            Triple: {triple}

            Peer Truthfulness answer: {context}

            Answer:
            """
        )
    
    def _propose(self, triple: str, model_name: str) -> ProposeOutput:
        prompt = self.weigh_prompt.format(triple=triple)
        structured_llm = self.models[model_name].with_structured_output(ProposeOutput, method="json_schema")
        return structured_llm.invoke(prompt)

    def _judge(self, triple: str, context: ProposeOutput, model_name: str) -> JudgeOutput:
        prompt = self.judge_prompt.format(context=context, triple=triple)
        structured_llm = self.models[model_name].with_structured_output(JudgeOutput, method="json_schema")
        return structured_llm.invoke(prompt)
    
    def _parallel_judgments(self, triple: str, context: ProposeOutput, judge_names: List[str]) -> Dict[str, JudgeOutput]:
        chains = {}

        for name in judge_names:
            chains[name] = self.judge_prompt | self.models[name].with_structured_output(JudgeOutput, method="json_schema")
        
        parallel = RunnableParallel(chains)
        results: Dict[str, JudgeOutput] = parallel.invoke({"context": context, "triple": triple})

        return results
    
    def evaluate(self, triple: str) -> FinalReport:
        model_names = list(self.models.keys())
        rounds: List[RoundReport] = []

        for proposer in model_names:
            proposal = self._propose(triple, proposer)
            judgments = self._parallel_judgments(triple, proposal, model_names)
            rounds.append(
                RoundReport(
                    proposer=proposer,
                    proposal=proposal,
                    judges=judgments,
                )
            )
        return FinalReport(triple=triple, rounds=rounds)