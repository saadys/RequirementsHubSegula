"""
Deterministic Score Node

Pure Python scoring engine — NO LLM calls.
Applies fixed weights to FactExtraction fields to produce a feasibility score.

Owner: Track B
"""

# TODO [Track B]: Implement deterministic_score node
#
# Input from state: extracted_facts, similar_projects, rag_scores
# Output to state: score, score_breakdown, decision
#
# Agreed scoring weights:
#   Problem clarity:        20 pts (has_clear_problem_statement)
#   AI solvability:         15 pts (problem_is_ai_solvable)
#   Data availability:      20 pts (data_availability: none=0, partial=10, full=20)
#   Similar project exists: 15 pts (from RAG scores)
#   Research required:      10 pts (requires_new_research: no=10, yes=3)
#   Technique identified:   10 pts (ai_technique_identified != "unknown")
#   Integration complexity: 10 pts (low=10, medium=7, high=3)
#   TOTAL:                 100 pts
#
# Thresholds:
#   >= 70 = "GO"
#   40-69 = "NEEDS_CLARIFICATION"
#   < 40  = "NO_GO"
