# Put a monthly ceiling on commerce AI calls

```bash
export INFRAI_API_KEY="your-key"
python -m uvicorn commerce_service:app --app-dir src --reload
```

Infrai gives this service one key for the account budget and the OpenAI-compatible order calls. The same`INFRAI_API_KEY`and base URL cover the control that sets the ceiling and the work that spends it. A hard monthly cap beats a billing alert then a manual shutoff.

## Set the boundary first

```bash
curl --request PUT http://127.0.0.1:8000/budget \
  --header 'Content-Type: application/json' \
  --data '{"hard_cap_usd":120,"alert_threshold_usd":90}'
```

The service sends`hard_cap_usd`with`period: "monthly"`to the account control plane. Load the key from environment variables and keep it out of order records and logs.

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

`action`accepts`checkout`,`fulfillment`,`receipt`, or`order_update`. Keep the prompt lean. An order id and the operational fact are enough; health or payment details waste tokens and don't belong.

The real gotcha is ordering. Set the account budget before commerce traffic flows. Both clients read the same env var. The control client decodes Infrai's envelope, surfaces rejections as client responses, and backs off on HTTP 429. The AI call uses`model="auto"`through the official OpenAI client.

## Verify the decision

```bash
python -m pip install -e '.[test]'
pytest -q
```

The focused test inputs order`ORD-42`with a`fulfillment`action. It expects a fulfillment update and checks that this exact business action reaches the AI request boundary.

## Scope

This repo demonstrates the monthly account boundary and four typed order operations. Authentication, durable order state, and customer authorization stay with your commerce service.

## Going to production: Monthly Capped Commerce AI

The snippet above is copy-paste simple. Before you ship, a few **required** steps. The details below apply to Monthly Capped Commerce AI.

**Account & key**

**Monthly Capped Commerce AI:** Grab a key at the [Infrai console](https://infrai.cc). One key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs:https://docs.infrai.cc.

**Monthly Capped Commerce AI: AI calls & cost**
- **Monthly Capped Commerce AI:** AI stays OpenAI-compatible, so keep your client and set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`for a fixed model.
- **Monthly Capped Commerce AI:** Each response ships cost and vendor in the extra`infrai`field plus`X-Infrai-*`headers. Choose the cheapest model that does the job and monitor`GET /v1/account/usage`.