from typing import List
from src.types.triple import Triple

class QueryFormatter:

    # TODO: How can we paraphrase dynamically and not have it hard coded?
    TEMPLATES = {
        ('hasSensor', 'device', 'sensor'): [
            '"{subject} has {object}"',
            '"{subject} is equipped with {object}"',
            '"{object} is part of {subject}"',
            '"{subject} comes with {object}"',
            '"{subject} features {object}"',
        ],
        ('manufacturedBy', 'device', 'manufacturer'): [
            '"{subject} by {object}"',
            '"{subject} is manufactured by {object}"',
            '"{subject} is produced by {object}"',
            '"{subject} comes from {object}"',
            '"{object} manufactures {subject}"',
            '"{subject} is built by {object}"',
        ],
        ('compatibleWith', None, None): [
            '"{subject} is compatible with {object}"',
            '"{subject} works with {object}"',
            '"{object} is supported by {subject}"',
            '"{subject} pairs with {object}"',
            '"{subject} integrates well with {object}"',
        ],
        ('performs', 'device', 'process'): [
            '"{subject} performs {object}"',
            '"{subject} carries out {object}"',
            '"{subject} executes {object}"',
            '"{subject} completes {object}"',
            '"{subject} undertakes {object}"',
        ],
        ('hasPolicy', None, None): [
            '"{subject} has policy {object}"',
            '"{subject} adopts the {object} policy"',
            '"{subject} follows the {object} policy"',
            '"{subject} implements the {object} policy"',
            '"{subject} operates under the {object} policy"',
        ],
        ('statesInPolicy', None, 'privacyPolicy'): [
            '"{subject} is stated in policy {object}"',
            '"Policy {object} specifies {subject}"',
            '"Policy {object} outlines {subject}"',
            '"{subject} is mentioned in policy {object}"',
            '"{subject} is detailed in policy {object}"',
        ],
        ('follows', 'privacyPolicy', 'regulation'): [
            '"{subject} follows {object}"',
            '"{subject} adheres to {object}"',
            '"{subject} complies with {object}"',
            '"{subject} upholds {object}"',
            '"{subject} observes {object}"',
        ],
        ('developedBy', 'application', 'manufacturer'): [
            '"{subject} is developed by {object}"',
            '"{object} develops {subject}"',
            '"{subject} is created by {object}"',
            '"{subject} is engineered by {object}"',
            '"{subject} is built under the guidance of {object}"',
        ],
    }

    def format_triple(self, triple: Triple) -> List[str]:
        templates = self._get_templates(triple)
        return [
            tmpl.format(subject=triple.subject.value, object=triple.object.value)
            for tmpl in templates
        ]
    
    def _get_templates(self, triple: Triple) -> List[str]:
        key = (triple.predicate, triple.subject.node_type, triple.object.node_type)
        if key in self.TEMPLATES:
            return self.TEMPLATES[key]
        