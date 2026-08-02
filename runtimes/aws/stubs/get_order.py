"""Stub Lambda: get order / care plan status (no DB yet)."""


def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"ok": true, "function": "get_order", "note": "stub only"}',
    }
