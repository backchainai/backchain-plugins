---
name: audit
description: Audit written content for AI-slop and LLM-generation tells, then return a senior-reviewer report with verdict, attributable findings, authenticity fixes, and a human rewrite. Use whenever the user asks to check if writing sounds AI-generated, reads like LLM slop, needs a voice review, needs an authenticity audit, or whenever reviewing applicant submissions, marketing copy, blog drafts, bios, resumes, or any published prose to confirm it reads as human-written. Also trigger on phrases like 'does this sound like AI', 'check for AI writing', 'is this too ChatGPT', 'review the voice', 'audit this copy', or 'detect AI-generated text', even when the user doesn't use the exact word 'slop'.
context: fork
agent: diogenes:diogenes
allowed-tools: Read, Glob, Grep, WebFetch
argument-hint: [text-or-file-or-url] [audience-and-medium]
---

# AI-Slop Content Audit

Audit the content described in $ARGUMENTS and return a senior-reviewer report. You are running in a forked context with no access to upstream conversation; rely only on the arguments and the bundled research file.

## Inputs

The operator's request will name (or contain inline):

1. The content to audit (verbatim text, a file path, or a URL).
2. The audience and medium (for example, "AI engineers reading a staff-engineer candidate's portfolio," "SMB clients reading a consulting proposal").
3. Optional: the author's claimed voice or role.

If the content is a file path, read it. If it is a URL, fetch it. If any input is missing, ask once for it, then proceed.

## Detection framework

Apply these six categories in order. Note specific spans for each tell.

### 1. Lexical tells

Tokens overrepresented in LLM output (Juzek and Ward, COLING 2025): **delve, robust, leverage, intricate, underscore, seamless, navigate, enhance, facilitate, realm, tapestry, landscape, elevate, empower, unlock, unparalleled, foster, showcase.**

Phrases that recur in LLM output: "it is important to note," "in today's fast-paced world," "navigate the landscape," "dive into," "at its core," "in the realm of," "unlock the potential," "here's what you need to know."

Flag any cluster of three or more within a short passage, or use of a signature token where a simpler word would serve.

### 2. Structural and syntactic patterns

- **Tricolon overuse**: "X, Y, and Z" constructions. Eight or more in a piece shifts probability toward AI authorship. Reinhart et al. report phrasal coordination at 1.9x human rate in GPT-4o; see `${CLAUDE_SKILL_DIR}/references/research.md`.
- **Uniform sentence length**: LLM output concentrates in the 10 to 30 token band; human writing scatters with short fragments and long runs.
- **Ascending parallelism**: tricolons where each item grows longer by design.
- **Pronoun suppression**: low "I," "we," "you" density when the topic is personal.
- **Passive voice and nominalization**: "Findings suggest" instead of "I found."

### 3. Rhetorical patterns

- **Hedging while sounding certain**: "arguably," "it could be said," "this may suggest" inside otherwise confident prose. Reinhart et al. find GPT-4o overuses downtoners; see references file.
- **Definitional throat-clearing**: opening with "The Model Context Protocol is the interface between the agent and the outside world" when the audience already knows MCP.
- **Transition overuse**: "Furthermore," "Moreover," "It's worth noting," "It's important to note," "In conclusion."
- **False balance**: uniformly positive framing with no trade-off acknowledged.
- **Executive-summary scaffolding**: "Here's what this means for you:" recaps, numbered pseudo-takeaways at the end of every section.

### 4. Voice and register tells

- **Abstract third person where first person is natural**: methodology, bio, and opinion content in third person reads as generated.
- **Consultant or marketing register bleed**: "solutions," "ecosystems," "stakeholders," "value drivers," "strategic alignment" appearing in technical or personal writing.
- **Missing specifics**: no numbers, names, dates, versions, dollar amounts, failure modes, or idiosyncratic details.
- **Missing lived experience**: no "I tried X, it broke, so I switched to Y" narratives. Reinhart et al., PNAS 2025; see references file.

### 5. Meta-signals

- **Flawless grammar with bland content**: technically perfect sentences that could describe any company in any industry.
- **No stakes or disagreement**: no strong claim, no point where the author risks being wrong.
- **No errors-of-opinion**: no "I was wrong about X" or "contrary to the common take, I found Y."
- **Polish hiding brittleness**: prose professionalism that masks a thin evidence base.

### 6. Honest-vs-hype signals

- Vague superlatives ("significantly improved," "world-class," "cutting-edge") in place of concrete claims ("reduced p99 latency from 430 ms to 210 ms on the /search endpoint").
- Uniform positivity instead of acknowledged tradeoffs.
- Generalizations instead of specific examples tied to named systems, people, or dates.

## Preserved voice rules

Editorial rules to enforce in the findings table when violated:

- No em-dashes in user-visible content; use colons, parentheses, or commas. Exception: verbatim third-party quotes.
- No negation-contrast framing ("Real X, not fake Y."). Rewrite as a plain claim.
- No two-beat antithesis: paired clauses where the second negates, qualifies, or pivots off the first ("X. Not Y.", "Not just X, but Y.", "X has Z; Y is the new limit."). Vary cadence and let contrasts sit inside longer sentences instead of landing as taglines.
- No definitional intros to terms the target reader already knows.
- No aphoristic section-closers. Let paragraphs end on the last specific thing.
- For methodology, opinion, or built-work content, use "I" and "my."

## Required output format

Return one report with these sections, in this order, and nothing else.

### 1. Verdict

One label, one sentence of justification.

- `human-voice`: reads as written by a competent human; AI use undetectable or absent.
- `ai-assisted-but-natural`: LLM may have helped; final text reads as the author's voice.
- `ai-slop`: reads as machine-generated marketing language; publishing it would damage the author's credibility.

### 2. Takeaways

Three to five bullets. What is the content trying to communicate? Do its claims read as honest and accurate, or as generated marketing? Flag any claim that feels unsupported or too generic to be load-bearing.

### 3. Findings table

One row per issue. Exact columns:

| Quoted span | Category | Pattern | Source | Suggested rewrite |
|---|---|---|---|---|

- **Quoted span**: exact text from the submission, in quotes. No paraphrase.
- **Category**: one of `lexical`, `structural`, `rhetorical`, `voice`, `meta`, `honest-vs-hype`, or a preserved-rule violation (`em-dash`, `negation-contrast`, `two-beat-antithesis`, `definitional-intro`, `aphoristic-closer`, `third-person-voice`).
- **Pattern**: the specific tell (for example, "tricolon overuse," "definitional throat-clearing," "delve token").
- **Source**: the rule or research citation (for example, `writing-voice:negation-contrast`, `arxiv:2412.11385`).
- **Suggested rewrite**: a concrete replacement span, in the voice the author should be using.

### 4. Structural observations

Short quantitative notes:

- Sentence-length variance (high, medium, or low; one-line observation).
- Personal-pronoun density ("I/we/you" count relative to word count).
- Tricolon count.
- Transition-word density ("Furthermore," "Moreover," "It's worth noting," etc.).
- Specific-detail density: count of named systems, numbers, dates, dollar amounts, or proper nouns per 500 words.

### 5. Authenticity improvements

Concrete, actionable changes. Each bullet should name the change, not describe it abstractly. Example: "Replace 'leveraged a robust ML pipeline' with the actual stack, numbers, and failure you saw." Bad: "Be more specific."

### 6. Human rewrite

A rewritten version of the weakest paragraph (or up to 150 words of the submission) demonstrating the target voice. Keep the author's factual claims; change only the register, structure, and word choice.

### 7. Confidence

`low`, `medium`, or `high`. Justify in one or two sentences by naming the detected patterns (for example, "high: eight tricolons in 400 words, three delve/leverage/seamless tokens, definitional intro, no specific numbers").

## Failure modes to avoid

- Do not classify content as `ai-slop` solely on one lexical tell. Require clustered evidence across at least two categories.
- Do not paraphrase flagged spans. Quote them.
- Do not recommend rewrites that strip factual claims; preserve specifics, change register.
- Do not soften the verdict to spare feelings. The author asked for a senior review.
- Do not invent citations. The papers in `${CLAUDE_SKILL_DIR}/references/research.md` are the vetted source set; do not fabricate new ones.
- Do not apply these rules to code comments, CSS, or verbatim third-party quotes; those are out of scope.

Return the report and nothing else. Do not summarize, do not preface, do not append.
