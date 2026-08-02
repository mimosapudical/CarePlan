"""Stub Lambda: generate care plan (no DB/SQS/LLM yet)."""


def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"ok": true, "function": "generate_careplan", "note": "stub only"}',
    }
