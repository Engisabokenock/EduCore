from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware


def configure_compression_layers(app: FastAPI) -> None:
    """
    Binds Gzip encoding compression down across outgoing transport pipes.

    Compresses large structural payload matrices (like analytics or time-series arrays)
    whenever responses exceed the minimum byte threshold.
    """
    app.add_middleware(
        GZipMiddleware,
        minimum_size=1024,  # Only compress responses exceeding 1 Kilobyte
        compresslevel=5,    # Balanced setting optimization for CPU overhead vs compression ratio
    )
