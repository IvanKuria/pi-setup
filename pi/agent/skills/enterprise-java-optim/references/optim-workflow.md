# IBM Optim / Data Archiving Workflow

## Core Concepts to Separate

- **Source inventory**: DB platform, schemas, table groups, relationships, volumes.
- **Selection criteria**: date/status/business rules for archive eligibility.
- **Access definition**: object/table relationship graph and extract scope.
- **Extract**: read/copy eligible records into Optim-managed extract/archive form.
- **Archive/storage**: retention target, naming, encryption, compression, cataloging.
- **Delete/purge**: destructive phase; requires explicit approval and validation.
- **Restore/access**: how archived records are queried or restored.
- **Compare/reconcile**: counts, checksums, referential checks, audit reports.

## Required Questions Before Implementation

1. What is the system of record?
2. Which tables/entities are in scope and out of scope?
3. What retention policy and legal hold constraints apply?
4. Is deletion/purge part of this task or only extract/archive?
5. How is referential integrity preserved?
6. What is the restore/query path and RTO/RPO expectation?
7. How will we validate counts and correctness?
8. What is rollback if the job partially fails?
9. What environment is safe for testing?

## Safe Implementation Defaults

- Treat purge/delete as a separate, explicitly approved step.
- Add dry-run/report-only mode where possible.
- Use checkpointing/idempotency for long-running jobs.
- Reconcile source eligible count vs archived count vs post-purge count.
- Log identifiers carefully; avoid sensitive data in logs.
- Use transactions/batches deliberately and document limits.

## Review Checklist

- [ ] No unintended broad selection criteria.
- [ ] No hidden delete/purge behavior.
- [ ] Validation checks exist before destructive actions.
- [ ] Restore/query path is known.
- [ ] Failure and restart behavior is safe.
- [ ] Credentials/secrets are not committed or logged.
