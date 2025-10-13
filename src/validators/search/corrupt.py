import random
from typing import List
from src.types.triple import Triple, TripleNode
from src.validators.search.format import QueryFormatter


############## TODO: move db logic out ##############
import os
from dotenv import load_dotenv
from arango import ArangoClient

load_dotenv()
client = ArangoClient(hosts=os.getenv("HOST_URL"))
db = client.db(
    "_system",
    username=os.getenv("ARANGO_DB_USERNAME"),
    password=os.getenv("ARANGO_DB_PASSWORD"),
)
graph = db.graph("IoT_KG")
###################################################

class TripleCorruptor:

    def __init__(self, query_formatter: QueryFormatter):
        self.query_formatter = query_formatter

    # TODO: how can we corrupt a triple with "best effort" and not randomly
    def generate_corrupted_queries(self, triple: Triple, max_corruptions=3):
        corrupt_subject = random.random() < 0.5

        if corrupt_subject:
            vertex_col = triple.subject.node_type
        else:
            vertex_col = triple.object.node_type
        
        top_vertices = self._top_by_edge(edge_col=triple.predicate, vertex_col=vertex_col, direction="INBOUND", limit=3)

        all_queries = []
        corruption_count = 0

        for vertex_doc in top_vertices:
            if vertex_doc["name"] in (triple.subject.value, triple.object.value):
                continue

            if corruption_count >= max_corruptions:
                break;

            corrupted_triple = self._corrupt_triple(
                triple,
                vertex_doc["name"],
                corrupt_subject
            )

            queries = self.query_formatter.format_triple(corrupted_triple)
            all_queries.extend(queries)
            corruption_count += 1

        return all_queries

    def _corrupt_triple(self, triple: Triple, new_value: str, corrupt_subject: bool) -> Triple:
        if corrupt_subject:
            return Triple(
                subject=TripleNode(triple.subject.node_type, new_value),
                predicate=triple.predicate,
                object=triple.object
            )
        else:
            return Triple(
                subject=triple.subject,
                predicate=triple.predicate,
                object=TripleNode(triple.object.node_type, new_value)
            )

    # TODO: move db logic out
    # TODO: Test to see what happens when we try to findind something that does not exist
    def _top_by_edge(self, edge_col: str, vertex_col: str, direction: str = "INBOUND", limit: int = 3):
        print("RUNNING TOP_BY_EDGE")
        query = f"""
            FOR v IN `{vertex_col}`
            LET edgeCount = LENGTH(
                FOR w IN 1..1 {direction} v `{edge_col}`
                RETURN 1
            )
            SORT edgeCount DESC
            LIMIT @limit
            RETURN {{ name: v.name, count: edgeCount }}
        """
        return list(db.aql.execute(query, bind_vars={"limit": limit}))