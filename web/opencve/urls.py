from django.contrib import admin
from django.http import HttpResponseNotFound
from django.urls import include, path, Resolver404, URLResolver
from rest_framework_nested import routers
from django_ratelimit.decorators import ratelimit

from cves.resources import (
    CveViewSet,
    ProductCveViewSet,
    ProductViewSet,
    VendorCveViewSet,
    VendorViewSet,
    WeaknessCveViewSet,
    WeaknessViewSet,
)
from organizations.resources import OrganizationViewSet
from projects.resources import ProjectCveViewSet, ProjectViewSet
from users.views import CustomLoginView, CustomSignupView

# API Router
router = routers.SimpleRouter(trailing_slash=False)
router.register(r"cve", CveViewSet, basename="cve")

router.register(r"weaknesses", WeaknessViewSet, basename="weakness")
weaknesses_router = routers.NestedSimpleRouter(router, r"weaknesses", lookup="weakness")
weaknesses_router.register(r"cve", WeaknessCveViewSet, basename="weakness-cves")

router.register(r"organizations", OrganizationViewSet, basename="organization")
organizations_router = routers.NestedSimpleRouter(
    router, r"organizations", lookup="organization"
)
organizations_router.register(
    r"projects", ProjectViewSet, basename="organization-projects"
)

projects_cves_router = routers.NestedSimpleRouter(
    organizations_router, "projects", lookup="project"
)
projects_cves_router.register(
    r"cve", ProjectCveViewSet, basename="organization-projects-cves"
)

router.register(r"vendors", VendorViewSet, basename="vendor")
vendors_router = routers.NestedSimpleRouter(router, r"vendors", lookup="vendor")
vendors_router.register(r"products", ProductViewSet, basename="vendor-products")
vendors_router.register(r"cve", VendorCveViewSet, basename="vendor-cves")
products_cves_router = routers.NestedSimpleRouter(
    vendors_router, "products", lookup="product"
)
products_cves_router.register("cve", ProductCveViewSet, basename="product-cves")

# Combine all API URL patterns into one list.
api_urlpatterns = [
    path("", include(router.urls)),
    path("", include(organizations_router.urls)),
    path("", include(projects_cves_router.urls)),
    path("", include(vendors_router.urls)),
    path("", include(products_cves_router.urls)),
    path("", include(weaknesses_router.urls)),
]

# Create a URLResolver for the API endpoints.
api_resolver = URLResolver(r'^', api_urlpatterns)

@ratelimit(key="ip", rate="2/m", method="GET", block=True)
def api_dispatcher(request, *args, **kwargs):
    """
    Dispatcher view for /api/ that applies rate limiting.
    It removes the /api prefix, strips any leading slash, and dispatches to the appropriate API view.
    """
    # Remove the '/api' prefix
    relative_path = request.path_info[len('/api'):]
    # Strip the leading slash, as the resolver expects a relative path
    relative_path = relative_path.lstrip('/')
    
    try:
        match = api_resolver.resolve(relative_path)
        return match.func(request, *match.args, **match.kwargs)
    except Resolver404:
        return HttpResponseNotFound("API endpoint not found")

urlpatterns = [
    path("__debug__/", include("debug_toolbar.urls")),
    path("", include("changes.urls")),
    path("", include("cves.urls")),
    path("", include("onboarding.urls")),
    path("", include("organizations.urls")),
    path("", include("projects.urls")),
    path("", include("django_prometheus.urls")),
    path("settings/", include("allauth.urls")),
    path("login/", CustomLoginView.as_view(), name="account_login"),
    path("signup/", CustomSignupView.as_view(), name="account_signup"),
    path("settings/", include("users.urls")),
    path("admin/", admin.site.urls),
    path("hijack/", include("hijack.urls")),
    # API routes: all /api/ endpoints are dispatched via api_dispatcher (which is rate-limited)
    path("api/", api_dispatcher),
]

# Custom errors
handler404 = "cves.views.handle_page_not_found"
handler500 = "cves.views.handle_server_error"
