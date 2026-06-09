# Why we moved our background jobs off Celery

We ran Celery with a Redis broker for about three years. It worked, mostly. The trouble started when our job volume crossed roughly 2 million tasks a day and we began seeing tasks silently dropped during Redis failovers. Debugging it ate a sprint and a half.

The core issue was that we were treating Redis as a durable queue when it isn't really built for that. Acknowledgement semantics under failover were murky, and our retry logic papered over data loss rather than preventing it. Once I understood that, the fix direction was obvious: we needed a broker with real delivery guarantees.

We evaluated three options: RabbitMQ, AWS SQS, and Postgres-backed queues via a library called procrastinate. I leaned toward SQS because we were already on AWS and I didn't want to operate another stateful service. The tradeoff is visibility latency: SQS gives at-least-once delivery, so we had to make our task handlers idempotent. That took two weeks of work across about 40 task types, and we found three handlers that were quietly non-idempotent and had probably been double-charging a handful of customers. We refunded them.

Migration ran for six weeks behind a feature flag, routing a growing percentage of traffic to the new path. We cut over fully in March. Dropped-task incidents went to zero. The cost went up about $200 a month, which was an easy trade against the engineering time we'd been burning.

If I were starting over, I'd reach for SQS or a Postgres queue before Celery-on-Redis. Redis is a great cache. It's a mediocre durable broker, and we learned that the expensive way.
