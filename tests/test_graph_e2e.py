"""
End-to-End LangGraph Pipeline Integration Tests
"""

import pytest
from unittest.mock import patch
from backend.graph.builder import get_compiled_graph


@pytest.mark.asyncio
async def test_graph_e2e_deterministic_go_flow():
    """Test full LangGraph execution for a strong feasible AI project."""
    graph = get_compiled_graph()
    
    initial_state = {
        "form_data": {
            "project_name": "Supplier Invoice OCR & Matching",
            "department": "corporate_support",
            "team_contact_name": "Sarah Miller",
            "team_contact_email": "s.miller@segula.fr",
            "problem_description": "Accounts payable receives 1,200 PDF invoices monthly. Two accountants manually compare invoice line items against SAP ERP purchase orders, taking ~35 hours per week.",
            "current_process": "Accountants manually open each PDF, match line items with SAP table ME23N, and flag discrepancies.",
            "expected_outcome": "Automated OCR extraction and fuzzy line-item matching against SAP POs, automatically validating invoices under 5,000€.",
            "data_description": "3 years of historical PDF invoices (36,000 files) with corresponding SAP ERP transactional settlement logs and discrepancy tags in SQL.",
            "deadline_urgency": "high",
        },
        "clarification_round": 0,
        "clarification_answers": [],
    }

    mock_rag = [("Historical invoice project", 0.72, {"project_name": "InvoiceMatcher", "solution_description": "Automated OCR extraction for supplier invoices", "ai_techniques": ["OCR", "NLP"]})]
    with patch("backend.nodes.rag_search.search_similar", return_value=mock_rag):
        final_state = await graph.ainvoke(initial_state)

    assert final_state is not None
    assert final_state.get("decision") in ["GO", "FAST_TRACK"]
    assert final_state.get("score") >= 70
    assert "report" in final_state
    assert "# 📋 AI Project Feasibility Dossier" in final_state["report"]
    assert final_state.get("veto_triggered") is False
    assert "sub_scores" in final_state


@pytest.mark.asyncio
async def test_graph_e2e_fast_track_flow():
    """Test full LangGraph execution when RAG finds an exact match (>=0.75 threshold)."""
    graph = get_compiled_graph()

    initial_state = {
        "form_data": {
            "project_name": "Segula Knowledge Hub AI Assistant",
            "department": "corporate_support",
            "team_contact_name": "Karim Bennani",
            "team_contact_email": "k.bennani@segula.fr",
            "problem_description": "New engineers spend 2 hours searching internal PDF onboarding guides and technical standards on SharePoint.",
            "current_process": "Ask colleagues or search folder trees manually.",
            "expected_outcome": "Conversational RAG assistant that answers questions with verified citations from internal PDFs.",
            "data_description": "350 structured PDF and Markdown documents from internal knowledge base.",
            "deadline_urgency": "medium",
        },
        "clarification_round": 0,
        "clarification_answers": [],
    }

    mock_exact = [("IRFANE Knowledge Hub", 0.96, {"project_name": "IRFANE Chatbot", "solution_description": "Internal document Q&A chatbot using RAG", "ai_techniques": ["RAG", "LLM"]})]
    with patch("backend.nodes.rag_search.search_similar", return_value=mock_exact):
        final_state = await graph.ainvoke(initial_state)

    assert final_state is not None
    assert final_state.get("decision") == "FAST_TRACK"
    assert final_state.get("score") == 95
    assert "report" in final_state
    assert "# 🚀 Fast Track Evaluation" in final_state["report"]



@pytest.mark.asyncio
async def test_graph_e2e_deterministic_veto_not_ai():
    """Test full LangGraph execution for a deterministic ETL rule-based task (NO_GO)."""
    graph = get_compiled_graph()
    
    initial_state = {
        "form_data": {
            "project_name": "Nightly CSV to XML File Converter",
            "department": "corporate_support",
            "team_contact_name": "Marc Lemaire",
            "team_contact_email": "m.lemaire@segula.fr",
            "problem_description": "Every night at 2 AM, the payroll team needs to convert a fixed CSV table into a standardized XML format with SHA-256 checksums.",
            "current_process": "A person runs an Excel macro in the morning manually.",
            "expected_outcome": "A script or AI model to convert CSV columns to XML tags and calculate the checksum.",
            "data_description": "Standard tabular CSV files with 10 fixed columns.",
            "deadline_urgency": "medium",
        },
        "clarification_round": 0,
        "clarification_answers": [],
    }

    with patch("backend.nodes.rag_search.search_similar", return_value=[]):
        final_state = await graph.ainvoke(initial_state)

    assert final_state is not None
    assert final_state.get("decision") == "NO_GO"
    assert final_state.get("score") <= 20
    assert final_state.get("veto_triggered") is True
    assert "report" in final_state
    assert "Executive Verdict: **NO_GO**" in final_state["report"]


@pytest.mark.asyncio
async def test_graph_e2e_clarification_generation():
    """Test that requests needing clarification branch to generate_questions."""
    graph = get_compiled_graph()

    initial_state = {
        "form_data": {
            "project_name": "Automated Legal Contract Clause Negotiation Assistant",
            "department": "corporate_support",
            "team_contact_name": "Julien Robert",
            "team_contact_email": "j.robert@segula.fr",
            "problem_description": "Legal counsel spends hours reviewing customer master service agreements (MSAs) to ensure non-standard liability clauses comply with Segula legal guidelines.",
            "current_process": "Lawyers read Word documents and insert standard redline edits manually.",
            "expected_outcome": "AI highlights risky liability clauses and auto-suggests pre-approved replacement clauses.",
            "data_description": "We do not have a centralized contract database yet; contracts are saved on individual lawyers' laptops in different formats without labeling.",
            "deadline_urgency": "low",
        },
        "clarification_round": 0,
        "clarification_answers": [],
    }

    with patch("backend.nodes.rag_search.search_similar", return_value=[]):
        final_state = await graph.ainvoke(initial_state)

    assert final_state is not None
    assert final_state.get("decision") == "NEEDS_CLARIFICATION"
    assert final_state.get("clarification_questions") is not None
    assert len(final_state["clarification_questions"]) > 0
    assert final_state.get("clarification_round") == 1





