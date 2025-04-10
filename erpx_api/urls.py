from django.urls import include, path

urlpatterns = [
    path("auth/", include("erpx_api.api_urls.auth.urls")),
    path("asset/", include("erpx_api.api_urls.asset.urls")),
    path("base/", include("erpx_api.api_urls.base.urls")),
    path("employee/", include("erpx_api.api_urls.employee.urls")),
    path("notifications/", include("erpx_api.api_urls.notifications.urls")),
    path("payroll/", include("erpx_api.api_urls.payroll.urls")),
    path("attendance/", include("erpx_api.api_urls.attendance.urls")),
    path("leave/", include("erpx_api.api_urls.leave.urls")),
]
