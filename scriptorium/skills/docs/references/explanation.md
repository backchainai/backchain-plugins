# Explanation

A reader who is away from the keyboard, thinking about the system rather than operating it, reads an explanation to understand why it works the way it does.

## Key principles

- Explanation discusses; it is the one mode that openly admits opinion, judgment, and alternatives rather than staying neutral.
- It gives history and context: why a decision was made, what was considered and set aside, what trade-off was accepted.
- It is bounded to one topic; a single explanation page argues one point or clarifies one area, not the whole system at once.
- It is read away from the work: the reader isn't mid-task, isn't about to run a command, and doesn't need the page to produce an action.
- It may compare the current design to alternatives, including ones that were rejected, in a way reference and how-to never do.
- It builds understanding that then informs decisions the reader makes later, rather than telling the reader what to do right now.
- It can be read start to finish as connected prose, unlike reference, which is read by jumping to one entry.
- It stays honest about uncertainty or disagreement where it exists, rather than presenting a single account as settled when it isn't.

## Language markers

- Causal and comparative connectives carry the argument: because, therefore, whereas, however, an alternative would be, this trades X for Y.
- First person or authorial voice is more at home here than in the other three modes, since explanation admits a point of view.
- Questions posed and then answered in the prose ("why not do X instead?") are a normal move; the other modes rarely pose open questions.
- References to history use past tense deliberately: "we originally tried X," "earlier versions did Y," marking what has changed and why.
- No imperative verbs directing the reader to act; nothing in explanation should read as an instruction to run or configure something.

## What it is not

- **Not a tutorial.** Explanation builds understanding without asking the reader to do anything; a tutorial exists entirely to produce a done action and a visible result.
- **Not a how-to guide.** Explanation has no goal to complete and no steps; a how-to is nothing but goal and steps.
- **Not reference.** Explanation admits opinion and stays bounded to one topic in connected prose; reference stays neutral and spans every entry a reader might look up. Test: is the reader at work looking something up, or away from work building understanding?

## Shape on the page

Explanation typically opens by naming the topic and the question it's going to address, then develops the discussion in ordinary prose sections, each building on the last. It may include a comparison table of alternatives, but the table serves the argument rather than standing alone as an enumeration. There is no numbered task sequence and no field-by-field enumeration standing in for the discussion.

## What explanation guarantees the reader

- A clear statement of the one topic the page addresses, so the reader can tell before finishing whether this is the discussion they wanted.
- Reasoning that connects a decision to the trade-off it made, not just an assertion that the decision was made.
- Honest treatment of alternatives that were considered, including ones the current design didn't choose.
- A page that stands on its own as something to read, not something the reader has to act on to get value from it.

## Signs a draft has drifted out of mode

- A numbered list of commands to run has drifted toward a how-to; extract it into its own how-to and keep the reasoning here.
- A complete table of every option a component supports has drifted toward reference; keep a short illustrative example if needed and link to reference for the rest.
- A walkthrough narrating one path step by step, with a visible result at each point, has drifted toward a tutorial; extract it and keep the discussion of why that path exists.
- A page trying to cover two unrelated design questions at once has drifted past its bound of one topic; split into two explanation pages.

## Common mistakes

- Presenting the current design as though no alternative was ever considered removes the honesty about trade-offs that gives explanation its value.
- Padding a discussion with step-by-step instructions "just so the reader can try it" turns the page into a how-to with commentary, satisfying neither mode well.
- Writing an explanation so broad it tries to cover an entire system's history and every design choice in it loses the one-topic boundary that keeps it readable.
- Stating a rationale as settled fact when it's actually one contributor's opinion, with no acknowledgment of disagreement, misrepresents the page's own honesty guarantee.

## A short example contrast

An explanation passage reads: "We chose polling over webhooks because our clients often sit behind firewalls that block inbound connections; webhooks would have required every client to expose a public endpoint, which most of our users can't do." It states a decision, a reason, and the alternative it displaced.

The same underlying fact written for reference would instead simply state: "The client polls the `/status` endpoint at a fixed interval; it does not accept inbound webhook calls." No reason, no alternative, just the current behavior.

## Checking a draft against this file

- Confirm the page states one topic up front and stays inside it.
- Confirm at least one alternative or trade-off appears somewhere in the discussion, if the topic has one.
- Confirm no numbered action sequence or exhaustive field table has crept in; either belongs elsewhere, linked from here.
- Confirm the reasoning, not just the conclusion, is present: a reader should understand why, not just what was decided.
