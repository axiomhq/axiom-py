#!/usr/bin/env python

from create_dataset import create_dataset
from ingest import ingest
from query import query
from query_legacy import queryLegacy


def main():
    create_dataset()
    ingest()
    query()
    queryLegacy()


if __name__ == "__init__":
    main()
