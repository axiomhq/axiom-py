from axiom import Client


def list_datasets():
    client = Client()
    res = client.datasets.get_list()
    for dataset in res:
        print(f"found dataset: {dataset.name}")
