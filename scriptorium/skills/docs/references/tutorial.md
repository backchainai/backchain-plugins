# Tutorial

A newcomer reads a tutorial to gain a skill through the experience of successfully doing something for the first time, not to look anything up or evaluate options.

## Key principles

- A tutorial is a learning experience, not a lookup tool and not a shortcut for a task the reader could already do.
- The reader succeeds by following the one path laid out, in order, without deciding anything along the way.
- Every step produces a concrete, visible result the reader can check against before moving to the next one.
- The tutorial offers no options: one way to do the thing, chosen for the reader in advance.
- Explanation stays minimal: enough to keep the reader oriented, not enough to interrupt the doing.
- The reader's attention belongs to the action in front of them, not to alternatives, edge cases, or what happens if something goes wrong in a way the tutorial didn't plan for.
- A tutorial builds confidence through a sequence of small, repeated successes, not through completeness of coverage.
- Nothing in a tutorial should require the reader to already know the subject; every prerequisite is either met by the tutorial itself or stated up front.

## Language markers

- Guided narration with an observable outcome named at each step: "you will see", "notice that", "your output should now read".
- Imperative instructions paired with a stated result, never left open-ended with no way to check success.
- The opening establishes the starting state explicitly; nothing about the reader's environment is assumed without saying so.
- No conditional branches ("if you want X instead, do Y") anywhere in the body; a tutorial has exactly one path from start to finish.
- Sentences stay short and sequential; the prose mirrors the order of the steps rather than jumping ahead or circling back.
- First person plural or second person address ("we'll", "you'll") carries the narration; the reader is never addressed as an abstract "the user."

## What it is not

- **Not a how-to guide.** A how-to serves a reader who already has the skill and wants a specific result; a tutorial serves a reader acquiring the skill for the first time. Test: does the reader need to be taught, or do they just need the steps?
- **Not a reference.** A tutorial narrates one path in a fixed order; a reference has no path at all, only an organized set of facts a reader can enter at any point and in any order.
- **Not an explanation.** A tutorial asks the reader to act and watch the result; an explanation asks the reader to sit with an idea away from any keyboard, with no action required.

## Shape on the page

A tutorial typically opens with one sentence stating what the reader will have built or done by the end, followed by any setup the tutorial handles itself. The body is a single numbered or otherwise strictly ordered sequence, each entry pairing one action with its visible result. The tutorial closes by confirming the end state matches what was promised at the start, and stops there: no "next steps" menu of options, at most a single link onward.

## What a tutorial guarantees the reader

- A working result at the end, produced by following exactly what's written, with no independent troubleshooting required.
- A starting point that doesn't assume anything the tutorial hasn't already provided or explicitly named as a prerequisite.
- A single, unambiguous next action at every point in the sequence; the reader never has to decide what to do next.
- Enough visible feedback at each step that the reader knows, without guessing, whether it worked.

## Signs a draft has drifted out of mode

- A step that asks the reader to choose between two approaches has drifted toward a how-to guide; extract the choice into its own how-to and pick one path for the tutorial.
- A paragraph explaining the internals behind a step has drifted toward an explanation; extract it into its own explanation page and link it, don't delete it.
- A step that lists every available flag for a command has drifted toward a reference; keep the one flag the tutorial needs and link to the reference for the rest.
- A troubleshooting subsection covering multiple possible failures has drifted toward a how-to; a tutorial handles the one path where things work, and a how-to (or an explanation of common failure modes) covers the rest.

## Common mistakes

- Writing a tutorial as a condensed how-to guide, with steps but no narration of what the reader should see, leaves a newcomer unable to tell success from failure.
- Adding a "why this works" aside after every step turns the tutorial into an explanation wearing a numbered list; move the asides to their own explanation page.
- Covering two related tasks in one tutorial ("set up a project, then also configure deployment") doubles the chance the reader loses the thread; one tutorial, one outcome.
- Assuming the reader has already installed a prerequisite without saying so anywhere in the document breaks the guarantee that the tutorial's starting point is self-contained.

## A short example contrast

A tutorial step reads: "Run `init --starter` and wait for the confirmation message; you should see `Project ready` printed to the terminal." It names one command, one flag, and one observable result.

The same content written for a how-to reader instead would read: "To scaffold a project, run `init` with either `--starter` or `--blank` depending on whether you want example files." That sentence offers a choice, which is exactly what a tutorial withholds from its reader until they've had at least one full success with the single supported path.

## Checking a draft against this file

- Read the draft top to bottom as if seeing it for the first time; note any point where a decision is required of the reader.
- Confirm every step names a result the reader can check, not just an action to perform.
- Confirm no paragraph exceeds a sentence or two of explanation before the narration resumes.
- Confirm the tutorial's closing line matches the outcome promised in its opening line.
- Confirm nothing in the body offers the reader a choice; if one appears, it belongs in a how-to guide instead.
