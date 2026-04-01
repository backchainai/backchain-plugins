# Operator References

## Execution Patterns

### Pattern 1: Crawl-Walk-Run
**Phase 1 (Crawl)**: Manual process, 10 customers
**Phase 2 (Walk)**: Semi-automated, 100 customers  
**Phase 3 (Run)**: Fully automated, 1000+ customers

### Pattern 2: Concierge MVP
1. Do it manually for first customers
2. Document exactly what you do
3. Automate only repeated tasks
4. Scale only proven processes
5. Maintain manual override capability

### Pattern 3: Time-boxed Experiments
- Hypothesis: Clear success criteria
- Timeline: Maximum 30 days
- Budget: Maximum 10% of runway
- Decision: Continue, pivot, or kill
- Learning: Document for next iteration

## Operational Calculations

### Build vs Buy Decision
```
Build Cost = Development Time × Team Cost + Maintenance Forever
Buy Cost = License Fees + Integration Cost + Vendor Risk
Decision: Build only if core differentiator
```

### Hiring Timeline Reality
```
Time to Hire = Req Approval (1w) + Sourcing (3w) + 
                Interviews (3w) + Decision (1w) + 
                Start Date (3w) + Ramp (12w)
Total: 23 weeks minimum for productivity (typical for full-time hires in mid-to-large organizations; adjust significantly for contractors or smaller teams)
```

### Technical Debt Accumulation

Monitor technical debt through observable indicators:
- Velocity reduction over time (sprints taking longer for similar work)
- Time spent on rework vs. new features
- Complexity growth in critical paths
- Frequency of production incidents from existing code

Establish team-specific thresholds for when debt remediation takes priority over new work.

## Resource Efficiency Frameworks

### Lean Operations
- Eliminate: What can we stop doing?
- Automate: What can machines do?
- Delegate: What can others do cheaper?
- Optimize: What must we do better?

### Capital Efficiency
- Revenue per dollar raised
- Months to cash flow positive
- LTV/CAC ratio (SaaS benchmarks — adjust for your business model)
- Gross margin (SaaS benchmarks — adjust for your business model)
- Sales efficiency

### Time Efficiency
- Cycle time reduction
- Batch size optimization
- Queue management
- Work in progress limits
- Continuous deployment

## Operational Red Flags

### Resource Flags
- Single points of failure (bus factor = 1)
- Burn multiple increasing
- Hiring ahead of revenue
- Infrastructure before users
- Premature optimization

### Process Flags
- No customer feedback loops
- Long release cycles (>2 weeks)
- Manual processes at scale
- No metrics tracking
- Decisions without data

### Execution Flags
- Feature creep
- Scope expansion
- Timeline slippage
- Quality shortcuts
- Communication breakdown
