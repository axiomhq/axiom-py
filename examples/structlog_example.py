from axiom_py import Client
from axiom_py.structlog import AxiomProcessor
import structlog


def main():
    client = Client()

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso", key="_time"),
            AxiomProcessor(client, "my-dataset"),
            structlog.dev.ConsoleRenderer(),
        ]
    )

    log = structlog.get_logger()
    log.info("hello", who="world")


if __name__ == "__main__":
    main()
