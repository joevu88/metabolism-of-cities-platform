from django.contrib.sites.models import Site

from core.models import RecordRelationship, Project, ProjectDesign, Work
from django.conf import settings

def site(request):
    site = Site.objects.get_current()
    permissions = open = None

    if hasattr(request, "project"):
        project = Project.objects.get(pk=request.project)
    else:
        project = Project.objects.get(pk=1)

    if request.user.is_authenticated and request.user.people:
        people = request.user.people
        permissions = RecordRelationship.objects.filter(
            record_parent_id = request.user.people.id, 
            record_child = project, 
            relationship__is_permission = True
        )
        open = Work.objects.filter(part_of_project=project, status=1, assigned_to__isnull=True).count()

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
        "BACK_LINK": design.back_link,
        "CUSTOM_CSS": design.custom_css,
        "LOGO": design.logo.url if design.logo else None,
        "OPEN_TASKS": open,
    }
