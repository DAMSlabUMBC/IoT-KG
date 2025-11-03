# https://medium.com/data-and-beyond/chains-in-langchain-part-1-040624795f91

from typing_extensions import Annotated, TypedDict

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain.output_parsers import StructuredOutputParser, ResponseSchema

class WeightOutput(TypedDict):
    weight: Annotated[float, 0.0, "The weight of the triple, from 0.0 to 1.0"]
    conclusion: Annotated[str, ..., "The explanation and reasoning for the weight you created"]

class JudgeOutput(TypedDict):
    valid: Annotated[bool, False, "The bool representing if the conclsuion and weight is valid or not"]
    conclusion: Annotated[str, ..., "The explanation and reasoning for the bool you provided for the statement regarding the conclusion and weight"]

class JudgeValidator:
    def __init__(self):
        self.llm_gemma = ChatOllama(model="gemma3:4b")
        self.llm_qwen = ChatOllama(model="qwen3:8b")
        self.llm_llama = ChatOllama(model="llama3.1:8b")
        self.llm_mistral = ChatOllama(model="mistral:7b")
        
        self.weigh_prompt = PromptTemplate.from_template(
            """
            Evaluate the truth of the following triple.
            Assign a confidence weight between 0.0 and 1.0, where:

            - 0.0 = absolutely false based on the evidence
            - 1.0 = absolutely true based on the evidence
            - Any value in between reflects partial or uncertain support.

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
            Evaluate the truth of the weight and conclusion drawn from the triple:
            weight and conclusion: {context}
            triple: {triple}

            Determine whether the weight and consluion provided is valid or not. Explain why.
             Output MUST be a single JSON object and nothing else.
            Do NOT use Markdown, code fences, backticks, comments, the word json, or prose in your final output.
            The FIRST character of your reply must be "{{" and the LAST must be "}}".
            If evidence is insufficient, set "valid" to false and explain briefly in "conclusion".
            The output should include a conclusion and valid.

            Example Output:

            {{
                "conclusion": "<brief reasoning>",
                "valid": "<true or false, is the weight and conclusion accurate to the triple ">
            }}

            Answer:
            """
        )
    
    def _build_sequence_chain():
        print("build")

    def parallel_chain():
        print("parallel")
    
    def sequence_chain(self):

        triple = "(('device','EchoDot'),'manufacturedBy',('manufacturer','Google'))"

        prompt = self.weigh_prompt.format(triple=triple)
        structured_llm = self.llm_gemma.with_structured_output(WeightOutput, method="json_schema")
        result = structured_llm.invoke(prompt)

        prompt1 = self.judge_prompt.format(context=result, triple=triple)
        structured_llm1 = self.llm_llama.with_structured_output(JudgeOutput, method="json_schema")
        result1 = structured_llm1.invoke(prompt1)

        prompt2 = self.judge_prompt.format(context=result, triple=triple)
        structured_llm2 = self.llm_mistral.with_structured_output(JudgeOutput, method="json_schema")
        result2 = structured_llm2.invoke(prompt2)

        prompt3 = self.judge_prompt.format(context=result, triple=triple)
        structured_llm3 = self.llm_qwen.with_structured_output(JudgeOutput, method="json_schema")
        result3 = structured_llm3.invoke(prompt3)

        prompt4 = self.judge_prompt.format(context=result, triple=triple)
        structured_llm4 = self.llm_gemma.with_structured_output(JudgeOutput, method="json_schema")
        result4 = structured_llm4.invoke(prompt4)

        print(result)
        print(result4)
        print(result1)
        print(result2)
        print(result3)

