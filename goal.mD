Design a system where:

Frontend clients hit a load balancer.
A single centralized Auth service (Keycloak SSO) handles login, issues JWT/OIDC tokens.
All business apps (Core app, Leave Management, CRM, Underwriting, KYC, etc.) are separate services.
Every app verifies permissions based on JWT at both API and view (page/route) levels.
Show internal and external connections.
Below is a clear, text diagram and a recommended reference architecture.

High-level ASCII diagram
[Internet/Users]
      |
    HTTPS
      |
+------------------+
|   Load Balancer  |  (e.g., Nginx/ALB/Ingress)
+------------------+
      |            \ 
      |             \ (only /auth/* routed here)
      |              \
      |           +--------------------+
      |           |  Auth Service      |
      |           |  (Keycloak SSO)    |
      |           |  OIDC/OAuth2       |
      |           +--------------------+
      |                 ^        |
      |                 |        | (JWKS /userinfo /introspect)
      |                 |        v
      |           +--------------------+
      |           | Identity Provider  |  (optional: LDAP/AD, SAML, Social)
      |           +--------------------+
      |
      |    (All other routes to apps via LB/Ingress)
      v
+----------------------+      +----------------------+      +----------------------+
| Core App Service     |      | Leave Mgmt Service  |      | CRM Service          |
| (API + UI)           |      | (API + UI)          |      | (API + UI)           |
+----------------------+      +----------------------+      +----------------------+
      |                         |                              |
      |                         |                              |
      |                         |                              |
      v                         v                              v
+-----------+            +-------------+                 +-------------+
| Core DB   |            | Leave DB    |                 | CRM DB      |
+-----------+            +-------------+                 +-------------+

Other domain apps follow the same pattern.

Common internal services:
+----------------------+        +---------------------+
| API Gateway (opt.)   |<------>| Observability Stack |
| (rate limit, routing)|        | (Logs, Metrics, Traces)
+----------------------+        +---------------------+
Request/auth flows
Login (external)
Browser → LB → Keycloak /realms/{realm}/protocol/openid-connect/auth
User completes auth (password, SSO, MFA).
Keycloak redirects back to frontend with code → frontend exchanges code for tokens (Access JWT, Refresh token) via token endpoint.
Tokens stored securely (HTTP-only, Secure cookies preferred; short-lived access token + refresh rotation).
App access (external)
Browser requests app route/API: Browser → LB → App Service.
Frontend attaches Access JWT in Authorization: Bearer .
App validates token signature using Keycloak JWKS (cached) and checks:
exp, nbf, iss, aud
realm roles, client roles, permissions
Authorization (internal, in each app)
API layer: middleware validates JWT + enforces RBAC/ABAC for endpoints.
View/UI layer: route guards check scopes/roles to show/hide features.
Fine-grained: use Keycloak Authorization Services (RPT, UMA) or embed permissions claims.
Token lifecycle
Short-lived access token (e.g., 5–15 min).
Refresh token rotation via frontend → Keycloak token endpoint.
Backend-to-backend calls use service accounts or mTLS + client credentials flow.
Detailed connection map
External connections

Clients → LB: HTTPS 443
LB → Keycloak: HTTPS 443 (/auth endpoints)
LB → Each App: HTTPS 443 (app-specific hostnames or paths)
Optional: Public JWKS endpoint from Keycloak consumed by apps
Internal connections

Apps → Keycloak:
HTTPS GET /.well-known/openid-configuration
HTTPS GET JWKS endpoint to validate signatures
HTTPS POST /token (for server-side flows or service accounts)
HTTPS /introspect (optional if using opaque or to double-check)
Apps → Their own DBs: private network, mTLS or TLS, least-privileged accounts
Apps → Shared services (e.g., Message Bus, Cache, Object Store) as needed
Observability: Apps → Log/metrics/trace collectors
Optional API Gateway in front of apps (then LB → Gateway → Apps)
Suggested routing at the Load Balancer/Ingress
auth.example.com → Keycloak service
core.example.com → Core App service
leave.example.com → Leave Mgmt service
crm.example.com → CRM service
underwriting.example.com → Underwriting service
kyc.example.com → KYC service
Path-based alternative:

example.com/auth/* → Keycloak
example.com/core/* → Core App
...
JWT/permission model
Issuer (iss): https://auth.example.com/realms/your-realm
Audience (aud): app client IDs (e.g., core-app, leave-app)
Realm roles: admin, manager, employee
Client roles (per app): core:viewer, core:editor; leave:approver; crm:agent
Resource-based permissions (Keycloak Authorization Services) for fine-grain:
Resources: “leave-request:{id}”, “customer:{id}”
Scopes: view, update, approve
Each app enforces:

API middleware: verify signature via JWKS; reject if invalid/expired.
Check roles/permissions per route.
UI route guards: hide/disable actions if missing scopes.
Optional policy enforcement point (PEP) using Keycloak adapters or OPA/OPAL.
Security recommendations
Use mTLS between LB and services or at least TLS within cluster.
Rotate signing keys; use RS256/ES256; cache JWKS with expiry.
Use SameSite=strict, HttpOnly cookies if storing tokens in browser.
Enable PKCE for public clients; enable refresh token rotation and reuse detection.
Rate-limit auth and token endpoints at LB/Gateway.
Separate networks/namespaces for Auth vs Apps.
Optional enhancements
API Gateway for:
Centralized rate limiting, request auth (JWT verification at edge), header propagation
Canary/blue-green, WAF rules
Service Mesh (Istio/Linkerd) for:
mTLS, traffic policies, retries/timeouts, telemetry
Centralized policy with OPA:
Apps call OPA sidecar with JWT + resource for ABAC decisions; OPA fetches policy from control plane.
Minimal component list (deployable)
Load Balancer/Ingress (Nginx, AWS ALB, GCP LB)
Keycloak (HA, external database like Postgres)
Apps:
Core App (Django/Node/etc.) + its DB
Leave Mgmt App + its DB
CRM App + its DB
Underwriting App + its DB
KYC App + its DB
Shared:
Central logging (ELK/CloudWatch)
Metrics (Prometheus/Grafana)
Tracing (Jaeger/OTel)
If you want, I can generate an editable architecture diagram (SVG) in the Playground with the exact boxes/arrows for your team.