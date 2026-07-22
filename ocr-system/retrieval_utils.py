import re
from typing import Set


SYNONYMS = {
    "technical": ["skills", "technologies", "programming", "tools", "experience"],
    "stack": ["technologies", "tools", "frameworks", "platforms"],
    "skills": ["abilities", "expertise", "competencies", "proficiencies"],
    "experience": ["work", "employment", "career", "background"],
    "policy": ["rules", "guidelines", "procedures", "regulations"],
    "benefits": ["perks", "compensation", "allowances", "rewards"],
    "leave": ["vacation", "holiday", "time off", "sabbatical"],
    "salary": ["pay", "compensation", "wage", "income"],
    "education": ["degree", "qualification", "certification", "training"],
    "project": ["initiative", "program", "campaign", "assignment"],
    "document": ["file", "paper", "report", "manual", "record"],
    "question": ["ask", "inquiry", "query", "request"],
}


def expand_query_terms(query: str) -> Set[str]:
    query_lower = re.sub(r"[^a-z0-9]+", " ", query.lower()).strip()
    terms = set(query_lower.split())

    for word in list(terms):
        for key, syns in SYNONYMS.items():
            if word in syns or word == key:
                terms.update(syns)
                terms.add(key)

    return terms


def score_chunk_relevance(query: str, chunk: str) -> float:
    query_terms = expand_query_terms(query)
    chunk_lower = re.sub(r"[^a-z0-9]+", " ", chunk.lower()).strip()
    if not query_terms or not chunk_lower:
        return 0.0

    matches = sum(1 for term in query_terms if term in chunk_lower)
    if matches == 0:
        return 0.0

    return min(1.0, matches / max(2, len(query_terms)))
