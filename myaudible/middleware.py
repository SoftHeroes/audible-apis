import re
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.middleware import AuthenticationMiddleware

class CustomAuthenticationMiddleware(AuthenticationMiddleware):
    def process_request(self, request):
        # Define the regular expressions for excluded paths
        excluded_paths = [
            r'^/devices/add-device/[^/]+/[^/]+/$',
            r'^/devices/add-device/$',
        ]

        # Check if the current path matches any of the excluded path patterns
        for pattern in excluded_paths:
            if re.match(pattern, request.path_info):
                # Create the excluded_user if it doesn't exist
                user_model = get_user_model()
                username = 'excluded_user'
                user, created = user_model.objects.get_or_create(
                    username=username)
                if created:
                    user.set_unusable_password()
                    user.save()
                request.user = user
                return None  # Skip authentication for excluded paths

        # Perform the authentication as usual
        response = super().process_request(request)
        return response


class HeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        
        if request.path.startswith('/api/'):
            adp_token = request.META.get('HTTP_ADP_TOKEN')
            private_key = request.META.get('HTTP_PRIVATE_KEY')

            if not adp_token or not private_key:
                # Create a JSON response with an error message
                
                if re.match('^/api/catalog/products.*$', request.path) or re.match('^/api/product/.*$', request.path):
                    request.META['HTTP_ADP_TOKEN'] = "{enc:some_encryption}{key:some_key}{iv:some_iv}{name:some_name}{serial:Mg==}"
                    request.META['HTTP_PRIVATE_KEY'] = '-----BEGIN RSA PRIVATE KEY-----\n-----END RSA PRIVATE KEY-----\n'
                else:
                    response_data = {
                        'error': {
                            'code': 'Request_BadRequest',
                            'message': 'Required headers are missing.'
                        }
                    }
                    return JsonResponse(response_data, status=400)

        response = self.get_response(request)
        return response
