from arango import ArangoClient, AQLQueryKillError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_compatible_devices(application):

	# Initialize the ArangoDB client.
	client = ArangoClient(hosts=os.getenv("HOST_URL"))

  	# connect to IoT-KG database as root user
	db = client.db("_system", username=os.getenv('ARANGO_DB_USERNAME'), password=os.getenv('ARANGO_DB_PASSWORD'))

  	# returns all devices compatible with a given application
	application_id = f"application/{application}"

	# Execute the query
	cursor = db.aql.execute(
		"""
		FOR edge IN compatibleWith
			FILTER edge._to == @appKey
			FOR node IN device
				FILTER node._id == edge._from
				RETURN node
		""",
		bind_vars={'appKey': application_id}
	)

	# Iterate through the result cursor
	device_keys = [doc['_key'] for doc in cursor]

	return device_keys

def get_collected_datatypes(application):
	#print("calling application -> data")

	# Initialize the ArangoDB client.
	client = ArangoClient(hosts=os.getenv("HOST_URL"))

	# connect to IoT-KG database as root user
	db = client.db("_system", username=os.getenv('ARANGO_DB_USERNAME'), password=os.getenv('ARANGO_DB_PASSWORD'))

	# returns all devices compatible with a given application
	application_id = f"application/{application}"

	# Execute the query
	cursor = db.aql.execute(
		"""
		FOR edge IN collects
			FILTER edge._from == @appKey
			FOR node IN data
				FILTER node._id == edge._to
				RETURN node
		""",
		bind_vars={'appKey': application_id}
	)

	# Iterate through the result cursor
	data_keys = [doc['_key'] for doc in cursor]

	return data_keys

if __name__ == "__main__":
	results = get_collected_datatypes("smartthings")
	#print(f"Results {results}")
	for data in results:
		print(data)