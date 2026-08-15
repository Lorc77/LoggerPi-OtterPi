# Legacy

This directory documents the legacy LoggerPi implementation that is currently
still running in production.

## `observer.py`

[`observer.md`](observer.md) documents the original `observer.py` running on the
LoggerPi.

The legacy implementation is **not** the target architecture of the
LoggerPi → OtterPi project. It is preserved here as a reference for:

- understanding the existing production system,
- identifying existing data sources and hardware interfaces,
- comparing legacy behaviour with the new architecture,
- preserving knowledge during the migration.

The legacy application currently starts through `/etc/rc.local` and therefore
must not be modified or disabled casually while the LoggerPi is still relying
on it.

## Migration status

The long-term goal is to replace the legacy `observer.py` with the new
LoggerPi → OtterPi architecture documented elsewhere in this repository.

Until the migration is complete, the legacy implementation should be treated
as **production-critical**.
