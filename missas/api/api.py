from django.conf import settings
from django.core.signing import BadSignature
from django.utils.crypto import constant_time_compare
from django.views.decorators.debug import sensitive_variables
from ninja import NinjaAPI, Query
from ninja.errors import AuthenticationError, HttpError
from ninja.security import APIKeyHeader

from missas.api.schemas import ParishPage
from missas.api.services import ParishListChanged, parish_page


class SharedSecret(APIKeyHeader):
    param_name = "X-API-Key"

    @sensitive_variables("key", "secret")
    def authenticate(self, request, key):
        secret = settings.MISSAS_API_SHARED_SECRET
        if secret and secret.strip() and key and constant_time_compare(key, secret):
            return True
        raise AuthenticationError()


api = NinjaAPI(auth=SharedSecret(), docs_url=None, openapi_url=None)


@api.exception_handler(AuthenticationError)
def unauthorized(request, exc):
    return api.create_response(request, {"detail": "Não autorizado"}, status=401)


@api.get("/parishes", response=ParishPage)
def parishes(
    request,
    limit: int = Query(100, ge=1, le=100),
    cursor: str | None = Query(None, max_length=2048),
):
    try:
        return parish_page(limit, cursor)
    except BadSignature as exc:
        raise HttpError(400, "Cursor inválido ou expirado") from exc
    except ParishListChanged as exc:
        raise HttpError(409, "A lista mudou; reinicie a paginação") from exc
