"""
Root WSGI entry point for Render / gunicorn.

Render's default Start Command is `gunicorn app:app` (without --chdir).
This shim re-exports the Flask app from Backend/app.py so both
`gunicorn app:app`  and  `gunicorn --chdir Backend app:app` work.
"""

from Backend.app import app  # noqa: F401

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    # Render sets PORT; keep debug off in production
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    app.run(host="0.0.0.0", port=port, debug=debug)
