from axiom import Client


def delete_dataset(dataset_name):
    client = Client()
    client.datasets.delete(dataset_name)
    print("deleted dataset: my-dateset")
