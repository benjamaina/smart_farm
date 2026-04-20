from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from fields.models import Field, FieldUpdate, UserProfile


def require_admin(view_func):
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, "profile") or not request.user.profile.is_admin():
            messages.error(request, "You do not have permission to access this page.")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)
    wrapper.__wrapped__ = view_func
    return login_required(wrapper)


def require_agent(view_func):
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, "profile") or not request.user.profile.is_agent():
            messages.error(request, "This page is for field agents only.")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)
    wrapper.__wrapped__ = view_func
    return login_required(wrapper)


@login_required
def dashboard(request):
    profile = getattr(request.user, "profile", None)

    if profile and profile.is_admin():
        fields = Field.objects.select_related("assigned_to").all()
        agents = User.objects.filter(profile__role=UserProfile.ROLE_AGENT)

        total = fields.count()
        active_count = sum(1 for f in fields if f.status == Field.STATUS_ACTIVE)
        at_risk_count = sum(1 for f in fields if f.status == Field.STATUS_AT_RISK)
        completed_count = sum(1 for f in fields if f.status == Field.STATUS_COMPLETED)

        stage_counts = {
            "planted": fields.filter(stage=Field.STAGE_PLANTED).count(),
            "growing": fields.filter(stage=Field.STAGE_GROWING).count(),
            "ready": fields.filter(stage=Field.STAGE_READY).count(),
            "harvested": fields.filter(stage=Field.STAGE_HARVESTED).count(),
        }

        recent_updates = FieldUpdate.objects.select_related("field", "agent").order_by("-created_at")[:10]

        context = {
            "fields": fields,
            "agents": agents,
            "total": total,
            "active_count": active_count,
            "at_risk_count": at_risk_count,
            "completed_count": completed_count,
            "stage_counts": stage_counts,
            "recent_updates": recent_updates,
            "is_admin": True,
        }
        return render(request, "fields/dashboard_admin.html", context)

    else:
        fields = Field.objects.filter(assigned_to=request.user).select_related("assigned_to")

        total = fields.count()
        active_count = sum(1 for f in fields if f.status == Field.STATUS_ACTIVE)
        at_risk_count = sum(1 for f in fields if f.status == Field.STATUS_AT_RISK)
        completed_count = sum(1 for f in fields if f.status == Field.STATUS_COMPLETED)

        context = {
            "fields": fields,
            "total": total,
            "active_count": active_count,
            "at_risk_count": at_risk_count,
            "completed_count": completed_count,
            "is_admin": False,
        }
        return render(request, "fields/dashboard_agent.html", context)


@require_admin
def field_list(request):
    fields = Field.objects.select_related("assigned_to").all()

    stage_filter = request.GET.get("stage")
    agent_filter = request.GET.get("agent")

    if stage_filter:
        fields = fields.filter(stage=stage_filter)
    if agent_filter:
        fields = fields.filter(assigned_to_id=agent_filter)

    agents = User.objects.filter(profile__role=UserProfile.ROLE_AGENT)

    context = {
        "fields": fields,
        "agents": agents,
        "stage_choices": Field.STAGE_CHOICES,
        "stage_filter": stage_filter,
        "agent_filter": agent_filter,
    }
    return render(request, "fields/field_list.html", context)


@require_admin
def field_create(request):
    agents = User.objects.filter(profile__role=UserProfile.ROLE_AGENT)

    if request.method == "POST":
        name = request.POST.get("name")
        crop_type = request.POST.get("crop_type")
        planting_date = request.POST.get("planting_date")
        stage = request.POST.get("stage", Field.STAGE_PLANTED)
        assigned_to_id = request.POST.get("assigned_to") or None
        notes = request.POST.get("notes", "")

        assigned_to = None
        if assigned_to_id:
            assigned_to = get_object_or_404(User, pk=assigned_to_id)

        try:
            field = Field(
                name=name,
                crop_type=crop_type,
                planting_date=planting_date,
                stage=stage,
                assigned_to=assigned_to,
                created_by=request.user,
                notes=notes,
            )
            field.save()
            messages.success(request, f'Field "{field.name}" created successfully.')
            return redirect("field_list")
        except ValidationError as e:
            messages.error(request, str(e))

    context = {
        "agents": agents,
        "stage_choices": Field.STAGE_CHOICES,
    }
    return render(request, "fields/field_form.html", context)


@require_admin
def field_edit(request, pk):
    field = get_object_or_404(Field, pk=pk)
    agents = User.objects.filter(profile__role=UserProfile.ROLE_AGENT)

    if request.method == "POST":
        field.name = request.POST.get("name")
        field.crop_type = request.POST.get("crop_type")
        field.planting_date = request.POST.get("planting_date")
        field.stage = request.POST.get("stage")
        assigned_to_id = request.POST.get("assigned_to") or None
        field.assigned_to = get_object_or_404(User, pk=assigned_to_id) if assigned_to_id else None
        field.notes = request.POST.get("notes", "")

        try:
            field.save()
            messages.success(request, f'Field "{field.name}" updated successfully.')
            return redirect("field_detail", pk=field.pk)
        except ValidationError as e:
            messages.error(request, str(e))

    context = {
        "field": field,
        "agents": agents,
        "stage_choices": Field.STAGE_CHOICES,
    }
    return render(request, "fields/field_form.html", context)


@login_required
def field_detail(request, pk):
    profile = getattr(request.user, "profile", None)

    if profile and profile.is_admin():
        field = get_object_or_404(Field.objects.select_related("assigned_to", "created_by"), pk=pk)
    else:
        field = get_object_or_404(
            Field.objects.select_related("assigned_to", "created_by"),
            pk=pk,
            assigned_to=request.user,
        )

    updates = field.updates.select_related("agent").all()

    context = {
        "field": field,
        "updates": updates,
        "stage_choices": Field.STAGE_CHOICES,
        "is_admin": profile and profile.is_admin(),
    }
    return render(request, "fields/field_detail.html", context)


@require_admin
def field_delete(request, pk):
    field = get_object_or_404(Field, pk=pk)

    if request.method == "POST":
        name = field.name
        field.delete()
        messages.success(request, f'Field "{name}" deleted.')
        return redirect("field_list")

    return render(request, "fields/field_confirm_delete.html", {"field": field})


@login_required
def add_field_update(request, pk):
    profile = getattr(request.user, "profile", None)

    if profile and profile.is_admin():
        field = get_object_or_404(Field, pk=pk)
    else:
        field = get_object_or_404(Field, pk=pk, assigned_to=request.user)

    if request.method == "POST":
        stage = request.POST.get("stage")
        notes = request.POST.get("notes", "").strip()

        if not notes:
            messages.error(request, "Notes are required for a field update.")
            return redirect("field_detail", pk=pk)

        with transaction.atomic():
            FieldUpdate.objects.create(
                field=field,
                agent=request.user,
                stage=stage,
                notes=notes,
            )
            field.stage = stage
            field.save()

        messages.success(request, "Field update recorded.")
        return redirect("field_detail", pk=pk)

    return redirect("field_detail", pk=pk)


@require_admin
def agent_list(request):
    agents = User.objects.filter(profile__role=UserProfile.ROLE_AGENT).prefetch_related("assigned_fields")
    context = {"agents": agents}
    return render(request, "fields/agent_list.html", context)


@require_admin
def agent_create(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")
        email = request.POST.get("email", "")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "fields/agent_form.html")

        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email,
            )
            UserProfile.objects.create(user=user, role=UserProfile.ROLE_AGENT)

        messages.success(request, f"Agent {username} created successfully.")
        return redirect("agent_list")

    return render(request, "fields/agent_form.html")


@require_admin
def agent_delete(request, pk):
    agent = get_object_or_404(User, pk=pk, profile__role=UserProfile.ROLE_AGENT)

    if request.method == "POST":
        username = agent.username
        agent.delete()
        messages.success(request, f"Agent {username} deleted.")
        return redirect("agent_list")

    return render(request, "fields/agent_confirm_delete.html", {"agent": agent})