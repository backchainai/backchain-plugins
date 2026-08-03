# Reference

A working reader consults a reference to look up a fact about the system while mid-task, not to be taught, walked through a task, or persuaded of a design choice.

## Key principles

- Reference describes the system's parts neutrally: what exists, what it accepts, what it returns, with no narration of a task around it.
- It is structured to mirror the product itself, one entry per command, endpoint, field, or option, so the layout matches what the reader is looking up.
- It states facts and nothing else: no rationale, no opinion, no history, no "you might want to."
- It is optimized for lookup, not for reading start to finish; a reader should be able to jump to one entry and find a complete answer there.
- Every entry is complete on its own terms: if it documents a command's flags, it documents all of them, not a representative sample.
- It carries no implicit order; entries can be alphabetical, grouped by category, or otherwise organized, but the reader never has to read entry three to understand entry one.
- Consistency across entries matters more than any single entry's polish; the same kind of fact appears in the same place in every entry.
- It does not tell the reader what to do; it tells the reader what is true.

## Language markers

- Neutral declarative statements: "accepts an integer between 1 and 100," not "you can pass a number here if you want."
- Present tense, third person, describing the system as it currently behaves: "returns," "accepts," "defaults to."
- No second-person imperative verbs of the how-to kind ("run", "configure") except inside a signature or example block.
- No causal connectives (because, in order to, so that); if a sentence needs one, the content belongs in explanation, not reference.
- Consistent field labels across entries: the same word for "default," "type," or "required" everywhere it appears.

## What it is not

- **Not a how-to guide.** Reference has no goal and no sequence; a how-to has both. Test: does the reader want a fact, or a path to an outcome?
- **Not a tutorial.** Reference assumes the reader can already navigate the system; a tutorial assumes they cannot yet and teaches them to.
- **Not an explanation.** Reference states what is true without saying why; an explanation exists specifically to say why, and admits opinion and alternatives reference never does. Test: is the reader at work looking something up, or away from work building understanding?

## Shape on the page

Reference typically opens with a short statement of what the page documents (a command, an API surface, a config schema) and then proceeds entry by entry in a consistent structure: name, description, parameters or fields, return value or effect, and an example only if the example clarifies the signature rather than narrating a task. There is no goal statement, no numbered task sequence, and no closing "next steps."

## What reference guarantees the reader

- Every field, flag, parameter, or option that exists is documented somewhere on the page; nothing is left out because it seemed minor.
- The same fact never contradicts itself between two entries or between the reference page and the system's actual behavior at the version documented.
- A reader can enter at any single entry, with no prior reading of the page, and get a complete answer for that entry.
- No entry requires the reader to already understand another entry to make sense of it, beyond genuinely shared vocabulary defined once at the top.

## Signs a draft has drifted out of mode

- A sentence starting with "you'll want to" or "if you're trying to" has drifted toward a how-to; keep the fact, cut the task framing, and link to a how-to if the task is worth covering.
- A sentence starting with "the reason this exists is" has drifted toward an explanation; extract it to its own explanation page and link it from the entry.
- A worked walkthrough spanning several paragraphs has drifted toward a tutorial or how-to; keep a short signature example and move the walkthrough out.
- An entry that's incomplete because "the common case is enough" has drifted away from reference's core guarantee of completeness; finish the entry or flag the gap explicitly.

## Common mistakes

- Writing reference entries in the order a tutorial would introduce them, rather than in an order suited to lookup, forces every reader to scan past irrelevant entries.
- Leaving a field's default value unstated because it "should be obvious" breaks the guarantee that every entry is complete on its own.
- Mixing a task-oriented example ("first do this, then that") into an entry blurs reference into how-to for that one entry, even if the rest of the page stays clean.
- Describing what a field "usually" does, instead of what it does, introduces ambiguity a reference page exists to remove.

## A short example contrast

A reference entry reads: "`--timeout <seconds>`: sets the request timeout. Type: integer. Default: 30. Range: 1-300." It states facts, in a fixed structure, with no narration.

The same content written for a how-to would instead read: "If requests are timing out, increase the value with `--timeout <seconds>`; try 60 first." That sentence assumes a task and a symptom, neither of which belongs in a neutral description of the flag.

## Checking a draft against this file

- Confirm no entry contains a rationale sentence; if one appears, it belongs in explanation, linked rather than inlined.
- Confirm no entry assumes a specific task is underway; if one does, it belongs in a how-to.
- Confirm every documented command, field, or endpoint lists all of its options, not a subset.
- Confirm the same kind of fact (default, type, required) appears in the same position across every entry on the page.
