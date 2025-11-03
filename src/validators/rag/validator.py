# https://python.langchain.com/docs/tutorials/rag/
# https://docs.crawl4ai.com/core/crawler-result/#2-html-variants
# Structured llm output: https://python.langchain.com/docs/how_to/structured_output/

from typing import List
from typing_extensions import Annotated, TypedDict

import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate

# TODO: We can move this into types
class StructuredOutput(TypedDict):
    weight: Annotated[float, 0.0, "The weight of the triple, from 0.0 to 1.0"]
    conclusion: Annotated[str, ..., "The explanation and reasoning for the weight you created"]
    sources: Annotated[str, ..., "specific URLs from the provided context that support your conclusion"]
class RAGValidator:

    def __init__(self):
        print("Initialize any objects")
        self.llm = ChatOllama(model="gemma3:27b")
        self.search = DuckDuckGoSearchResults(output_format="list", max_results=5)
        self.embeddings = HuggingFaceEmbeddings(
            model_name = "sentence-transformers/all-mpnet-base-v2",
            model_kwargs = {'device': 'cpu'},
            encode_kwargs = {'normalize_embeddings': False}
        )
        self.browser_config = BrowserConfig()
        self.run_config = CrawlerRunConfig()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a fact-checking assistant."),
            ("human", 
            """
            Use the provided context to evaluate the truth of the following triple.
            Assign a confidence weight between 0.0 and 1.0, where:

            - 0.0 = absolutely false based on the evidence
            - 1.0 = absolutely true based on the evidence
            - Any value in between reflects partial or uncertain support.

            If the context does not provide enough information to make a judgment,
            output a weight of 0.0 and explain that there is insufficient evidence.

            Output MUST be a single JSON object and nothing else.
            Do NOT use Markdown, code fences, backticks, comments, the word json, or prose in your final output.
            The FIRST character of your reply must be "{{" and the LAST must be "}}".
            If evidence is insufficient, set "weight" to 0.0 and explain briefly in "conclusion".
            The output should include a conclusion, weight, and sources.

            Example Output:

            {{
                "conclusion": "<brief reasoning>",
                "weight": <value between 0.0 and 1.0>,
                "sources": [
                    "<specific URLs, titles, or identifiers from the provided context that support your conclusion>"
                ]
            }}

            Triple: {triple}

            Context: {context}

            Answer:
            """)
        ]) # TODO: Make this prompt cleaner since we have typed json output now

    def validate(self, triple: str) -> float:
        """Validate a triple by comparing query to triple search results"""

        urls = self._search_urls(triple)
        docs = asyncio.run(self._scrape(urls))

        # TODO: We can write a fast fail for zero docs, but the return should not be an int but rather a StructuredOutput
        # if not docs:
        #     return 0

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        all_splits = text_splitter.split_documents(docs)
        vector_store = InMemoryVectorStore(self.embeddings)
        vector_store.add_documents(all_splits)

        retrieved_docs = vector_store.similarity_search(triple)
        context_text =  "\n\n".join(doc.page_content for doc in retrieved_docs)
        messages = self.prompt.invoke({"triple": triple, "context": context_text})
        structured_llm = self.llm.with_structured_output(StructuredOutput, method="json_schema")
        response = structured_llm.invoke(messages)

        print("Response: ", response)
        return response

    def _search_urls(self, triple: str) -> List[str]:
        return self.search.invoke(triple)
    
    async def _scrape(self, urls: List[str]) -> List[Document]:

        docs: List[Document] = []

        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            for url in urls:
                text = await crawler.arun(
                    url=url["link"],
                    config=self.run_config
                )
                docs.append(Document(page_content=text.markdown, metadata={"source": url}))

        return docs
