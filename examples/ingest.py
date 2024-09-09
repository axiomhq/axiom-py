from axiom import Client


def ingest(dataset_name):
    client = Client()
    res = client.ingest_events(dataset_name, [{"foo": "bar"}])
    print(f"Ingested {len(res.ingested)} events with {
          len(res.failures)} failures")
