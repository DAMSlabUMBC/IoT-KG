from dataclasses import dataclass
from typing import Tuple

@dataclass
class TripleNode:
    node_type: str
    value: str

@dataclass
class Triple:
    subject: TripleNode
    predicate: str
    object: TripleNode

    @classmethod
    def from_tuple(cls, triplet: Tuple[Tuple[str, str], str, Tuple[str,str]]):
        (subject_type, subject_value), predicate, (object_type, object_value) = triplet
        return cls(
            subject=TripleNode(subject_type, subject_value),
            predicate=predicate,
            object=TripleNode(object_type, object_value)
        )
    