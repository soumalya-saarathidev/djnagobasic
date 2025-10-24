import os,sys
from unicodedata import is_normalized
import django
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakGetError, KeycloakPostError

#Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "employeesystem.settings")
django.setup()

from core.models import Employee, Department
# ----------------------------
# Realm-specific admin setup
# ----------------------------
KEYCLOAK_SERVER_URL = settings.KEYCLOAK_SERVER_URL
REALM_NAME = settings.KEYCLOAK_REALM
CLIENT_ID = settings.KEYCLOAK_ADMIN_CLIENT_ID
CLIENT_SECRET = settings.KEYCLOAK_ADMIN_CLIENT_SECRET

keycloak_admin = KeycloakAdmin(
    server_url=f"{KEYCLOAK_SERVER_URL}",
    realm_name=REALM_NAME,
    client_id=CLIENT_ID,
    client_secret_key=CLIENT_SECRET,
    verify=True,
)


print(f"✅ Connected to Keycloak realm: {REALM_NAME}")

# ---------------------------------------------------
# Helper Functions
# ---------------------------------------------------
def derive_role_level(position: str) -> str:
    position = (position or "").lower()
    if "ceo" in position:
        return "ceo"
    if "vp" in position or "vice president" in position:
        return "vp"
    if "manager" in position:
        return "manager"
    return "employee"


def get_or_create_group(group_name, parent_id=None):
    try:
        all_groups = keycloak_admin.get_groups()
        for g in all_groups:
            if g["name"].lower() == group_name.lower():
                return g

        print(f"➕ Creating group: {group_name}")
        keycloak_admin.create_group({"name": group_name}, parent=parent_id)

        # Refresh groups and return newly created
        new_groups = keycloak_admin.get_groups()
        for g in new_groups:
            if g["name"].lower() == group_name.lower():
                return g
        return None
    except KeycloakGetError as e:
        print(f"❌ Error managing group {group_name}: {e}")
        return None


def get_or_create_subgroup(parent_group, subgroup_name):
    subgroups = parent_group.get("subGroups", [])
    for sg in subgroups:
        if sg["name"].lower() == subgroup_name.lower():
            return sg

    print(f"📂 Creating subgroup '{subgroup_name}' under '{parent_group['name']}'")
    keycloak_admin.create_group({"name": subgroup_name}, parent=parent_group["id"])

    refreshed = keycloak_admin.get_group(parent_group["id"])
    for sg in refreshed.get("subGroups", []):
        if sg["name"].lower() == subgroup_name.lower():
            return sg
    return None


# ---------------------------------------------------
# 1️⃣ Create Department Groups
# ---------------------------------------------------
groups_cache = {}
for dept in Department.objects.all():
    group = get_or_create_group(dept.name)
    if group:
        groups_cache[dept.name] = group
print(f"✅ Synced {len(groups_cache)} top-level department groups.")

# ---------------------------------------------------
# 2️⃣ Create Hierarchy Subgroups
# ---------------------------------------------------
hierarchy_levels = ["ceo", "vp", "manager", "employee"]
for dept_name, dept_group in groups_cache.items():
    for level in hierarchy_levels:
        get_or_create_subgroup(dept_group, level)
print("🌳 Department hierarchy subgroups created.")

# ---------------------------------------------------
# 3️⃣ Sync Employees
# ---------------------------------------------------
for emp in Employee.objects.all():
    email = emp.email
    username = emp.employee_id
    first_name = emp.first_name
    last_name = emp.last_name
    dept_name = emp.department.name if emp.department else None
    position = emp.position
    role_level = derive_role_level(position)
    manager = emp.manager
    manager_id = manager.employee_id if manager else ""
    manager_email = manager.email if manager else ""
    is_manager = "true" if role_level in ["ceo", "vp" , "manager" , "admin"] else "false"

    # Check existing user by username or email
    existing_users = keycloak_admin.get_users(query={"username": username})
    if not existing_users:
        existing_users = keycloak_admin.get_users(query={"email": email})

    if existing_users:
        user_id = existing_users[0]["id"]
        print(f"👤 Updating existing user: {email} / {username}")

        # Update firstName, lastName, and attributes
        keycloak_admin.update_user(user_id, {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "attributes": {
                "department": str(dept_name or ""),
                "position": str(position),
                "role_level": str(role_level),
                "manager_id": str(manager_id),
                "manager_email": str(manager_email),
                "country": str(emp.country),
                "is_manager": str(is_manager),
            }
        })
    else:
        print(f"➕ Creating user: {first_name} {last_name} ({email})")
        user_id = keycloak_admin.create_user({
            "username": username,
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "enabled": True,
            "emailVerified": True,
            "credentials": [{
                "type": "password",
                "value": "TempPass123!",
                "temporary": True
            }],
            "attributes": {
                "department": str(dept_name or ""),
                "position": str(position),
                "role_level": str(role_level),
                "manager_id": str(manager_id),
                "manager_email": str(manager_email),
                "country": str(emp.country),
                "is_manager": str(is_manager),
            }
        })

    # Assign user to subgroup
    if dept_name in groups_cache:
        dept_group = groups_cache[dept_name]
        subgroup = get_or_create_subgroup(dept_group, role_level)
        subgroup_id = subgroup["id"]

        user_groups = keycloak_admin.get_user_groups(user_id)
        group_ids = [g["id"] for g in user_groups]
        if subgroup_id not in group_ids:
            keycloak_admin.group_user_add(user_id, subgroup_id)
            print(f"🏷️ {email} → {dept_name}/{role_level}")

print("🎯 ABAC + Hierarchical sync complete!")

# ---------------------------------------------------
# 4️⃣ Ensure Token Mappers for the Backend Client
# ---------------------------------------------------
app_client_name = "auth_service_backend"

# Fetch the internal Keycloak UUID for the backend client
try:
    app_client_id = keycloak_admin.get_client_id(app_client_name)
except Exception as e:
    print(f"❌ Could not find client '{app_client_name}': {e}")
    app_client_id = None

if app_client_id:
    print(f"✅ Found client '{app_client_name}' with ID: {app_client_id}")

    token_mappers = [
        {
            "name": "department",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",
            "consentRequired": False,
            "config": {
                "user.attribute": "department",
                "claim.name": "department",
                "jsonType.label": "String",
                "id.token.claim": "true",
                "access.token.claim": "true",
            },
        },
        {
            "name": "position",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",
            "consentRequired": False,
            "config": {
                "user.attribute": "position",
                "claim.name": "position",
                "jsonType.label": "String",
                "id.token.claim": "true",
                "access.token.claim": "true",
            },
        },
        {
            "name": "role_level",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",
            "consentRequired": False,
            "config": {
                "user.attribute": "role_level",
                "claim.name": "role_level",
                "jsonType.label": "String",
                "id.token.claim": "true",
                "access.token.claim": "true",
            },
        },
        {
            "name": "manager_id",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",
            "consentRequired": False,
            "config": {
                "user.attribute": "manager_id",
                "claim.name": "manager_id",
                "jsonType.label": "String",
                "id.token.claim": "true",
                "access.token.claim": "true",
            },
        },
        {
            "name": "manager_email",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",
            "consentRequired": False,
            "config": {
                "user.attribute": "manager_email",
                "claim.name": "manager_email",
                "jsonType.label": "String",
                "id.token.claim": "true",
                "access.token.claim": "true",
            },
        },
        {
            "name": "country",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",
            "consentRequired": False,
            "config": {
                "user.attribute": "country",
                "claim.name": "country",
                "jsonType.label": "String",
                "id.token.claim": "true",
                "access.token.claim": "true",
            },
        },
        {
            "name": "is_manager",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",
            "consentRequired": False,
            "config": {
                "user.attribute": "is_manager",
                "claim.name": "is_manager",
                "jsonType.label": "boolean",
                "id.token.claim": "true",
                "access.token.claim": "true",
            },
        },
    ]

    for mapper in token_mappers:
        try:
            keycloak_admin.add_mapper_to_client(app_client_id, mapper)
            print(f"🔹 Mapper '{mapper['name']}' added to client '{app_client_name}'")
        except Exception as e:
            print(f"⚠️ Error creating mapper '{mapper['name']}': {e}")

else:
    print(f"❌ Cannot create mappers because client '{app_client_name}' was not found")