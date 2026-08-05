import logging

import structlog


def setup_logging(debug: bool = False, environment: str = "development") -> None:
    """Configure structlog for the application.

    Development: ColourConsoleRenderer (human-readable)
    Production:  JSONRenderer (machine-parseable for Render log drains)
    """
    log_level = logging.DEBUG if debug else logging.INFO

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
    ]

    if environment == "production":
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Route stdlib loggers (SQLAlchemy, uvicorn, alembic) through structlog sink
    logging.basicConfig(level=log_level, format="%(message)s")
