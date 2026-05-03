from typing import Any, Literal, TypedDict, Annotated
import operator

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END


# ============================================================
# Models
# ============================================================

class Task(BaseModel):
    tool: Literal[
        "analyst_agent",
        "explanation_rag",
        "general_knowledge_agent",
        "project_structure_agent",
        "information_request",
        "derive_from_context",
    ] = Field(
        description="Which agent/tool must execute this task."
    )

    instruction: str = Field(
        description=(
            "Exact instruction string to pass verbatim to the selected tool. "
            "Must be a complete, unambiguous request phrased as if directly "
            "addressing the tool."
        )
    )


class Plan(BaseModel):
    agent: Literal["planner"] = Field(
        default="planner",
        description="Fixed identifier for the planner agent.",
    )

    user_intent: str = Field(
        description="One-sentence clarified user intent."
    )

    tasks: list[Task] = Field(
        description="Ordered list of tool invocations required to satisfy the intent."
    )


class ToolOutput(BaseModel):
    tool: str
    instruction: str
    output: Any


class ExecutorState(TypedDict):
    # Current turn
    user_query: str
    plan: Plan | None
    task_index: int
    aggregated_context: str | None
    final_answer: str | None

    # Accumulated fields
    tool_outputs: Annotated[list[ToolOutput], operator.add]
    general_knowledge: Annotated[list[str], operator.add]
    facts: Annotated[list[str], operator.add]


# ============================================================
# Prompts
# ============================================================

executor_prompt = """
You are a planner agent.

Your job is to convert the user's request into a short ordered plan.

Available tools:

1. analyst_agent
Use for data analysis, table operations, calculations, aggregations, SQL-style reasoning,
plot/table preparation, and structured data processing.

2. explanation_rag
Use for answering questions from documentation, help text, internal docs,
or retrieved explanatory context.

3. general_knowledge_agent
Use for general conceptual explanations or common knowledge.

4. project_structure_agent
Use for questions about available projects, datasets, studies, files, folders,
or project organization.

5. information_request
Use only when the user request cannot be executed because required information is missing.

6. derive_from_context
Use when enough context has already been collected and the next step is to infer,
summarize, compare, or synthesize facts from previous tool outputs.

Rules:
- Return only a valid structured Plan.
- Keep the plan minimal.
- Do not invent unavailable data.
- Each task instruction must be complete and directly executable by the selected tool.
- Prefer 1 task if the request is simple.
- Use derive_from_context after other tools when synthesis is needed.
"""


presenter_prompt = """
You are the presenter node.

Given the original user query, the clarified intent, and all tool outputs,
produce the final user-facing answer.

Be concise.
Do not mention internal graph mechanics unless necessary.
"""


# ============================================================
# Helpers
# ============================================================

def get_current_task(state: ExecutorState) -> Task:
    plan = state["plan"]

    if plan is None:
        raise ValueError("No plan found in state.")

    task_index = state["task_index"]

    if task_index >= len(plan.tasks):
        raise IndexError("Task index is out of range.")

    return plan.tasks[task_index]


def make_tool_output(
    state: ExecutorState,
    tool_name: str,
    output: Any,
) -> ToolOutput:
    task = get_current_task(state)

    return ToolOutput(
        tool=tool_name,
        instruction=task.instruction,
        output=output,
    )


def make_dummy_node_update(
    state: ExecutorState,
    tool_name: str,
) -> dict:
    output = f"{tool_name} was called and finished ok."

    return {
        "tool_outputs": [
            make_tool_output(
                state=state,
                tool_name=tool_name,
                output=output,
            )
        ],
        "task_index": state["task_index"] + 1,
    }


# ============================================================
# Nodes
# ============================================================

def planner_node(state: ExecutorState) -> dict:
    messages = [
        {
            "role": "system",
            "content": executor_prompt,
        },
        {
            "role": "user",
            "content": state["user_query"],
        },
    ]

    structured_llm = llm.with_structured_output(Plan)
    plan = structured_llm.invoke(messages)

    print("PLAN:")
    print(plan.model_dump_json(indent=2))

    return {
        "plan": plan,
        "task_index": 0,
        "aggregated_context": None,
        "final_answer": None,
    }


def executor_node(state: ExecutorState) -> dict:
    """
    Central execution checkpoint.

    Later this can:
    - validate the plan
    - validate the current task
    - enforce max task count
    - check required context exists
    - handle retries
    - log progress
    - stop early on information_request
    """

    plan = state["plan"]

    if plan is None:
        raise ValueError("No plan found in state.")

    print(
        f"Executor checkpoint: "
        f"task_index={state['task_index']}, "
        f"total_tasks={len(plan.tasks)}"
    )

    return {}


def analyst_node(state: ExecutorState) -> dict:
    return make_dummy_node_update(
        state=state,
        tool_name="analyst_agent",
    )


def general_knowledge_node(state: ExecutorState) -> dict:
    tool_name = "general_knowledge_agent"
    update = make_dummy_node_update(state, tool_name)

    output_text = str(update["tool_outputs"][-1].output)

    return {
        **update,
        "general_knowledge": [output_text],
    }


def project_structure_node(state: ExecutorState) -> dict:
    return make_dummy_node_update(
        state=state,
        tool_name="project_structure_agent",
    )


def explanation_rag_node(state: ExecutorState) -> dict:
    return make_dummy_node_update(
        state=state,
        tool_name="explanation_rag",
    )


def information_request_node(state: ExecutorState) -> dict:
    return make_dummy_node_update(
        state=state,
        tool_name="information_request",
    )


def derive_from_context_node(state: ExecutorState) -> dict:
    tool_name = "derive_from_context"
    update = make_dummy_node_update(state, tool_name)

    output_text = str(update["tool_outputs"][-1].output)

    return {
        **update,
        "facts": [output_text],
    }


def aggregator_node(state: ExecutorState) -> dict:
    plan = state["plan"]

    if plan is None:
        raise ValueError("No plan found in state.")

    chunks: list[str] = []

    chunks.append(f"User query:\n{state['user_query']}")
    chunks.append(f"User intent:\n{plan.user_intent}")

    chunks.append("Tool outputs:")

    for i, item in enumerate(state["tool_outputs"], start=1):
        chunks.append(
            f"""
Task {i}
Tool: {item.tool}
Instruction: {item.instruction}
Output:
{item.output}
""".strip()
        )

    if state["general_knowledge"]:
        chunks.append(
            "General knowledge:\n"
            + "\n".join(f"- {x}" for x in state["general_knowledge"])
        )

    if state["facts"]:
        chunks.append(
            "Facts:\n"
            + "\n".join(f"- {x}" for x in state["facts"])
        )

    aggregated_context = "\n\n---\n\n".join(chunks)

    print("AGGREGATED CONTEXT:")
    print(aggregated_context)

    return {
        "aggregated_context": aggregated_context,
    }


def presenter_node(state: ExecutorState) -> dict:
    aggregated_context = state["aggregated_context"]

    if aggregated_context is None:
        raise ValueError("No aggregated context found in state.")

    messages = [
        {
            "role": "system",
            "content": presenter_prompt,
        },
        {
            "role": "user",
            "content": aggregated_context,
        },
    ]

    response = llm.invoke(messages)

    return {
        "final_answer": response.content,
    }


# ============================================================
# Router
# ============================================================

def route_next_task(state: ExecutorState) -> str:
    plan = state["plan"]

    if plan is None:
        raise ValueError("No plan found in state.")

    task_index = state["task_index"]

    if task_index >= len(plan.tasks):
        return "aggregate"

    task = plan.tasks[task_index]

    return task.tool


# ============================================================
# Build graph
# ============================================================

