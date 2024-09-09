from axiom_py import Client, DatasetCreateRequest


def main():
    client = Client()
    dataset_name = "my-dataset"

    # List datasets
    res = client.datasets.get_list()
    for dataset in res:
        print(dataset.name)

    # Create a dataset
    client.datasets.create(
        DatasetCreateRequest(name=dataset_name, description="A description.")
    )

    # Ingest events
    client.ingest_events(dataset_name, [{"foo": "bar"}])

    # Query events
    res = client.query(f"['{dataset_name}'] | where status == 500")
    for match in res.matches:
        print(match.data)

    # Delete the dataset
    client.datasets.delete(dataset_name)


if __name__ == "__main__":
    main()
