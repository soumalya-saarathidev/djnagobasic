from typing import Dict, Any


def parse_claims(claims: Dict[str, Any]) -> Dict[str, Any]:
    roles = set((claims.get('realm_access') or {}).get('roles', []))
    role_level = claims.get('role_level') or ''
    department = claims.get('department') or ''
    is_admin = 'admin' in roles or 'realm-admin' in roles
    is_manager = 'manager' in roles or role_level in ('manager', 'vp', 'ceo')
    return {
        'roles': roles,
        'role_level': role_level,
        'department': department,
        'is_admin': is_admin,
        'is_manager': is_manager or is_admin,
        'is_employee': not (is_admin or is_manager),
    }


