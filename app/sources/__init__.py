"""Data sources. One small module per public health feed.

Each module exposes ``get_series()`` (or ``reference_sources()``) and is fully
responsible for attaching provenance to the numbers it returns.
"""
