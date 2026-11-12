"""Request bodies for the UnderCover API."""

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator


class Decision(BaseModel):
    """The agent's decision on a claim."""

    decision: Literal["approve", "decline", "refer"]
    payout: float = Field(ge=0)
    reason: str = Field(min_length=1)
    policy_section: str = Field(min_length=1)

    @model_validator(mode="after")
    def no_payout_unless_approved(self) -> Self:
        if self.decision != "approve" and self.payout > 0:
            raise ValueError("Only an approved claim has a payout")
        return self


class Payment(BaseModel):
    """A payment on an approved claim."""

    amount: float = Field(gt=0)


class SignOff(BaseModel):
    """A handler's sign-off on a payment over the approval limit."""

    handler_id: str


class Step(BaseModel):
    """One step of the agent's work on a claim."""

    kind: Literal["tool_call", "tool_result", "answer", "error"]
    text: str
