"""Explanatory command-line path through one matter intake login."""

import os

from .infrai_sms_otp import InfraiSmsOtp
from .matter_access import CodeRequest, CodeSubmission, LegalAction, LegalLoginService


def main() -> None:
    phone_number = os.environ.get("LEGAL_LOGIN_PHONE", "")
    if not phone_number:
        raise RuntimeError("LEGAL_LOGIN_PHONE is required")

    login = LegalLoginService(InfraiSmsOtp())
    request = CodeRequest(
        phone_number=phone_number,
        matter_id="DEMO-MATTER-204",
        action=LegalAction.MATTER_INTAKE,
    )
    login.request_code(request)
    print(f"Code sent for {request.matter_id}")

    code = input("Enter the SMS code: ").strip()
    result = login.verify(CodeSubmission(**request.model_dump(), code=code))
    print(result.model_dump_json())


if __name__ == "__main__":
    main()
