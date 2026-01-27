"""
Async version of annotation models and methods with AsyncAnnotationsClient.
"""

import ujson
import httpx
from typing import List, Optional
from dataclasses import asdict
from datetime import datetime
from urllib.parse import urlencode

from .annotations import (
    Annotation,
    AnnotationCreateRequest,
    AnnotationUpdateRequest,
)
from .util import from_dict
from ._error_handling import check_response_error


class AsyncAnnotationsClient:
    """AsyncAnnotationsClient has async methods to manipulate annotations."""

    client: httpx.AsyncClient

    def __init__(self, client: httpx.AsyncClient):
        """
        Initialize the async annotations client.

        Args:
            client: httpx AsyncClient instance for making HTTP requests
        """
        self.client = client

    async def get(self, id: str) -> Annotation:
        """
        Asynchronously get an annotation by id.

        Args:
            id: Annotation identifier

        Returns:
            Annotation object

        See https://axiom.co/docs/restapi/endpoints/getAnnotation
        """
        path = f"/v2/annotations/{id}"
        response = await self.client.get(path)
        check_response_error(response.status_code, response.json())
        return from_dict(Annotation, response.json())

    async def create(self, req: AnnotationCreateRequest) -> Annotation:
        """
        Asynchronously create an annotation with the given properties.

        Args:
            req: Annotation creation request

        Returns:
            Created Annotation object

        See https://axiom.co/docs/restapi/endpoints/createAnnotation
        """
        path = "/v2/annotations"
        payload = ujson.dumps(asdict(req))
        response = await self.client.post(path, content=payload)
        check_response_error(response.status_code, response.json())
        return from_dict(Annotation, response.json())

    async def list(
        self,
        datasets: List[str] = [],
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Annotation]:
        """
        Asynchronously list all annotations.

        Args:
            datasets: Optional list of dataset names to filter by
            start: Optional start time filter
            end: Optional end time filter

        Returns:
            List of Annotation objects

        See https://axiom.co/docs/restapi/endpoints/getAnnotations
        """
        query_params = {}
        if len(datasets) > 0:
            query_params["datasets"] = ",".join(datasets)
        if start is not None:
            query_params["start"] = start.isoformat()
        if end is not None:
            query_params["end"] = end.isoformat()
        path = f"/v2/annotations?{urlencode(query_params, doseq=True)}"

        response = await self.client.get(path)
        check_response_error(response.status_code, response.json())

        annotations = []
        for record in response.json():
            ds = from_dict(Annotation, record)
            annotations.append(ds)

        return annotations

    async def update(
        self, id: str, req: AnnotationUpdateRequest
    ) -> Annotation:
        """
        Asynchronously update an annotation with the given properties.

        Args:
            id: Annotation identifier
            req: Annotation update request

        Returns:
            Updated Annotation object

        See https://axiom.co/docs/restapi/endpoints/updateAnnotation
        """
        path = f"/v2/annotations/{id}"
        payload = ujson.dumps(asdict(req))
        response = await self.client.put(path, content=payload)
        check_response_error(response.status_code, response.json())
        return from_dict(Annotation, response.json())

    async def delete(self, id: str):
        """
        Asynchronously delete an annotation with the given id.

        Args:
            id: Annotation identifier

        See https://axiom.co/docs/restapi/endpoints/deleteAnnotation
        """
        path = f"/v2/annotations/{id}"
        response = await self.client.delete(path)
        check_response_error(response.status_code, response.json())
