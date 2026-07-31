from backend.services.llm import get_structured_llm , get_clarification_llm
from backend.contracts.schemas import FactExtraction
from langchain_core.messages import HumanMessage , AIMessage

structured_llm = get_structured_llm()
result = structured_llm.invoke(
    "A manufacturing team wants to use AI to detect welding defects "
    "from camera images on their production line. They have 50,000 "
    "labeled images from the past 2 years."
)
print(f"Type: {type(result)}")  # Should be FactExtraction
print(f"Problem clear: {result.has_clear_problem_statement}")
print(f"AI solvable: {result.problem_is_ai_solvable}")
print(f"Category: {result.problem_category}")
print(f"Data: {result.data_availability}")
print(f"Summary: {result.summary}")
print(f"\nFull JSON:\n{result.model_dump_json(indent=2)}") 

messages = [
    HumanMessage(content=
    "A manufacturing team wants to use AI to detect welding defects "
    "from camera images on their production line. They have 50,000 "
    "labeled images from the past 2 years."),
    AIMessage(content=result.model_dump_json(indent=2))
]
clarification_llm = get_clarification_llm()

clarification_result = clarification_llm.invoke(messages)
print(f"\nClarification Questions:\n{clarification_result.model_dump_json(indent=2)}")