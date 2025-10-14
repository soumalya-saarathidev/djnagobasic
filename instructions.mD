# Django Auth SSO Service - Development Instructions

## Tech Stack
- **Backend Framework**: Django 4.2+, Django REST Framework
- **Authentication**: Keycloak, python-keycloak, djangorestframework-simplejwt
- **OAuth/OIDC**: google-auth, python-jose, requests
- **Database**: PostgreSQL (recommended) / MySQL / SQLite
- **ORM**: Django ORM
- **Security**: JWT tokens, httpOnly cookies

---

## Core Functionalities

### 1. Keycloak-Based Authentication
**Requirements:**
- Integration with Keycloak as primary SSO provider
- Multi-provider support (Keycloak, Google OIDC, Rediff Mail)
- Token-based authentication with JWT
- Automatic user synchronization from Keycloak to Django

**Key Points:**
- Login redirects to Keycloak authorization page
- Callback endpoint handles authorization code exchange
- JWT tokens issued for authenticated users
- User data synced between Keycloak and Django database
- Support for refresh token rotation

### 2. Role-Based Access Control (RBAC)
**Requirements:**
- Role synchronization from Keycloak to Django
- Module-level permission management (No Access, View, Edit)
- View protection using decorators and middleware
- Admin interface for role and permission configuration

**Key Points:**
- Roles defined in Keycloak and synced to Django
- Permissions mapped to Django models and views
- Automatic permission checks on protected endpoints
- Role hierarchy support (Admin > Manager > Employee > External User)

### 3. Attribute-Based Access Control (ABAC)
**Requirements:**
- Department-level data filtering
- User attribute storage and resolution
- Dynamic QuerySet filtering based on user attributes
- Policy-based access decisions

**Guardrails:**
- Managers can only access their department's data
- Admins have unrestricted access across all departments
- External users have limited scope based on attributes
- Automatic filtering applied transparently to business logic

**Key Points:**
- Attribute storage in Django models
- Policy evaluation engine for access decisions
- QuerySet filters applied based on user attributes
- No manual filtering required in business logic

### 4. Admin Management Portal(Provided by Keycloak)
**Requirements:**
- Role and permission management interface
- User attribute configuration
- Keycloak role synchronization controls
- Audit log viewer(need to create)

**Key Points:**
- CRUD operations for roles and permissions
- User-role assignment interface
- Attribute assignment per user
- Real-time sync with Keycloak
- token management dashboard

---

## Key User Flows

### Employee Login Flow
```
1. User visits application → Redirects to SSO page
2. User selects provider (Keycloak - Google / Rediff)
3. Provider authenticates user → Returns authorization code
4. Backend exchanges code for access token
5. JWT token issued and stored (httpOnly cookie)
6. User redirected to dashboard with authenticated session
7. Token automatically refreshed before expiry
8. On logout → Token blacklisted and session destroyed
```

### Permission Check Flow
```
1. User attempts to access protected resource
2. Middleware extracts JWT token from request
3. Token validated and user object attached to request
4. Permission middleware checks required permissions
5. RBAC check: Does user role have permission?
6. ABAC check: Does user attribute match resource?
7. If both pass → Request proceeds to view
8. If either fails → 403 Forbidden response returned
```

### Admin Role Management Flow
```
1. Admin logs into Django admin panel
2. Admin navigates to Roles section
3. Admin creates/edits role with:
   - Role name and description
   - Keycloak role ID mapping
   - Module permissions (view/edit per module)
4. Admin runs sync command to pull latest roles from Keycloak
5. Changes reflected immediately in permission checks
```

---

## Database Schema (Django ORM)

### KeycloakUser Model
```python
class KeycloakUser(models.Model):
    keycloak_id = models.UUIDField(unique=True, db_index=True)
    employee = models.OneToOneField('core.Employee', on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    user_type = models.CharField(max_length=20, choices=[
        ('internal', 'Internal Employee'),
        ('external', 'External User')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_keycloak_users'
        indexes = [
            models.Index(fields=['keycloak_id']),
            models.Index(fields=['email']),
        ]
```

### Role Model
```python
class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    keycloak_role_id = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    is_system_role = models.BooleanField(default=False)
    users = models.ManyToManyField(KeycloakUser, related_name='roles')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_roles'
```

### Permission Model
```python
class Permission(models.Model):
    module = models.CharField(max_length=100)  # e.g., 'attendance', 'payroll'
    action = models.CharField(max_length=20, choices=[
        ('view', 'View Only'),
        ('edit', 'Edit Access')
    ])
    resource_type = models.CharField(max_length=100, blank=True)
    roles = models.ManyToManyField(Role, related_name='permissions')
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'auth_permissions'
        unique_together = ['module', 'action', 'resource_type']
```

### UserAttribute Model
```python
class UserAttribute(models.Model):
    user = models.ForeignKey(KeycloakUser, on_delete=models.CASCADE, related_name='attributes')
    attribute_name = models.CharField(max_length=100)  # e.g., 'department', 'location'
    attribute_value = models.CharField(max_length=255)  # e.g., 'engineering', 'mumbai'
    
    class Meta:
        db_table = 'auth_user_attributes'
        unique_together = ['user', 'attribute_name']
```

### AuthAuditLog Model
```python
class AuthAuditLog(models.Model):
    user = models.ForeignKey(KeycloakUser, on_delete=models.SET_NULL, null=True)
    event_type = models.CharField(max_length=50)  # login, logout, permission_denied
    resource = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=True)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_audit_logs'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['event_type']),
        ]
```

### TokenBlacklist Model
```python
class TokenBlacklist(models.Model):
    token = models.TextField(unique=True)
    user = models.ForeignKey(KeycloakUser, on_delete=models.CASCADE)
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'auth_token_blacklist'
```

---

## API Endpoints

### Authentication APIs
- `GET /api/auth/providers` - List available auth providers
- `GET /api/auth/login/{provider}` - Initiate login (redirects to provider)
- `POST /api/auth/callback/{provider}` - Handle OAuth callback
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout and blacklist token
- `GET /api/auth/me` - Get current user info with roles and permissions

### Role & Permission APIs (Admin Only)
- `GET /api/auth/roles` - List all roles
- `POST /api/auth/roles` - Create new role
- `PUT /api/auth/roles/{id}` - Update role
- `DELETE /api/auth/roles/{id}` - Delete role
- `POST /api/auth/roles/{id}/permissions` - Assign permissions to role
- `POST /api/auth/roles/sync` - Sync roles from Keycloak

### User Management APIs (Admin Only)
- `GET /api/auth/users` - List all users
- `GET /api/auth/users/{id}` - Get user details
- `POST /api/auth/users/{id}/roles` - Assign roles to user
- `POST /api/auth/users/{id}/attributes` - Set user attributes
- `GET /api/auth/users/{id}/permissions` - Get effective permissions for user

### Audit APIs (Admin Only)
- `GET /api/auth/audit-logs` - Get audit logs with filters
- `GET /api/auth/audit-logs/user/{id}` - Get logs for specific user

---

## Service Layer Implementation

### AI Service (Keycloak Integration)
```python
# services/keycloak_service.py
class KeycloakService:
    def __init__(self):
        # Singleton pattern - single connection instance
        
    def authenticate(self, code, redirect_uri):
        # 1. Exchange authorization code for tokens
        # 2. Validate access token
        # 3. Fetch user info from Keycloak
        # 4. Return standardized user data
        
    def get_user_roles(self, access_token):
        # Fetch roles from Keycloak token claims
        
    def sync_roles(self):
        # Pull all roles from Keycloak and sync to Django
        
    def refresh_token(self, refresh_token):
        # Get new access token using refresh token
```

### Guardrail Service (Permission Checking)
```python
# services/permission_service.py
class PermissionService:
    @staticmethod
    def check_permission(user, module, action):
        # 1. Get user roles
        # 2. Check if any role has required permission
        # 3. Return True/False
        
    @staticmethod
    def filter_queryset_by_user(user, queryset):
        # 1. Determine user's access level (admin/manager/employee)
        # 2. Apply appropriate filters based on attributes
        # 3. Return filtered queryset
        
    @staticmethod
    def evaluate_abac_policy(user, resource):
        # 1. Extract user attributes
        # 2. Extract resource attributes
        # 3. Apply policy rules
        # 4. Return access decision
```

### Chat Service (ABAC Policy Engine)
```python
# services/abac_service.py
class ABACService:
    def __init__(self):
        self.policies = []
        
    def register_policy(self, policy):
        # Add new access policy
        
    def evaluate(self, user, resource, action):
        # 1. Iterate through registered policies
        # 2. Check if any policy denies access (deny override)
        # 3. Check if any policy allows access
        # 4. Default to deny if no policy matches
```

---

## Middleware Implementation

### Keycloak Authentication Middleware
```python
# middleware/keycloak_auth.py
class KeycloakAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # 1. Extract JWT token from request (cookie or header)
        # 2. Validate token signature and expiry
        # 3. Check if token is blacklisted
        # 4. Fetch user from database using token claims
        # 5. Attach user object to request
        # 6. If validation fails, return 401 Unauthorized
        return self.get_response(request)
```

### Permission Check Middleware
```python
# middleware/permission_middleware.py
class PermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # 1. Check if view requires permissions (has decorator metadata)
        # 2. Extract required roles/permissions
        # 3. Validate user has required access
        # 4. If validation fails, return 403 Forbidden
        # 5. Log access attempt to audit log
        return self.get_response(request)
```

---

## Decorator Implementation

### Role Requirement Decorator
```python
# decorators/require_role.py
def require_role(*roles):
    """
    Decorator to restrict view access to specific roles
    Usage: @require_role('admin', 'manager')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            user_roles = [role.name for role in request.user.roles.all()]
            if not any(role in user_roles for role in roles):
                # Log unauthorized access attempt
                return JsonResponse({'error': 'Insufficient permissions'}, status=403)
                
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

### Permission Requirement Decorator
```python
# decorators/require_permission.py
def require_permission(module, action):
    """
    Decorator to check module-level permissions
    Usage: @require_permission('attendance', 'edit')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not PermissionService.check_permission(request.user, module, action):
                # Log permission denial
                return JsonResponse({'error': 'Access denied'}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

---

## Frontend Components Structure

```
auth_service/
└── static/
    └── auth_admin/
        ├── components/
        │   ├── RoleManager.js          # Role CRUD interface
        │   ├── PermissionMatrix.js     # Visual permission assignment
        │   ├── UserList.js             # User management interface
        │   ├── AttributeEditor.js      # User attribute management
        │   ├── AuditLogViewer.js       # Audit log display
        │   └── SyncStatus.js           # Keycloak sync status
        ├── services/
        │   ├── authApi.js              # API calls to auth endpoints
        │   └── adminApi.js             # Admin-specific API calls
        └── App.js                      # Admin panel main component
```

---

## Implementation Priority

### Phase 1: Foundation Setup
1. Create `auth_service` Django app
2. Install and configure Keycloak
3. Implement basic authentication flow
4. Create core models (KeycloakUser, Role, Permission)
5. Build token validation middleware

### Phase 2: RBAC Implementation
1. Implement role synchronization from Keycloak
2. Create permission checking middleware
3. Build view decorators (`@require_role`, `@require_permission`)
4. Add audit logging

### Phase 3: ABAC Implementation
1. Create UserAttribute model
2. Implement attribute-based filtering service
3. Build policy evaluation engine
4. Integrate ABAC with existing views
5. Test department-level data filtering

### Phase 4: Multi-Provider SSO
1. Implement Google OIDC provider
2. Develop Rediff mail custom authentication
3. Create provider factory and strategy pattern
4. Build unified token format
5. Add provider selection UI

### Phase 5: Security & Session Management
1. Implement token refresh and rotation
2. Add token blacklisting on logout
3. Build session management dashboard(if provided by keycloak then don't)
4. Add rate limiting middleware

### Phase 6: Reusability & Documentation
1. Externalize all configurations
2. Create installation script
3. Write comprehensive documentation
4. Convert to pip-installable package
5. Create example integration project

---

## Project Structure

```
auth_service/                           # Django app root
├── migrations/
│   └── __init__.py
├── models/
│   ├── __init__.py
│   ├── user.py                        # KeycloakUser model
│   ├── role.py                        # Role model
│   ├── permission.py                  # Permission model
│   ├── attribute.py                   # UserAttribute model
│   └── audit.py                       # AuthAuditLog model
├── services/
│   ├── __init__.py
│   ├── keycloak_service.py           # Keycloak API integration
│   ├── google_oidc_service.py        # Google OAuth integration
│   ├── rediff_service.py             # Rediff custom auth
│   ├── permission_service.py         # RBAC logic
│   └── abac_service.py               # ABAC policy engine
├── middleware/
│   ├── __init__.py
│   ├── keycloak_auth.py              # Token validation middleware
│   └── permission_middleware.py      # Permission check middleware
├── decorators/
│   ├── __init__.py
│   ├── require_role.py               # Role decorator
│   ├── require_permission.py         # Permission decorator
│   └── require_attribute.py          # Attribute decorator
├── serializers/
│   ├── __init__.py
│   ├── user_serializer.py            # User serialization
│   ├── role_serializer.py            # Role serialization
│   └── permission_serializer.py      # Permission serialization
├── views/
│   ├── __init__.py
│   ├── auth_views.py                 # Login/logout/callback views
│   ├── role_views.py                 # Role management views
│   ├── user_views.py                 # User management views
│   └── audit_views.py                # Audit log views
├── utils/
│   ├── __init__.py
│   ├── token_utils.py                # JWT handling utilities
│   ├── attribute_resolver.py         # Attribute resolution
│   └── policy_engine.py              # Policy evaluation
├── management/
│   └── commands/
│       ├── __init__.py
│       ├── sync_keycloak_roles.py    # Role sync command
│       └── create_default_roles.py   # Default role creation
├── templates/
│   └── auth_service/
│       └── login_select.html         # Provider selection page
├── static/
│   └── auth_admin/                   # Admin panel frontend
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_services.py
│   ├── test_middleware.py
│   └── test_decorators.py
├── __init__.py
├── apps.py                            # App configuration
├── admin.py                           # Django admin registration
├── urls.py                            # URL routing
└── config.py                          # Auth configuration
```

---

## Configuration File Structure

```python
# auth_service/config.py
import os
from typing import Dict, Any

class AuthConfig:
    """Centralized configuration for auth_service"""
    
    # Keycloak Configuration
    KEYCLOAK_SERVER_URL: str = os.getenv('KEYCLOAK_SERVER_URL')
    KEYCLOAK_REALM: str = os.getenv('KEYCLOAK_REALM')
    KEYCLOAK_CLIENT_ID: str = os.getenv('KEYCLOAK_CLIENT_ID')
    KEYCLOAK_CLIENT_SECRET: str = os.getenv('KEYCLOAK_CLIENT_SECRET')
    KEYCLOAK_REDIRECT_URI: str = os.getenv('KEYCLOAK_REDIRECT_URI')
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET: str = os.getenv('GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI: str = os.getenv('GOOGLE_REDIRECT_URI')
    
    # Rediff Configuration
    REDIFF_API_URL: str = os.getenv('REDIFF_API_URL')
    REDIFF_CLIENT_ID: str = os.getenv('REDIFF_CLIENT_ID')
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_LIFETIME: int = int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME', 3600))
    JWT_REFRESH_TOKEN_LIFETIME: int = int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME', 604800))
    
    # Security Settings
    SESSION_TIMEOUT: int = int(os.getenv('SESSION_TIMEOUT', 1800))
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv('MAX_LOGIN_ATTEMPTS', 5))
    ENABLE_IP_WHITELIST: bool = os.getenv('ENABLE_IP_WHITELIST', 'false').lower() == 'true'
```

---

## Environment Variables (.env)

```bash
# Keycloak Configuration
KEYCLOAK_SERVER_URL=https://keycloak.example.com
KEYCLOAK_REALM=employee-management
KEYCLOAK_CLIENT_ID=djangobasic-client
KEYCLOAK_CLIENT_SECRET=your-client-secret
KEYCLOAK_REDIRECT_URI=http://localhost:8000/api/auth/callback/keycloak

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback/google

# Rediff Configuration
REDIFF_API_URL=https://api.rediff.com
REDIFF_CLIENT_ID=your-rediff-client-id

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ACCESS_TOKEN_LIFETIME=3600
JWT_REFRESH_TOKEN_LIFETIME=604800

# Security
SESSION_TIMEOUT=1800
MAX_LOGIN_ATTEMPTS=5
ENABLE_IP_WHITELIST=false

# # Database
# DATABASE_URL=postgresql://user:password@localhost:5432/employee_db
```

---

## Management Commands

```bash
# Sync roles from Keycloak
python manage.py sync_keycloak_roles

# Create default roles
python manage.py create_default_roles

# Create admin user
python manage.py createsuperuser

# Run migrations
python manage.py makemigrations auth_service
python manage.py migrate

# Install auth_service in new project
python -m auth_service.install
```

---

## Testing Strategy

### Unit Tests
- Model validation and relationships
- Service layer logic (permission checking, token validation)
- Decorator functionality
- Utility functions

### Integration Tests
- Authentication flow end-to-end
- Role and permission assignment
- ABAC policy evaluation
- Multi-provider authentication

### Security Tests
- Token tampering detection
- Permission bypass attempts
- SQL injection prevention
- Rate limiting effectiveness

---

## Design Patterns Used

| Pattern | Implementation | Location |
|---------|---------------|----------|
| **Strategy** | Auth provider abstraction | `services/auth_provider.py` |
| **Factory** | Provider and filter creation | `services/provider_factory.py` |
| **Chain of Responsibility** | Permission check pipeline | `middleware/permission_middleware.py` |
| **Decorator** | View protection | `decorators/require_role.py` |
| **Singleton** | Keycloak connection | `services/keycloak_service.py` |
| **Adapter** | Rediff auth standardization | `services/rediff_service.py` |
| **Repository** | Data access abstraction | `repositories/user_repository.py` |
| **Policy** | ABAC rule evaluation | `services/abac_service.py` |

---

## Security Best Practices

1. **Token Storage**: Use httpOnly cookies for web apps, secure storage for mobile
2. **Token Rotation**: Implement refresh token rotation on each use
3. **Rate Limiting**: Limit authentication attempts to prevent brute force
4. **Audit Logging**: Log all authentication and authorization events
5. **HTTPS Only**: Enforce HTTPS in production environments
6. **Secret Management**: Never commit secrets, use environment variables
7. **Input Validation**: Validate all user inputs to prevent injection attacks
8. **CORS Configuration**: Restrict CORS to trusted domains only

---

## Deployment Checklist

- [ ] All environment variables configured
- [ ] Keycloak realm and clients set up
- [ ] Database migrations applied
- [ ] SSL/TLS certificates installed
- [ ] CORS settings configured
- [ ] Rate limiting enabled
- [ ] Audit logging enabled
- [ ] Token blacklist cleanup job scheduled
- [ ] Backup strategy in place
- [ ] Monitoring and alerting configured