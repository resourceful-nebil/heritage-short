# One command for the whole film: `make film` (needs uv: https://docs.astral.sh/uv/ ; FFmpeg on PATH; keys in .env)
# Windows without make: `uv run python -m pipeline film`
PY = uv run python -m pipeline

.PHONY: film radio smoke validate keyframes narration costs
film:      ; $(PY) film
radio:     ; $(PY) radio
smoke:     ; $(PY) smoke
validate:  ; $(PY) validate
keyframes: ; $(PY) keyframes
narration: ; $(PY) narration
costs:     ; $(PY) costs
