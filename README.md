# backchain-plugins

Claude Code plugins by [Backchain](https://backchain.ai)

## Plugins

### [Advisors](./advisors)

**Team of Rivals**

AI assistants tend to agree with you, even when your idea is... ill-advised. This skill set provides a panel of role-specific advisory agents that argue from focussed perspectives. Inspired by Lincoln's executive cabinet strategy: appoint your most challenging opponents to senior roles, rather than loyalists, so you receive direct and honest feedback from different perspectives. They will disagree with each other and they will disagree with you. The result is synthesized into a single honest recommendation designed to help identify blind spots and promote critical thinking.

| Agent | Perspective |
|---------|-------------|
| **Visionary** | Expands possibilities, challenges constraints, identifies moonshot opportunities |
| **Skeptic** | Demands evidence, calculates failure probabilities, exposes hidden assumptions |
| **Operator** | Maps resources, identifies dependencies, grounds vision in execution reality |
| **Ethicist** | Evaluates stakeholder impact, assesses long-term consequences, applies moral frameworks |

## Installation

### From GitHub (recommended)

```
/plugin marketplace add backchainai/backchain-plugins
/plugin install advisors@backchain-plugins
```

### Local Development

```bash
git clone https://github.com/backchainai/backchain-plugins.git
/plugin marketplace add ./backchain-plugins
/plugin install advisors@backchain-plugins
```

## Usage

```
# Run the full advisory panel — all four advisors + synthesis
/advisory-panel consider my unrefined idea

# Or invoke individual advisors for focused analysis
/advisor-visionary "Should we build an in-house ML platform?"
/advisor-skeptic "Can we hit 10M users in 12 months?"
/advisor-operator "What's required to ship v2.0 by Q3?"
/advisor-ethicist "What are the implications of this data collection policy?"
```

The **advisory panel** runs all four advisors independently, then synthesizes their insights into a unified recommendation with areas of agreement, disagreement, and a risk-adjusted verdict.

Each **individual advisor** provides structured analysis through their specialized lens — designed for productive disagreement, not false consensus.


## Example
*(individual agent feedback removed here for brevity)*

❯ /advisors:advisory-panel We're considering building SaaS based cookie delivery platform

⏺ Reading the four advisor frameworks first.

  Read 4 files (ctrl+o to expand)

⏺ Launching all four advisor analyses in parallel.

⏺ 4 agents finished (ctrl+o to expand)
   ├─ visionary: Visionary advisor analysis · 0 tool uses
   │  ⎿  Done
   ├─ skeptic: Skeptic advisor analysis · 0 tool uses
   │  ⎿  Done
   ├─ operator: Operator advisor analysis · 0 tool uses
   │  ⎿  Done
   └─ ethicist: Ethicist advisor analysis · 0 tool uses
      ⎿  Done

⏺ Advisory Panel: SaaS Cookie Delivery Platform

  ---
  Synthesis

  Areas of Agreement

  Start small, prove demand before building software. All four advisors converge on a narrow geographic launch. The Visionary says "one
  college town," the Operator says "one ZIP code with a Shopify storefront," and the Skeptic's kill conditions all center on validating unit
   economics before scaling. Even the Ethicist frames local bakery partnerships as the ethical foundation. Consensus: **do not build a
  platform until the delivery model works manually**.

  Unit economics are the make-or-break question. The Visionary, Skeptic, and Operator all flag that **delivery cost on a low-ticket perishable
   item is the central risk.** The Operator sets the bar at 60%+ gross margin; the Skeptic says if average order value stays under $20, the
  model is unworkable. This is the single most important variable to validate.

  Food safety and regulatory compliance are non-negotiable. The Operator identifies **food permits as the zero-slack critical path** item. The
  Ethicist elevates **allergen transparency and food safety** as ethical imperatives. The Skeptic notes each new market is a "compliance
  restart." Three advisors agree: this is not a software problem, it's a licensed food operation first.

  Areas of Disagreement

  Scale ambition vs. reality. The Visionary sees cookies as a wedge into a $400B last-mile logistics platform. The Skeptic sees "a logistics
   company with a website" with a 2-5% base rate of reaching profitability. Root cause: fundamentally different reference classes. The
  Visionary compares to Amazon's book wedge; the Skeptic compares to the graveyard of food delivery startups. Both are valid -- the question
   is which reference class you're actually in.

  "SaaS-based" as a concept. The Skeptic directly challenges whether the SaaS framing adds any value -- **"unable to articulate why this
  requires software rather than a bakery with a phone number"** is a kill condition. The Visionary assumes the platform layer is the entire
  point. This disagreement exposes an unresolved question: **is this a tech company or a food company** that uses technology?

  Critical Callouts

  - Visionary: Cookies are the wedge product, not the business -- the real opportunity is owning hyperlocal perishable logistics
  infrastructure.
  - Skeptic: A $5 cookie becomes $15 delivered -- who is this customer, and does the demand density exist to make routes viable?
  - Operator: You cannot ship a single cookie without health department approval -- food safety compliance is the critical path, not
  software.
  - Ethicist: The platform's ethical standing hinges on how it treats delivery workers -- plan for employee classification, not gig labor.

  Risk-Adjusted Recommendation

  Confidence Level: MEDIUM

  Key Conditions:
  1. Average order value must exceed $25 (bundle, gifting, or corporate orders -- not single cookies)
  2. Gross margin per delivered order must hit 50%+ within 90 days of concierge operation
  3. Validate demand with zero custom software -- Shopify storefront, manual coordination, contract delivery
  4. Secure food safety permits and commercial kitchen partnership before taking a single order

  Primary Risk:
  Delivery economics on a low-ticket perishable item never reach profitability at the volumes achievable in a single market.

  Recommended Next Step:
  Run a 30-day concierge test in one dense neighborhood -- take orders via a free Shopify store, bake in a rented commercial kitchen,
  deliver personally or via a single contract driver -- and measure order value, repeat rate, and true cost per delivery before investing in
   any technology.

  Rationale:
  The Visionary's platform vision is genuinely compelling but is a Phase 3 conversation -- irrelevant until the Skeptic's core challenge is
  answered: do the unit economics work for delivering cookies? The Operator provides the playbook: concierge first, automate later. The
  Ethicist's concerns (labor, local partnerships, food safety) are easily addressable at small scale and become differentiators if handled
  well. The entire decision hinges on a $500 experiment, not a $500K software build.
