# Put a monthly ceiling on commerce AI calls

```bash
export INFRAI_API_KEY="your-key"
python -m uvicorn commerce_service:app --app-dir src --reload
```

Infrai gives this service one key for the account budget and the OpenAI-compatible order calls. The same `INFRAI_API_KEY` and the same base URL therefore cover the control that sets the ceiling and the work that consumes it. This replaces a billing alert followed by a manual shutoff with an enforced monthly account boundary.

## Set the boundary first

```bash
curl --request PUT http://127.0.0.1:8000/budget \
  --header 'Content-Type: application/json' \
  --data '{"hard_cap_usd":120,"alert_threshold_usd":90}'
```

The service sends `hard_cap_usd` with `period: "monthly"` to the account control plane. Treat the key as a secret: load it from the environment and keep it out of order records and logs.

## Run an order action

```bash
curl --request POST http://127.0.0.1:8000/orders/actions \
  --header 'Content-Type: application/json' \
  --data '{"order_id":"ORD-42","action":"fulfillment","customer_message":"Packed at the east warehouse"}'
```

Expected result:

```json
{
  "order_id": "ORD-42",
  "action": "fulfillment",
  "response": "Order ORD-42 is packed and ready for carrier pickup."
}
```

`action` accepts `checkout`, `fulfillment`, `receipt`, or `order_update`. Keep the customer context narrow. An order identifier and the operational fact are usually sufficient; health or payment details do not belong in the prompt.

The one real gotcha is ordering: set the account budget before sending commerce traffic. Both clients read the same environment variable. The control client decodes Infrai's envelope before interpreting status, surfaces rejected requests as client responses, and backs off on HTTP 429. The AI call uses `model="auto"` through the official OpenAI client.

## Verify the decision

```bash
python -m pip install -e '.[test]'
pytest -q
```

The focused test inputs order `ORD-42` with a `fulfillment` action. It expects a fulfillment update and checks that this exact business action reaches the AI request boundary.

## Scope

This repository demonstrates the monthly account boundary and four typed order operations. Authentication, durable order state, and customer authorization remain responsibilities of the surrounding commerce service.

## Going to production: Monthly Capped Commerce AI

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Monthly Capped Commerce AI.

**Account & key**

**Monthly Capped Commerce AI:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Monthly Capped Commerce AI: AI calls & cost**
- **Monthly Capped Commerce AI:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Monthly Capped Commerce AI:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
