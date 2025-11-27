class SimpleCORSMiddleware:
    """
    Middleware simple para habilitar CORS sin dependencias externas.
    Solo para desarrollo; en producción usar configuraciones más estrictas.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Responder preflight
        if request.method == 'OPTIONS':
            response = self._build_options_response()
        else:
            response = self.get_response(request)

        # Encabezados CORS básicos
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def _build_options_response(self):
        from django.http import HttpResponse

        resp = HttpResponse()
        resp.status_code = 200
        resp['Access-Control-Allow-Origin'] = '*'
        resp['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        resp['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return resp
