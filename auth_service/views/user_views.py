from django.http import JsonResponse, HttpResponseBadRequest


def me(request):
    claims = getattr(request, 'auth_claims', None)
    if not claims:
        return HttpResponseBadRequest('Missing or invalid token')
    return JsonResponse({'claims': claims})


def permissions(request):
    claims = getattr(request, 'auth_claims', None)
    if not claims:
        return HttpResponseBadRequest('Missing or invalid token')
    # Example mapping: roles in token drive permissions matrix
    realm_access = claims.get('realm_access', {})
    roles = realm_access.get('roles', [])
    module_perms = {
        'attendance': 'edit' if 'manager' in roles or 'admin' in roles else 'view',
        'payroll': 'view' if 'manager' in roles or 'admin' in roles else 'none',
    }
    return JsonResponse({'roles': roles, 'module_permissions': module_perms})


