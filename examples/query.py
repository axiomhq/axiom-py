from axiom import Client


def query(dataset_name):
    aplQuery = f"['{dataset_name}'] | where status == 500"

    client = Client()
    res = client.query(aplQuery)
    for match in res.matches:
        print(match.data)
