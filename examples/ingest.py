from axiom import Client


def ingest(dataset_name):
    client = Client()
    res = client.ingest_events(dataset_name, [{"foo": "bar"}])
    print("Ingested %d events with %d failures".format(res.ingested, res.failed))
