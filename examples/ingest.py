from axiom import Client


def ingest():
    client = Client()
    res = client.ingest_events("my-dataset", [{"foo": "bar"}])
    print("Ingested %d events with %d failures".format(res.ingested, res.failed))


ingest()
