"""FastAPI routes for requesting and verifying a legal login code."""

from fastapi import FastAPI, HTTPException, status

from .infrai_sms_otp import InfraiError, InfraiSmsOtp
from .matter_access import CodeRequest, CodeSubmission, LegalLoginService, VerificationResult

app = FastAPI(title="Legal matter SMS verification")


def service() -> LegalLoginService:
    return LegalLoginService(InfraiSmsOtp())


def client_status(error: InfraiError) -> int:
    if 400 <= error.status_code < 500:
        return error.status_code
    return status.HTTP_502_BAD_GATEWAY


@app.post("/login/code", status_code=status.HTTP_202_ACCEPTED)
def request_login_code(request: CodeRequest) -> dict[str, str]:
    try:
        service().request_code(request)
    except InfraiError as error:
        raise HTTPException(
            status_code=client_status(error),
            detail={"code": error.code, "details": error.details},
        ) from error
    return {"matter_id": request.matter_id, "status": "code_sent"}


@app.post("/login/verify", response_model=VerificationResult)
def verify_login_code(request: CodeSubmission) -> VerificationResult:
    try:
        return service().verify(request)
    except InfraiError as error:
        raise HTTPException(
            status_code=client_status(error),
            detail={"code": error.code, "details": error.details},
        ) from error
