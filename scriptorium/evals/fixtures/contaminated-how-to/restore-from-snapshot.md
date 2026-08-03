# Restore a database from a snapshot

Point-in-time restore matters because a snapshot alone only gets you back to the moment it was taken, and the moment you actually want to recover to is rarely that exact instant. The reason a raw snapshot restore lands you earlier than the incident you are trying to fix is that a snapshot captures the data files as they existed at capture time, not the write-ahead log entries generated after that point; replaying the transaction log from the snapshot forward to a chosen timestamp is what lets you undo a bad migration, a mistaken bulk delete, or a corruption event without losing every change made after the snapshot was captured.

The trade-off is between restore speed and the size of the data-loss window, and the alternatives sit at opposite ends of it: restoring straight from the newest snapshot is the fastest option but discards everything written since it was taken, while replaying the log up to a precise target timestamp narrows that loss window to nearly nothing at the cost of a restore that takes as long as the log replay does.

1. Identify the snapshot whose timestamp sits closest to, but before, the point in time you want to restore to.
2. Provision a new database instance from that snapshot.
3. Replay the transaction log from the snapshot's timestamp forward to the target restore point.
4. Point the application's connection string at the restored instance once replay completes.
5. Verify row counts and a sample of known records against the pre-incident state.
6. Decommission the old instance once verification confirms a match.
