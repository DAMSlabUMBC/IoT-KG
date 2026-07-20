from src.database.flexible_db import get_schema
import os
from arango import ArangoClient
import json

if __name__ == "__main__":
    client = ArangoClient(
        hosts=os.getenv("HOST_URL")
    )

    db = client.db(
        "_system",
        username=os.getenv("ARANGO_DB_USERNAME"),
        password=os.getenv("ARANGO_DB_PASSWORD")
    )

    schema = get_schema(db)

    with open("schema.json", "w", encoding="utf-8") as j:
        json.dump(schema, j, indent=4)

    #print(schema)