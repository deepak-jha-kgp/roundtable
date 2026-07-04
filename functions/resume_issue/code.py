#input_type_name: ResumeIssueInput
#output_type_name: ResumeIssueResult
#function_name: resume_issue

from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod


class ResumeIssueInput(BaseModel):
    issue_id: str
    body: str


class ResumeIssueResult(BaseModel):
    ok: bool


RESUMABLE_STATUSES = {"in_review", "backlog"}


async def resume_issue(ctx: FunctionContext, data: ResumeIssueInput) -> ResumeIssueResult:
    pod = Pod.from_env()
    issue = pod.table("issues").get(data.issue_id)
    cid = issue.get("conversation_id")
    run_state = str(issue.get("run_state") or "").strip().lower()
    status = str(issue.get("status") or "").strip().lower()
    if not cid or (run_state != "waiting" and status not in RESUMABLE_STATUSES):
        return ResumeIssueResult(ok=False)
    pod.table("issues").update(data.issue_id, {"run_state": "running"})
    pod.records.create("events", {
        "issue_id": data.issue_id, "kind": "resumed",
        "actor_kind": "system", "detail": {},
    })
    resp = pod.conversations.send_stream(cid, data.body)
    try:
        resp.close()
    except Exception:
        pass
    return ResumeIssueResult(ok=True)
