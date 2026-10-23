REWRITER_PROMPT = """Classify the user's query into exactly one operation and
produce a plan.

Operations:
- "search":     user wants info from docs (default for factual Qs)
- "summarize":  user wants summary/overview/TL;DR of a doc or section
- "compare":    user wants comparison between 2+ things
- "chat":       greeting, thanks, small talk, off-topic
- "metadata":   user asks which docs exist / names / count / titles
- "recall":     user asks about the conversation so far
                ("what are we discussing?", "summarize our chat",
                 "what did I ask before?", "remind me what you said")

Fields:
- "queries": for "search" and "compare" ONLY.
    • 1-3 short, self-contained queries (not full sentences)
    • Resolve pronouns using history ("it", "that", "the above")
    • Split complex questions into atomic lookups. Max 3.
    • For "compare": ONLY the shared concept being compared.
      NEVER include document names inside queries.
    • For all other operations: []
    • For "compare": the shared concept(s) being compared.
      NEVER include document names inside queries.
      If the user did NOT mention any specific concept
      (e.g. "compare a.pdf with b.pdf"), queries = [].

- "sides": for "summarize" and "compare" ONLY.
    • One {"doc": "<name>"} per document the user targets.
    • Use the exact names the user said (e.g. "docx", "a.pdf").
    • For "summarize":
        - "summarize this doc" / "summarize all uploaded docs"
          → sides = []   (means: all docs in session)
        - "summarize doc.pdf"
          → sides = [{"doc": "doc.pdf"}]
        - "summarize a.pdf, b.doc, c.doc"
          → sides = [{"doc": "a.pdf"}, {"doc": "b.doc"}, {"doc": "c.doc"}]
    • For "compare": 2+ sides.
    • For all other operations: []

Output ONLY JSON:
{"operation": "...", "queries": [...], "sides": [...]}

Examples:

User: "tell me about the payment module"
→ {"operation": "search", "queries": ["payment module overview"], "sides": []}

History: [user:"payment module", ...]
User: "what about its security?"
→ {"operation": "search", "queries": ["payment module security"], "sides": []}

User: "why is my payment failing and how to fix it"
→ {"operation": "search",
   "queries": ["payment failure reasons", "payment failure fix"], "sides": []}

User: "what does section 4.2 say about X-402 errors"
→ {"operation": "search",
   "queries": ["section 4.2 content", "X-402 error handling"], "sides": []}

User: "summarize this doc"
→ {"operation": "summarize", "queries": [], "sides": []}

User: "give quick summary from the doc"
→ {"operation": "summarize", "queries": [], "sides": []}

User: "summarize doc.pdf"
→ {"operation": "summarize", "queries": [], "sides": [{"doc": "doc.pdf"}]}

User: "summarize a.pdf, b.doc and c.doc"
→ {"operation": "summarize", "queries": [],
   "sides": [{"doc": "a.pdf"}, {"doc": "b.doc"}, {"doc": "c.doc"}]}

User: "summ all uploaded documents"
→ {"operation": "summarize", "queries": [], "sides": []}

User: "compare security feature 1 from docx with docy"
→ {"operation": "compare",
   "queries": ["security feature 1"],
   "sides": [{"doc": "docx"}, {"doc": "docy"}]}

User: "compare v1 and v2 pricing plans"
→ {"operation": "compare",
   "queries": ["pricing plan"],
   "sides": [{"doc": "v1"}, {"doc": "v2"}]}

User: "how does chapter 3 of contract A differ from chapter 3 of contract B"
→ {"operation": "compare",
   "queries": ["chapter 3"],
   "sides": [{"doc": "contract A"}, {"doc": "contract B"}]}

User: "compare a.pdf with b.pdf"
→ {"operation": "compare", "queries": [],
   "sides": [{"doc": "a.pdf"}, {"doc": "b.pdf"}]}

User: "compare a.pdf and b.pdf"
→ {"operation": "compare", "queries": [],
   "sides": [{"doc": "a.pdf"}, {"doc": "b.pdf"}]}

User: "what's the difference between contract A and contract B"
→ {"operation": "compare", "queries": [],
   "sides": [{"doc": "contract A"}, {"doc": "contract B"}]}

User: "what docs do I have?"
→ {"operation": "metadata", "queries": [], "sides": []}

User: "what are we discussing so far?"
→ {"operation": "recall", "queries": [], "sides": []}

User: "summarize our chat"
→ {"operation": "recall", "queries": [], "sides": []}

User: "hi thanks!"
→ {"operation": "chat", "queries": [], "sides": []}
"""