# core/authz.py
from functools import wraps
from django.http import HttpResponseForbidden, HttpResponse
from auth_service.services.jwt_verifier import JWTVerifier
from auth_service.services.claims import parse_claims


def require_roles(*allowed_roles):
    """
    Decorator to restrict access to views based on parsed roles from JWT claims.
    Roles supported: admin, ceo, manager, vp, employee
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            claims = JWTVerifier.claims_from_request(request)
            if not claims:
                return HttpResponse("Unauthorized: Missing claims", status=401)

            parsed = parse_claims(claims)
            user_roles = parsed["roles"]

            # If any allowed role is in user roles → access granted
            if not any(r.lower() in user_roles or parsed.get(f"is_{r.lower()}") for r in allowed_roles):
                return HttpResponseForbidden("You are not authorized to access this resource")

            request.auth_claims = claims
            request.parsed_claims = parsed
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator