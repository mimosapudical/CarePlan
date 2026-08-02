"""Stub Lambda: create order (no DB/SQS yet)."""


def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"ok": true, "function": "create_order", "note": "stub only"}',
    }
