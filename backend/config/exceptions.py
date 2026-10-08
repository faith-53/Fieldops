from rest_framework.views import exception_handler


class WorkflowError(Exception):
    def __init__(self, detail, status_code=400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        return response
    if isinstance(exc, WorkflowError):
        from rest_framework.response import Response

        return Response({"detail": exc.detail}, status=exc.status_code)
    return response
