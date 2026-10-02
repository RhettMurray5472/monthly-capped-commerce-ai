from __future__ import annotations

from typing import Literal, Protocol

from openai import OpenAI
from pydantic import BaseModel, Field


OrderAction = Literal["checkout", "fulfillment", "receipt", "order_update"]


class BudgetRequest(BaseModel):
    hard_cap_usd: float = Field(gt=0)
    alert_threshold_usd: float | None = Field(default=None, gt=0)


class OrderRequest(BaseModel):
    order_id: str = Field(min_length=1, max_length=80)
    action: OrderAction
    customer_message: str = Field(min_length=1, max_length=2000)


class OrderResult(BaseModel):
    order_id: str
    action: OrderAction
    response: str


class TextGenerator(Protocol):
    def generate(self, prompt: str) -> str:
        raise RuntimeError("protocol method called directly")


class OpenAIOrderWriter:
    def __init__(self, api_key: str, base_url: str) -> None:
        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    def generate(self, prompt: str) -> str:
        completion = self._client.chat.completions.create(
            model="auto",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Write a concise e-commerce operational response. "
                        "Minimize personal data and never infer health information."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        return completion.choices[0].message.content or ""


class OrderWorkflow:
    def __init__(self, writer: TextGenerator) -> None:
        self._writer = writer

    def run(self, request: OrderRequest) -> OrderResult:
        prompt = (
            f"Order {request.order_id}; action={request.action}; "
            f"customer context={request.customer_message}"
        )
        return OrderResult(
            order_id=request.order_id,
            action=request.action,
            response=self._writer.generate(prompt),
        )
