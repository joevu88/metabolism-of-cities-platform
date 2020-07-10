from django.contrib.sites.models import Site

from django.utils import timezone
import pytz

from core.models import RecordRelationship, Project, ProjectDesign, Work, WorkSprint, Notification
from django.conf import settings

def site(request):
    site = Site.objects.get_current()
    permissions = None
    open = None
    sprints = None
    notifications = None
    system_name_singular = None
    system_name_plural = None

    if hasattr(request, "project"):
        project = Project.objects.get(pk=request.project)
    else:
        project = Project.objects.get(pk=1)

    if project.slug == "data" or project.slug == "cityloops":
        system_name_singular = "city"
        system_name_plural = "cities"
    elif project.slug == "islands":
        system_name_singular = "island"
        system_name_plural = "islands"

    if request.user.is_authenticated and request.user.people:
        people = request.user.people
        permissions = RecordRelationship.objects.filter(
            record_parent_id = request.user.people.id, 
            record_child = project, 
            relationship__is_permission = True
        )
        open = Work.objects.filter(part_of_project=project, status=1, assigned_to__isnull=True).count()
        sprints = WorkSprint.objects.filter(projects=project, start_date__lte=timezone.now(), end_date__gte=timezone.now())
        notifications = Notification.objects.filter(people=request.user.people, is_read=False)

    design = ProjectDesign.objects.select_related("project").get(pk=project)

    return {
        "SITE_ID": site.id, 
        "SITE_URL": site.domain, 
        "SITE_NAME": site.name, 
        "MAPBOX_API_KEY": "pk.eyJ1IjoibWV0YWJvbGlzbW9mY2l0aWVzIiwiYSI6ImNqcHA5YXh6aTAxcmY0Mm8yMGF3MGZjdGcifQ.lVZaiSy76Om31uXLP3hw-Q", 
        "DEBUG": settings.DEBUG,
        "CURRENT_PAGE": request.get_full_path(),
        "PERMISSIONS": permissions,
        "PROJECT": project,
        "HEADER_STYLE": design.header,
        "DESIGN": design,
        "LOGO": design.logo.url if design.logo else None,
        "OPEN_TASKS": open,
        "SPRINTS": sprints,
        "NOTIFICATIONS": notifications,
        "SYSTEM_NAME_SINGULAR": system_name_singular,
        "SYSTEM_NAME_PLURAL": system_name_plural,
    }
