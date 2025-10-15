# core/views/__init__.py
from .dashboards import dashboard
from .employees import *
from .departments import *
from .team import *
from core.authz import require_roles