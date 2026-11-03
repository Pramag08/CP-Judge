"""Private bounded single-ZIP HTTP request boundary for the live DMOJ site."""
import re
import shutil

from django.conf import settings
from django.core.exceptions import PermissionDenied, RequestDataTooBig
from django.core.files.uploadhandler import FileUploadHandler, StopUpload
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

from compat.archive import ArchiveLimits

UPLOAD_PATH = re.compile(r'^/contest/([^/]+)/import/$')
MULTIPART_OVERHEAD_LIMIT = 64 * 1024


class BoundedBodyStream:
    """Bound all parser reads, including multipart fields and trailing bytes."""
    def __init__(self, stream, limit):
        self.stream, self.limit, self.received = stream, limit, 0

    def _read(self, method, size=-1):
        remaining = self.limit - self.received
        size = remaining + 1 if size is None or size < 0 else min(size, remaining + 1)
        data = getattr(self.stream, method)(size)
        self.received += len(data)
        if self.received > self.limit:
            raise RequestDataTooBig('Upload request exceeds the configured body limit.')
        return data

    def read(self, size=-1):
        return self._read('read', size)

    def readline(self, size=-1):
        return self._read('readline', size)

    def close(self):
        return self.stream.close()


def limits():
    return ArchiveLimits(**getattr(settings, 'CPJ_ARCHIVE_LIMITS', {}))


class BoundedZipUploadHandler(FileUploadHandler):
    """Count the actual file chunks Django receives, independent of size headers."""

    def __init__(self, request, byte_limit):
        super().__init__(request)
        self.byte_limit = byte_limit
        self.file_count = 0
        self.received = 0
        self.exceeded = False
        self.multiple = False

    def new_file(self, *args, **kwargs):
        super().new_file(*args, **kwargs)
        self.file_count += 1
        if self.file_count > 1:
            self.multiple = True
            raise StopUpload(connection_reset=True)

    def receive_data_chunk(self, raw_data, start):
        self.received += len(raw_data)
        if self.received > self.byte_limit:
            self.exceeded = True
            raise StopUpload(connection_reset=True)
        return raw_data

    def file_complete(self, file_size):
        return None


class UploadBoundaryMiddleware(MiddlewareMixin):
    """Reject unauthorized uploads before body parsing and cap streamed bodies.

    The file handler counts received ZIP bytes even when a caller supplies no or
    dishonest Content-Length. For a WSGI server that cannot delimit a body with
    neither Content-Length nor wsgi.input_terminated, return 411 rather than
    accepting an unbounded request. Chunked/terminated streams are parsed with
    a fixed ceiling (ZIP limit plus bounded multipart framing).
    """

    def process_request(self, request):
        match = UPLOAD_PATH.fullmatch(request.path_info)
        if not match or request.method != 'POST':
            return None

        from judge.models import Contest
        from .imports import authorize

        if not request.user.is_authenticated:
            return HttpResponse('Please sign in before uploading.', status=401)
        contest = Contest.objects.filter(key=match.group(1)).first()
        if contest is None:
            from django.http import Http404
            raise Http404
        try:
            authorize(request.user, contest)
        except PermissionDenied:
            from django.http import Http404
            raise Http404

        configured = limits().upload_bytes
        body_limit = configured + MULTIPART_OVERHEAD_LIMIT
        from .imports import private_root
        root = private_root()
        reserve = int(getattr(settings, 'CPJ_UPLOAD_RESERVE_BYTES', 512*1024**2))
        if (reserve <= 0 or shutil.disk_usage(root).free < configured + reserve or
                shutil.disk_usage(settings.FILE_UPLOAD_TEMP_DIR).free < configured + reserve):
            return HttpResponse('Private upload storage is temporarily full.', status=503)
        transfer_encoding = request.META.get('HTTP_TRANSFER_ENCODING', '').lower()
        raw_length = request.META.get('CONTENT_LENGTH', '')
        try:
            length = int(raw_length) if raw_length else None
        except (TypeError, ValueError):
            return HttpResponse('Invalid Content-Length.', status=400)

        # A transfer-encoded stream has its own framing; don't let a conflicting
        # Content-Length truncate the Django multipart parser's accounting.
        terminated = bool(request.META.get('wsgi.input_terminated'))
        if transfer_encoding and not terminated:
            return HttpResponse('The server cannot safely receive this transfer encoding.', status=400)
        if terminated:
            request.META['CONTENT_LENGTH'] = str(body_limit)
        elif length is None:
            return HttpResponse('This server requires a framed request body.', status=411)
        elif length < 0:
            return HttpResponse('Invalid Content-Length.', status=400)
        elif length > body_limit:
            return HttpResponse('ZIP exceeds the configured upload limit.', status=413)

        handler = BoundedZipUploadHandler(request, configured)
        request.cpj_zip_upload_handler = handler
        request.upload_handlers.insert(0, handler)
        request.cpj_zip_body_limit = body_limit
        request._stream = BoundedBodyStream(request._stream, body_limit)
        return None
