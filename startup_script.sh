#!/bin/bash

# moves to database directory
cd src/database

echo "ENVIRONMENT VARIABLES"
cat .env

# loads triples to the KG
echo "📦 Loading KG..."
python flexible_db.py

# runs the server for mcp tools
echo "🧠 Starting MCPO..."
mcpo --port 9000 -- python mcp_tools.py

echo "❌ THIS LINE WON'T RUN IF MCPO IS LONG-RUNNING"

