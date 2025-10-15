# auth_service/services/claims.py
def parse_claims(claims):
    """
    Extracts user identity, access roles, and Keycloak custom attributes from JWT claims.
    Works with mappers defined in populate_keycloak.py.
    """

    if not claims:
        return {
            "roles": set(),
            "is_admin": False,
            "is_manager": False,
            "is_employee": False,
            "role_level": None,
            "department": None,
            "position": None,
            "manager_id": None,
            "manager_email": None,
            "country": None,
        }

    # -----------------------
    # 1️⃣ Aggregate roles
    # -----------------------
    roles = set()
    if "realm_access" in claims:
        roles.update(claims["realm_access"].get("roles", []))
    if "resource_access" in claims:
        for app, access in claims["resource_access"].items():
            roles.update(access.get("roles", []))

    # -----------------------
    # 2️⃣ Extract user attributes
    # -----------------------
    department = claims.get("department")
    position = claims.get("position")
    role_level = (claims.get("role_level") or "").lower()
    country = claims.get("country")
    manager_id = claims.get("manager_id")
    manager_email = claims.get("manager_email")

    # Handle boolean attributes safely
    raw_is_manager = str(claims.get("is_manager", "")).lower()
    is_manager = raw_is_manager in ["true", "1", "yes"]

    # -----------------------
    # 3️⃣ Derive role flags
    # -----------------------
    is_admin = "admin" in role_level or any("admin" in r for r in roles)
    # manager includes CEO, VP, Manager
    is_manager = is_manager or role_level in ["manager", "vp", "ceo"]
    is_employee = not (is_admin or is_manager)

    return {
        "roles": list(roles),
        "is_admin": is_admin,
        "is_manager": is_manager,
        "is_employee": is_employee,
        "role_level": role_level,
        "department": department,
        "position": position,
        "manager_id": manager_id,
        "manager_email": manager_email,
        "country": country,
    }