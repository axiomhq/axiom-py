"""This package provides annotation models and methods as well as an AnnotationsClient"""

import ujson
from requests import Session
from typing import List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
from urllib.parse import urlencode
from .util import from_dict


@dataclass
class Annotation:
    """Represents an Axiom annotation"""

    id: str = field(init=False)
    datasets: List[str]
    time: datetime
    endTime: Optional[datetime]
    title: Optional[str]
    description: Optional[str]
    url: Optional[str]
    type: str


@dataclass
class AnnotationCreateRequest:
    """Request used to create an annotation"""

    datasets: List[str]
    time: Optional[datetime]
    endTime: Optional[datetime]
    title: Optional[str]
    description: Optional[str]
    url: Optional[str]
    type: str


@dataclass
class AnnotationUpdateRequest:
    """Request used to update an annotation"""

    datasets: Optional[List[str]]
    time: Optional[datetime]
    endTime: Optional[datetime]
    title: Optional[str]
    description: Optional[str]
    url: Optional[str]
    type: Optional[str]


class AnnotationsClient:  # pylint: disable=R0903
    """AnnotationsClient has methods to manipulate annotations."""

    session: Session

    def __init__(self, session: Session):
        self.session = session

    def get(self, id: str) -> Annotation:
        """
        Get a annotation by id.

        See https://axiom.co/docs/restapi/endpoints/getAnnotation
        """
        path = "/v2/annotations/%s" % id
        res = self.session.get(path)
        decoded_response = res.json()
        return from_dict(Annotation, decoded_response)

    def create(self, req: AnnotationCreateRequest) -> Annotation:
        """
        Create an annotation with the given properties.

        See https://axiom.co/docs/restapi/endpoints/createAnnotation
        """
        path = "/v2/annotations"
        res = self.session.post(path, data=ujson.dumps(asdict(req)))
        annotation = from_dict(Annotation, res.json())
        return annotation

    def list(
        self,
        datasets: List[str] = [],
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Annotation]:
        """
        List all annotations.

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

        res = self.session.get(path)

        annotations = []
        for record in res.json():
            ds = from_dict(Annotation, record)
            annotations.append(ds)

        return annotations

    def update(self, id: str, req: AnnotationUpdateRequest) -> Annotation:
        """
        Update an annotation with the given properties.

        See https://axiom.co/docs/restapi/endpoints/updateAnnotation
        """
        path = "/v2/annotations/%s" % id
        res = self.session.put(path, data=ujson.dumps(asdict(req)))
        annotation = from_dict(Annotation, res.json())
        return annotation

    def delete(self, id: str):
        """
        Deletes an annotation with the given id.

        See https://axiom.co/docs/restapi/endpoints/deleteAnnotation
        """
        path = "/v2/annotations/%s" % id
        self.session.delete(path)
