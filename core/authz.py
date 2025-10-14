from auth_service.services.jwt_verifier import JWTVerifier


def require_roles(*required_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # The user object is now attached by the authentication class
            if not request.user or not request.user.is_authenticated:
                from django.http import HttpResponse
                return HttpResponse(status=401)

            roles = set(request.auth.get('realm_access', {}).get('roles', []))
            
            if required_roles and not roles.intersection(set(required_roles)):
                from django.http import HttpResponse
                return HttpResponse(status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


