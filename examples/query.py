from axiom import Client


def query():
    aplQuery = "['my-dataset'] | where status == 500"

    client = Client()
    res = client.query(aplQuery)
    for match in res.matches:
        print(match.data)


query()
