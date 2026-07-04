#input_type_name: TransitionIssueInput
#output_type_name: TransitionIssueResult
#function_name: transition_issue

from typing import Optional
from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod


class TransitionIssueInput(BaseModel):
    issue_id: str
    status: Optional[str] = None
    run_state: Optional[str] = None


class TransitionIssueResult(BaseModel):
    ok: bool


async def transition_issue(ctx: FunctionContext, data: TransitionIssueInput) -> TransitionIssueResult:
    pod = Pod.from_env()
    patch = {}
    if data.status:
        patch["status"] = data.status
    if data.run_state:
        patch["run_state"] = data.run_state
    if not patch:
        return TransitionIssueResult(ok=False)
    issue = pod.table("issues").get(data.issue_id)
    pod.table("issues").update(data.issue_id, patch)
    pod.records.create("events", {
        "issue_id": data.issue_id, "kind": "transitioned",
        "actor_kind": "agent", "actor_name": issue.get("assignee_name"), "detail": patch,
    })
    return TransitionIssueResult(ok=True)
