from django.http import HttpResponse
from .models import Log
from django.template import loader
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.db.models import Avg, Max, Min
import json
from django.core.serializers.json import DjangoJSONEncoder

def index(request):
    latest_log_list = Log.objects.order_by("-date")
    template = loader.get_template("logs/index.html")
    context = {
        "latest_log_list_json": json.dumps([
            {"id": log.id, "date": str(log.date), "log_text": log.log_text}
            for log in latest_log_list
        ], cls=DjangoJSONEncoder),
        "latest_log_list": latest_log_list,
    }
    return HttpResponse(template.render(context, request))


def detail(request, log_id):
    log = get_object_or_404(Log, pk=log_id)
    sleep_duration_str = None
    if log.sleep_duration:
        total_seconds = log.sleep_duration.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        sleep_duration_str = f"{hours}時間 {minutes}分"
    return render(request, "logs/detail.html", {"log": log, "sleep_duration_str": sleep_duration_str})


def update_log(request, log_id):
    log = get_object_or_404(Log, id=log_id)

    if request.method == "POST":
        log.date = parse_datetime(request.POST.get("date")) or log.date
        log.log_text = request.POST.get("log_text", "")
        log.sleep_time = parse_datetime(request.POST.get("sleep_time")) or log.sleep_time
        log.wakeup_time = parse_datetime(request.POST.get("wakeup_time")) or log.wakeup_time
        log.mood = int(request.POST.get("mood", log.mood))

        # sleep_duration を自動更新
        if log.sleep_time and log.wakeup_time:
            log.sleep_duration = log.wakeup_time - log.sleep_time
        else:
            log.sleep_duration = None

        log.save()
        return redirect("logs:detail", log_id=log.id)

    return render(request, "detail.html", {"log": log})


def analyze(request):
    logs = Log.objects.exclude(sleep_duration__isnull=True).order_by('-date')

    durations = [
        log.sleep_duration.total_seconds() / 3600
        for log in logs
        if 0 < log.sleep_duration.total_seconds() / 3600 <= 24
    ]

    if durations:
        average_duration = round(sum(durations) / len(durations), 2)
        longest_duration = round(max(durations), 2)
        shortest_duration = round(min(durations), 2)
    else:
        average_duration = longest_duration = shortest_duration = 0

    print(durations)

    for log in logs:
        if log.sleep_duration:
            log.duration_hours = round(log.sleep_duration.total_seconds() / 3600, 2)
        else:
            log.duration_hours = "-"


    context = {
        "logs": logs,
        "average_duration": average_duration,
        "longest_duration": longest_duration,
        "shortest_duration": shortest_duration,
        "latest_log_list_json": json.dumps([
            {
                "date": str(log.date),
                "sleep_time": log.sleep_time.isoformat() if log.sleep_time else None,
                "wakeup_time": log.wakeup_time.isoformat() if log.wakeup_time else None
            }
            for log in logs
        ], cls=DjangoJSONEncoder)
    }
    return render(request, "logs/analyze.html", context)


def create_log(request):
    if request.method == "POST":
        date = request.POST.get("date") or timezone.now().date()
        log_text = request.POST.get("log_text", "").strip()
        sleep_time = parse_datetime(request.POST.get("sleep_time")) or None
        wakeup_time = parse_datetime(request.POST.get("wakeup_time")) or None
        mood = int(request.POST.get("mood", 5))

        sleep_duration = None
        if sleep_time and wakeup_time:
            sleep_duration = wakeup_time - sleep_time

        log = Log.objects.create(
            date=date,
            log_text=log_text,
            sleep_time=sleep_time,
            wakeup_time=wakeup_time,
            mood=mood,
            sleep_duration=sleep_duration
        )
        return redirect("logs:index")

    return render(request, "logs/create_log.html")


def delete_log(request, log_id):
    log = get_object_or_404(Log, id=log_id)
    log.delete()
    return redirect("logs:index")
