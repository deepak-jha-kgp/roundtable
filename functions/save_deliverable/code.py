#input_type_name: SaveDeliverableInput
#output_type_name: SaveDeliverableResult
#function_name: save_deliverable

import re

from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod


class SaveDeliverableInput(BaseModel):
    issue_id: str
    slug: str
    content: str


class SaveDeliverableResult(BaseModel):
    path: str


async def save_deliverable(ctx: FunctionContext, data: SaveDeliverableInput) -> SaveDeliverableResult:
    pod = Pod.from_env()
    issue = pod.table("issues").get(data.issue_id)
    slug = re.sub(r"[^a-z0-9-]+", "-", data.slug.lower()).strip("-")[:60] or "deliverable"
    path = f"/knowledge/deliverables/RT-{issue.get('number')}-{slug}.md"
    pod.files.write_text(path, data.content)
    pod.records.create("events", {
        "issue_id": data.issue_id, "kind": "saved_deliverable",
        "actor_kind": "agent", "actor_name": issue.get("assignee_name"),
        "detail": {"path": path},
    })
    return SaveDeliverableResult(path=path)
