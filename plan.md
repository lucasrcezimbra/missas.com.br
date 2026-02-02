# Plan: Prioritize Location Display in Schedule Cards

## Problem

When a Parish has multiple locations (chapels), showing the Parish name as the most prominent info is confusing. Users might go to the main parish building when the Mass is actually at a chapel.

## Solution

Invert the visual hierarchy: show location as primary info, parish as secondary.

## Behavior Specification

### Card Header Structure

```
[Primary]    Location name (prominent)         ← location.name || location_name || parish.name
[Address]    📍 R. do Motor, 673...            ← location.address (Maps link, only if location exists)
[Secondary]  Paróquia de Nossa Senhora...      ← parish.name (only if primary ≠ parish)
```

### Priority Order for Primary Display

1. `schedule.location.name` - from Location FK (first choice)
2. `schedule.location_name` - text field on Schedule (second choice)
3. `schedule.parish.name` - fallback (always available)

### Secondary Display (Parish Name)

- Show `schedule.parish.name` only if primary is NOT already the parish name
- Avoids redundancy when falling back to parish name

### Address Line

- Show `schedule.location.address` as Google Maps link
- Only displayed when `schedule.location` exists
- Positioned below primary, above secondary

### Example Outcomes

| location.name | location_name | Primary shows | Secondary shows |
|---------------|---------------|---------------|-----------------|
| "Capela X"    | "Sala Y"      | Capela X      | Parish name     |
| null          | "Sala Y"      | Sala Y        | Parish name     |
| "Capela X"    | null          | Capela X      | Parish name     |
| null          | null          | Parish name   | *(nothing)*     |

## Files to Modify

- `missas/core/templates/cards.html` - main card template
