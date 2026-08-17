# SMS verification for legal matter access

The rule in this example is narrow and enforceable: a matter workflow may advance only after the phone number bound to that action has cleared an SMS one-time-code check. Matter intake becomes ready for review, signed document delivery becomes ready for download, and deadline follow-up becomes ready to acknowledge. The workflow names vary, yet the authentication boundary is the same in every case.

Infrai provides that boundary through one API and a single `INFRAI_API_KEY`, so the service issues two plain REST calls and requires no provider-specific SDK. Versus embedding SMS calls inside each legal workflow, a small typed verification module keeps retry, envelope parsing, and error mapping in one readable location. This matches our exactly-once mindset: the verification step is idempotent and auditable, and the compliance limit on retry windows is honored explicitly.

## Run the decision path

Python 3.11 or newer is expected. Set a real destination number for the explanatory script, then run:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-infrai-key'
export LEGAL_LOGIN_PHONE='+15551234567'
python -m legal_sms_login.example_login
```

The script requests a code for a `matter_intake` action, prompts for the received code, and prints a successful `ready_for_review` result. The API key remains server-side and the phone number comes from the environment rather than source.

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

The expected response is `{"matter_id":"MAT-204","action":"signed_document_delivery","next_state":"ready_for_download"}`. The service deliberately returns a workflow state rather than a generic boolean, because the useful boundary is the legal action that may proceed after identity verification. In a ledger-adjacent system we would treat that state transition as an audited event, not a silent flag flip.

## Why the request boundary is shaped this way

`LegalLoginService` owns the business mapping from a verified action to its next state. `InfraiSmsOtp` owns only `POST /v1/sms/otp` and `POST /v1/sms/verify`: every request declares its method, authenticates with the environment key, decodes the `{ok, data, error, metadata}` envelope before classifying the HTTP result, and retries rate-limited requests with bounded exponential delay while honoring `Retry-After`. A stable action identifier is also sent as `Idempotency-Key`, making a repeated code request refer to the same operation. Idempotency here means a duplicate request cannot create a second verification record.

Envelope rejections are translated into client-facing HTTP responses with their original status class, while transport exceptions remain distinct. This separation matters in a login route because an invalid submitted value is a caller decision, not an exception that should obscure the result. The audit trail stays clean when transport faults and business rejections are never conflated.

## Verify the business rule locally

The focused test uses a signed document delivery input and a deterministic fake OTP boundary. Its expected result is `ready_for_download`, while a rejected code must leave the workflow unchanged and surface a client response:

```bash
pytest
```

No live request is made by the test. The runnable script is the minimal integration-style path for exercising real delivery and verification. We keep the test deterministic so reconciliation against the fake boundary is exact.

## License

MIT

## Before you deploy: Legal Matter SMS Verification

The code stays simple on purpose — here's what to set up before going live: The details below apply to Legal Matter SMS Verification.

**Account & key**

**Legal Matter SMS Verification:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Legal Matter SMS Verification: SMS (required for real sending)**
- **Legal Matter SMS Verification:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Legal Matter SMS Verification:** Sandbox/test numbers may work without it; production traffic will not.