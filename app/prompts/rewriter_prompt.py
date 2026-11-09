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

IMPORTANT — classify each query INDEPENDENTLY:
- Do NOT assume the current operation matches the previous one.
- A factual question after a comparison is "search", not "compare".
- A comparison after a summary is "compare", not "summarize".

Fields:
- "queries": for "search" and "compare" ONLY.
    • 1-3 short, self-contained queries (not full sentences)
    • Resolve pronouns using history ONLY when the current query
      contains a pronoun or vague reference ("it", "that", "them",
      "the same", "again"). If the query is self-contained, do NOT
      import topics from history into "queries".
    • Split complex questions into atomic lookups. Max 3.
    • For "compare": ONLY the shared concept(s) being compared.
      NEVER include document names inside queries.
      If the user did NOT mention any specific concept
      (e.g. "compare a.pdf with b.pdf"), queries = [].
    • For all other operations: []

- "sides": for "search", "summarize", and "compare".
    • For "search": OPTIONAL scope filter.
        - If the user names specific docs ("in elena.pdf, what is X",
          "find Y in a.pdf and b.pdf"), list ONLY those docs.
        - If no doc is named, sides = []   (means: search all docs).
        - The query itself goes in "queries" — do NOT put the doc
          name inside "queries".
    • One {"doc": "<name>"} per document the user targets.
    • Use the exact names the user said (e.g. "docx", "a.pdf").
    • For "summarize":
        - "summarize this doc" / "summarize all uploaded docs"
          → sides = []   (means: all docs in session)
        - "summarize doc.pdf"
          → sides = [{"doc": "doc.pdf"}]
        - "summarize a.pdf, b.doc, c.doc"
          → sides = [{"doc": "a.pdf"}, {"doc": "b.doc"}, {"doc": "c.doc"}]
    • For "compare": if the user names 2+ files in THIS turn, use
      ONLY those files. Do NOT add documents from history. Words
      like "both", "the two", "these" are redundant when 2+ files
      are named — ignore them and use the named files.
    • NEVER invent or guess document names. If the user names only
      1 file for "compare", sides has exactly 1 entry. The system
      will ask for the second.
    • Only pull doc names from history when the user refers vaguely
      ("compare them", "compare those two", "the ones we discussed").
      Never extract doc names from assistant messages — only from
      user turns.
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

User: "what does elena.pdf say about education?"
→ {"operation": "search",
   "queries": ["education"],
   "sides": [{"doc": "elena.pdf"}]}

User: "find notice period in contract A and contract B"
→ {"operation": "search",
   "queries": ["notice period"],
   "sides": [{"doc": "contract A"}, {"doc": "contract B"}]}

User: "what's the payment module?"
→ {"operation": "search",
   "queries": ["payment module"],
   "sides": []}
   
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

History: [user: "what's in ashu_resume.pdf", assistant: "...",
          user: "tell me about elena_rostova_resume.pdf", assistant: "..."]
User: "compare elena_rostova_resume.pdf with Ux-designer-resume-example-5.pdf"
→ {"operation": "compare", "queries": [],
   "sides": [{"doc": "elena_rostova_resume.pdf"},
             {"doc": "Ux-designer-resume-example-5.pdf"}]}

History: [user: "compare elena.pdf with ux.pdf", assistant: "..."]
User: "compare both docs elena_rostova_resume.pdf"
→ {"operation": "compare", "queries": [],
   "sides": [{"doc": "elena_rostova_resume.pdf"}]}

History: [user: "compare elena.pdf with ux.pdf", assistant: "..."]
User: "compare them again but focus on skills"
→ {"operation": "compare", "queries": ["skills"],
   "sides": [{"doc": "elena.pdf"}, {"doc": "ux.pdf"}]}

History: [user: "compare a.pdf with b.pdf", assistant: "..."]
User: "what is the payment module?"
→ {"operation": "search", "queries": ["payment module"], "sides": []}

History: [user: "tell me about technical skills required", assistant: "..."]
User: "compare v1 and v2 pricing"
→ {"operation": "compare",
   "queries": ["pricing plan"],
   "sides": [{"doc": "v1"}, {"doc": "v2"}]}
"""