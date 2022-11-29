#!/usr/bin/env python

from create_dataset import create_dataset
from delete_dataset import delete_dataset
from list_datasets import list_datasets
from ingest import ingest
from query import query
from query_legacy import queryLegacy


def main():
    dataset_name = "my-dataset"
    # create a new dataset
    create_dataset(dataset_name)
    list_datasets()
    # ingest some data
    ingest(dataset_name)
    # query the ingested data
    query(dataset_name)
    queryLegacy(dataset_name)
    # finally, delete the dataset
    delete_dataset(dataset_name)


if __name__ == "__main__":
    main()
