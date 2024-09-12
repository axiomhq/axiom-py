import axiom_py
from axiom_py.logging import AxiomHandler
import logging


def main():
    # Add Axiom handler to root logger
    client = axiom_py.Client()
    handler = AxiomHandler(client, "my-dataset")
    logging.getLogger().addHandler(handler)

    # Get logger and log something
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.info("Hello world")


if __name__ == "__main__":
    main()
