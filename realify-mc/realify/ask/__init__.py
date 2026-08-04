"""Ask — the agent-shaped conversational home.

An agent skeleton, not a chatbot echo: a question routes through a `tools` layer that reads the tenant's
REAL data (the same domain code the cards use), a `context` pack is assembled, and a provider-agnostic
`narrator` composes the answer as structured parts. Today the narrator is a data-grounded STUB; a
self-hosted model drops in behind the same `Narrator` protocol with no contract change. `service`
orchestrates one turn and yields SSE frames; `models` is the picker registry; `CATEGORY_QUESTIONS` are
the curated seed questions.
"""
