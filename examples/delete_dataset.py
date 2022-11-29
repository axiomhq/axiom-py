from axiom import Client, DatasetCreateRequest


def delete_dataset(dataset_name):
    client = Client()
    client.datasets.delete(dataset_name)
    print(f"deleted dataset: my-dateset")
