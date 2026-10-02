from capped_commerce.order_workflow import OrderRequest, OrderWorkflow


class RecordingWriter:
    def __init__(self) -> None:
        self.prompt = ""

    def generate(self, prompt: str) -> str:
        self.prompt = prompt
        return "Order ORD-42 is packed and ready for carrier pickup."


def test_fulfillment_action_produces_customer_safe_update() -> None:
    writer = RecordingWriter()
    result = OrderWorkflow(writer).run(
        OrderRequest(
            order_id="ORD-42",
            action="fulfillment",
            customer_message="Packed at the east warehouse",
        )
    )

    assert result.order_id == "ORD-42"
    assert result.action == "fulfillment"
    assert result.response == "Order ORD-42 is packed and ready for carrier pickup."
    assert "action=fulfillment" in writer.prompt

