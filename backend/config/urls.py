from django.urls import path
from tracker import views

urlpatterns = [
    path("auth/register", views.register), path("auth/login", views.login),
    path("auth/refresh", views.refresh), path("auth/logout", views.logout),
    path("auth/me", views.me), path("auth/me/notifications", views.notification_settings),
    path("notifications/run", views.notifications_run),
    path("supplements", views.supplements), path("supplements/<int:supplement_id>", views.supplement_detail),
    path("supplements/<int:supplement_id>/restock", views.restock),
    path("supplements/<int:supplement_id>/sources", views.add_source), path("sources/<int:source_id>", views.delete_source),
]
