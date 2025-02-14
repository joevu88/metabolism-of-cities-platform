from core.models import *
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import Q, Count
from django.http import Http404, HttpResponseRedirect, JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.admin.views.decorators import staff_member_required
from django.forms import modelform_factory
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from datetime import date

from django.utils import timezone
import pytz
from core.mocfunctions import *

def index(request):
    info = get_object_or_404(Project, pk=request.project)
    research = Tag.objects.filter(parent_tag_id=1227, include_in_glossary=True)
    projects = PublicProject.objects.filter(part_of_project=info).order_by("-start_date")
    carousel = News.objects.filter(projects=info, include_in_timeline=True).distinct().order_by("-date")

    context = {
        "webpage": get_object_or_404(Webpage, pk=1002744),
        "team": People.objects.filter(parent_list__record_child=info).filter(Q(parent_list__relationship__name="Admin") | Q(parent_list__relationship__name="Core member")).distinct(),
        "research": research,
        "carousel": carousel,
        "projects": projects[:3],
        "today": date.today(),
    }
    return render(request, "peeide/index.html", context)

def research(request):
    info = get_object_or_404(Project, pk=request.project)

    research = Tag.objects.filter(parent_tag_id=1227).order_by("name")
    all_projects = PublicProject.objects.filter(part_of_project=info)
    projects = all_projects.filter(Q(meta_data__proposal=False) | Q(meta_data__proposal__isnull=True)).distinct().order_by("name")
    proposals = all_projects.filter(meta_data__proposal=True).distinct().order_by("name")

    context = {
        "webpage": get_object_or_404(Webpage, pk=51471),
        "projects": projects,
        "proposals": proposals,
        "research": research,
        "today": date.today(),
        "header_image": LibraryItem.objects.get(pk=1009391)
    }

    return render(request, "peeide/research.html", context)

def people(request):
    info = get_object_or_404(Project, pk=request.project)
    context = {
        "webpage": get_object_or_404(Webpage, pk=51472),
        "team": People.objects.filter(parent_list__record_child=info).filter(Q(parent_list__relationship__name="Admin") | Q(parent_list__relationship__name="Core member")).distinct(),
        "network": People.objects.filter(parent_list__record_child=info, parent_list__relationship__name="Team member").distinct(),
        "header_image": LibraryItem.objects.get(pk=1009390)
    }

    return render(request, "peeide/people.html", context)

def bibliography(request):
    ndee_tag = Tag.objects.get(id=1643)
    sectors = Tag.objects.filter(parent_tag__id=1089).exclude(name="Hide").annotate(total=Count("record", filter=Q(record__is_deleted=False, record__is_public=True, record__tags=ndee_tag))).filter(total__gt=0).order_by("name")
    technologies = Tag.objects.filter(parent_tag__id=1088).annotate(total=Count("record", filter=Q(record__is_deleted=False, record__is_public=True, record__tags=ndee_tag))).filter(total__gt=0).order_by("name")
    context = {
        "webpage": get_object_or_404(Webpage, pk=51473),
        "sectors": sectors,
        "technologies": technologies,
        "types": LibraryItemType.objects.all(),
        "header_image": LibraryItem.objects.get(pk=1009392)
    }

    return render(request, "peeide/library.html", context)

def bibliography_suggestion(request):
    project = get_project(request)
    if request.method == "POST" and "details" in request.POST:
        email = request.POST.get("email")
        posted_by = request.POST.get("name")
        details = request.POST.get("details")

        sender = settings.SITE_EMAIL
        try:
            recipient = project.meta_data.get("email")
        except:
            recipient = sender

        message = EmailMultiAlternatives(
            f"Suggestion for the bibliography - {project.name}",
f'''Someone submitted a suggestion for the bibliography. The details can be found below.

Submitted by: {posted_by}
Email: {email}

----------------------
Details
----------------------
{details}''',
            sender,
            [recipient],
            reply_to=[email],
        )
        message.send()
        msg = "Your message was sent - thanks for your input!"
        messages.success(request, msg)

    context = {
        "title": "Submit a suggestion",
    }

    return render(request, "peeide/suggestion.html", context)

def bibliography_list(request, id=None):
    keyword = request.GET.get("keyword")
    author = request.GET.get("author")
    type = request.GET.get("type")
    tag = None
    # In the beginning, we simply filtered to see if the tags included a nDEE-specific sector...
    items = LibraryItem.objects.filter(tags__parent_tag__parent_tag_id=1087).distinct()
    # But then we got other sites using those tags too, so we had to do this tweak...
    ndee_tag = Tag.objects.get(id=1643)
    # Ideally we fully streamline this and use one or the other, not both
    items = items.filter(tags=ndee_tag)
    if request.GET.get("search"):
        id = request.GET.get("search")
    if id:
        tag = Tag.objects.get(pk=id)
        items = items.filter(tags=tag)
    if keyword:
        abstract_search = request.GET.get("abstract")
        title_search = request.GET.get("title")
        if abstract_search and title_search:
            items = items.filter(Q(name__icontains=keyword)|Q(description__icontains=keyword))
        elif abstract_search:
            items = items.filter(description__icontains=keyword)
        elif title_search:
            items = items.filter(name__icontains=keyword)
    if author:
        items = items.filter(Q(author_list__icontains=author))
    if type:
        items = items.filter(type_id=type)
        type = LibraryItemType.objects.get(id=type)

    sectors = None
    technologies = None
    additional_tag = None

    if "tag" in request.GET:
        # We allow the user to narrow down the results by adding another tag
        additional_tag = get_object_or_404(Tag, pk=request.GET["tag"])
        items = items.filter(tags=additional_tag)
    else:
        sectors = Tag.objects.filter(parent_tag__id=1089).exclude(id=id).annotate(
            total=Count("record", filter=Q(record__libraryitem__in=items))
        )
        technologies = Tag.objects.filter(parent_tag__id=1088).exclude(id=id).annotate(
            total=Count("record", filter=Q(record__libraryitem__in=items))
        )

    context = {
        "tag": tag,
        "items": items,
        "load_datatables": True,
        "sectors": sectors,
        "technologies": technologies,
        "additional_tag": additional_tag,
        "keyword": keyword,
        "author": author,
        "type": type,
        "types": LibraryItemType.objects.all(),
        "header_image": LibraryItem.objects.get(pk=1009392)
    }

    return render(request, "peeide/library.list.html", context)

def news_list(request, header_subtitle=None):
    project = get_object_or_404(Project, pk=request.project)
    list = News.objects.filter(projects=project).distinct()
    news = list.filter(meta_data__category="news")
    events = list.filter(meta_data__category="event")
    resources = list.filter(meta_data__category="resource")
    other = list.filter(Q(meta_data__category="other") | Q(meta_data__category__isnull=True))

    context = {
        "webpage": get_object_or_404(Webpage, pk=1002742),
        "list": list,
        "add_link": "/controlpanel/news/create/?next=/peeide/controlpanel/news/",
        "title": "Resources and community",
        "menu": "news",
        "news": news,
        "events": events,
        "resources": resources,
        "other": other,
        "header_image": LibraryItem.objects.get(pk=1009394)
    }
    return render(request, "peeide/news.list.html", context)

@login_required
def controlpanel_project_form(request, slug=None, id=None):

    curator = False
    if has_permission(request, request.project, ["curator"]):
        curator = True

    project = get_object_or_404(Project, pk=request.project)

    research_topics = Tag.objects.filter(parent_tag_id=1227).order_by("name")

    ModelForm = modelform_factory(
        PublicProject,
        fields=["name", "url", "start_date", "end_date", "image", "part_of_project"],
        labels={"image": "Image", "url": "Website URL", "part_of_project": "Project"},
        )
    if id:
        info = get_object_or_404(PublicProject, pk=id)
        form = ModelForm(request.POST or None, request.FILES or None, instance=info)
    else:
        form = ModelForm(request.POST or None, request.FILES or None, initial={"part_of_project": request.project})
        info = None

    if request.method == "POST":
        if "delete" in request.POST:
            info.is_deleted = True
            info.save()
            messages.success(request, "The project was deleted.")
            return redirect(request.GET.get("next"))
        elif form.is_valid():
            info = form.save(commit=False)
            info.description = request.POST.get("description")

            if not info.meta_data:
                info.meta_data = {}

            info.meta_data["project_leader"] = request.POST.get("project_leader")
            info.meta_data["research_team"] = request.POST.get("research_team")
            info.meta_data["researcher"] = request.POST.get("researcher")
            info.meta_data["institution"] = request.POST.get("institution")
            info.meta_data["research_topics"] = request.POST.get("research_topics")
            info.meta_data["proposal"] = True if request.POST.get("proposal") else False

            info.save()

            messages.success(request, "The information was saved.")

            if not id:
                RecordRelationship.objects.create(
                    record_parent = request.user.people,
                    record_child = info,
                    relationship_id = RELATIONSHIP_ID["uploader"],
                )

                work = Work.objects.create(
                    status = Work.WorkStatus.COMPLETED,
                    part_of_project = project,
                    workactivity_id = 31, # Need to add new activity and update this TODO!
                    related_to = info,
                    assigned_to = request.user.people,
                    name = "Adding new project",
                )
                message = Message.objects.create(posted_by=request.user.people, parent=work, name="Status change", description="Task was completed")

            if "next" in request.GET:
                return redirect(request.GET.get("next"))
            else:
                return redirect(project.slug + ":controlpanel_projects")
        else:
            messages.error(request, "We could not save your form, please fill out all fields")

    context = {
        "form": form,
        "title": "Add project" if not id else "Edit project",
        "load_markdown": True,
        "load_select2": True,
        "curator": curator,
        "info": info,
        "research_topics": research_topics,
    }

    return render(request, "controlpanel/project.form.html", context)

@login_required
def controlpanel_projects(request, type=None):
    if not has_permission(request, request.project, ["curator", "admin", "publisher"]):
        unauthorized_access(request)

    project = request.project
    list = PublicProject.objects.filter(part_of_project_id=project)

    context = {
        "load_datatables": True,
        "list": list,
        "type": type,
    }
    return render(request, "controlpanel/projects.html", context)

@login_required
def controlpanel_header_images(request):
    if not has_permission(request, request.project, ["curator", "admin", "publisher"]):
        unauthorized_access(request)

    pages = LibraryItem.objects.filter(id__in=[1009390,1009391,1009392,1009393,1009394])

    context = {
        "pages": pages
    }

    return render(request, "peeide/controlpanel.header-images.html", context)

@login_required
def controlpanel_header_image_form(request, id=None):
    if not has_permission(request, request.project, ["curator", "admin", "publisher"]):
        unauthorized_access(request)

    info = get_object_or_404(LibraryItem, pk=id)

    if request.method == "POST":
        info.image = request.FILES["image"]
        info.save()
        messages.success(request, "The image was saved.")

    context = {
        "info": info,
    }
    return render(request, "peeide/controlpanel.header-image.form.html", context)