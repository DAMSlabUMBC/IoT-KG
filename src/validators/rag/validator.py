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
from langchain_core.prompts import PromptTemplate

# TODO: We can move this into types
class StructuredOutput(TypedDict):
    truthfulness: Annotated[bool, ..., "The truthfulness of a triple is determined by its factual accuracy, supported by reliable data or external evidence"]
    confidence: Annotated[str, ..., "Your level of certainty based on the strength and consistency of the evidence"]
    reasoning: Annotated[str, ..., "Concise explanation of why the triple is true or false, including factual evidence"]
    sources: Annotated[str, ..., "List of URLs or references used to support your conclusion"]
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
        self.prompt = PromptTemplate.from_template(
            """
            You are a Knowledge Graph Engineer specialized in evaluating the truthfulness of a triple.
            The truthfulness of a triple is determined by its factual accuracy, supported by reliable data or external evidence.

            Your task is to determine whether the given triple is true or not.

            You must provide your response strictly in the following JSON format:

            {{
                "truthfulness": true | false,
                "confidence": "Low Confidence" | "Medium Confidence" | "High Confidence",
                "reasoning": "Concise explanation of why the triple is true or false, including factual evidence.",
                "sources": ["List of URLs or references used to support your conclusion"]
            }}

            Definitions:
            - Truthfulness: Whether the triple aligns with factual, verifiable information.
            - Confidence: Your level of certainty based on the strength and consistency of the evidence.

            Example:
            Input: (('device','EchoDot'),'manufacturedBy',('manufacturer','Amazon'))

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

            Context: {context}

            Answer:
            """
        )

    def validate(self, triple: str) -> float:
        """Validate a triple by comparing query to triple search results"""

        urls = self._search_urls(triple)
        docs = asyncio.run(self._scrape(urls))

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        all_splits = text_splitter.split_documents(docs)
        vector_store = InMemoryVectorStore(self.embeddings)
        vector_store.add_documents(all_splits)

        retrieved_docs = vector_store.similarity_search(triple)
        context =  "\n\n".join(doc.page_content for doc in retrieved_docs)
        prompt = self.prompt.format(triple=triple, context=context)
        structured_llm = self.llm.with_structured_output(StructuredOutput, method="json_schema")
        response = structured_llm.invoke(prompt)

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
