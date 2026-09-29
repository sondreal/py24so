# AUTO-GENERATED from py24so/resources/_async by scripts/unasync.py. DO NOT EDIT.

import time
from typing import Optional, Union

from py24so._utils import FileInput, path_param, read_file
from py24so.exceptions import APIError, APITimeoutError
from py24so.models.accounting import Document, FileUpload, FileUploadStatus
from py24so.resources._sync._resource import Resource


class Files(Resource):
    """``/fileUpload``: upload files (e.g. receipts) to the document archive.

    Uploading is a two-step process: :meth:`create_upload` returns a pre-signed
    URL, the bytes are sent there, and the file is then processed into a
    document in the background. :meth:`upload` does all of it in one call.
    """

    def create_upload(self, content_type: str) -> FileUpload:
        """Request a pre-signed URL to upload a file of ``content_type`` to."""
        return self._client.request(
            "POST", "/fileUpload", json={"contentType": content_type}, cast_to=FileUpload
        )

    def get_status(self, file_id: str) -> FileUploadStatus:
        """Get the processing status of an uploaded file."""
        return self._client.request(
            "GET", f"/fileUpload/{path_param(file_id)}", cast_to=FileUploadStatus
        )

    def upload(
        self,
        file: FileInput,
        *,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
        wait: bool = False,
        timeout: float = 60.0,
        poll_interval: float = 1.0,
    ) -> FileUploadStatus:
        """Upload a file and return its status.

        Args:
            file: Raw bytes, a file path, or a file object opened in binary mode.
            filename: Used to guess ``content_type`` when it is not given.
            content_type: MIME type of the file, e.g. ``application/pdf``.
            wait: Poll until the file has been archived and has a ``document_id``.
            timeout: Maximum seconds to wait when ``wait=True``.
            poll_interval: Seconds between status checks when ``wait=True``.
        """
        content, _, media_type = read_file(file, filename, content_type)
        target = self.create_upload(media_type)
        if not target.upload_url or not target.file_id:
            raise ValueError(f"The API did not return an upload URL: {target!r}")
        self._client.send_external(
            target.upload_method or "PUT",
            target.upload_url,
            content=content,
            headers={"Content-Type": media_type},
        )
        if wait:
            return self.wait_until_processed(
                target.file_id, timeout=timeout, poll_interval=poll_interval
            )
        return self.get_status(target.file_id)

    def wait_until_processed(
        self, file_id: str, *, timeout: float = 60.0, poll_interval: float = 1.0
    ) -> FileUploadStatus:
        """Poll :meth:`get_status` until the file has a ``document_id``.

        Raises:
            APIError: If processing failed (status ``Failed``).
            APITimeoutError: If the file is not processed within ``timeout`` seconds.
        """
        deadline = time.monotonic() + timeout
        while True:
            status = self.get_status(file_id)
            if status.document_id is not None:
                return status
            if (status.status or "").lower() == "failed":
                raise APIError(f"Processing of file {file_id} failed (status {status.status!r})")
            if time.monotonic() + poll_interval > deadline:
                raise APITimeoutError(
                    f"File {file_id} was not processed within {timeout:.0f}s "
                    f"(last status: {status.status!r})"
                )
            self._client._sleep(poll_interval)


class Documents(Resource):
    """``/documents``: archived documents (vouchers, attachments)."""

    def get(self, document_id: Union[int, str]) -> Document:
        """Get a document's metadata, including short-lived download and preview URLs."""
        return self._client.request(
            "GET", f"/documents/{path_param(document_id)}", cast_to=Document
        )
