from typing import Any

import pytest

from legal_sms_login.infrai_sms_otp import InfraiError
from legal_sms_login.matter_access import (
    CodeSubmission,
    LegalAction,
    LegalLoginService,
    NextState,
)


class RecordingOtp:
    def __init__(self, rejection: InfraiError | None = None) -> None:
        self.rejection = rejection
        self.calls: list[tuple[str, str, str]] = []

    def request_code(self, phone_number: str, operation_id: str) -> dict[str, Any]:
        return {"accepted": True}

    def verify_code(
        self, phone_number: str, code: str, operation_id: str
    ) -> dict[str, Any]:
        self.calls.append((phone_number, code, operation_id))
        if self.rejection:
            raise self.rejection
        return {"verified": True}


def signed_delivery() -> CodeSubmission:
    return CodeSubmission(
        phone_number="+15551234567",
        matter_id="MAT-204",
        action=LegalAction.SIGNED_DOCUMENT_DELIVERY,
        code="123456",
    )


def test_verified_phone_releases_signed_document_delivery() -> None:
    otp = RecordingOtp()

    result = LegalLoginService(otp).verify(signed_delivery())

    assert result.next_state is NextState.READY_FOR_DOWNLOAD
    assert otp.calls == [
        (
            "+15551234567",
            "123456",
            "legal-login:MAT-204:signed_document_delivery",
        )
    ]


def test_rejected_code_does_not_produce_a_workflow_state() -> None:
    otp = RecordingOtp(InfraiError("invalid code", {"message": "Try again"}, 400))

    with pytest.raises(InfraiError):
        LegalLoginService(otp).verify(signed_delivery())
