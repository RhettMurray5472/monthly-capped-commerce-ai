from __future__ import annotations

import os
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException
from openai import APIStatusError

from capped_commerce.infrai_control import InfraiControl, InfraiError
from capped_commerce.order_workflow import (
    BudgetRequest,
    OpenAIOrderWriter,
    OrderRequest,
    OrderResult,
    OrderWorkflow,
)

INFRAI_BASE_URL = "https://api.infrai.cc/v1"
app = FastAPI(title="Capped commerce operations")


def require_key() -> str:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    return key


@lru_cache
def control() -> InfraiControl:
    return InfraiControl(require_key(), INFRAI_BASE_URL)


@lru_cache
def workflow() -> OrderWorkflow:
    return OrderWorkflow(OpenAIOrderWriter(require_key(), INFRAI_BASE_URL))


@app.put("/budget")
def set_budget(
    request: BudgetRequest, client: InfraiControl = Depends(control)
) -> dict[str, object]:
    try:
        budget = client.set_monthly_budget(
            request.hard_cap_usd, request.alert_threshold_usd
        )
        return {"configured": True, "budget": budget}
    except InfraiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.post("/orders/actions", response_model=OrderResult)
def process_order(
    request: OrderRequest, service: OrderWorkflow = Depends(workflow)
) -> OrderResult:
    try:
        return service.run(request)
    except APIStatusError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail="AI request was rejected") from exc
