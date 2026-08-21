"""
Tests for LLM Framework (Factory, Providers, Interfaces, and Pipeline Nodes)
"""

from unittest.mock import patch
from pydantic import BaseModel
from backend.LLM.LLMEnums import LLMProviderEnum, LLMModelEnum
from backend.LLM.LLMInterfaces import LLMInterface
from backend.LLM.LLMProviderFactory import LLMProviderFactory
from backend.LLM.providers.base_provider import BaseLLMProvider
from backend.LLM.providers.fallback_provider import FallbackLLMProvider
from backend.LLM.providers.GeminiProvider import GeminiProvider
from backend.LLM.providers.openai_provider import OpenAIProvider
from backend.services.llm import get_llm, get_structured_llm, get_clarification_llm
from backend.schemas import (
    FactExtraction,
    ClarificationQuestions,
    ClarificationQuestionsModel,
    QuestionItem,
    CategoricalFactExtraction,
    PillarAIViability,
    PillarDataReadiness,
    PillarProblemClarity,
    PillarIntegration,
    PillarGovernance,
)


class DummySchema(BaseModel):
    summary: str


class MockSuccessProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__(model_name="mock-success")

    async def generate_text(self, prompt, system_prompt=None, chat_history=None, max_output_tokens=None, temperature=None):
        self.last_model_used = self.model_name
        return "Success"

    async def generate_structured_output(self, prompt, response_schema, system_prompt=None, temperature=None):
        self.last_model_used = self.model_name
        if response_schema == CategoricalFactExtraction:
            return CategoricalFactExtraction(
                ai_viability=PillarAIViability(category="HIGHLY_VIABLE", reason="Clear NLP task"),
                data_readiness=PillarDataReadiness(category="READY", reason="Sufficient data"),
                problem_clarity=PillarProblemClarity(category="CLEAR", reason="Clear scope"),
                integration_feasibility=PillarIntegration(category="SIMPLE", reason="API integration"),
                governance_and_safety=PillarGovernance(category="SAFE", reason="No privacy risks"),
                identified_technique="NLP / LLM",
                project_summary="Valid AI project request.",
            )
        elif response_schema == FactExtraction:
            return FactExtraction(
                has_clear_problem_statement=True,
                problem_is_ai_solvable=True,
                problem_category="nlp",
                data_availability="full",
                data_volume_sufficient="yes",
                ai_technique_identified="RAG",
                requires_new_research=False,
                integration_complexity="low",
                estimated_effort="small",
                risks_identified=["Data privacy"],
                extracted_requirements=["Fast query time"],
                summary="Valid AI project request."
            )
        elif response_schema in (ClarificationQuestions, ClarificationQuestionsModel):
            return ClarificationQuestionsModel(
                questions=[
                    QuestionItem(
                        target_pillar="problem_clarity",
                        question="How many users will access the system?",
                        technical_reasoning="To assess scalability and infrastructure capacity.",
                    )
                ]
            )
        return response_schema(summary="Mock Result")

    def health_check(self) -> bool:
        return True


class MockFailingProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__(model_name="mock-failing")

    async def generate_text(self, prompt, system_prompt=None, chat_history=None, max_output_tokens=None, temperature=None):
        raise RuntimeError("API Connection Error")

    async def generate_structured_output(self, prompt, response_schema, system_prompt=None, temperature=None):
        raise RuntimeError("API Connection Error")

    def health_check(self) -> bool:
        return False


def test_llm_enums():
    assert LLMProviderEnum.GEMINI == "gemini"
    assert LLMProviderEnum.OPENAI == "openai"
    assert LLMModelEnum.GPT_4O == "gpt-4o"


def test_base_provider_message_formatting():
    provider = MockSuccessProvider()
    msgs = provider._format_messages(prompt="User prompt", system_prompt="System prompt")
    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert msgs[1]["content"] == "User prompt"


def test_gemini_provider_init_and_keys():
    provider = GeminiProvider(model_name="gemini-1.5-flash")
    assert provider.model_name == "gemini/gemini-1.5-flash"
    assert isinstance(provider.api_keys, list)


def test_openai_provider_init():
    provider = OpenAIProvider(model_name="gpt-4o")
    assert provider.model_name == "openai/gpt-4o"


def test_factory_instantiation():
    provider = LLMProviderFactory.get_provider()
    assert isinstance(provider, LLMInterface)


async def test_fallback_provider_success():
    primary = MockSuccessProvider()
    fallback = MockFailingProvider()
    provider = FallbackLLMProvider(primary_provider=primary, fallback_provider=fallback)

    result = await provider.generate_text("Hello")
    assert result == "Success"
    assert provider.last_model_used == "mock-success"

    struct_result = await provider.generate_structured_output("Hello", DummySchema)
    assert struct_result.summary == "Mock Result"


async def test_fallback_provider_fails_over():
    primary = MockFailingProvider()
    fallback = MockSuccessProvider()
    provider = FallbackLLMProvider(primary_provider=primary, fallback_provider=fallback)

    result = await provider.generate_text("Hello")
    assert result == "Success"
    assert provider.last_model_used == "mock-success"

    struct_result = await provider.generate_structured_output("Hello", DummySchema)
    assert struct_result.summary == "Mock Result"


def test_service_facade():
    llm = get_llm()
    assert isinstance(llm, LLMInterface)

    structured_llm = get_structured_llm()
    assert isinstance(structured_llm, LLMInterface)

    clarification_llm = get_clarification_llm()
    assert isinstance(clarification_llm, LLMInterface)


def test_string_template_builder():
    from backend.LLM.templates.template import build_system_prompt

    dept_ctx = "Department: HR JSON schema: {\"key\": \"val\"}"
    sim_projects = [
        {"project_name": "CV Matcher", "solution_description": "NLP screening", "ai_techniques": ["NLP", "BERT"]}
    ]
    prompt = build_system_prompt(
        department_context=dept_ctx,
        similar_projects=sim_projects,
        clarification_round=1,
        clarification_questions=["What volume?"],
        clarification_answers=["10,000 CVs"],
    )

    assert "Segula Technologies" in prompt
    assert "Department: HR" in prompt
    assert "CV Matcher" in prompt
    assert "Clarification Round 1" in prompt


@patch("backend.nodes.llm_analyze.get_structured_llm")
async def test_llm_analyze_node_integration(mock_get_llm):
    from backend.nodes.llm_analyze import llm_analyze

    mock_get_llm.return_value = MockSuccessProvider()
    state = {
        "form_data": {
            "project_name": "HR Assistant",
            "problem_description": "We need to parse candidate resumes automatically."
        }
    }
    result = await llm_analyze(state)
    assert "extracted_facts" in result
    assert result["extracted_facts"]["ai_viability"]["category"] == "HIGHLY_VIABLE"
    assert result["extracted_facts"]["identified_technique"] == "NLP / LLM"
    assert result["extracted_facts_model_used"] == "mock-success"


@patch("backend.nodes.generate_questions.get_clarification_llm")
async def test_generate_questions_node_integration(mock_get_llm):
    from backend.nodes.generate_questions import generate_questions

    mock_get_llm.return_value = MockSuccessProvider()
    state = {
        "form_data": {
            "project_name": "Vague Project",
            "problem_description": "We want AI."
        },
        "extracted_facts": {
            "ai_viability": {"category": "MARGINAL", "reason": "Unclear scope"},
            "data_readiness": {"category": "UNLABELED_OR_MESSY", "reason": "No labels"},
            "problem_clarity": {"category": "VAGUE", "reason": "Vague goals"},
            "integration_feasibility": {"category": "COMPLEX", "reason": "Unknown"},
            "governance_and_safety": {"category": "SAFE", "reason": "Safe"},
        },
        "clarification_round": 0
    }
    result = await generate_questions(state)
    assert "clarification_questions" in result
    assert len(result["clarification_questions"]) == 1
    assert result["clarification_round"] == 1
    assert result["clarification_model_used"] == "mock-success"


def test_corporate_support_template_module():
    from backend.LLM.templates.corporate_support import get_prompt, DEPARTMENT_CONTEXT

    assert "Corporate & Support Services" in DEPARTMENT_CONTEXT
    form_data = {
        "project_name": "IT Ticket Bot",
        "department": "IT",
        "problem_description": "Auto classify Jira tickets."
    }
    messages = get_prompt(form_data=form_data)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "IT Ticket Bot" in messages[1]["content"]
    assert "Human Resources" in messages[0]["content"]
