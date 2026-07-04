#input_type_name: PostCommentInput
#output_type_name: PostCommentResult
#function_name: post_comment

from typing import Optional
from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod


class PostCommentInput(BaseModel):
    issue_id: str
    body: str
    author_kind: str = "agent"
    author_name: Optional[str] = None


class PostCommentResult(BaseModel):
    comment_id: str


async def post_comment(ctx: FunctionContext, data: PostCommentInput) -> PostCommentResult:
    pod = Pod.from_env()
    row = pod.table("comments").create({
        "issue_id": data.issue_id, "body": data.body,
        "author_kind": data.author_kind, "author_name": data.author_name,
    })
    pod.records.create("events", {
        "issue_id": data.issue_id, "kind": "commented",
        "actor_kind": data.author_kind, "actor_name": data.author_name,
        "detail": {"preview": data.body[:140]},
    })
    return PostCommentResult(comment_id=str(row["id"]))
