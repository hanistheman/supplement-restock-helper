from django.urls import path
from tracker import views

urlpatterns = [
    path("auth/register", views.RegisterView.as_view()), path("auth/login", views.LoginView.as_view()),
    path("auth/refresh", views.RefreshView.as_view()), path("auth/logout", views.LogoutView.as_view()),
    path("auth/me", views.MeView.as_view()), path("auth/me/notifications", views.NotificationSettingsView.as_view()),
    path("notifications/run", views.NotificationsRunView.as_view()),
    path("supplements", views.SupplementListView.as_view()),
    path("supplements/<int:supplement_id>", views.SupplementDetailView.as_view()),
    path("supplements/<int:supplement_id>/restock", views.RestockView.as_view()),
    path("supplements/<int:supplement_id>/sources", views.SourceListView.as_view()),
    path("sources/<int:source_id>", views.SourceDetailView.as_view()),
    path("supplements/<int:supplement_id>/skipped-days", views.SkippedDayListView.as_view()),
    path("supplements/<int:supplement_id>/skipped-days/<int:skipped_day_id>", views.SkippedDayDetailView.as_view()),
]
