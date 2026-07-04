#input_type_name: DispatchIssueInput
#output_type_name: DispatchIssueResult
#function_name: dispatch_issue

from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod

SEED = """Task #{number}: {title}

{description}

Priority: {priority}
issue_id for your tools: {issue_id}

Do this task directly from the brief. Finish EVERY run by:
1. post_comment(issue_id, <your full answer in markdown>) — your chat reply alone does NOT count; the result only exists as a comment.
2. transition_issue(issue_id, status="in_review", run_state="done").

If you need a human decision, propose a sensible default via post_comment, then
transition_issue(issue_id, run_state="waiting") and stop. On any human reply,
proceed and finish — never re-block.
"""


class DispatchIssueInput(BaseModel):
    issue_id: str


class DispatchIssueResult(BaseModel):
    conversation_id: str


async def dispatch_issue(ctx: FunctionContext, data: DispatchIssueInput) -> DispatchIssueResult:
    pod = Pod.from_env()
    issue = pod.table("issues").get(data.issue_id)

    agent_name = issue.get("assignee_name")
    if issue.get("assignee_kind") not in ("agent", "squad") or not agent_name or issue.get("conversation_id"):
        return DispatchIssueResult(conversation_id=issue.get("conversation_id") or "")

    conv = pod.conversations.create_for_agent(
        agent_name, title=f"#{issue.get('number')} {issue.get('title')}"
    )
    cid = str(conv.id)

    pod.table("issues").update(
        data.issue_id,
        {"conversation_id": cid, "run_state": "running", "status": "in_progress"},
    )
    pod.records.create("events", {
        "issue_id": data.issue_id, "kind": "dispatched",
        "actor_kind": "system", "actor_name": agent_name,
        "detail": {"conversation_id": cid},
    })

    resp = pod.conversations.send_stream(cid, SEED.format(
        number=issue.get("number"), title=issue.get("title"),
        description=issue.get("description") or "(no description)",
        priority=issue.get("priority"), issue_id=data.issue_id,
    ))
    try:
        resp.close()
    except Exception:
        pass
    return DispatchIssueResult(conversation_id=cid)
