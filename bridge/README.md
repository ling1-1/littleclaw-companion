# OpenClaw Bridge

This directory holds the reusable bridge layer between Companion and OpenClaw.

Responsibilities:
- send text and attachments to current OpenClaw chat
- dispatch learn / screenshot actions
- collect final assistant replies
- normalize bridge results for the UI

Current structure:
- `direct_send.py`: reusable direct-send bridge logic
- `direct_send_openclaw.py`: thin runtime entrypoint
- some orchestration still remains in `companion_webview.py`

Open-source note:
- this directory is part of the distributable runtime
- local absolute paths should not be introduced here
