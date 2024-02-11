from axiom import Client, QueryLegacy, QueryOptions, QueryKind
from datetime import datetime, timedelta


def queryLegacy(dataset_name):
    endTime = datetime.now()
    startTime = endTime - timedelta(days=1)
    query = QueryLegacy(startTime=startTime, endTime=endTime)

    client = Client()
    res = client.query_legacy(
        dataset_name, query, QueryOptions(save_as_kind=QueryKind.ANALYTICS)
    )
    if res.matches is None or len(res.matches) == 0:
        print("No matches found")
        return

    for match in res.matches:
        print(match.data)
