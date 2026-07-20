# Makes triplets from the data/html path
triplets:
	uv run -m src.index

# Validates triplets from the data/triplets path
validate:
	uv run -m src.validate
