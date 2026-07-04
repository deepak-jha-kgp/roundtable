#input_type_name: CreateSubissueInput
#output_type_name: CreateSubissueResult
#function_name: create_subissue

from typing import Optional
from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod


class CreateSubissueInput(BaseModel):
    parent_issue_id: str
    title: str
    description: Optional[str] = None
    assignee_name: Optional[str] = None
    assignee_kind: str = "agent"


class CreateSubissueResult(BaseModel):
    issue_id: str


async def create_subissue(ctx: FunctionContext, data: CreateSubissueInput) -> CreateSubissueResult:
    pod = Pod.from_env()
    parent = pod.table("issues").get(data.parent_issue_id)
    # An "agent" assignment without a name can never be dispatched — treat it as unassigned.
    assignee_kind = data.assignee_kind if data.assignee_name else "unassigned"
    row = pod.table("issues").create({
        "title": data.title,
        "description": data.description or "",
        "status": "todo",
        "priority": parent.get("priority", "none"),
        "parent_issue_id": data.parent_issue_id,
        "project_id": parent.get("project_id"),
        "assignee_kind": assignee_kind,
        "assignee_name": data.assignee_name,
    })
    pod.records.create("events", {
        "issue_id": str(row["id"]), "kind": "subissue_created",
        "actor_kind": "agent", "actor_name": parent.get("assignee_name"),
        "detail": {"parent_issue_id": data.parent_issue_id, "title": data.title},
    })
    return CreateSubissueResult(issue_id=str(row["id"]))
