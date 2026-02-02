"""API package with strict versioning discipline.

VERSIONING STRATEGY:
- All public endpoints MUST be served under versioned paths: /api/v1/, /api/v2/, etc.
- Current stable version: v1
- Breaking changes require new version number
- Deprecated versions maintained for 6 months minimum

STRUCTURE:
├── api/
│   ├── v1/          # Current stable API (frozen contracts)
│   ├── v2/          # Future: Next version (when needed)
│   └── __init__.py  # This file

BEST PRACTICES:
- Never add routes directly to FastAPI app without version prefix
- Use APIRouter in version-specific modules
- Document breaking changes in CHANGELOG.md
- Coordinate with frontend team before deprecating endpoints

See: https://fastapi.tiangolo.com/tutorial/bigger-applications/
"""
