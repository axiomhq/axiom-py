from axiom import Client, DatasetCreateRequest


def create_dataset(dataset_name):
    client = Client()
    res = client.datasets.create(
        DatasetCreateRequest(name=dataset_name, description="")
    )
    print(f"created dataset: {res.id}")
