from django.http import HttpResponsePermanentRedirect

class HTTPSRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.is_secure():
            url = request.build_absolute_uri(request.get_full_path())
            url = url.replace("https://", "http://")
            return HttpResponsePermanentRedirect(url)
        return self.get_response(request)
