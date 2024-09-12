"""This module contains the tests for the AnnotationsClient."""

import os

import unittest
from logging import getLogger
from .helpers import get_random_name
from axiom_py import (
    Client,
    AnnotationCreateRequest,
    AnnotationUpdateRequest,
)


class TestAnnotations(unittest.TestCase):
    client: Client
    dataset_name: str

    @classmethod
    def setUpClass(cls):
        cls.logger = getLogger()

        cls.client = Client(
            os.getenv("AXIOM_TOKEN"),
            os.getenv("AXIOM_ORG_ID"),
            os.getenv("AXIOM_URL"),
        )

        # create dataset
        cls.dataset_name = get_random_name()
        cls.client.datasets.create(
            cls.dataset_name, "test_annotations.py (dataset_name)"
        )

    def test_happy_path_crud(self):
        """
        Test the happy path of creating, reading, updating, and deleting an
        annotation.
        """
        # Create annotation
        req = AnnotationCreateRequest(
            datasets=[self.dataset_name],
            type="test",
            time=None,
            endTime=None,
            title=None,
            description=None,
            url=None,
        )
        created_annotation = self.client.annotations.create(req)
        self.logger.debug(created_annotation)

        # Get annotation
        annotation = self.client.annotations.get(created_annotation.id)
        self.logger.debug(annotation)
        assert annotation.id == created_annotation.id

        # List annotations
        annotations = self.client.annotations.list(
            datasets=[self.dataset_name]
        )
        self.logger.debug(annotations)
        assert len(annotations) == 1

        # Update
        newTitle = "Update title"
        updateReq = AnnotationUpdateRequest(
            datasets=None,
            type=None,
            time=None,
            endTime=None,
            title=newTitle,
            description=None,
            url=None,
        )
        updated_annotation = self.client.annotations.update(
            annotation.id, updateReq
        )
        self.logger.debug(updated_annotation)
        assert updated_annotation.title == newTitle

        # Delete
        self.client.annotations.delete(annotation.id)

    @classmethod
    def tearDownClass(cls):
        """Delete datasets"""
        cls.client.datasets.delete(cls.dataset_name)
