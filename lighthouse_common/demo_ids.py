"""Fixed demo identities, shared across all three tracks.

Hard-coded UUIDs (not generated) so the demo person and guardian have the SAME ids
on every machine — the database seed, the agents, and the dashboard all reference
these constants instead of inventing their own.
"""

# Demo protected person.
MARGARET_PERSON_ID = "11111111-1111-1111-1111-111111111111"

# Demo guardian (authorized family member).
PRIYA_GUARDIAN_ID = "22222222-2222-2222-2222-222222222222"

__all__ = ["MARGARET_PERSON_ID", "PRIYA_GUARDIAN_ID"]
