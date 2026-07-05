## Notes

- To run this app
`uv run uvicorn main:app --reload`
- Ensure the AIPIPE TOKEN is set in the terminal in which the server is running
`export AIPIPE_TOKEN="your-aipipe-token-here"
- Build command in Render
`uv sync --frozen && uv cache prune --ci`
- Start command in Render
`uv run uvicorn main:app --host 0.0.0.0 --port $PORT --reload`
