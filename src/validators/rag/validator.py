# https://python.langchain.com/docs/tutorials/rag/
# https://docs.crawl4ai.com/core/crawler-result/#2-html-variants

from typing import Literal

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
from langgraph.graph import START, StateGraph
from typing_extensions import Annotated, List, TypedDict

triple = 'alexa privacy policy location tracking'
search = DuckDuckGoSearchResults(output_format="list", max_results=5)
result = search.invoke(triple)

print("Search results: ", result)

docs = []
browser_config = BrowserConfig()
run_config = CrawlerRunConfig()

async def scrape():
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for item in result:
            text = await crawler.arun(
                url=item["link"],
                config=run_config
            )
            docs.append(Document(page_content=text.markdown))

asyncio.run(scrape())

llm = ChatOllama(model="gemma3:27b")

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
all_splits = text_splitter.split_documents(docs)

embeddings = HuggingFaceEmbeddings(
     model_name = "sentence-transformers/all-mpnet-base-v2",
     model_kwargs = {'device': 'cpu'},
     encode_kwargs = {'normalize_embeddings': False}
)

# Index chunks
vector_store = InMemoryVectorStore(embeddings)
_ = vector_store.add_documents(all_splits)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a fact-checking assistant."),
    ("human", 
     "Use the provided context to evaluate the truth of the following triple.\n"
     "Assign a confidence weight between 0.0 and 1.0, where:\n"
     "- 0.0 = absolutely false based on the evidence\n"
     "- 1.0 = absolutely true based on the evidence\n"
     "- Any value in between reflects partial or uncertain support.\n\n"
     "If the context does not provide enough information to make a judgment, output a weight of 0.0 and explain that there is insufficient evidence.\n\n"
     "Return your answer in the following format:\n\n"
     "Conclusion:\n"
     "- Weight: <value between 0.0 and 1.0>\n"
     "- Explanation: <brief reasoning>\n\n"
     "Sources:\n"
     "- <list of specific URLs, titles, or identifiers from the provided context that support your conclusion>\n\n"
     "Triple: {triple}\n\n"
     "Context: {context}\n\n"
     "Answer:")
])

# Define schema for search
class Search(TypedDict):
    """Search query."""

    query: Annotated[str, ..., "Search query to run."]
    section: Annotated[
        Literal["beginning", "middle", "end"],
        ...,
        "Section to query.",
    ]

# Define state for application
class State(TypedDict):
    triple: str
    query: Search
    context: List[Document]
    answer: str


def analyze_query(state: State):
    structured_llm = llm.with_structured_output(Search)
    query = structured_llm.invoke(state["triple"])
    return {"query": query}


def retrieve(state: State):
    query = state["query"]
    retrieved_docs = vector_store.similarity_search(query["query"])
    return {"context": retrieved_docs}


def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = prompt.invoke({"triple": state["triple"], "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content}


graph_builder = StateGraph(State).add_sequence([analyze_query, retrieve, generate])
graph_builder.add_edge(START, "analyze_query")
graph = graph_builder.compile()

out = graph.invoke({"triple": triple})
print(out["answer"])