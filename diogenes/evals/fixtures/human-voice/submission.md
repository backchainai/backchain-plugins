# How I cut our search latency in half (and the one change that did most of it)

We had a problem. Our `/search` endpoint p99 sat at 430ms, and on Black Friday 2023 it spiked past 1.2s and we shed maybe 8% of carts before I rolled back the deploy at 2am.

I spent the first week convinced it was the database. It wasn't. I added a tracing span around the Elasticsearch call and another around the result-ranking step we'd written in Python, and the ranking step was eating 60% of the wall time. We were re-scoring 500 candidate docs per query in a loop with a numpy call inside it. Classic.

So I moved the scoring into a single vectorized operation. p99 dropped to 210ms overnight. Not the database. Our own code.

The thing nobody tells you: I almost didn't add that second tracing span. I was so sure it was Elasticsearch that I'd already drafted a ticket to bump the cluster from 3 nodes to 6, which would have cost us about $1,400/month and fixed nothing. Sara on the platform team talked me into instrumenting first. She was right, I was wrong, and I bought her a coffee.

A few things I'd do differently. I'd have set up the latency budget per span from day one instead of bolting it on under fire. And I still haven't fixed the cold-start case where the first query after a deploy hits an empty cache and takes 900ms. That one's still open. If you've solved warm-up for a ranking cache without pre-baking the top 10k queries, I want to hear about it.
