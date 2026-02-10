---
name: logging
description: Generate structured log messages following the action-oriented pattern. Use when writing log statements, adding logging to code, or when user mentions "logging", "log messages", or asks to add logs. Pattern uses three phases - Preparing/Attempting (before action), Successfully (after success), Failed (after failure) - with structured parameters for searchability.
---

# Structured Logging Pattern

Action-oriented log messages with structured parameters for searchability and observability.

## Philosophy

Logs should tell a story. When debugging at 2am, you're reading logs like a book - scanning for the narrative thread that leads to the problem. Good logs read like prose:

```
DEBUG  Preparing to sync contacts. Count: 150
INFO   Successfully synced contacts. Count: 150, Duration: 3.2s
DEBUG  Preparing to publish notification. ContactId: 42
ERROR  Failed to publish notification. ContactId: 42, Error: Connection refused
```

You can *read* what happened. Bad logs require a decoder ring.

## Pattern

| Phase | Template | Level |
|-------|----------|-------|
| Before | `Preparing to {action}. {Context}` | Debug |
| Success | `Successfully {past-tense}. {Context}` | Info |
| Failure | `Failed to {action}. {Context}` | Error |

**Context format:** `Key: {Key}, OtherKey: {OtherKey}`

## Log Levels

| Level | When to use |
|-------|-------------|
| **Trace** | Inner-loop diagnostics, per-item in batch, breadcrumbs (use Debug if unavailable) |
| **Debug** | "Preparing to..." messages, intermediate state, skipped items |
| **Info** | "Successfully..." messages, count checkpoints, business events |
| **Warning** | Recoverable issues, degraded behavior, unexpected but handled |
| **Error** | "Failed to..." messages, operation couldn't complete |
| **Critical** | System is broken, wake someone up, data integrity at risk |

**Rule of thumb:** In production at `Info` level, you see the success story. Turn on `Debug` for the full narrative.

## Message Templates

### Basic Operation

```
DEBUG  Preparing to save user. UserId: {user_id}
INFO   Successfully saved user. UserId: {user_id}
ERROR  Failed to save user. UserId: {user_id}, Error: {error}
```

### With Timing

```
DEBUG  Preparing to fetch metadata. BusinessUnitId: {unit_id}
INFO   Successfully fetched metadata. BusinessUnitId: {unit_id}, Count: {count}, Duration: {duration}
```

### Multiple Context Values

```
DEBUG  Preparing to process order. OrderId: {order_id}, CustomerId: {customer_id}, ItemCount: {item_count}
INFO   Successfully processed order. OrderId: {order_id}, Total: {total}
ERROR  Failed to process order. OrderId: {order_id}, Stage: {stage}, Error: {error}
```

## Guidelines

1. **Action verbs** - save, load, process, sync, validate, publish, upload, download
2. **Past tense for success** - "saved", "loaded", "processed", "synced"
3. **Present tense for failure** - "Failed to save" (not "Failed to saved")
4. **Structured parameters** - Use placeholders, never string interpolation
5. **Identify the entity** - Primary identifier (Id, Name, Key) first
6. **ISO 8601 dates** - `2024-01-15T14:30:00Z`

## Anti-patterns

```
# Bad: No context
INFO   Done

# Bad: String interpolation (not searchable/groupable)
INFO   Saved user 123

# Bad: Vague action
INFO   Processing complete

# Bad: Missing structured keys
INFO   Saved {0}
```

## Techniques

### Timed Operations

Add `Duration` to success logs for operations worth measuring.

### Logger Scopes / Context Managers

Attach context to all logs within a block - no need to repeat IDs in every message.

### Count Checkpoints

Log counts at key stages to track data flow:

```
INFO   Loaded business units. Count: {count}
INFO   Generated date ranges. Count: {count}
INFO   Published messages. Count: {count}
```

Spot data loss: "Loaded 150 → Generated 148 → Published 145" means 5 vanished.

### Guard Clauses

Log *why* you're bailing early:

```
WARN   Skipping database upsert. Reason: {reason}
DEBUG  Skipping processing. Reason: {reason}, BusinessUnitId: {unit_id}
```

### Batch Progress

For long operations, log progress periodically:

```
DEBUG  Preparing to process contacts. TotalCount: {total}
TRACE  Processing batch. Progress: {processed}/{total}
INFO   Successfully processed contacts. Count: {count}, Duration: {duration}
```

### Critical Alerts

Reserve for "wake someone up" situations:

```
CRIT   Consumer disconnected from Kafka. Facility: {facility}
CRIT   No business units are currently enabled
CRIT   Message failed validation. Type: {type}
```

### Helper Functions

Standardize common patterns (API errors, auth failures, etc.) into reusable functions to ensure consistency.
