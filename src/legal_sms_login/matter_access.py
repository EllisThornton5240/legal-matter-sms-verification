"""Business decisions that follow a verified legal-tech login."""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, Field


class LegalAction(StrEnum):
    MATTER_INTAKE = "matter_intake"
    SIGNED_DOCUMENT_DELIVERY = "signed_document_delivery"
    DEADLINE_FOLLOW_UP = "deadline_follow_up"


class NextState(StrEnum):
    READY_FOR_REVIEW = "ready_for_review"
    READY_FOR_DOWNLOAD = "ready_for_download"
    READY_TO_ACKNOWLEDGE = "ready_to_acknowledge"


class CodeRequest(BaseModel):
    phone_number: str = Field(min_length=8, max_length=32)
    matter_id: str = Field(min_length=1, max_length=80)
    action: LegalAction


class CodeSubmission(CodeRequest):
    code: str = Field(min_length=4, max_length=12)


class VerificationResult(BaseModel):
    matter_id: str
    action: LegalAction
    next_state: NextState


class OtpBoundary(Protocol):
    def request_code(self, phone_number: str, operation_id: str) -> dict[str, object]:
        pass

    def verify_code(
        self, phone_number: str, code: str, operation_id: str
    ) -> dict[str, object]:
        pass


NEXT_STATE = {
    LegalAction.MATTER_INTAKE: NextState.READY_FOR_REVIEW,
    LegalAction.SIGNED_DOCUMENT_DELIVERY: NextState.READY_FOR_DOWNLOAD,
    LegalAction.DEADLINE_FOLLOW_UP: NextState.READY_TO_ACKNOWLEDGE,
}


class LegalLoginService:
    def __init__(self, otp: OtpBoundary) -> None:
        self.otp = otp

    def request_code(self, request: CodeRequest) -> None:
        self.otp.request_code(request.phone_number, self._operation_id(request))

    def verify(self, request: CodeSubmission) -> VerificationResult:
        self.otp.verify_code(
            request.phone_number,
            request.code,
            self._operation_id(request),
        )
        return VerificationResult(
            matter_id=request.matter_id,
            action=request.action,
            next_state=NEXT_STATE[request.action],
        )

    @staticmethod
    def _operation_id(request: CodeRequest) -> str:
        return f"legal-login:{request.matter_id}:{request.action.value}"
