# How-to guide

A working reader who already has the underlying skill reads a how-to guide to get through one specific task, not to learn the subject or to look up every option along the way.

## Key principles

- A how-to serves a reader who already has the competence and a concrete goal; it does not re-teach fundamentals the reader is assumed to have.
- The document is a sequence of actions toward one stated result, not a lesson and not an open-ended survey of the subject.
- It cuts anything the goal doesn't require: no background beyond what the task needs, no tangents, no justification the reader didn't ask for.
- It may branch on real conditions the reader is likely to hit ("if you're using X, do Y instead"), unlike a tutorial's single fixed path.
- It defers full option lists, complete flag tables, and exhaustive enumerations to reference, linking out rather than inlining them.
- It states the goal at the top so the reader can confirm this is the task they're trying to do before reading further.
- It assumes a working environment; it does not re-derive setup already covered by a tutorial or reference.
- It ends when the goal is reached; it does not continue into related tasks the reader didn't ask about.

## Language markers

- Imperative verbs driving each step: "run", "set", "configure", "verify" (commands to a reader who is already capable of acting on them).
- Conditional framing tied to real variation the reader might face: "if you want X, do Y" names a branch, not an open menu of unrelated options.
- Goal-first phrasing: "to rotate a key, do the following" states the destination before the steps, so the reader can confirm relevance immediately.
- Minimal hedging; a how-to states what to do, not a survey of ways it could theoretically be done.
- References to specific values, flags, or fields point outward ("see the reference for the full list") rather than reproducing them inline.

## What it is not

- **Not a tutorial.** A how-to assumes competence a tutorial exists to build; test: could the reader already do this if simply told the goal, or do they need to be taught the underlying skill first?
- **Not a reference.** A how-to sequences actions toward one outcome; a reference has no sequence and no single outcome, only facts organized for lookup from any entry point.
- **Not an explanation.** A how-to tells the reader what to do; an explanation tells the reader why the system works the way it does, with no obligation to produce an action at all.

## Shape on the page

A how-to guide typically opens with a one-line statement of the goal, optionally a short prerequisites list, then a numbered sequence of steps. Branches, where they exist, are marked clearly as conditional on something the reader can check about their own situation. The guide ends with a way to confirm the goal was reached, and stops: no unrelated follow-up tasks folded in because they happened to be nearby.

## What a how-to guide guarantees the reader

- A path from their current, already-competent state to one named goal, with nothing extraneous in between.
- Every step assumes only what a competent user of the system would already have or know.
- Branches, when present, are triggered by something the reader can actually observe about their own situation, not by taste.
- A way to verify the goal was reached that doesn't require guessing whether the steps "probably" worked.

## Signs a draft has drifted out of mode

- A step that stops to teach a concept the reader is assumed to already know has drifted toward a tutorial; move the teaching to its own tutorial and assume the competence here.
- A paragraph of rationale for why the task matters or why the system is built this way has drifted toward an explanation; extract it and link it, don't delete it.
- A step that lists every possible value for a field, rather than the one the task needs, has drifted toward a reference; keep the one value and link out for the rest.
- Two unrelated goals combined into one guide because they happen to touch the same feature have drifted into scope creep; split into two how-tos, one goal each.

## Common mistakes

- Writing steps that only work for one configuration and presenting them as universal, with no branch for the reader who differs, breaks the guide silently for part of the audience.
- Padding the guide with background paragraphs "for context" turns a fast task into a slow read for a reader who came in already knowing the context.
- Omitting the verification step leaves the reader unsure whether they succeeded, which defeats the guide's purpose even if every action was correct.
- Bundling optional steps in with required ones, without marking which is which, forces every reader through work only some of them need.

## Checking a draft against this file

- Confirm the opening line states a goal, not just a topic.
- Confirm every step is an action, not an explanation dressed up as one.
- Confirm any branch is tied to something observable, not to reader preference alone.
- Confirm the guide ends with a check the reader can perform, and stops there.

## A short example contrast

A how-to step reads: "To rotate a key, run `keys rotate --id <key-id>` and update any service still referencing the old ID." It states the goal in the header, gives the exact command, and names the one follow-up action the task requires.

The same content written for a reference would instead describe `keys rotate` on its own, neutrally: its flags, its exit codes, what it accepts as input, with no goal statement and no assumption that the reader is mid-task rotating anything right now.
