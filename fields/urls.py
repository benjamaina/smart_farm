from django.urls import path
from fields.views.web import (
    dashboard,
    field_list, field_create, field_edit, field_detail, field_delete,
    add_field_update,
    agent_list, agent_create, agent_delete,
)
from fields.views.auth import login_view, logout_view
from fields.views.api import (
    FieldListView, FieldDetailView, FieldUpdateCreateView,
    AgentListView, DashboardStatsView,
)

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("dashboard/", dashboard, name="dashboard"),
    path("", dashboard, name="home"),

    path("fields/", field_list, name="field_list"),
    path("fields/add/", field_create, name="field_create"),
    path("fields/<int:pk>/", field_detail, name="field_detail"),
    path("fields/<int:pk>/edit/", field_edit, name="field_edit"),
    path("fields/<int:pk>/delete/", field_delete, name="field_delete"),
    path("fields/<int:pk>/update/", add_field_update, name="add_field_update"),

    path("agents/", agent_list, name="agent_list"),
    path("agents/add/", agent_create, name="agent_create"),
    path("agents/<int:pk>/delete/", agent_delete, name="agent_delete"),

    path("api/fields/", FieldListView.as_view(), name="api_field_list"),
    path("api/fields/<int:pk>/", FieldDetailView.as_view(), name="api_field_detail"),
    path("api/fields/<int:pk>/updates/", FieldUpdateCreateView.as_view(), name="api_field_update"),
    path("api/agents/", AgentListView.as_view(), name="api_agent_list"),
    path("api/dashboard/stats/", DashboardStatsView.as_view(), name="api_dashboard_stats"),
]