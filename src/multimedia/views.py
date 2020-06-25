from django.shortcuts import render
from core.models import *
from django.shortcuts import render, get_object_or_404, redirect

TAG_ID = settings.TAG_ID_LIST
PAGE_ID = settings.PAGE_ID_LIST
PROJECT_ID = settings.PROJECT_ID_LIST
RELATIONSHIP_ID = settings.RELATIONSHIP_ID_LIST
THIS_PROJECT = PROJECT_ID["multimedia"]

# Get all the parent relationships, but making sure we only show is_deleted=False and is_public=True
def get_parents(record):
    list = RecordRelationship.objects.filter(record_child=record).filter(record_parent__is_deleted=False, record_parent__is_public=True)
    return list

def index(request):
    webpage = get_object_or_404(Project, pk=PAGE_ID["multimedia_library"])
    videos = Video.objects.filter(tags__parent_tag__id=749).distinct()
    podcasts = LibraryItem.objects.filter(type__name="Podcast").order_by("-date_created")
    dataviz = LibraryItem.objects.filter(type__name="Data visualisation").order_by("-date_created")
    context = {
        "edit_link": "/admin/core/project/" + str(webpage.id) + "/change/",
        "show_project_design": True,
        "webpage": webpage,
        "videos_count": videos.count(),
        "videos": videos.order_by("-date_created")[:5],
        "podcasts_count": podcasts.count(),
        "podcasts": podcasts[:5],
        "dataviz": dataviz[:5],
        "dataviz_count": dataviz.count(),
    }
    if "import" in request.GET:
        from django.core.files import File
        from urllib import request as rq
        import os
        for each in videos:
            if each.video_site == "youtube" and not each.image:
                try:
                    url = "http://i3.ytimg.com/vi/" + each.embed_code + "/maxresdefault.jpg"
                    result = rq.urlretrieve(url)
                    each.image.save(
                        os.path.basename(url),
                        File(open(result[0], 'rb'))
                    )
                    each.save()
                except:
                    print("Sorry, no luck")

    return render(request, "multimedia/index.html", context)

def videos(request):
    collections = Tag.objects.get(pk=749)
    context = {
        "webpage": get_object_or_404(Webpage, pk=61),
        "list": Video.objects.filter(tags__parent_tag=collections).distinct(),
        "categories": Tag.objects.filter(parent_tag=collections).order_by("id"),
    }
    return render(request, "multimedia/video.list.html", context)

def podcasts(request):
    context = {
        "webpage": get_object_or_404(Webpage, pk=62),
        "list": LibraryItem.objects.filter(type__name="Podcast"),
        "load_datatables": True,
    }
    return render(request, "multimedia/podcast.list.html", context)

def podcast(request, id):
    context = {
        "info": get_object_or_404(Video, pk=id),
    }
    return render(request, "multimedia/podcast.html", context)

def datavisualizations(request):
    context = {
        "webpage": get_object_or_404(Webpage, pk=67),
        "list": LibraryItem.objects.filter(type__name="Data visualisation").order_by("-date_created"),
    }
    return render(request, "multimedia/dataviz.list.html", context)

def dataviz(request, id):
    info = get_object_or_404(LibraryItem, pk=id)
    parents = get_parents(info)
    context = {
        "info": info,
        "parents": parents,
        "show_relationship": info.id,
        "title": info.name,
    }
    return render(request, "multimedia/dataviz.html", context)

def upload(request):
    info = get_object_or_404(Webpage, part_of_project_id=PROJECT_ID["library"], slug="/upload/")
    types = [31, 24, 33]
    context = {
        "webpage": info,
        "info": info,
        "types": LibraryItemType.objects.filter(id__in=types),
    }
    return render(request, "library/upload.html", context)

