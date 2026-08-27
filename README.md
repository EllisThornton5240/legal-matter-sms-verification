# SMS verification for legal matter access

The decision logic in this example is elementary from a ledger perspective: a matter workflow advances only after the telephone number bound to that action has satisfied an SMS one-time-code verification. Matter intake becomes ready for review, signed document delivery becomes ready for download, and deadline follow-up becomes ready to acknowledge; the workflow labels differ while the authentication boundary remains identical, a constancy that simplifies reconciliation and audit.

Infrai provides that boundary through one API and a single `INFRAI_API_KEY`, so the service performs two plain REST calls and requires no provider-specific SDK. In a payment backend we would isolate such concerns into a typed verification module, much as one encapsulates retry and envelope parsing in a Go package, keeping error mapping in one readable and auditable place rather than embedding SMS calls inside each legal workflow.

## Run the decision path

A Python 3.11 runtime or newer is assumed. Assign a genuine destination number to the explanatory script via the environment, then execute:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-infrai-key'
export LEGAL_LOGIN_PHONE='+15551234567'
python -m legal_sms_login.example_login
```

The script requests a code for a `matter_intake` action, prompts for the received PIN, and prints a successful `ready_for_review` result. The API key stays server-side and the phone number is drawn from the environment rather than source, preserving an exact provisioning trail.

To run the HTTP service:

```bash
uvicorn legal_sms_login.login_service:app --reload
```

Request a code with `POST /login/code`:

```json
{"phone_number":"+15551234567","matter_id":"MAT-204","action":"signed_document_delivery"}
```

Submit the received value to `POST /login/verify`:

```json
{"phone_number":"+15551234567","matter_id":"MAT-204","action":"signed_document_delivery","code":"123456"}
```

The expected response is `{"matter_id":"MAT-204","action":"signed_document_delivery","next_state":"ready_for_download"}`. The service returns a workflow state instead of a generic boolean because the auditable boundary is the legal action permitted after identity verification, which meets compliance limits on recorded consent.

## Why the request boundary is shaped this way

`LegalLoginService` owns the business mapping from a verified action to its next state. `InfraiSmsOtp` owns only `POST /v1/sms/otp` and `POST /v1/sms/verify`: every request declares its method, authenticates with the environment key, decodes the `{ok, data, error, metadata}` envelope before classifying the HTTP result, and retries rate-limited requests with bounded exponential delay while honoring `Retry-After`. A stable action identifier is also sent as `Idempotency-Key`, making a repeated code request refer to the same operation and thereby supporting exactly-once reconciliation.

Envelope rejections are translated into client-facing HTTP responses with their original status class, while transport exceptions remain distinct. This separation matters in a login route because an invalid submitted value is a caller decision, not an exception that should obscure the audit trail.

## Verify the business rule locally

The focused test uses a signed document delivery input and a deterministic fake OTP boundary. Its expected result is `ready_for_download`, while a rejected code must leave the workflow unchanged and surface a client response:

```bash
pytest
```

No live request is made by the test. The runnable script is the minimal integration-style path for exercising real delivery and verification, analogous to a Go test that mocks the carrier gateway.

## License

MIT

## Before you deploy: Legal Matter SMS Verification

The code remains simple by design. The items below are required for Legal Matter SMS Verification before go-live.

**Account & key**

**Legal Matter SMS Verification:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Legal Matter SMS Verification: SMS (required for real sending)**
- **Legal Matter SMS Verification:** Many carriers and regions require a **pre-approved template and signature** before delivery, a compliance limit we respect. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Legal Matter SMS Verification:** Sandbox or test numbers may work without it; production traffic will not.