from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView

from variantenrichment.tool.views import (
    ProjectCreateView,
    ProjectDetailView,
    ProjectUpdateView,
    FileUploadView,
    FilesDeleteView,
    ConfirmProcessingView,
    CheckCaddView,
    ProjectResultsView,
    SearchView
)

urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path(
        "about/", TemplateView.as_view(template_name="pages/about.html"), name="about"
    ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("variantenrichment.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    # Your stuff: custom urls includes go here
    path("project/create", ProjectCreateView.as_view(), name="project-create"),
    path("project/detail/<uuid:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    path("project/update/<uuid:pk>/", ProjectUpdateView.as_view(), name="project-update"),
    path("project/upload-file/<uuid:pk>/", FileUploadView.as_view(), name="file-upload"),
    path("project/delete-files/<uuid:pk>/", FilesDeleteView.as_view(), name="files-delete"),
    path("project/start-processing/<uuid:pk>/", ConfirmProcessingView.as_view(), name="confirm-processing"),
    path("project/check-cadd/<uuid:pk>", CheckCaddView.as_view(), name="check-cadd"),
    path("project/results/<uuid:pk>/", ProjectResultsView.as_view(), name="project-results"),
    path("search/", SearchView.as_view(), name="search"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
