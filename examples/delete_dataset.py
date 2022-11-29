from axiom import Client, DatasetCreateRequest


def delete_dataset():
    client = Client()
    client.datasets.delete("my-dataset")
    print(f"deleted dataset: my-dateset")


delete_dataset()
