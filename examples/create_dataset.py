from axiom import Client, DatasetCreateRequest


def create_dataset():
    client = Client()
    res = client.datasets.create(
        DatasetCreateRequest(name="my-dataset", description="")
    )
    print(f"created dataset: {res.id}")


create_dataset()
