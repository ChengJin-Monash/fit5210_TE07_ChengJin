#!/bin/bash
curl -X POST http://20.11.48.94:8001/chat_reset \
  -H "Content-Type: application/json" \
  -d '{"session_id": "all"}'
