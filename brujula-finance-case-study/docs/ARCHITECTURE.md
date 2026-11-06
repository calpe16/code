# Brújula financial workflow

```mermaid
flowchart LR
    A[Statement file] --> B[Parse and normalize]
    B --> C[Compare with original records]
    C --> D[Human review of uncertain matches]
    D --> E[Local financial records]
    E --> F[Pending operations and version]
    F --> G[Private cloud processor]
    G --> H[State and acknowledgement receipt]
    H --> E
```

The public code covers money normalization and structured-row matching only.
The full private application separately queues operations and waits for state plus receipts
before discarding pending changes. Version conflicts remain visible rather than silently
overwriting another device. A lost response must not be treated as proof that an operation failed.

This diagram is descriptive. It does not publish the cloud implementation or certify its security.
