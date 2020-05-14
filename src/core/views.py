from io import BytesIO

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.contrib.sites.models import Site
from django.contrib.auth import login
from django.http import Http404, HttpResponseRedirect

# These are used so that we can send mail
from django.core.mail import send_mail
from django.template.loader import render_to_string, get_template

from django.conf import settings

from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth import authenticate, login, logout


from collections import defaultdict
from .models import *
from stafdb.models import *

from django.contrib.sites.shortcuts import get_current_site

from django.template import Context
from django.forms import modelform_factory


from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration
from datetime import datetime
import csv

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.admin.utils import construct_change_message
from django.contrib.contenttypes.models import ContentType

from django.utils import timezone
import pytz

from functools import wraps
import json
import logging

logger = logging.getLogger(__name__)

# This array defines all the IDs in the database of the articles that are loaded for the
# various pages in the menu. Here we can differentiate between the different sites.

PAGE_ID = {
    "people": 12,
    "projects": 50,
    "library": 2,
    "multimedia_library": 3,
    "multiplicity": 4,
    "stafcp": 14,
    "platformu": 16,
    "ascus": 8,
    "podcast": 3458,
    "community": 18,
}

# This array does the same for user relationships

USER_RELATIONSHIPS = {
    "member": 1,
}

# This defines tags that are frequently used
TAG_ID = {
    "platformu_segments": 747,
    "case_study": 1,
    "urban": 11,
    "methodologies": 318,
}

def get_site_tag(request):
    if request.site.id == 1:
        # For MoC, the urban tag should be used to filter items
        return 11
    elif request.site.id == 2:
        # For MoI, the island tag should be used to filter items
        return 219       

def get_space(request, slug):
    # Here we can build an expansion if we want particular people to see dashboards that are under construction
    check = get_object_or_404(ActivatedSpace, slug=slug, site=request.site)
    return check.space

# Get all the child relationships, but making sure we only show is_deleted=False and is_public=True
def get_children(record):
    list = RecordRelationship.objects.filter(record_parent=record).filter(record_child__is_deleted=False, record_child__is_public=True)
    return list

# Get all the parent relationships, but making sure we only show is_deleted=False and is_public=True
def get_parents(record):
    list = RecordRelationship.objects.filter(record_child=record).filter(record_parent__is_deleted=False, record_parent__is_public=True)
    return list

# We use getHeader to obtain the header settings (type of header, title, subtitle, image)
# This dictionary has to be created for many different pages so by simply calling this
# function instead we don't repeat ourselves too often.
def load_design(context, project=1, webpage=None):
    project = project if project else 1
    design = ProjectDesign.objects.select_related("project").get(pk=project)
    page_design = header_title = header_subtitle = None
    if webpage:
        page_design = WebpageDesign.objects.filter(pk=webpage)
        if page_design:
            page_design = page_design[0]
    if "header_title" in context:
        header_title = context["header_title"]
    elif page_design and page_design.header_title:
        header_title = page_design.header_title
    if "header_subtitle" in context:
        header_subtitle = context["header_subtitle"]
    elif page_design and page_design.header_subtitle:
        header_subtitle = page_design.header_subtitle
        
    create_design = {
        "header_style": page_design.header if page_design and page_design.header and page_design.header != "inherit" else design.header,
        "header_title": header_title,
        "header_subtitle": header_subtitle,
        "header_image": page_design.header_image.huge.url if page_design and page_design.header_image else None,
        "back_link": design.back_link,
        "custom_css": page_design.custom_css if page_design and page_design.custom_css else design.custom_css,
        "logo": design.logo.url if design.logo else None,
        "breadcrumbs": None,
        "project": design.project,
        "webpage_id": webpage,
        "webpage_design_id": webpage if page_design else None,
    }

    return {**context, **create_design}


# General script to check if a user is part of a certain group
# This is used for validating access to certain pages only, so superusers
# must always have access.
def is_member(user, group):
    return user.is_superuser or user.groups.filter(name=group).exists()

# If users ARE logged in, but they try to access pages that they don't have
# access to, then we log this request for further debugging/review
def unauthorized_access(request):
    from django.core.exceptions import PermissionDenied
    logger.error("No access to this UploadSession")
    Work.objects.create(
        name = "Unauthorized access detected",
        description = request.META,
        priority = WorkPriority.HIGH,
    )
    raise PermissionDenied

# Authentication of users

def user_register(request, subsite=None):
    if request.method == "POST":
        password = request.POST.get("password")
        email = request.POST.get("email")
        name = request.POST.get("name")
        if not password:
            messages.error(request, "You did not enter a password.")
        else:
            check = User.objects.filter(email=email)
            if check:
                messages.error(request, "A user already exists with this e-mail address. Please log in or reset your password instead.")
            else:
                user = User.objects.create_user(email, email, password)
                user.first_name = name
                if subsite == "platformu":
                    user.is_superuser = False
                    user.is_staff = False
                    group = Group.objects.get(name="PlatformU Admin")
                    user.groups.add(group)
                    organization = Organization.objects.create(name=request.POST["organization"], type="other")
                    user_relationship = UserRelationship()
                    user_relationship.record = organization
                    user_relationship.user = user
                    user_relationship.relationship = Relationship.objects.get(pk=USER_RELATIONSHIPS["member"])
                    user_relationship.save()
                    redirect_page = "platformu_admin"
                else:
                    user.is_staff = True
                    user.is_superuser = True
                    redirect_page = "index"
                user.save()
                messages.success(request, "User was created.")
                login(request, user)

                mailcontext = {
                    "name": name,
                }
                msg_html = render_to_string("mailbody/welcome.html", mailcontext)
                msg_plain = render_to_string("mailbody/welcome.txt", mailcontext)
                sender = '"' + request.site.name + '" <' + settings.DEFAULT_FROM_EMAIL + '>'
                recipient = '"' + name + '" <' + email + '>'

                send_mail(
                    "Welcome to Metabolism of Cities",
                    msg_plain,
                    sender,
                    [recipient],
                    html_message=msg_html,
                )

                return redirect(redirect_page)

    context = {}
    if subsite:
        return render(request, "auth/register.html", load_design(context, PAGE_ID[subsite]))
    else:
        return render(request, "auth/register.html", context)

def user_login(request, project=None):

    if project:
        project = get_object_or_404(Project, pk=project)
        redirect_url = project.url
    else:
        redirect_url = "index"

    if request.user.is_authenticated:
        return redirect(redirect_url)

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "You are logged in.")
            return redirect(redirect_url)
        else:
            messages.error(request, "We could not authenticate you, please try again.")

    context = {}
    return render(request, "auth/login.html", load_design(context, project))

def user_logout(request, project=None):
    logout(request)
    messages.warning(request, "You are now logged out")
    if project:
        info = Project.objects.get(pk=project)
        return redirect(info.url)
    else:
        return redirect("login")

def user_reset(request):
    return render(request, "auth/reset.html")

def user_profile(request):
    user = request.user
    organizations = UserRelationship.objects.filter(relationship__id=USER_RELATIONSHIPS["member"], user=user)
    context = {
        "organizations": organizations,
    }
    return render(request, "auth/profile.html", context)

# Homepage

def index(request):
    context = {
        "header_title": "Metabolism of Cities",
        "header_subtitle": "Your hub for anyting around urban metabolism",
        "show_project_design": True,
    }
    return render(request, "index.html", load_design(context))

# The template section allows contributors to see how some
# commonly used elements are coded, and allows them to copy/paste

def templates(request):
    return render(request, "template/index.html")

def template(request, slug):
    page = "template/" + slug + ".html"
    return render (request, page)

# The internal projects section

def projects(request):
    article = get_object_or_404(Webpage, pk=PAGE_ID["projects"])
    context = {
        "list": Project.objects.all(),
        "article": article,
        "header_title": "Projects",
        "header_subtitle": "Overview of projects undertaken by the Metabolism of Cities community",
    }
    return render(request, "projects.html", load_design(context))

def project(request, id):
    article = get_object_or_404(Webpage, pk=PAGE_ID["projects"])
    info = get_object_or_404(Project, pk=id)
    context = {
        "edit_link": "/admin/core/project/" + str(info.id) + "/change/",
        "info": info,
        "team": People.objects.filter(parent_list__record_child=info, parent_list__relationship__name="Team member"),
        "alumni": People.objects.filter(parent_list__record_child=info, parent_list__relationship__name="Former team member"),
        "header_title": str(info),
        "header_subtitle_link": "<a href='/projects/'>Projects</a>",
        "show_relationship": info.id,
    }
    return render(request, "project.html", load_design(context))

# Webpage is used for general web pages, and they can be opened in
# various ways (using ID, using slug). They can have different presentational formats

def article(request, id=None, slug=None, prefix=None, project=None, subtitle=None):
    if id:
        info = get_object_or_404(Webpage, pk=id, site=request.site)
        if info.is_deleted and not request.user.is_staff:
            raise Http404("Webpage not found")
    elif slug:
        if prefix:
            slug = prefix + slug
        slug = slug + "/"
        info = get_object_or_404(Webpage, slug=slug, site=request.site)

    if not project:
        project = info.belongs_to.id

    context = {
        "info": info,
        "header_title": info.name,
        "header_subtitle": subtitle,
        "webpage": info,
    }
    return render(request, "article.html", load_design(context, project, info.id))

def article_list(request, id):
    info = get_object_or_404(Webpage, pk=id)
    list = Webpage.objects.filter(parent=info)
    context = {
        "info": info,
        "list": list,
    }
    return render(request, "article.list.html", context)




# Cities

def datahub(request):
    list = ActivatedSpace.objects.filter(site=request.site)
    context = {
        "show_project_design": True,
        "list": list,
    }
    return render(request, "data/index.html", load_design(context, PAGE_ID["multiplicity"]))

def datahub_overview(request):
    list = ActivatedSpace.objects.filter(site=request.site)
    context = {
        "list": list,
    }
    return render(request, "data/overview.html", load_design(context, PAGE_ID["multiplicity"]))

def datahub_dashboard(request, space):
    space = get_space(request, space)
    context = {
        "space": space,
        "header_image": space.photo,
        "dashboard": True,
    }
    return render(request, "data/dashboard.html", load_design(context, PAGE_ID["multiplicity"]))

def datahub_photos(request, space):
    space = get_space(request, space)
    context = {
        "space": space,
        "header_image": space.photo,
        "photos": Photo.objects.filter(space=space),
    }
    return render(request, "data/photos.html", load_design(context, PAGE_ID["multiplicity"]))

def datahub_maps(request, space):
    space = get_space(request, space)
    context = {
        "space": space,
        "header_image": space.photo,
    }
    return render(request, "data/maps.html", load_design(context, PAGE_ID["multiplicity"]))

def datahub_library(request, space, type):
    space = get_space(request, space)
    list = LibraryItem.objects.filter(spaces=space)
    if type == "articles":
        title = "Journal articles"
        list = list.filter(type__group="academic")
    elif type == "reports":
        list = list.filter(type__group="reports")
        title = "Reports"
    elif type == "theses":
        list = list.filter(type__group="theses")
        title = "Theses"
    context = {
        "space": space,
        "header_image": space.photo,
        "title": title,
        "items": list,
    }
    return render(request, "data/library.html", load_design(context, PAGE_ID["multiplicity"]))

def datahub_sector(request, space, sector):
    context = {
    }
    return render(request, "data/sector.html", load_design(context, PAGE_ID["multiplicity"]))

def datahub_dataset(request, space, dataset):
    context = {
    }
    return render(request, "data/dataset.html", load_design(context, PAGE_ID["multiplicity"]))

# Metabolism Manager

def metabolism_manager(request):
    info = get_object_or_404(Project, pk=PAGE_ID["platformu"])
    context = {
        "show_project_design": True,
    }
    return render(request, "metabolism_manager/index.html", load_design(context, PAGE_ID["platformu"]))

def metabolism_manager_admin(request):
    organizations = UserRelationship.objects.filter(relationship__id=USER_RELATIONSHIPS["member"], user=request.user)
    if organizations.count() == 1:
        id = organizations[0].record.id
        return redirect(reverse("platformu_admin_clusters", args=[id]))
    context = {
        "organizations": organizations,
    }
    return render(request, "metabolism_manager/admin/index.html", load_design(context, PAGE_ID["platformu"]))

def metabolism_manager_clusters(request, organization):
    my_organization = Organization.objects.get(pk=organization)
    if request.method == "POST":
        Tag.objects.create(
            name = request.POST["name"],
            parent_tag = Tag.objects.get(pk=TAG_ID["platformu_segments"]),
            belongs_to = my_organization,
        )
    context = {
        "info": my_organization,
        "tags": Tag.objects.filter(belongs_to=organization, parent_tag__id=TAG_ID["platformu_segments"]).order_by("id"),
        "my_organization": my_organization,
    }
    return render(request, "metabolism_manager/admin/clusters.html", load_design(context, PAGE_ID["platformu"]))

def metabolism_manager_admin_map(request, organization):
    my_organization = Organization.objects.get(pk=organization)
    context = {
        "page": "map",
        "my_organization": my_organization,
    }
    return render(request, "metabolism_manager/admin/map.html", load_design(context, PAGE_ID["platformu"]))

def metabolism_manager_admin_entity(request, organization, id):
    my_organization = Organization.objects.get(pk=organization)
    context = {
        "page": "entity",
        "my_organization": my_organization,
        "info": Organization.objects.get(pk=id),
    }
    return render(request, "metabolism_manager/admin/entity.html", load_design(context, PAGE_ID["platformu"]))

def metabolism_manager_admin_entity_form(request, organization, id=None):
    my_organization = Organization.objects.get(pk=organization)
    edit = False
    if id:
        info = Organization.objects.get(pk=id)
        edit = True
    else:
        info = None
    if request.method == "POST":
        if not edit:
            info = Organization()
        info.name = request.POST["name"]
        info.description = request.POST["description"]
        info.url = request.POST["url"]
        info.email = request.POST["email"]
        if "status" in request.POST:
            info.is_deleted = False
        else:
            info.is_deleted = True
        if "image" in request.FILES:
            info.image = request.FILES["image"]
        info.save()
        if "tag" in request.GET:
            tag = Tag.objects.get(pk=request.GET["tag"])
            info.tags.add(tag)
        messages.success(request, "The information was saved.")
        if edit:
            return redirect(reverse("platformu_admin_entity", args=[my_organization.id, info.id]))
        else:
            return redirect(reverse("platformu_admin_clusters", args=[my_organization.id]))
    context = {
        "page": "entity_form",
        "my_organization": my_organization,
        "info": info,
        "sectors": Sector.objects.all(),
    }
    return render(request, "metabolism_manager/admin/entity.form.html", load_design(context, PAGE_ID["platformu"]))

def metabolism_manager_admin_entity_users(request, organization, id=None):
    my_organization = Organization.objects.get(pk=organization)
    info = Organization.objects.get(pk=id)
    context = {
        "page": "entity_users",
        "my_organization": my_organization,
        "info": info,
    }
    return render(request, "metabolism_manager/admin/entity.users.html", load_design(context, PAGE_ID["platformu"]))

def metabolism_manager_admin_entity_materials(request, organization, id):
    my_organization = Organization.objects.get(pk=organization)
    info = Organization.objects.get(pk=id)
    context = {
        "page": "entity_materials",
        "my_organization": my_organization,
        "info": info,
    }
    return render(request, "metabolism_manager/admin/entity.materials.html", load_design(context, PAGE_ID["platformu"]))

def metabolism_manager_admin_entity_material(request, organization, id):
    my_organization = Organization.objects.get(pk=organization)
    info = Organization.objects.get(pk=id)
    context = {
        "page": "entity_materials",
        "my_organization": my_organization,
        "info": info,
    }
    return render(request, "metabolism_manager/admin/entity.material.html", load_design(context, PAGE_ID["platformu"]))

def metabolism_manager_admin_entity_data(request, organization, id):
    my_organization = Organization.objects.get(pk=organization)
    info = Organization.objects.get(pk=id)
    context = {
        "page": "entity_data",
        "my_organization": my_organization,
        "info": info,
    }
    return render(request, "metabolism_manager/admin/entity.data.html", load_design(context, PAGE_ID["platformu"]))

def metabolism_manager_admin_entity_log(request, organization, id):
    my_organization = Organization.objects.get(pk=organization)
    info = Organization.objects.get(pk=id)
    context = {
        "page": "entity_log",
        "my_organization": my_organization,
        "info": info,
    }
    return render(request, "metabolism_manager/admin/entity.log.html", load_design(context, PAGE_ID["platformu"]))

def metabolism_manager_admin_entity_user(request, organization, id, user=None):
    my_organization = Organization.objects.get(pk=organization)
    info = Organization.objects.get(pk=id)
    context = {
        "page": "entity_form",
        "my_organization": my_organization,
        "info": info,
    }
    return render(request, "metabolism_manager/admin/entity.user.html", load_design(context, PAGE_ID["platformu"]))

def metabolism_manager_dashboard(request):
    my_organization = Organization.objects.get(pk=organization)
    info = Organization.objects.get(pk=id)
    context = {
        "page": "dashboard",
        "my_organization": my_organization,
        "info": info,
    }
    return render(request, "metabolism_manager/dashboard.html", load_design(context, PAGE_ID["platformu"]))

def metabolism_manager_material(request):
    my_organization = Organization.objects.get(pk=organization)
    context = {
        "page": "material",
        "my_organization": my_organization,
        "info": info,
    }
    return render(request, "metabolism_manager/material.html", load_design(context, PAGE_ID["platformu"]))

def metabolism_manager_material_form(request):
    my_organization = Organization.objects.get(pk=organization)
    context = {
        "page": "material",
        "my_organization": my_organization,
        "info": info,
    }
    return render(request, "metabolism_manager/material.form.html", load_design(context, PAGE_ID["platformu"]))

def metabolism_manager_report(request):
    my_organization = Organization.objects.get(pk=organization)
    context = {
        "page": "report",
        "my_organization": my_organization,
        "info": info,
    }
    return render(request, "metabolism_manager/report.html", load_design(context, PAGE_ID["platformu"]))

def metabolism_manager_marketplace(request):
    context = {
        "page": "marketplace",
    }
    return render(request, "metabolism_manager/marketplace.html", load_design(context, PAGE_ID["platformu"]))

def metabolism_manager_forum(request):
    article = get_object_or_404(Webpage, pk=17)
    list = ForumMessage.objects.filter(parent__isnull=True)
    context = {
        "list": list,
    }
    return render(request, "forum.list.html", load_design(context, PAGE_ID["platformu"]))

# STAFCP

def stafcp(request):
    context = {
        "show_project_design": True,
    }
    return render(request, "stafcp/index.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_review(request):
    context = {
    }
    return render(request, "stafcp/review/index.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_review_pending(request):
    context = {
        "list": UploadSession.objects.filter(is_uploaded=False),
    }
    return render(request, "stafcp/review/files.pending.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_review_uploaded(request):
    context = {
        "list": UploadSession.objects.filter(is_uploaded=True, is_processed=False),
    }
    return render(request, "stafcp/review/files.uploaded.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_review_processed(request):
    context = {
    }
    return render(request, "stafcp/review/files.processed.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_review_session(request, id):
    session = get_object_or_404(UploadSession, pk=id)
    if session.user is not request.user and not is_member(request.user, "Data administrators"):
        unauthorized_access(request)
    context = {
    }
    return render(request, "stafcp/review/session.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_upload_gis(request, id=None):
    context = {
        "design_link": "/admin/core/articledesign/" + str(PAGE_ID["stafcp"]) + "/change/",
        "list": GeocodeScheme.objects.filter(is_deleted=False),
        "geocodes": Geocode.objects.filter(is_deleted=False, scheme__is_deleted=False),
    }
    return render(request, "stafcp/upload/gis.html", load_design(context, PAGE_ID["stafcp"]))

@login_required
def stafcp_upload_gis_file(request, id=None):
    if request.method == "POST":
        session = UploadSession.objects.create(user=request.user, name=request.POST.get("name"))
        for each in request.FILES.getlist("file"):
            UploadFile.objects.create(
                session = session,
                file = each,
            )
        return redirect("stafcp_upload_gis_verify", id=session.id)
    context = {
    }
    return render(request, "stafcp/upload/gis.file.html", load_design(context, PAGE_ID["stafcp"]))

@login_required
def stafcp_upload(request):
    context = {
    }
    return render(request, "stafcp/upload/index.html", load_design(context, PAGE_ID["stafcp"]))

@login_required
def stafcp_upload_gis_verify(request, id):
    import shapefile
    session = get_object_or_404(UploadSession, pk=id)
    if session.user is not request.user and not is_member(request.user, "Data administrators"):
        unauthorized_access(request)
    files = UploadFile.objects.filter(session=session)
    geojson = None
    try:
        shape = shapefile.Reader(settings.MEDIA_ROOT + "/" + files[0].file.name)
        feature = shape.shape(0)
        geojson = feature.__geo_interface__ 
        geojson = json.dumps(geojson) 
    except Exception as e:
        messages.error(request, "Your file could not be loaded. Please review the error below.<br><strong>" + str(e) + "</strong>")
    context = {
        "geojson": geojson,
        "session": session,
    }
    return render(request, "stafcp/upload/gis.verify.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_upload_gis_meta(request, id):
    session = get_object_or_404(UploadSession, pk=id)
    if session.user is not request.user and not is_member(request.user, "Data administrators"):
        unauthorized_access(request)
    if request.method == "POST":
        session.is_uploaded = True
        session.meta_data = request.POST
        session.save()
        messages.success(request, "Thanks, the information has been uploaded! Our review team will review and process your information.")
        return redirect("stafcp_upload")
    context = {
        "session": session,
    }
    return render(request, "stafcp/upload/gis.meta.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_referencespaces(request, group=None):
    list = geocodes = None
    if group == "administrative":
        list = GeocodeScheme.objects.filter(is_deleted=False).exclude(name__startswith="Sector").exclude(name__startswith="Subdivision")
        geocodes = Geocode.objects.filter(is_deleted=False).exclude(scheme__name__startswith="Sector").exclude(scheme__name__startswith="Subdivision")
    elif group == "national":
        list = GeocodeScheme.objects.filter(is_deleted=False, name__startswith="Subdivision")
        geocodes = Geocode.objects.filter(is_deleted=False, scheme__name__startswith="Subdivision")
    elif group == "sectoral":
        list = GeocodeScheme.objects.filter(is_deleted=False, name__startswith="Sector")
        geocodes = Geocode.objects.filter(is_deleted=False, scheme__name__startswith="Sector")
    context = {
        "list": list,
        "geocodes": geocodes,
    }
    return render(request, "stafcp/referencespaces.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_referencespaces_list(request, id):
    geocode = get_object_or_404(Geocode, pk=id)
    context = {
        "list": ReferenceSpace.objects.filter(geocodes=geocode),
        "geocode": geocode,
        "load_datatables": True,
    }
    return render(request, "stafcp/referencespaces.list.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_referencespace(request, id):
    info = ReferenceSpace.objects.get(pk=id)
    this_location = info.location.geometry
    inside_the_space = ReferenceSpace.objects.filter(location__geometry__contained=this_location).order_by("name").prefetch_related("geocodes").exclude(pk=id)
    context = {
        "info": info,
        "location": info.location,
        "inside_the_space":inside_the_space,
        "load_datatables": True,
    }
    return render(request, "stafcp/referencespace.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_activities_catalogs(request):
    context = {
        "list": ActivityCatalog.objects.all(),
    }
    return render(request, "stafcp/activities.catalogs.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_activities(request, catalog, id=None):
    catalog = ActivityCatalog.objects.get(pk=catalog)
    list = Activity.objects.filter(catalog=catalog)
    if id:
        list = list.filter(parent_id=id)
    else:
        list = list.filter(parent__isnull=True)
    context = {
        "list": list,
    }
    return render(request, "stafcp/activities.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_activity(request, catalog, id):
    list = Activity.objects.all()
    context = {
        "list": list,
    }
    return render(request, "stafcp/activities.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_flowdiagrams(request):
    list = FlowDiagram.objects.all()
    context = {
        "list": list,
    }
    return render(request, "stafcp/flowdiagrams.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_flowdiagram(request, id):
    activities = Activity.objects.all()
    context = {
        "design_link": "/admin/core/articledesign/" + str(PAGE_ID["stafcp"]) + "/change/",
        "activities": activities,
        "load_select2": True,
        "load_mermaid": True,
    }
    return render(request, "stafcp/flowdiagram.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_flowdiagram_form(request, id):
    info = get_object_or_404(FlowDiagram, pk=id)
    if request.method == "POST":
        if "delete" in request.POST:
            item = FlowBlocks.objects.filter(diagram=info, pk=request.POST["delete"])
            if item:
                item.delete()
                messages.success(request, "This block was removed.")
        else:
            FlowBlocks.objects.create(
                diagram = info,
                origin_id = request.POST["from"],
                destination_id = request.POST["to"],
                origin_label = request.POST["from_label"],
                destination_label = request.POST["to_label"],
                description = request.POST["label"],
            )
            messages.success(request, "The information was saved.")
    blocks = info.blocks.all()
    activities = Activity.objects.all()
    context = {
        "design_link": "/admin/core/articledesign/" + str(PAGE_ID["stafcp"]) + "/change/",
        "activities": activities,
        "load_select2": True,
        "load_mermaid": True,
        "info": info,
        "blocks": blocks,
    }
    return render(request, "stafcp/flowdiagram.form.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_flowdiagram_meta(request, id=None):
    ModelForm = modelform_factory(FlowDiagram, fields=("name", "description"))
    if id:
        info = FlowDiagram.objects.get(pk=id)
        form = ModelForm(request.POST or None, instance=info)
    else:
        info = None
        form = ModelForm(request.POST or None)
    if request.method == "POST":

        if form.is_valid():
            info = form.save()
            messages.success(request, "The information was saved.")
            return redirect(reverse("stafcp_flowdiagram_form", args=[info.id]))
        else:
            messages.error(request, "The form could not be saved, please review the errors below.")
    context = {
        "info": info,
        "form": form,
        "load_mermaid": True,
    }
    return render(request, "stafcp/flowdiagram.meta.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_geocodes(request):
    context = {
        "list": GeocodeScheme.objects.all(),
    }
    return render(request, "stafcp/geocode/list.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_geocode(request, id):
    info = GeocodeScheme.objects.get(pk=id)
    geocodes = info.geocodes.all()
    context = {
        "info": info,
        "geocodes": geocodes,
        "load_mermaid": True,
    }
    return render(request, "stafcp/geocode/view.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_geocode_form(request, id=None):
    ModelForm = modelform_factory(GeocodeScheme, fields=("name", "description", "url"))
    if id:
        info = GeocodeScheme.objects.get(pk=id)
        form = ModelForm(request.POST or None, instance=info)
        add = False
        geocodes = info.geocodes.all()
    else:
        info = None
        form = ModelForm(request.POST or None)
        add = True
        geocodes = Geocode()
    if request.method == "POST":
        if form.is_valid():
            info = form.save()
            change_message = construct_change_message(form, None, add)
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(GeocodeScheme).pk,
                object_id=info.id,
                object_repr=info.name,
                action_flag=CHANGE if not add else ADDITION,
                change_message=change_message,
            )
            geocodes = zip(
                request.POST.getlist("geocode_level"),
                request.POST.getlist("geocode_name"),
            )
            for level, name in geocodes:
                Geocode.objects.create(
                    scheme = info,
                    name = name,
                    depth = level,
                )
            messages.success(request, "The information was saved.")
            return redirect(info.get_absolute_url())
        else:
            messages.error(request, "The form could not be saved, please review the errors below.")
    context = {
        "info": info,
        "form": form,
        "load_mermaid": True,
        "depths": range(1,11),
        "geocodes": geocodes,
    }
    return render(request, "stafcp/geocode/form.html", load_design(context, PAGE_ID["stafcp"]))

def stafcp_article(request, id):
    context = {
        "design_link": "/admin/core/articledesign/" + str(PAGE_ID["stafcp"]) + "/change/",

    }
    return render(request, "stafcp/index.html", load_design(context, PAGE_ID["stafcp"]))

# Library

def library(request):
    context = {
        "show_project_design": True,
    }
    return render(request, "library/browse.html", load_design(context, PAGE_ID["library"]))

def library_search(request, article):
    info = get_object_or_404(Webpage, pk=article)
    context = {
        "article": info,
    }
    return render(request, "library/search.html", load_design(context, PAGE_ID["library"]))

def library_download(request):
    info = get_object_or_404(Webpage, pk=PAGE_ID["library"])
    context = {
        "design_link": "/admin/core/articledesign/" + str(info.id) + "/change/",
        "info": info,
        "menu": Webpage.objects.filter(parent=info),
    }
    return render(request, "article.html", load_design(context, PAGE_ID["library"]))

def library_casestudies(request, slug=None):
    list = LibraryItem.objects.filter(status="active", tags__id=TAG_ID["case_study"])
    list = list.filter(tags__id=get_site_tag(request))
    totals = None
    page = "casestudies.html"
    if slug == "calendar":
        page = "casestudies.calendar.html"
        totals = list.values("year").annotate(total=Count("id")).order_by("year")
    context = {
        "list": list,
        "totals": totals,
        "load_datatables": True,
        "slug": slug,
    }
    return render(request, "library/" + page, load_design(context, PAGE_ID["library"]))

def library_journals(request, article):
    info = get_object_or_404(Webpage, pk=article)
    list = Organization.objects.prefetch_related("parent_to").filter(type="journal")
    context = {
        "article": info,
        "list": list,
    }
    return render(request, "library/journals.html", load_design(context, PAGE_ID["library"]))

def library_journal(request, slug):
    info = get_object_or_404(Organization, type="journal", slug=slug)
    context = {
        "info": info,
        "items": info.publications,
    }
    return render(request, "library/journal.html", load_design(context, PAGE_ID["library"]))

def library_item(request, id):
    info = get_object_or_404(LibraryItem, pk=id)
    section = "library"
    if info.type.group == "multimedia":
        section = "multimedia_library"
    context = {
        "info": info,
    }
    return render(request, "library/item.html", load_design(context, PAGE_ID[section]))

def library_map(request, article):
    info = get_object_or_404(Webpage, pk=article)
    items = LibraryItem.objects.filter(status="active", tags__id=TAG_ID["case_study"])
    items = items.filter(tags__id=get_site_tag(request))
    context = {
        "article": info,
        "items": items,
    }
    return render(request, "library/map.html", load_design(context, PAGE_ID["library"]))

def library_authors(request):
    info = get_object_or_404(Webpage, pk=PAGE_ID["library"])
    context = {
        "design_link": "/admin/core/articledesign/" + str(info.id) + "/change/",
        "info": info,
        "menu": Webpage.objects.filter(parent=info),
    }
    return render(request, "article.html", load_design(context, PAGE_ID["library"]))

def library_contribute(request):
    info = get_object_or_404(Webpage, pk=PAGE_ID["library"])
    context = {
        "design_link": "/admin/core/articledesign/" + str(info.id) + "/change/",
        "info": info,
        "menu": Webpage.objects.filter(parent=info),
    }
    return render(request, "article.html", load_design(context, PAGE_ID["library"]))

# People

def person(request, id):
    article = get_object_or_404(Webpage, pk=PAGE_ID["people"])
    info = get_object_or_404(People, pk=id)
    context = {
        "edit_link": "/admin/core/people/" + str(info.id) + "/change/",
        "info": info,
    }
    return render(request, "person.html", context)

def people_list(request):
    info = get_object_or_404(Webpage, pk=PAGE_ID["people"])
    context = {
        "edit_link": "/admin/core/article/" + str(info.id) + "/change/",
        "info": info,
        "list": People.objects.all(),
    }
    return render(request, "people.list.html", context)

# NEWS AND EVENTS

def news_list(request):
    article = get_object_or_404(Webpage, pk=15)
    list = News.objects.all()
    context = {
        "list": list[3:],
        "shortlist": list[:3],
        "add_link": "/admin/core/news/add/"
    }
    return render(request, "news.list.html", load_design(context, PAGE_ID["community"]))

def news(request, id):
    article = get_object_or_404(Webpage, pk=15)
    context = {
        "info": get_object_or_404(News, pk=id),
        "latest": News.objects.all()[:3],
        "edit_link": "/admin/core/news/" + str(id) + "/change/"
    }
    return render(request, "news.html", context)

def event_list(request):
    article = get_object_or_404(Webpage, pk=47)
    today = timezone.now().date()
    context = {
        "upcoming": Event.objects.filter(end_date__gte=today).order_by("start_date"),
        "archive": Event.objects.filter(end_date__lt=today),
        "add_link": "/admin/core/event/add/",
        "header_title": "Events",
        "header_subtitle": "Find out what is happening around you!",
    }
    return render(request, "event.list.html", load_design(context, PAGE_ID["community"]))

def event(request, id):
    article = get_object_or_404(Webpage, pk=16)
    info = get_object_or_404(Event, pk=id)
    header["title"] = info.name
    today = timezone.now().date()
    context = {
        "header": header,
        "info": info,
        "upcoming": Event.objects.filter(end_date__gte=today).order_by("start_date")[:3],
    }
    return render(request, "event.html", context)

# FORUM

def forum_list(request):
    article = get_object_or_404(Webpage, pk=17)
    list = ForumMessage.objects.filter(parent__isnull=True)
    context = {
        "list": list,
    }
    return render(request, "forum.list.html", context)

def forum_topic(request, id):
    article = get_object_or_404(Webpage, pk=17)
    info = get_object_or_404(ForumMessage, pk=id)
    list = ForumMessage.objects.filter(parent=id)
    context = {
        "info": info,
        "list": list,
    }
    if request.method == "POST":

        new = ForumMessage()
        new.name = "Reply to: "+ info.name
        new.description = request.POST["text"]
        new.parent = info
        new.user = request.user
        new.save()

        if request.FILES:
            files = request.FILES.getlist("file")
            for file in files:
                info_document = Document()
                info_document.file = file
                info_document.save()
                new.documents.add(info_document)
        messages.success(request, "Your message has been posted.")
    return render(request, "forum.topic.html", context)

def forum_form(request, id=False):
    article = get_object_or_404(Webpage, pk=17)
    context = {
    }
    if request.method == "POST":
        new = ForumMessage()
        new.name = request.POST["name"]
        new.description = request.POST["text"]
        new.user = request.user
        new.save()

        if request.FILES:
            files = request.FILES.getlist("file")
            for file in files:
                info_document = Document()
                info_document.file = file
                info_document.save()
                new.documents.add(info_document)
        messages.success(request, "Your message has been posted.")
        return redirect(new.get_absolute_url())
    return render(request, "forum.form.html", context)

# Podcast series

def podcast_series(request):
    webpage = get_object_or_404(Project, pk=PAGE_ID["podcast"])
    list = LibraryItem.objects.filter(type__name="Podcast").order_by("-date_created")
    context = {
        "show_project_design": True,
        "webpage": webpage,
        "header_title": "Podcast Series",
        "header_subtitle": "Agressive questions. Violent answers.",
        "list": list,
    }
    return render(request, "podcast/index.html", load_design(context, PAGE_ID["podcast"]))

# Community hub

def community(request):
    webpage = get_object_or_404(Project, pk=PAGE_ID["community"])
    context = {
        "show_project_design": True,
        "webpage": webpage,
        "header_title": "Welcome!",
        "header_subtitle": "Join for the money. Stay for the food.",
        "list": list,
    }
    return render(request, "community/index.html", load_design(context, PAGE_ID["community"]))


# MULTIMEDIA

def multimedia(request):
    webpage = get_object_or_404(Project, pk=PAGE_ID["multimedia_library"])
    videos = Video.objects.all().order_by("-date_created")[:5]
    podcasts = LibraryItem.objects.filter(type__name="Podcast").order_by("-date_created")[:5]
    dataviz = LibraryItem.objects.filter(type__name="Image").order_by("-date_created")[:5]
    context = {
        "edit_link": "/admin/core/project/" + str(webpage.id) + "/change/",
        "show_project_design": True,
        "webpage": webpage,
        "videos": videos,
        "podcasts": podcasts,
        "dataviz": dataviz,
    }
    return render(request, "multimedia/index.html", load_design(context, PAGE_ID["multimedia_library"]))

def video_list(request):
    context = {
        "webpage": get_object_or_404(Webpage, pk=61),
        "list": LibraryItem.objects.filter(type__name="Video Recording"),
    }
    return render(request, "multimedia/video.list.html", load_design(context, PAGE_ID["multimedia_library"]))

def video(request, id):
    context = {
        "info": get_object_or_404(Video, pk=id),
    }
    return render(request, "multimedia/video.html", load_design(context, PAGE_ID["multimedia_library"]))

def podcast_list(request):
    context = {
        "info": get_object_or_404(Webpage, pk=62),
        "list": LibraryItem.objects.filter(type__name="Podcast"),
        "load_datatables": True,
    }
    return render(request, "multimedia/podcast.list.html", load_design(context, PAGE_ID["multimedia_library"]))

def podcast(request, id):
    context = {
        "info": get_object_or_404(Video, pk=id),
    }
    return render(request, "multimedia/podcast.html", load_design(context, PAGE_ID["multimedia_library"]))

def dataviz_list(request):
    context = {
        "info": get_object_or_404(Webpage, pk=67),
        "list": LibraryItem.objects.filter(type__name="Image"),
    }
    return render(request, "multimedia/dataviz.list.html", load_design(context, PAGE_ID["multimedia_library"]))

def dataviz(request, id):
    info = get_object_or_404(LibraryItem, pk=id)
    parents = get_parents(info)
    context = {
        "info": info,
        "parents": parents,
        "show_relationship": info.id,
    }
    return render(request, "multimedia/dataviz.html", load_design(context, PAGE_ID["multimedia_library"]))

# AScUS conference

def check_ascus_access(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        global PAGE_ID
        check_participant = None
        if not request.user.is_authenticated:
            return redirect("/login/")
        if request.user.is_authenticated and hasattr(request.user, "people"):
            check_participant = RecordRelationship.objects.filter(
                record_parent = request.user.people,
                record_child_id = PAGE_ID["ascus"],
                relationship__name = "Participant",
            )
        if not check_participant or not check_participant.exists():
            return redirect("/register/?existing=true")
        else:
            check_organizer = RecordRelationship.objects.filter(
                record_parent = request.user.people,
                record_child_id = PAGE_ID["ascus"],
                relationship__name = "Organizer",
            )
            if check_organizer.exists():
                request.user.is_ascus_organizer = True
            return function(request, *args, **kwargs)
    return wrap

def check_ascus_admin_access(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        global PAGE_ID
        check_organizer = None
        if not request.user.is_authenticated:
            return redirect("/login/")
        if request.user.is_authenticated and hasattr(request.user, "people"):
            check_organizer = RecordRelationship.objects.filter(
                record_parent = request.user.people,
                record_child_id = PAGE_ID["ascus"],
                relationship__name = "Organizer",
            )
        if not check_organizer.exists():
            return redirect("/register/?existing=true")
        else:
            request.user.is_ascus_organizer = True
            return function(request, *args, **kwargs)
    return wrap

def ascus(request):
    context = {
        "show_project_design": True,
        "header_title": "AScUS Unconference",
        "header_subtitle": "Actionable Science for Urban Sustainability · 3-5 June 2020",
        "edit_link": "/admin/core/project/" + str(PAGE_ID["ascus"]) + "/change/",
        "info": get_object_or_404(Project, pk=PAGE_ID["ascus"]),
        "show_relationship": PAGE_ID["ascus"],
    }
    return render(request, "article.html", load_design(context, PAGE_ID["ascus"]))

@check_ascus_access
def ascus_account(request):
    my_discussions = Event.objects_include_private \
        .filter(child_list__record_parent=request.user.people) \
        .filter(parent_list__record_child__id=PAGE_ID["ascus"]) \
        .filter(tags__id=770)
    my_presentations = LibraryItem.objects_include_private \
        .filter(child_list__record_parent=request.user.people) \
        .filter(parent_list__record_child__id=PAGE_ID["ascus"]) \
        .filter(tags__id=771)
    my_intro = LibraryItem.objects_include_private \
        .filter(child_list__record_parent=request.user.people) \
        .filter(parent_list__record_child__id=PAGE_ID["ascus"]) \
        .filter(tags__id=769)
    my_roles = RecordRelationship.objects.filter(
        record_parent = request.user.people, 
        record_child__id = PAGE_ID["ascus"],
    )
    show_discussion = show_abstract = False
    for each in my_roles:
        if each.relationship.name == "Session organizer":
            show_discussion = True
        elif each.relationship.name == "Presenter":
            show_abstract = True
    context = {
        "header_title": "My Account",
        "header_subtitle": "Actionable Science for Urban Sustainability · 3-5 June 2020",
        "edit_link": "/admin/core/project/" + str(PAGE_ID["ascus"]) + "/change/",
        "info": get_object_or_404(Project, pk=PAGE_ID["ascus"]),
        "my_discussions": my_discussions,
        "my_presentations": my_presentations,
        "my_intro": my_intro,
        "show_discussion": show_discussion, 
        "show_abstract": show_abstract,
    }
    return render(request, "ascus/account.html", load_design(context, PAGE_ID["ascus"]))

@check_ascus_access
def ascus_account_edit(request):
    info = get_object_or_404(Webpage, slug="/ascus/account/edit/")
    ModelForm = modelform_factory(
        People, 
        fields = ("name", "description", "research_interests", "image", "website", "email", "twitter", "google_scholar", "orcid", "researchgate", "linkedin"),
        labels = { "description": "Profile/bio", "image": "Photo" }
    )
    form = ModelForm(request.POST or None, request.FILES or None, instance=request.user.people)
    if request.method == "POST":
        if form.is_valid():
            info = form.save()
            messages.success(request, "Your profile information was saved.")
            if not info.image:
                messages.warning(request, "Please do not forget to upload a profile photo!")
            return redirect("/account/")
        else:
            messages.error(request, "We could not save your form, please fill out all fields")
    context = {
        "header_title": "Edit profile",
        "header_subtitle": "Actionable Science for Urban Sustainability · 3-5 June 2020",
        "edit_link": "/admin/core/webpage/" + str(info.id) + "/change/",
        "info": info,
        "form": form,
    }
    return render(request, "ascus/account.edit.html", load_design(context, PAGE_ID["ascus"]))

@check_ascus_access
def ascus_account_discussion(request):
    info = get_object_or_404(Webpage, slug="/ascus/account/discussion/")
    my_discussions = Event.objects_include_private \
        .filter(child_list__record_parent=request.user.people) \
        .filter(parent_list__record_child__id=PAGE_ID["ascus"]) \
        .filter(tags__id=770)
    ModelForm = modelform_factory(
        Event, 
        fields = ("name", "description"),
        labels = { "name": "Title", "description": "Abstract (please include the goals, format, and names of all organizers)" }
    )
    event = None
    form = ModelForm(request.POST or None, instance=event)
    if request.method == "POST":
        if form.is_valid():
            info = form.save(commit=False)
            info.site = request.site
            info.is_public = False
            info.type = "other"
            info.save()
            info.tags.add(Tag.objects.get(pk=770))
            messages.success(request, "Your discussion topic was saved.")
            RecordRelationship.objects.create(
                record_parent = info,
                record_child_id = PAGE_ID["ascus"],
                relationship = Relationship.objects.get(name="Presentation"),
            )
            RecordRelationship.objects.create(
                record_parent = request.user.people,
                record_child = info,
                relationship = Relationship.objects.get(name="Organizer"),
            )
            Work.objects.create(
                name = "Review discussion topic",
                description = "Please check to see if this looks good. If all is well, then please add any additional organizers to this record (as per the description).",
                part_of_project_id = 8,
                related_to = info,
                workactivity_id = 14,
            )
            return redirect("/account/")
        else:
            messages.error(request, "We could not save your form, please fill out all fields")
    context = {
        "header_title": "Discussion topic",
        "header_subtitle": "Actionable Science for Urban Sustainability · 3-5 June 2020",
        "edit_link": "/admin/core/webpage/" + str(info.id) + "/change/",
        "info": info,
        "form": form,
        "list": my_discussions,
    }
    return render(request, "ascus/account.discussion.html", load_design(context, PAGE_ID["ascus"]))

@check_ascus_access
def ascus_account_presentation(request, introvideo=False):
    form = None
    if introvideo:
        info = get_object_or_404(Webpage, slug="/ascus/account/introvideo/")
        my_documents = LibraryItem.objects_include_private \
            .filter(child_list__record_parent=request.user.people) \
            .filter(parent_list__record_child__id=PAGE_ID["ascus"]) \
            .filter(tags__id=769)
        ModelForm = modelform_factory(
            Video, 
            fields = ("file",),
        )
        form = ModelForm(request.POST or None, request.FILES or None)
        html_page = "ascus/account.introvideo.html"
    else:
        info = get_object_or_404(Webpage, slug="/ascus/account/presentation/")
        my_documents = LibraryItem.objects_include_private \
            .filter(child_list__record_parent=request.user.people) \
            .filter(parent_list__record_child__id=PAGE_ID["ascus"]) \
            .filter(tags__id=771)
        html_page = "ascus/account.presentation.html"

    type = None
    if "type" in request.GET:
        type = request.GET.get("type")
        if type == "video":
            ModelForm = modelform_factory(
                Video, 
                fields = ("name", "description", "author_list", "url", "is_public"), 
                labels = { "description": "Abstract", "name": "Title", "url": "URL", "author_list": "Author(s)", "is_public": "After the unconference, make my contribution publicly available through the Metabolism of Cities digital library." }
            )
        elif type == "poster" or type == "paper":
            ModelForm = modelform_factory(
                LibraryItem, 
                fields = ("name", "file", "description", "author_list", "is_public"), 
                labels = { "description": "Abstract", "name": "Title", "author_list": "Author(s)", "is_public": "After the unconference, make my contribution publicly available through the Metabolism of Cities digital library." }
            )
        elif type == "other":
            ModelForm = modelform_factory(
                LibraryItem, 
                fields = ("name", "file", "type", "description", "author_list", "is_public"), 
                labels = { "description": "Abstract", "name": "Title", "author_list": "Author(s)", "is_public": "After the unconference, make my contribution publicly available through the Metabolism of Cities digital library." }
            )
        form = ModelForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            info = form.save(commit=False)
            info.status = "active"
            info.year = 2020
            if type == "video":
                info.type = LibraryItemType.objects.get(name="Video Recording")
            elif type == "poster":
                info.type = LibraryItemType.objects.get(name="Poster")
            elif type == "paper":
                info.type = LibraryItemType.objects.get(name="Conference Paper")
            elif introvideo:
                info.type = LibraryItemType.objects.get(name="Video Recording")
                info.name = "Introduction video: " + str(request.user.people)
                info.is_public = False
            info.save()
            if introvideo:
                # Adding the tag "Personal introduction video"
                info.tags.add(Tag.objects.get(pk=769))
                messages.success(request, "Thanks, we have received your introduction video!")
                review_title = "Review and upload personal video"
            else:
                # Adding the tag "Abstract presentation"
                info.tags.add(Tag.objects.get(pk=771))
                messages.success(request, "Thanks, we have received your work! Our team will review your submission and if there are any questions we will get in touch.")
                review_title = "Review uploaded presentation"
            RecordRelationship.objects.create(
                record_parent = info,
                record_child_id = PAGE_ID["ascus"],
                relationship = Relationship.objects.get(name="Presentation"),
            )
            RecordRelationship.objects.create(
                record_parent = request.user.people,
                record_child = info,
                relationship = Relationship.objects.get(name="Author"),
            )
            Work.objects.create(
                name = review_title,
                description = "Please check to see if this looks good. If it's a video, audio schould be of decent quality. Make sure there are no glaring problems with this submission. If there are, contact the submitter and discuss. If all looks good, then please look at the co-authors and connect this (create new relationships) to the other authors as well.",
                part_of_project_id = 8,
                related_to = info,
                workactivity_id = 14,
            )
            return redirect("/account/")
        else:
            messages.error(request, "We could not save your form, please fill out all fields")
    context = {
        "header_title": "My Presentation",
        "header_subtitle": "Actionable Science for Urban Sustainability · 3-5 June 2020",
        "edit_link": "/admin/core/webpage/" + str(info.id) + "/change/",
        "info": info,
        "form": form,
        "list": my_documents,
    }
    return render(request, html_page, load_design(context, PAGE_ID["ascus"]))

# AScUS admin section
@check_ascus_admin_access
def ascus_admin(request):
    context = {
        "header_title": "AScUS Admin",
        "header_subtitle": "Actionable Science for Urban Sustainability · 3-5 June 2020",
    }
    return render(request, "ascus/admin.html", load_design(context, PAGE_ID["ascus"]))

@check_ascus_admin_access
def ascus_admin_list(request, type="participant"):
    types = {
        "participant": "Participant", 
        "organizer": "Organizer", 
        "presenter": "Presenter", 
        "session": "Session organizer",
    }
    get_type = types[type]
    list = RecordRelationship.objects.filter(
        record_child = Project.objects.get(pk=PAGE_ID["ascus"]),
        relationship = Relationship.objects.get(name=get_type),
    ).order_by("record_parent__name")
    context = {
        "header_title": "AScUS Admin",
        "header_subtitle": "Actionable Science for Urban Sustainability · 3-5 June 2020",
        "list": list,
        "load_datatables": True,
        "types": types,
        "type": type,
    }
    return render(request, "ascus/admin.list.html", load_design(context, PAGE_ID["ascus"]))

@check_ascus_admin_access
def ascus_admin_work(request):
    list = Work.objects.filter(
        part_of_project_id = PAGE_ID["ascus"],
        name = "Monitor for payment",
    )
    context = {
        "header_title": "AScUS Admin",
        "header_subtitle": "Payments",
        "list": list,
        "load_datatables": True,
    }
    return render(request, "ascus/admin.work.html", load_design(context, PAGE_ID["ascus"]))

@check_ascus_admin_access
def ascus_admin_work_item(request, id):
    info = Work.objects.get(
        part_of_project_id = PAGE_ID["ascus"],
        name = "Monitor for payment",
        pk=id,
    )
    ModelForm = modelform_factory(
        Work, 
        fields = ("description", "status", "tags"),
    )
    form = ModelForm(request.POST or None, request.FILES or None, instance=info)
    if request.method == "POST":
        if form.is_valid():
            info = form.save()
            messages.success(request, "The details were saved.")
            return redirect("/account/admin/payments/")
        else:
            messages.error(request, "We could not save your form, please fill out all fields")

    context = {
        "header_title": "AScUS Admin",
        "header_subtitle": "Payments",
        "info": info,
        "form": form,
        "load_select2": True,
    }
    return render(request, "ascus/admin.work.item.html", load_design(context, PAGE_ID["ascus"]))


def ascus_register(request):
    people = user = is_logged_in = None
    if request.user.is_authenticated:
        is_logged_in = True
        check = People.objects.filter(user=request.user)
        name = str(request.user)
        user = request.user
        if check:
            people = check[0]
        if people:
            check_participant = RecordRelationship.objects.filter(
                record_parent = people,
                record_child_id = PAGE_ID["ascus"],
                relationship__name = "Participant",
            )
            if check_participant:
                return redirect("/account/")
    if request.method == "POST":
        error = None
        if not user:
            password = request.POST.get("password")
            email = request.POST.get("email")
            name = request.POST.get("name")
            if not password:
                messages.error(request, "You did not enter a password.")
                error = True
            check = User.objects.filter(email=email)
            if check:
                messages.error(request, "A Metabolism of Cities account already exists with this e-mail address. Please <a href='/login/'>log in first</a> and then register for the AScUS unconference.")
                error = True
        if not error:
            if not user:
                user = User.objects.create_user(email, email, password)
                user.first_name = name
                user.is_superuser = False
                user.is_staff = False
                user.save()
                login(request, user)
                check = People.objects.filter(name=name)
                if check:
                    check_people = check[0]
                    if not check_people.user:
                        people = check_people
            if not people:
                people = People.objects.create(name=name, is_public=False, email=user.email)
            people.user = user
            people.save()
            RecordRelationship.objects.create(
                record_parent = people,
                record_child_id = 8,
                relationship_id = 12,
            )
            if request.POST.get("abstract") == "yes":
                RecordRelationship.objects.create(
                    record_parent = people,
                    record_child_id = 8,
                    relationship_id = 15,
                )
            if request.POST.get("discussion") == "yes":
                RecordRelationship.objects.create(
                    record_parent = people,
                    record_child_id = 8,
                    relationship_id = 16,
                )
            if not is_logged_in:
                Work.objects.create(
                    name = "Link city and organization of participant",
                    description = "Affiliation: " + request.POST.get("organization") + " -- City: " + request.POST.get("city"),
                    part_of_project_id = 8,
                    related_to = people,
                    workactivity_id = 14,
                )
            location = request.POST.get("city", "not set")
            Work.objects.create(
                name = "Monitor for payment",
                description = "Price should be based on their location: location = " + location,
                part_of_project_id = 8,
                related_to = people,
                workactivity_id = 13,
            )
            messages.success(request, "You are successfully registered for the AScUS Unconference.")

            tags = request.POST.getlist("tags")
            for each in tags:
                tag = Tag.objects.get(pk=each, parent_tag__id=757)
                people.tags.add(tag)

            return redirect("/payment/")

    context = {
        "header_title": "Register now",
        "header_subtitle": "Actionable Science for Urban Sustainability · 3-5 June 2020",
        "tags": Tag.objects.filter(parent_tag__id=757)
    }
    return render(request, "ascus/register.html", load_design(context, PAGE_ID["ascus"]))

# TEMPORARY PAGES DURING DEVELOPMENT

def pdf(request):
    name = request.GET["name"]
    score = request.GET["score"]
    date = datetime.now()
    date = date.strftime("%d %B %Y")
    site = Site.objects.get_current()

    context = Context({"name": name, "score": score, "date": date, "site": site.domain})

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = "inline; filename=test.pdf"
    html = render_to_string("pdf_template.html", context.flatten())

    font_config = FontConfiguration()
    HTML(string=html).write_pdf(response, font_config=font_config)

    return response

def socialmedia(request, type):
    list = SocialMedia.objects.filter(published=False, platform=type)
    for each in list:
        # send to api here
        success = False
        if type == "facebook":
            # Send to FB API
            message = each.blurb
            response = "response-from-api"
        elif type == "twitter":
            message = each.blurb
            response = "response-from-api"
        elif type == "linkedin":
            message = each.blurb
            response = "response-from-api"
        elif type == "instagram":
            message = each.blurb
            # In Instagram we need of course to post an image, so please use this as well:
            image = each.record.image
            response = "response-from-api"
        if success:
            each.published = True
        each.response = response
        each.save()

    messages.success(request, "Messages were posted.")
    return render(request, "template/blank.html")

#MOOC

def mooc(request, id):
    mooc = get_object_or_404(MOOC, pk=id)
    modules = mooc.modules.all().order_by("id")

    context = {
        "mooc": mooc,
        "modules": modules,
    }

    return render(request, "mooc/index.html", context)

def mooc_module(request, id, module):
    mooc = get_object_or_404(MOOC, pk=id)
    module = get_object_or_404(MOOCModule, pk=module)
    questions = module.questions.all()

    context = {
        "mooc": mooc,
        "module": module,
        "questions": questions,
    }

    return render(request, "mooc/module.html", context)

def load_baseline(request):

    return redirect("/")

def project_form(request):
    ModelForm = modelform_factory(Project, fields=("name", "content", "email", "url", "image"))
    form = ModelForm(request.POST or None, request.FILES or None)
    is_saved = False
    if request.method == "POST":
        if form.is_valid():
            info = form.save(commit=False)
            info.is_deleted = True
            info.save()
            info_id = info.id
            messages.success(request, "Information was saved.")
            is_saved = True
            name = request.POST["name"]
            user_email = request.POST["user_email"]
            posted_by = request.POST["name"]
            host_name = request.get_host()
            review_link = f"{host_name}/admin/core/project/{info_id}/change/"
            send_mail(
                "New project created",
f'''A new project was created, please review:

Project name: {name}
Submitted by: {posted_by}
Email: {user_email}

Link to review: {review_link}''',
                user_email,
                ["info@metabolismofcities.org"],
                fail_silently=False,
            )
        else:
            messages.error(request, "We could not save your form, please fill out all fields")
    context = {
        "form": form,
        "is_saved": is_saved
    }
    return render(request, "project.form.html", context)

# TEMPORARY
def dataimport(request):
    error = False
    if "table" in request.GET:
        messages.warning(request, "Trying to import " + request.GET["table"])
        file = settings.MEDIA_ROOT + "/import/" + request.GET["table"] + ".csv"
        messages.warning(request, "Using file: " + file)
        if request.GET["table"] == "activities":
            ActivityCatalog.objects.all().delete()
            nace = ActivityCatalog.objects.create(name="Statistical Classification of Economic Activities in the European Community, Rev. 2 (2008)", url="https://ec.europa.eu/eurostat/ramon/nomenclatures/index.cfm?TargetUrl=LST_NOM_DTL&StrNom=NACE_REV2&StrLanguageCode=EN&IntPcKey=&StrLayoutCode=HIERARCHIC")
            natural = ActivityCatalog.objects.create(name="Rupertismo List of Natural Processes")
            Activity.objects.all().delete()
            with open(file, "r") as csvfile:
                contents = csv.DictReader(csvfile)
                for row in contents:
                    id = int(row["id"])
                    catalog = None
                    if id > 398480:
                        catalog = nace
                    elif id > 65 and id < 95 and id != 92:
                        catalog = natural
                    if catalog:
                        Activity.objects.create(
                            old_id = row["id"], 
                            name = row["name"], 
                            description = row["description"], 
                            is_separator = row["is_separator"],
                            code = row["code"],
                            catalog = catalog,
                        )
            with open(file, "r") as csvfile:
                contents = csv.DictReader(csvfile)
                for row in contents:
                    id = int(row["id"])
                    parent = None
                    if id > 398480:
                        if int(row["parent_id"]) == 398480:
                            parent = None
                        else:
                            parent = Activity.objects.get(old_id=row["parent_id"])
                    elif id > 65 and id < 95 and id != 92:
                        if int(row["parent_id"]) == 92:
                            parent = None
                        else:
                            parent = Activity.objects.get(old_id=row["parent_id"])
                    if parent:
                        info = Activity.objects.get(old_id=row["id"])
                        info.parent = parent
                        info.save()
        elif request.GET["table"] == "libraryspaces":
            list = LibraryItem.objects.all()
            for each in list:
                each.spaces.clear()
            spaces = {}
            items = {}
            with open(file, "r") as csvfile:
                contents = csv.DictReader(csvfile)
                for row in contents:
                    if row["referencespace_id"] in spaces:
                        space = spaces[row["referencespace_id"]]
                    else:
                        space = ReferenceSpace.objects.filter(old_id=row["referencespace_id"])
                        if space:
                            space = space[0]
                        else:
                            print("COULD NOT FIND THIS!!")
                            print(row)
                        spaces[row["referencespace_id"]] = space
                    if row["reference_id"] in items:
                        item = items[row["reference_id"]]
                    else:
                        item = LibraryItem.objects.filter(old_id=row["reference_id"]).exclude(type__name="Video Recording").exclude(type__name="Image")
                        if item.count() == 1:
                            item = item[0]
                        else:
                            print("Duplication error!")
                            print(item)
                        items[row["reference_id"]] = item
                    if space:
                        item.spaces.add(space)
        elif request.GET["table"] == "sectors":
            Sector.objects.all().delete()
            with open(file, "r") as csvfile:
                contents = csv.DictReader(csvfile)
                for row in contents:
                    Sector.objects.create(
                        old_id = row["id"],
                        name = row["name"],
                        icon = row["icon"],
                        slug = row["slug"],
                        description = row["description"],
                    )
        elif request.GET["table"] == "sectoractivities":
            sectors = Sector.objects.all()
            for each in sectors:
                each.activities.clear()
            with open(file, "r") as csvfile:
                contents = csv.DictReader(csvfile)
                sectors = {}
                for row in contents:
                    row["processgroup_id"] = int(row["processgroup_id"])
                    if row["processgroup_id"] not in sectors:
                        sectors[row["processgroup_id"]] = Sector.objects.get(old_id=row["processgroup_id"])
                    sector = sectors[row["processgroup_id"]]
                    sector.activities.add(Activity.objects.get(old_id=row["process_id"]))
        elif request.GET["table"] == "spacesectors":
            with open(file, "r") as csvfile:
                contents = csv.DictReader(csvfile)
                for row in contents:
                    space = ReferenceSpace.objects.get(old_id=row["space_id"])
                    sector = Sector.objects.get(old_id=row["process_group_id"])
                    space.sectors.add(sector)
        elif request.GET["table"] == "photos":
            License.objects.all().delete()
            Photo.objects.all().delete()
            with open(settings.MEDIA_ROOT + "/import/licenses.csv", "r") as csvfile:
                contents = csv.DictReader(csvfile)
                for row in contents:
                    License.objects.create(
                        id = row["id"],
                        name = row["name"],
                        url = row["url"],
                    )
            with open(file, "r") as csvfile:
                contents = csv.DictReader(csvfile)
                for row in contents:
                    Photo.objects.create(
                        image = row["image"],
                        author = row["author"],
                        source_url = row["source_url"],
                        description = row["description"],
                        space_id = row["secondary_space_id"] if row["secondary_space_id"] else row["primary_space_id"],
                        uploaded_by_id = row["uploaded_by_id"],
                        is_deleted = row["deleted"],
                        license_id = row["license_id"],
                        type = row["type"],
                        position = row["position"],
                    )
        elif request.GET["table"] == "referencespaces":
            if int(request.GET["start"]) == 0:
                ReferenceSpaceLocation.objects.all().delete()
                ReferenceSpace.objects_unfiltered.all().delete()

            if "creategeo" in request.GET:
                GeocodeScheme.objects.all().delete()
                list = [
                    {
                        "name": "System Types",
                        "icon": "fal fa-fw fa-layer-group",
                        "items": ["Company", "Island", "Rural", "Urban", "Household"],
                    },
                    {
                        "name": "UN Statistics Division Groupings",
                        "icon": "fal fa-fw fa-universal-access",
                        "items": ["Least Developed Countries", "Land Locked Developing Countries", "Small Island Developing States", "Developed Regions", "Developing Regions"],
                    },
                    {
                        "name": "NUTS",
                        "icon": "fal fa-fw fa-globe-europe",
                        "items": ["NUTS 1"],
                        "items2": ["NUTS 2"],
                        "items3": ["NUTS 3"],
                        "items4": ["Local Administrative Unit (LAU)"],
                    },
                    {
                        "name": "ISO 3166-1",
                        "icon": "fal fa-fw fa-globe",
                        "items": ["Countries"],
                    },
                    {
                        "name": "Sector: Hotels and lodging",
                        "icon": "fal fa-fw fa-bed",
                        "items": ["Hotels", "Camping grounds"],
                    },
                    {
                        "name": "Sector: Transport",
                        "icon": "fal fa-fw fa-car",
                        "items": ["Bus stops", "Train stations", "Bicycle racks", "Bridges", "Electric charging stations", "Lighthouses", "Airports", "Ports", "Border Crossings"],
                    },
                    {
                        "name": "Sector: Water and sanitation",
                        "icon": "fal fa-fw fa-water",
                        "items": ["Marine outfalls", "Dams", "Water reservoirs", "Wastewater treatment plants", "Water treatment plants", "Pumping stations"],
                    },
                    {
                        "name": "Sector: Agriculture",
                        "icon": "fal fa-fw fa-seedling",
                        "items": ["Farms"],
                    },
                    {
                        "name": "Sector: Mining",
                        "icon": "fal fa-fw fa-digging",
                        "items": ["Mines"],
                    },
                    {
                        "name": "Sector: Construction",
                        "icon": "fal fa-fw fa-construction",
                        "items": ["Building site"],
                    },
                    {
                        "name": "Sector: Energy",
                        "icon": "fal fa-fw fa-bolt",
                        "items": ["Wind turbines", "Solar parks/farms", "Roof-top solar panels", "Power plants", "High voltage lines", "Substations", "Transmission masts"],
                    },
                    {
                        "name": "Sector: Waste",
                        "icon": "fal fa-fw fa-dumpster",
                        "items": ["Waste transfer station", "Waste drop-off sites", "Waste incinerators", "Landfills"],
                    },
                    {
                        "name": "Sector: Storage",
                        "icon": "fal fa-fw fa-container",
                        "items": ["Fuel storage facilities", "Energy storage"],
                    },
                    {
                        "name": "Sector: Fishing",
                        "icon": "fal fa-fw fa-fish",
                        "items": ["Fish farms"],
                    },
                    {
                        "name": "Sector: Food service",
                        "icon": "fal fa-fw fa-utensils",
                        "items": ["Restaurants", "Bars"],
                    },
                    {
                        "name": "Sector: Forestry",
                        "icon": "fal fa-fw fa-trees",
                        "items": ["Plantation"],
                    },
                    {
                        "name": "Sector: Manufacturing (Food)",
                        "icon": "fal fa-fw fa-hamburger",
                        "items": ["Abbatoir", "Bakery", "Bread mill", "Food processing facilities"],
                    },
                    {
                        "name": "Sector: Manufacturing (coke and petroleum products)",
                        "icon": "fal fa-fw fa-oil-can",
                        "items": ["Refineries"],
                    },
                    {
                        "name": "Subdivisions of South Africa",
                        "icon": "fal fa-fw fa-flag",
                        "items": ["Provinces"],
                        "items2": ["Metropolitan municipalities", "District municipalities"],
                        "items3": ["Local municipalilties"],
                        "items4": ["Wards"],
                    },
                    {
                        "name": "Subdivisions of Nicaragua",
                        "icon": "fal fa-fw fa-flag",
                        "items": ["Departments", "Autonomous regions"],
                        "items2": ["Municipalities"],
                    },
                    {
                        "name": "Subdivisions of Costa Rica",
                        "icon": "fal fa-fw fa-flag",
                        "items": ["Provinces"],
                        "items2": ["Cantons"],
                        "items3": ["Districts"],
                    },
                    {
                        "name": "Areas of France",
                        "icon": "fal fa-fw fa-flag",
                        "items": ["Ilots Regroupés pour l'information statistique (IRIS)", "Commune"],
                    },
                    {
                        "name": "Areas of Singapore",
                        "icon": "fal fa-fw fa-flag",
                        "items": ["Master Plan 2014 Subzones"],
                    },
                    {
                        "name": "Areas of Canada",
                        "icon": "fal fa-fw fa-flag",
                        "items": ["Neighbourhoods"],
                    },
                    {
                        "name": "Areas of South Africa",
                        "icon": "fal fa-fw fa-flag",
                        "items": ["Suburbs"],
                    },
                    {
                        "name": "Areas of the world",
                        "icon": "fal fa-fw fa-flag",
                        "items": ["Supra-national territory", "Sub-national territory"],
                    },
                    {
                        "name": "Areas of The Netherlands",
                        "icon": "fal fa-fw fa-flag",
                        "items": ["Buurten", "Stadsdelen", "Wijken"],
                    },
                    {
                        "name": "Areas of Belgium",
                        "icon": "fal fa-fw fa-flag",
                        "items": ["Quartiers", "Communes"],
                    },
                    {
                        "name": "Subdivisions of Grenada",
                        "icon": "fal fa-fw fa-flag",
                        "items": ["Parishes", "Dependencies"],
                    },

                ]
                for each in list:
                    scheme = GeocodeScheme.objects.create(
                        name = each["name"],
                        is_comprehensive = False,
                        icon = each["icon"],
                    )
                    for name in each["items"]:
                        Geocode.objects.create(
                            scheme = scheme,
                            name = name,
                            depth = 1,
                        )
                    if "items2" in each:
                        for name in each["items2"]:
                            Geocode.objects.create(
                                scheme = scheme,
                                name = name,
                                depth = 2,
                            )
                    if "items3" in each:
                        for name in each["items3"]:
                            Geocode.objects.create(
                                scheme = scheme,
                                name = name,
                                depth = 3,
                            )
                    if "items4" in each:
                        for name in each["items4"]:
                            Geocode.objects.create(
                                scheme = scheme,
                                name = name,
                                depth = 4,
                            )


            checkward = Geocode.objects.filter(name="Wards")
            checkcities = Geocode.objects.filter(name="Urban")
            checkcountries = Geocode.objects.filter(name="Countries")
            checkisland = Geocode.objects.filter(name="Island")
            count = 0
            with open(file, "r") as csvfile:
                contents = csv.DictReader(csvfile)
                for row in contents:
                    count = count+1
                    print(count)
                    if count >= int(request.GET["start"]) and count < int(request.GET["end"]):
                        deleted = False if row["active"] == "t" else True
                        space = ReferenceSpace.objects.create(
                            old_id = row["id"],
                            name = row["name"],
                            description = row["description"],
                            slug = row["slug"],
                            is_deleted = deleted,
                        )
                        if int(row["type_id"]) == 45 and checkward:
                            space.geocodes.add(checkward[0])
                        elif int(row["type_id"]) == 3 and checkcities:
                            space.geocodes.add(checkcities[0])
                        elif int(row["type_id"]) == 2 and checkcountries:
                            space.geocodes.add(checkcountries[0])
                        elif int(row["type_id"]) == 21 and checkisland:
                            space.geocodes.add(checkisland[0])
                        elif int(row["type_id"]) == 56:
                            space.geocodes.add(Geocode.objects.get(name="Ilots Regroupés pour l'information statistique (IRIS)"))
                        elif int(row["type_id"]) == 50:
                            space.geocodes.add(Geocode.objects.get(name="Master Plan 2014 Subzones"))
                        elif int(row["type_id"]) == 49:
                            space.geocodes.add(Geocode.objects.get(name="Border Crossings"))
                        elif int(row["type_id"]) == 47:
                            space.geocodes.add(Geocode.objects.get(name="Neighbourhoods"))
                        elif int(row["type_id"]) == 46:
                            space.geocodes.add(Geocode.objects.get(name="Suburbs"))
                        elif int(row["type_id"]) == 44:
                            space.geocodes.add(Geocode.objects.get(name="Supra-national territory"))
                        elif int(row["type_id"]) == 43:
                            space.geocodes.add(Geocode.objects.get(name="Sub-national territory"))
                        elif int(row["type_id"]) == 42:
                            space.geocodes.add(Geocode.objects.get(name="Bus stops"))
                        elif int(row["type_id"]) == 41:
                            space.geocodes.add(Geocode.objects.get(name="Train stations"))
                        elif int(row["type_id"]) == 40:
                            space.geocodes.add(Geocode.objects.get(name="Transmission masts"))
                        elif int(row["type_id"]) == 39:
                            space.geocodes.add(Geocode.objects.get(name="Pumping stations"))
                        elif int(row["type_id"]) == 38:
                            space.geocodes.add(Geocode.objects.get(name="Bicycle racks"))
                        elif int(row["type_id"]) == 37:
                            space.geocodes.add(Geocode.objects.get(name="Bridges"))
                        elif int(row["type_id"]) == 36:
                            space.geocodes.add(Geocode.objects.get(name="Wind turbines"))
                        elif int(row["type_id"]) == 35:
                            space.geocodes.add(Geocode.objects.get(name="Electric charging stations"))
                        elif int(row["type_id"]) == 34:
                            space.geocodes.add(Geocode.objects.get(name="Buurten"))
                        elif int(row["type_id"]) == 32:
                            space.geocodes.add(Geocode.objects.get(name="Parishes"))
                        elif int(row["type_id"]) == 31:
                            space.geocodes.add(Geocode.objects.get(name="Quartiers"))
                        elif int(row["type_id"]) == 30:
                            space.geocodes.add(Geocode.objects.get(name="Communes"))
                        elif int(row["type_id"]) == 29:
                            space.geocodes.add(Geocode.objects.get(name="Stadsdelen"))
                        elif int(row["type_id"]) == 28:
                            space.geocodes.add(Geocode.objects.get(name="Wijken"))
                        elif int(row["type_id"]) == 27:
                            space.geocodes.add(Geocode.objects.get(name="Marine outfalls"))
                        elif int(row["type_id"]) == 26:
                            space.geocodes.add(Geocode.objects.get(name="Lighthouses"))
                        elif int(row["type_id"]) == 25:
                            space.geocodes.add(Geocode.objects.get(name="Airports"))
                        elif int(row["type_id"]) == 24:
                            space.geocodes.add(Geocode.objects.get(name="Fuel storage facilities"))
                        elif int(row["type_id"]) == 23:
                            space.geocodes.add(Geocode.objects.get(name="Waste transfer station"))
                        elif int(row["type_id"]) == 22:
                            space.geocodes.add(Geocode.objects.get(name="Waste drop-off sites"))
                        elif int(row["type_id"]) == 19:
                            space.geocodes.add(Geocode.objects.get(name="Energy storage"))
                        elif int(row["type_id"]) == 18:
                            space.geocodes.add(Geocode.objects.get(name="Waste incinerators"))
                        elif int(row["type_id"]) == 17:
                            space.geocodes.add(Geocode.objects.get(name="Landfills"))
                        elif int(row["type_id"]) == 16:
                            space.geocodes.add(Geocode.objects.get(name="Food processing facilities"))
                        elif int(row["type_id"]) == 15:
                            space.geocodes.add(Geocode.objects.get(name="Farms"))
                        elif int(row["type_id"]) == 14:
                            space.geocodes.add(Geocode.objects.get(name="Mines"))
                        elif int(row["type_id"]) == 13:
                            space.geocodes.add(Geocode.objects.get(name="Ports"))
                        elif int(row["type_id"]) == 12:
                            space.geocodes.add(Geocode.objects.get(name="Power plants"))
                        elif int(row["type_id"]) == 11:
                            space.geocodes.add(Geocode.objects.get(name="Refineries"))
                        elif int(row["type_id"]) == 9:
                            space.geocodes.add(Geocode.objects.get(name="Dams"))
                        elif int(row["type_id"]) == 8:
                            space.geocodes.add(Geocode.objects.get(name="Water reservoirs"))
                        elif int(row["type_id"]) == 7:
                            space.geocodes.add(Geocode.objects.get(name="Wastewater treatment plants"))
                        elif int(row["type_id"]) == 6:
                            space.geocodes.add(Geocode.objects.get(name="Water treatment plants"))

        elif request.GET["table"] == "dataviz":
            with open(file, "r") as csvfile:
                contents = csv.DictReader(csvfile)
                for row in contents:
                    info = LibraryItem.objects.get(old_id=row["id"], name=row["title"])
                    print(info)
                    if row["space_id"]:
                        info.spaces.add(ReferenceSpace.objects.get(old_id=row["space_id"]))
                        print("Adding space!")
                    if row["process_group_id"]:
                        info.sectors.add(Sector.objects.get(old_id=row["process_group_id"]))
                        print("Adding sector!")

        elif request.GET["table"] == "referencespacelocations":
            import sys
            csv.field_size_limit(sys.maxsize)
            from django.contrib.gis.geos import Point
            from django.contrib.gis.geos import GEOSGeometry

            with open(file, "r") as csvfile:
                contents = csv.DictReader(csvfile)
                for row in contents:
                    check = ReferenceSpaceLocation.objects.filter(pk=row["id"])
                    if not check:
                        try:
                            lat = float(row["lat"])
                            lng = float(row["lng"])
                        except:
                            lat = None
                            lng = None
                        if row["geojson"] or lat:
                            deleted = True if not row["active"] else False
                            start = row["start"] if row["start"] else None
                            end = row["end"] if row["end"] else None
                            if row["geojson"]:
                                try:
                                    geometry = GEOSGeometry(row["geojson"])
                                except Exception as e:
                                    print("Houston, we have a problem!")
                                    print(e)
                                    print(row["id"])
                            elif lat and lng:
                                geometry = Point(lng, lat)
                            try:
                                location = ReferenceSpaceLocation.objects.create(
                                    id = row["id"],
                                    space = ReferenceSpace.objects.get(old_id=row["space_id"]),
                                    description = row["description"],
                                    start = start,
                                    end = end,
                                    is_deleted = deleted,
                                    geometry = geometry,
                                )
                                space = ReferenceSpace.objects.get(old_id=row["space_id"])
                                space.location = location
                                space.save()
                            except Exception as e:
                                print("Not imported because there is an error")
                                print(e)
                                print(row["space_id"])
        elif request.GET["table"] == "flowdiagrams":
            FlowDiagram.objects.all().delete()
            water = FlowDiagram.objects.create(name="Urban water cycle")
            def activity(id):
                a = Activity.objects.get(old_id=id)
                return a.id
            FlowBlocks.objects.create(origin_id=activity(67), origin_label="Rain, rivers, and other natural water processes", destination_id=activity(398932), destination_label="Collection of water in dams", diagram=water)
            FlowBlocks.objects.create(origin_id=activity(398932), origin_label="Collection of water in dams", destination_id=activity(67), destination_label="Evaporation, leaking, and losses of water", diagram=water)
            FlowBlocks.objects.create(origin_id=activity(398932), origin_label="Collection of water in dams", destination_id=activity(398932), destination_label="Water treatment", diagram=water)
            FlowBlocks.objects.create(origin_id=activity(398932), origin_label="Water treatment", destination_id=activity(399133), destination_label="Reservoirs", diagram=water)
            FlowBlocks.objects.create(origin_id=activity(398932), origin_label="Water treatment", destination_id=activity(67), destination_label="Evaporation, leaking, and losses of water", diagram=water)
            FlowBlocks.objects.create(origin_id=activity(399133), origin_label="Reservoirs", destination_id=activity(67), destination_label="Evaporation, leaking, and losses of water", diagram=water)
            FlowBlocks.objects.create(origin_id=activity(399133), origin_label="Reservoirs", destination_id=activity(399468), destination_label="Water consumption", diagram=water)
            FlowBlocks.objects.create(origin_id=activity(399468), origin_label="Water consumption", destination_id=activity(67), destination_label="Evaporation, leaking, and losses of water", diagram=water)
            FlowBlocks.objects.create(origin_id=activity(399468), origin_label="Water consumption", destination_id=activity(398935), destination_label="Wastewater treatment", diagram=water)
            FlowBlocks.objects.create(origin_id=activity(398935), origin_label="Wastewater treatment", destination_id=activity(67), destination_label="Evaporation, leaking, and losses of water", diagram=water)
            FlowBlocks.objects.create(origin_id=activity(398935), origin_label="Wastewater treatment", destination_id=activity(67), destination_label="Rain, rivers, and other natural water processes", diagram=water)
            FlowBlocks.objects.create(origin_id=activity(398935), origin_label="Wastewater treatment", destination_id=activity(399468), destination_label="Water consumption", diagram=water)
        if error:
            messages.error(request, "We could not import your data")
        else:
            messages.success(request, "Data was imported")
    context = {
        "tags": Tag.objects.all().count(),
        "activities": Activity.objects.all().count(),
        "projects": Project.objects.all().count(),
        "organizations": Organization.objects.all().count(),
        "videos": Video.objects.all().count(),
        "people": People.objects.all().count(),
        "spaces": ReferenceSpace.objects.all().count(),
        "locations": ReferenceSpaceLocation.objects.all().count(),
        "libraryitems": LibraryItem.objects.all().count(),
        "librarytypes": LibraryItemType.objects.all().count(),
        "tttt": Tag.objects.all().count(),
        "publishers": Organization.objects.filter(type="publisher").count(),
        "news": News.objects.all().count(),
        "blogs": Blog.objects.all().count(),
        "events": Event.objects.all().count(),
        "journals": Organization.objects.filter(type="journal").count(),
        "publications": LibraryItem.objects.all().count(),
        "users": User.objects.all().count(),
        "photos": Photo.objects.all().count(),
        "sectors": Sector.objects.all().count(),
        "sectoractivities": Sector.activities.through.objects.all().count(),
        "librarytags": LibraryItem.tags.through.objects.all().count(),
        "libraryspaces": LibraryItem.spaces.through.objects.all().count(),
        "spacesectors": ReferenceSpace.sectors.through.objects.all().count(),
        "flowdiagrams": FlowDiagram.objects.all().count(),
        "dataviz": LibraryItem.objects.filter(type__name="Image").count(),
        "flowblocks": FlowBlocks.objects.all().count(),
        "podcasts": LibraryItem.objects.filter(type__name="Podcast").count(),
        "project_team_members": RecordRelationship.objects.filter(relationship__name__in=["Team member", "Former team member"]).count(),
    }
    return render(request, "temp.import.html", context)
