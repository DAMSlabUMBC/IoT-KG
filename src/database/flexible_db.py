import os
import glob
import re
import ast
from dotenv import load_dotenv
from arango import ArangoClient
from tqdm import tqdm
import hashlib



load_dotenv()

#CACHE_FILE = "/cache/triple_cache.txt"

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

GRAPH_NAME = os.getenv("GRAPH_NAME", "IoT_KG")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

TRIPLETS_DIR = os.getenv("TRIPLETS_DIR", os.path.join(BASE_DIR, "data", "human_validated_triples"))

CACHE_FILE = os.path.join(BASE_DIR, "cache", "triple_cache.txt")

TRIPLETS_DIR = os.path.abspath(TRIPLETS_DIR)

# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------

def make_edge_key(from_id, to_id, relationship):
    raw = f"{from_id}-{to_id}-{relationship}"
    return hashlib.md5(raw.encode()).hexdigest()

def reset_graph(db, graph_name):
    if db.has_graph(graph_name):
        print(f"Dropping existing graph: {graph_name}")
        db.delete_graph(graph_name, drop_collections=True)
    else:
        print(f"No existing graph found: {graph_name}")

def read_cache():
    triples = []
    with open(CACHE_FILE, "r", encoding="utf-8") as c:
        for line in c:
            line = line.strip()

            if not line:
                continue

            try:
                triples.append(ast.literal_eval(line))
            except Exception as e:
                print(f"Could not parse line:\n{line}\n{e}")
    return triples

def load_triples_to_cache(triples):
    with open(CACHE_FILE, "w", encoding="utf-8") as c:
        for triple in triples:
            c.write(f"{triple}\n")

def get_schema(db):
    graph = db.graph(GRAPH_NAME)

    vertex_collections = graph.vertex_collections()

    edge_definitions = graph.edge_definitions()

    schema = {
        "vertices": list(vertex_collections),
        "edges": []
    }

    for e in edge_definitions:
        schema["edges"].append({
            "name": e["edge_collection"],
            "from": e["from_vertex_collections"],
            "to": e["to_vertex_collections"]
        })

    return schema

def sanitize_key(value: str) -> str:
    """
    Converts arbitrary text into a valid ArangoDB _key
    """
    value = value.strip()
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"[^a-zA-Z0-9_\-]", "_", value)
    return value.lower()


def normalize_collection_name(name: str) -> str:
    """
    Normalize collection names
    """
    return sanitize_key(name)


def load_triplets(filename):
    triplets = []

    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            try:
                triplets.append(ast.literal_eval(line))
            except Exception as e:
                print(f"Could not parse line:\n{line}\n{e}")

    return triplets


# -------------------------------------------------------------------
# GRAPH INITIALIZATION
# -------------------------------------------------------------------

def get_or_create_graph(db, graph_name):

    if db.has_graph(graph_name):
        print(f"Using existing graph: {graph_name}")
        return db.graph(graph_name)

    print(f"Creating graph: {graph_name}")
    return db.create_graph(graph_name)


def get_or_create_vertex_collection(graph, collection_name):

    collection_name = normalize_collection_name(collection_name)

    if graph.has_vertex_collection(collection_name):
        return graph.vertex_collection(collection_name)

    print(f"Creating vertex collection: {collection_name}")
    return graph.create_vertex_collection(collection_name)


def get_or_create_edge_definition(graph, edge_name, from_collections, to_collections):

    edge_name = normalize_collection_name(edge_name)

    if graph.has_edge_definition(edge_name):
        return graph.edge_collection(edge_name)

    print(f"Creating edge definition: {edge_name}")

    return graph.create_edge_definition(edge_collection=edge_name, from_vertex_collections=list(from_collections), to_vertex_collections=list(to_collections))


# -------------------------------------------------------------------
# NODE INSERTION
# -------------------------------------------------------------------

def insert_node(graph, node):

    node_type = normalize_collection_name(node[0])
    node_name = node[1]

    collection = get_or_create_vertex_collection(
        graph,
        node_type
    )

    node_key = sanitize_key(node_name)

    existing = collection.get(node_key)

    if existing:
        return existing["_id"]

    document = {
        "_key": node_key,
        "name": node_name,
        "entity_type": node_type
    }

    meta = collection.insert(document)

    return meta["_id"]


# -------------------------------------------------------------------
# EDGE INSERTION
# -------------------------------------------------------------------

def ensure_edge_definition(graph, relationship, from_type, to_type):

    relationship = normalize_collection_name(relationship)

    if graph.has_edge_definition(relationship):
        return graph.edge_collection(relationship)

    return graph.create_edge_definition(edge_collection=relationship, from_vertex_collections=[from_type], to_vertex_collections=[to_type])


def insert_edge(graph, from_id, to_id, relationship, weight=None, metadata=None):

    relationship = normalize_collection_name(relationship)
    edge_collection = graph.edge_collection(relationship)

    edge_doc = {
        "_key": make_edge_key(from_id, to_id, relationship),
        "_from": from_id,
        "_to": to_id
    }

    if weight is not None:
        # if there is an existing weight, return the average
        if "weight" in edge_doc:
            old_weight = edge_doc["weight"]
            edge_doc["weight"] = (weight + old_weight) / 2
        else:
            edge_doc["weight"] = weight

    if metadata and isinstance(metadata, dict):
        edge_doc.update(metadata)

    try:
        edge_collection.insert(edge_doc)
    except Exception as e:
        if "unique constraint violated" in str(e).lower():
            pass  # duplicate → ignore
        else:
            print(f"Edge insertion failed: {e}")


# -------------------------------------------------------------------
# MAIN KG CONSTRUCTION
# -------------------------------------------------------------------

def create_kg():

    client = ArangoClient(
        hosts=os.getenv("HOST_URL")
    )

    db = client.db(
        "_system",
        username=os.getenv("ARANGO_DB_USERNAME"),
        password=os.getenv("ARANGO_DB_PASSWORD")
    )

    reset_graph(db, GRAPH_NAME)

    graph = get_or_create_graph(db, GRAPH_NAME)

    all_triplets = []

    
    
    try:
        print("Loading triples from cache")
        all_triplets.extend(read_cache())
    except:
        print("No cache to read triples from")

    print(f"Loading triplets from: {TRIPLETS_DIR}")

    for path in glob.glob(os.path.join(TRIPLETS_DIR, "*.txt")):
        all_triplets.extend(load_triplets(path))

    all_triplets = list(set(all_triplets))

    #print(all_triplets)

    print(f"Loaded {len(all_triplets)} unique triplets")

    #exit()

    # ---------------------------------------------------------------
    # PASS 1:
    # Collect schema information dynamically
    # ---------------------------------------------------------------

    edge_schema = {}

    for triplet in all_triplets:

        #triplet = ast.literal_eval(triplet)

        if len(triplet) < 3:
            continue

        source = triplet[0]
        predicate = triplet[1]
        target = triplet[2]

        #print(f"{source} {predicate} {target}")

        source_type = normalize_collection_name(source[0])
        target_type = normalize_collection_name(target[0])
        predicate = normalize_collection_name(predicate)

        try:
            get_or_create_vertex_collection(graph, source_type)
        except:
            print(f"Unable to make vertex collection for {source_type}")
        
        try:
            get_or_create_vertex_collection(graph, target_type)
        except:
            print(f"Unable to make vertex collection for {target_type}")
            

        if predicate not in edge_schema:
            edge_schema[predicate] = {
                "from": set(),
                "to": set()
            }

        edge_schema[predicate]["from"].add(source_type)
        edge_schema[predicate]["to"].add(target_type)

    # ---------------------------------------------------------------
    # CREATE EDGE DEFINITIONS
    # ---------------------------------------------------------------

    for edge_name, schema in edge_schema.items():

        try:

            get_or_create_edge_definition(graph, edge_name, schema["from"], schema["to"])
        except Exception as e:
            print(f"UNABLE TO GET OR CREATE EDGE DEFINITION FOR: {schema['from']} {edge_name} {schema['to']}")

    # ---------------------------------------------------------------
    # PASS 2:
    # Insert nodes and edges
    # ---------------------------------------------------------------

    for triplet in tqdm(all_triplets):

        try:

            source = triplet[0]
            predicate = triplet[1]
            target = triplet[2]

            weight = None
            metadata = {}

            if len(triplet) >= 4:
                weight = triplet[3]

            if len(triplet) >= 5 and isinstance(triplet[4], dict):
                metadata = triplet[4]

            source_type = normalize_collection_name(source[0])
            target_type = normalize_collection_name(target[0])

            ensure_edge_definition(
                graph,
                predicate,
                source_type,
                target_type
            )

            from_id = insert_node(graph, source)
            to_id = insert_node(graph, target)

            insert_edge(
                graph,
                from_id,
                to_id,
                predicate,
                weight,
                metadata
            )
            

        except Exception as e:
            print(f"Failed processing triplet:\n{triplet}\n{e}")

    print("Knowledge graph construction complete.")

    load_triples_to_cache(all_triplets)
    print("Loaded all triples to cache")


# -------------------------------------------------------------------
# ENTRY
# -------------------------------------------------------------------

if __name__ == "__main__":
    create_kg()