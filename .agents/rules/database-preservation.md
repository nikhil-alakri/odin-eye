---
trigger: always_on
---

# Rule: Database Preservation and Destructive Operations Constraint

All agents working on this codebase must strictly preserve the state of the active database and avoid any operations that can lead to data loss, resets, or database wipes.

## Destructive Operations Restriction:
* **Never Clear Tables/Data**: Never run delete commands (e.g. `prisma.user.deleteMany()`), raw SQL `DELETE FROM`, or `DROP TABLE` inside seed scripts, setup scripts, or database queries.
* **No Destructive Database Resets**: Never execute prisma reset commands (`npx prisma migrate reset`) or push options that truncate data or wipe user records.
* **Safe Seeding Practices**: Always write non-destructive seed scripts. Use `upsert` or check if the record exists (e.g., `findUnique`) before creating it, rather than clearing the database first.
* **Confirm Schema Changes**: If a schema migration requires dropping columns or tables containing active data, you must notify the user and obtain explicit approval before running it.
