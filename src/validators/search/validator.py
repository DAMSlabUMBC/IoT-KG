"""Main triple validation orchestration."""

from src.types.triple import Triple
from .search import SearchClient
from .format import QueryFormatter
from .corrupt import TripleCorruptor


class SearchValidator:
    """Main validator that orchestrates the validation process."""
    
    def __init__(self, headless: bool = False):
        self.search_client = SearchClient(headless=headless)
        self.query_formatter = QueryFormatter()
        self.corruptor = TripleCorruptor(self.query_formatter)
    
    def close(self):
        """Close the shared browser session."""
        self.search_client.close()

    def validate(
        self,
        triple: Triple,
    ) -> float:
        """Validate a triple by comparing search results with corrupted variants."""

        # Search the triple and paraphrases
        normal_queries = self.query_formatter.format_triple(triple)
        print(f"Searching {len(normal_queries)} normal variants...")
        print(f"Normal Queries: ", normal_queries)
        normal_res = self.search_client.search_queries(normal_queries)
        print(f"Normal results: {normal_res}")

        # Quick check, are any variants showing lots of pages?
        max_normal_pages = max((r.pages for r in normal_res), default= 0)
        if max_normal_pages > 1:
            print(f"Strong evidence (pages> 1), skipping corruption check")
            return self._calculatePageWeight(max_normal_pages)
        
        print(f"Weak evidence (pages < 1), performing the corruption check")

        # The page check was inconclusive, create corrupted triples
        corrupt_queries = self.corruptor.generate_corrupted_queries(triple)
        print(f"Searching {len(corrupt_queries)} corrupted variants...")
        print(f"Corrupt Queries: ", corrupt_queries)
        corrupt_res = self.search_client.search_queries(corrupt_queries)
        print(f"Corrupted results: {corrupt_res}")

        # Compare the search results from the original and corrupted triple
        max_normal_results = max((r.results for r in normal_res), default=0)
        max_corrupt_results = max((r.results for r in corrupt_res), default=0)

        return self._calculateResultWeight(max_normal_results, max_corrupt_results)

    def _calculatePageWeight(self, pageNum: int):
        """ Any result with 5 >= pages is "likely" to be valid """
        return min(1, round(pageNum/5, 2))
    
    def _calculateResultWeight(self, maxNormal: int, maxCorrupt: int):
        """
        If the true query has more hits than the corrupted one, the claim is likely true.
        The bigger the gap, the higher the confidence (weight).

        The +1 and +2 avoids undefined outputs and absolute 0 / 1
        """
        return round(((maxNormal + 1)/ (maxNormal + maxCorrupt + 2)), 2)
