# Research References

The audit-ai-slop skill cites three peer-reviewed papers. This file holds a short summary of each, the specific LLM-generation signals each one identified, and direct links. Treat this set as vetted. Audit findings should cite from here, not invent new sources.

---

## 1. Juzek & Ward (COLING 2025), "Why Does ChatGPT 'Delve' So Much?"

- Title: *Why Does ChatGPT "Delve" So Much? Exploring the Sources of Lexical Overrepresentation in Large Language Models*
- Authors: Tom S. Juzek, Zina B. Ward
- Venue: 31st International Conference on Computational Linguistics, 2025
- arxiv: https://arxiv.org/abs/2412.11385

### Summary

The authors quantify how often a fixed set of "focal words" appears in post-ChatGPT scientific abstracts compared with a pre-ChatGPT baseline, then test whether model architecture, training data, or RLHF accounts for the shift. RLHF correlates with overuse, but model-development opacity prevents a clean causal claim. The contribution is the empirical list of 21 lexical items whose frequency jumped after late 2022, plus a documented structural pattern: abstracts containing a focal word tend to place it in the very first sentence.

### Top 20 signals

1. delve
2. delves
3. delved
4. delving
5. showcasing
6. showcases
7. boasts
8. underscores
9. underscoring
10. underscore
11. comprehending
12. intricacies
13. intricate
14. surpassing
15. surpasses
16. garnered
17. emphasizing
18. realm
19. groundbreaking
20. advancements

Paper's 21st focal word: "aligns." Paper also reports a "delve-initial" structural pattern: more than half of abstracts containing a focal word place it in the first sentence (often "This study delves into...").

---

## 2. Muñoz-Ortiz, Gómez-Rodríguez & Vilares (AI Review 2024), "Contrasting Linguistic Patterns in Human and LLM-Generated News Text"

- Title: *Contrasting Linguistic Patterns in Human and LLM-Generated News Text*
- Authors: Alberto Muñoz-Ortiz, Carlos Gómez-Rodríguez, David Vilares
- Venue: Artificial Intelligence Review, 2024
- PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC11422446/

### Summary

The authors compare New York Times articles from October 2023 to January 2024 against outputs from six base LLMs (Llama 7B/13B/30B/65B, Falcon 7B, Mistral 7B) prompted with each headline plus the first three words of the lead paragraph. They analyze morphosyntax (POS distributions, dependency parses), lexical diversity, constituent structure, emotion classification, and gender-pronoun ratios. Human text wins on vocabulary breadth and syntactic efficiency. LLMs cluster sentence lengths, lean noun-light and aux-heavy, and shift the emotion profile toward neutrality and joy.

### Top 20 signals

1. Sentence-length distribution: human text spans short fragments through long runs; LLM text clusters in the 10 to 30 token band.
2. Vocabulary richness (STTR): humans 0.491; LLMs 0.424 (Falcon) to 0.466 (Llama).
3. Vocabulary richness (MTLD): humans 96.5; LLMs 57.4 (Falcon) to 94.6 (Llama).
4. Noun share of tokens: humans 19.7%; LLMs ~17.7%.
5. Adjective share: humans 7.6%; LLMs ~6.8%.
6. Pronoun share: humans 5.3%; LLMs 6.1% to 7.3%.
7. Auxiliary verb share: humans 3.8%; LLMs 5.4% to 6.0%.
8. Numbers and symbols overrepresented in LLM output (POS tags NUM, SYM).
9. Punctuation share roughly comparable: human 11.9%, LLM 10.8% to 12.2%.
10. Dependency-length optimization (Ω score) higher in human text: longer absolute dependencies but more efficient ordering.
11. Numeric modifier (nummod) dependencies overrepresented in LLM output.
12. Adjective modifier (amod) dependencies underrepresented in LLM output.
13. Appositional modifier (appos) dependencies underrepresented in LLM output.
14. Verb-phrase constituent share: LLM 20.0% to 20.6%; human 18.1%.
15. Noun-phrase constituent share: humans 42.9%; LLMs 40.0% to 41.4%.
16. Prepositional-phrase constituent share: humans 14.1%; LLMs 12.6% to 12.9%.
17. Subordinate clause (SBAR) overrepresented in LLM output.
18. Fear-tagged content underrepresented in LLM output (human 10.8%; LLM 8.3% to 9.3%).
19. Disgust-tagged content underrepresented in LLM output (human 9.4%; LLM 7.2% to 8.3%).
20. Joy-tagged content overrepresented in LLM output (human 8.3%; LLM 8.5% to 9.8%).

Also reported: LLMs lean toward "neutral" emotion classification overall (>53% vs human 52.2%); Llama models magnify male-to-female pronoun ratio by 14% to 17% over human baseline (1.71 → 1.86 to 1.89); Falcon reduces it by 7.5%.

---

## 3. Reinhart, Markey, Laudenbach, Pantusen, Yurko, Weinberg & Brown (PNAS 2025), "Do LLMs write like humans?"

- Title: *Do LLMs write like humans? Variation in grammatical and rhetorical styles*
- Authors: Alex Reinhart, Ben Markey, Michael Laudenbach, Kachatad Pantusen, Ronald Yurko, Gordon Weinberg, David West Brown
- Venue: Proceedings of the National Academy of Sciences, vol 122 (2025), e2422455122
- DOI: https://doi.org/10.1073/pnas.2422455122
- arxiv preprint: https://arxiv.org/abs/2410.16107

### Summary

The authors apply Douglas Biber's 66-feature tagset to a parallel corpus generated by Llama 3 base and instruction-tuned variants and by GPT-4o, prompted to continue real human passages "in the same style, tone, and diction." Base models track human feature distributions (a feature-based classifier hits ~75% accuracy separating them from human text). Instruction-tuned siblings diverge sharply (93% to 98% classifier accuracy). The takeaway: instruction tuning pushes generation toward an informationally dense, nominalized, present-participial register that does not appear at comparable rates in any human reference corpus.

### Top 20 signals

1. Present participial clauses: GPT-4o uses them at 5.3× the human rate (Cohen's d 1.38). Example: "Bryan, leaning on his agility, dances around the ring."
2. That-clauses as subject: GPT-4o 2.6× human rate (d 0.77).
3. Nominalizations: GPT-4o 2.1× human rate (d 1.23). Example: "deforestation, habitat destruction, and pollution."
4. Phrasal coordination: GPT-4o 1.9× human rate (d 0.81).
5. Clausal coordination: Llama 3 instruct variants exceed human rate; GPT-4o suppresses it.
6. Downtoners (barely, nearly): both GPT-4o variants overuse.
7. Agentless passive voice: GPT-4o at ~50% of human rate (underuse).
8. Obscenities: instruction-tuned models 100× below human rate.
9. GPT-4o lexical overuse: camaraderie 162×.
10. GPT-4o lexical overuse: tapestry 155×.
11. GPT-4o lexical overuse: intricate 119×.
12. GPT-4o lexical overuse: underscore 107×.
13. GPT-4o lexical overuse: unspoken 102×.
14. GPT-4o lexical overuse: amidst 100×.
15. GPT-4o lexical overuse: palpable 95×, solace 95×, fleeting 84×, unravel 83×.
16. Llama 3 70B Instruct lexical overuse: unease 63×, palpable 47×, continuation 29×, shoutout 28×, pang 25×, camaraderie 24×, prioritize 24×.
17. Base models stay near human feature rates; instruction-tuned siblings drift far. The base-vs-instruct gap is itself a signal.
18. Informationally dense, noun-heavy register: nominalization plus that-clause plus participial-clause clustering inside one passage.
19. Llama 3 instruct generation artifact: outputs sometimes open "Here is the continuation of the text..."; "continuation" overrepresented at 29×.
20. Feature-based classifier accuracy: ~75% on base models, 93% to 98% on instruction-tuned. The size of the gap is itself diagnostic.

Note on year: PNAS publication is 2025; the arxiv preprint was submitted October 2024 and revised August 2025.
