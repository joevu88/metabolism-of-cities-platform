from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from core.models import *

PROJECT_ID = settings.PROJECT_ID_LIST

def index(request):

    context = {
        "show_project_design": True,
    }

    return render(request, "template/blank.html", context)

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


def projects(request):

    if "import" in request.GET:
        import csv
        print("importing")
        file = settings.MEDIA_ROOT + "/import/projects.csv"
        funders = {}
        with open(file, "r") as csvfile:
            contents = csv.DictReader(csvfile)
            for row in contents:
                meta = {}
                name = row["name"]
                print(name)
                check = PublicProject.objects.filter(name=name)
                if check:
                    info = check[0]
                    info.description = row["description"]
                    if row["start_date"]:
                        info.start_date = row["start_date"]
                    if row["end_date"]:
                        info.end_date = row["end_date"]
                    if row["logo"] and not info.image:
                        info.image = row["logo"]

                    if row["funding_program"]:
                        funder = row["funding_program"]
                        if funder in funders:
                            funder_id = funders[funder]
                        else:
                            checkfunder = Organization.objects.filter(name=funder)
                            if checkfunder:
                                f = checkfunder[0]
                            else:
                                f = Organization.objects.create(
                                    type = "funding_program",
                                    name = funder,
                                )
                            funder_id = f.id
                            funders[funder] = f.id

                        try:
                            RecordRelationship.objects.create(
                                relationship_id = 5,
                                record_parent_id = funder_id,
                                record_child = info,
                            )
                        except:
                            print("Error!")

                    if row["budget"]:
                        meta["budget"] = row["budget"]
                        meta["budget_currency"] = "EUR"
                    if row["institution"]:
                        meta["institution"] = row["institution"]
                    info.meta_data = meta
                    info.save()



    list = PublicProject.objects.all()
    context = {
        "list": list,
        "header_title": "Projects",
        "header_subtitle": "Research and intervention projects that are happening all over the world.",
    }
    return render(request, "community/projects.html", context)

def project(request, id):
    info = PublicProject.objects.get(pk=id)
    context = {
        "info": info,
        "header_title": info.name,
        "header_subtitle": "Projects",
        "edit_link": "/admin/core/publicproject/" + str(info.id) + "/change/",
        "show_relationship": info.id,
        "relationships": info.child_list.all(),
    }
    return render(request, "community/project.html", context)

def organizations(request, slug=None):
    list = Organization.objects.filter(type=slug)
    context = {
        "list": list,
        "load_datatables": True,
        "slug": slug,
        "header_title": slug,
        "header_subtitle": "List of organisations active in the field of urban metabolism",
    }
    return render(request, "community/organizations.html", context)

def organization(request, slug, id):
    info = get_object_or_404(Organization, pk=id)
    context = {
        "info": info,
        "header_title": info.name,
        "header_subtitle": info.get_type_display,
        "edit_link": "/admin/core/organization/" + str(info.id) + "/change/",
    }
    return render(request, "community/organization.html", context)

# FORUM

def forum_list(request):
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

