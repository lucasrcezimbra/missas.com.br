from django.middleware.cache import FetchFromCacheMiddleware, UpdateCacheMiddleware
from django.utils.cache import add_never_cache_headers


class SiteUpdateCacheMiddleware(UpdateCacheMiddleware):
    def process_response(self, request, response):
        if request.path_info.startswith("/api/"):
            add_never_cache_headers(response)
            return response
        return super().process_response(request, response)


class SiteFetchFromCacheMiddleware(FetchFromCacheMiddleware):
    def process_request(self, request):
        if request.path_info.startswith("/api/"):
            return None
        return super().process_request(request)
