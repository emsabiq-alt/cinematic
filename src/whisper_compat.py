"""whisper_compat — durable compatibility shims for faster-whisper.

Problem: faster-whisper passes ``metadata_errors="ignore"`` to ``av.open()``,
but ``av >= 14`` removed that keyword, raising ``TypeError`` at transcribe time.

Instead of hand-editing site-packages (which breaks on every reinstall),
import this module before using faster-whisper; it wraps ``av.open`` to drop
the unsupported keyword when the installed ``av`` rejects it.

Usage (top of whisper_aligner.py / render_continuous_babak.py)::

    import whisper_compat  # noqa: F401  (applies shim on import)
"""
import io

_APPLIED = False


def _av_rejects_metadata_errors() -> bool:
    try:
        import av
    except ImportError:
        return False
    try:
        av.open(io.BytesIO(b""), metadata_errors="ignore")
    except TypeError:
        return True
    except Exception:
        return False  # kwarg accepted; failed later for other reasons
    return False


def apply() -> bool:
    """Install the shim if needed. Returns True when patched."""
    global _APPLIED
    if _APPLIED:
        return False
    _APPLIED = True
    if not _av_rejects_metadata_errors():
        return False
    import av

    _orig_open = av.open

    def _open(*args, **kwargs):
        kwargs.pop("metadata_errors", None)
        return _orig_open(*args, **kwargs)

    av.open = _open
    return True


apply()
