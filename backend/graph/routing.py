"""
Conditional Routing Functions

Determines which node to execute next based on the current pipeline state.

Owner: TOGETHER (Phase 3 — Integration)
"""

# TODO [TOGETHER]: Implement routing functions
#
# def route_after_validation(state) -> str:
#     if state.get("missing_fields"):
#         return "return_incomplete"
#     return "rag_search"
#
# def route_after_rag(state) -> str:
#     if state["is_exact_match"]:
#         return "fast_track"
#     return "llm_analyze"
#
# def route_after_score(state) -> str:
#     if state["decision"] == "GO":
#         return "generate_report_go"
#     elif state["decision"] == "NO_GO":
#         return "generate_report_nogo"
#     else:  # NEEDS_CLARIFICATION
#         if state["clarification_round"] < MAX_CLARIFICATION_ROUNDS:
#             return "generate_questions"
#         return "generate_report_partial"
