# https://medium.com/data-and-beyond/chains-in-langchain-part-1-040624795f91

from typing_extensions import Annotated, TypedDict, Dict, List
from statistics import mean

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel

class WeightOutput(TypedDict):
    weight: Annotated[float, 0.0, "The weight of the triple, from 0.0 to 1.0"]
    conclusion: Annotated[str, ..., "The explanation and reasoning for the weight you created"]

class JudgeOutput(TypedDict):
    valid: Annotated[bool, False, "The bool representing if the conclsuion and weight is valid or not"]
    conclusion: Annotated[str, ..., "The explanation and reasoning for the bool you provided for the statement regarding the conclusion and weight"]

class RoundReport(TypedDict):
    proposer: str
    proposal: WeightOutput
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
        
        self.weigh_prompt = PromptTemplate.from_template(
            """
            Evaluate how true the following triple is.
            Assign a truth weight between 0.0 and 1.0, where:

            - 0.0 = completely false
            - 1.0 = completely true
            - Values in between reflect partial truth or uncertainty

            This weight must measure the truth of the triple.

            Output MUST be a single JSON object and nothing else.
            Do NOT use Markdown, code fences, backticks, comments, the word json, or prose in your final output.
            The FIRST character of your reply must be "{{" and the LAST must be "}}".
            If evidence is insufficient, set "weight" to 0.0 and explain briefly in "conclusion".
            The output should include a conclusion and weight.

            Example Output:

            {{
                "conclusion": "<brief reasoning>",
                "weight": <value between 0.0 and 1.0>,
            }}

            Triple: {triple}

            Answer:
            """
        )

        self.judge_prompt = PromptTemplate.from_template(
            """
            Evaluate whether the weight and conclusion proposed correctly represents how true the triple is.

            weight and conclusion: {context}
            triple: {triple}

            If the triple is false but the weight is high, mark it invalid.
            If the triple is true but the weight is low, mark it invalid.

            Output MUST be a single JSON object and nothing else.
            Do NOT use Markdown, code fences, backticks, comments, the word json, or prose in your final output.
            The FIRST character of your reply must be "{{" and the LAST must be "}}".
            If evidence is insufficient, set "valid" to false and explain briefly in "conclusion".
            The output should include a conclusion and valid.

            Example Output:

            {{
                "conclusion": "<brief reasoning for determining valid or invalid>",
                "valid": "<true or false, is the weight and conclusion accurate to the triple ">
            }}

            Answer:
            """
        )
    
    def _propose(self, triple: str, model_name: str) -> WeightOutput:
        prompt = self.weigh_prompt.format(triple=triple)
        structured_llm = self.models[model_name].with_structured_output(WeightOutput, method="json_schema")
        return structured_llm.invoke(prompt)

    def _judge(self, triple: str, context: WeightOutput, model_name: str) -> JudgeOutput:
        prompt = self.judge_prompt.format(context=context, triple=triple)
        structured_llm = self.models[model_name].with_structured_output(JudgeOutput, method="json_schema")
        return structured_llm.invoke(prompt)
    
    def _parallel_judgments(self, triple: str, context: WeightOutput, judge_names: List[str]) -> Dict[str, JudgeOutput]:
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