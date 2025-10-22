from django.http import HttpResponse
from .models import Log
from django.template import loader
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.db.models import Avg, Max, Min
import json
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime

def index(request):
    latest_log_list = Log.objects.order_by("-date")
    template = loader.get_template("logs/index.html")
    context = {
        "latest_log_list_json": json.dumps([
            {"id": log.id, "date": str(log.date)}
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
    return render(request, "logs/detail.html", {"log": log, "sleep_duration_str": sleep_duration_str, "mood_scale": range(1, 11)})


def _yyyymmdd_to_date(yyyymmdd: int):
    # 8桁整数 → date
    return datetime.strptime(str(yyyymmdd), "%Y%m%d").date()

def detail_by_date(request, yyyymmdd):
    d = _yyyymmdd_to_date(yyyymmdd)
    log = get_object_or_404(Log, date=d)
    sleep_duration_str = None
    if log.sleep_duration:
        total_seconds = log.sleep_duration.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        sleep_duration_str = f"{hours}時間 {minutes}分"
    return render(request, "logs/detail.html", {"log": log, "sleep_duration_str": sleep_duration_str, "mood_scale": range(1, 11)})


def update_log_by_date(request, yyyymmdd):
    d = _yyyymmdd_to_date(yyyymmdd)
    log = get_object_or_404(Log, date=d)
    if request.method == "POST":
        # ← ここは今の update_log と同じ処理でOK（log を date で取っているだけ）
        log.good_1 = (request.POST.get("good_1") or "").strip()
        log.good_2 = (request.POST.get("good_2") or "").strip()
        log.good_3 = (request.POST.get("good_3") or "").strip()
        log.growth = (request.POST.get("growth") or "").strip()
        try:
            log.mood = int(request.POST.get("mood", log.mood))
        except (TypeError, ValueError):
            pass

        def parse_dt(name, current):
            v = request.POST.get(name)
            if not v: return current
            dt = parse_datetime(v)
            if dt and timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.get_current_timezone())
            return dt

        log.sleep_time = parse_dt("sleep_time", log.sleep_time)
        log.wakeup_time = parse_dt("wakeup_time", log.wakeup_time)
        if log.sleep_time and log.wakeup_time:
            log.sleep_duration = log.wakeup_time - log.sleep_time
        else:
            log.sleep_duration = None

        # date は変更しない（編集で日付を動かさない方針）
        log.save()
        return redirect("logs:detail_by_date", yyyymmdd=yyyymmdd)

    return render(request, "logs/detail.html", {
        "log": log,
        "mood_scale": range(1, 11),
    })

def delete_log_by_date(request, yyyymmdd):
    d = _yyyymmdd_to_date(yyyymmdd)
    log = get_object_or_404(Log, date=d)
    if request.method == "GET":
        log.delete()
        return redirect("logs:index")
    return redirect("logs:detail_by_date", yyyymmdd=yyyymmdd)

def update_log(request, log_id):
    log = get_object_or_404(Log, id=log_id)

    if request.method == "POST":
        log.updated_at = timezone.now()
        log.good_1 = request.POST.get("good_1", "").strip()
        log.good_2 = request.POST.get("good_2", "").strip()
        log.good_3 = request.POST.get("good_3", "").strip()
        log.growth = request.POST.get("growth", "").strip()
        log.sleep_time = parse_datetime(request.POST.get("sleep_time")) or log.sleep_time
        log.wakeup_time = parse_datetime(request.POST.get("wakeup_time")) or log.wakeup_time
        log.mood = int(request.POST.get("mood", log.mood))
    
        log.comment = request.POST.get("comment", "")

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
        # テキスト系
        date_str = request.POST.get("date")
        date_val = parse_datetime(date_str) if date_str else timezone.localdate()
        good_1 = (request.POST.get("good_1") or "").strip()
        good_2 = (request.POST.get("good_2") or "").strip()
        good_3 = (request.POST.get("good_3") or "").strip()
        growth = (request.POST.get("growth") or "").strip()

        # 気分（1〜10）
        try:
            mood = int(request.POST.get("mood", 5))
        except (TypeError, ValueError):
            mood = 5

        # datetime-local → Python datetime（アウェア化）
        def parse_dt(name):
            v = request.POST.get(name)
            if not v:
                return None
            dt = parse_datetime(v)  # "YYYY-MM-DDTHH:MM"
            if dt and timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.get_current_timezone())
            return dt

        sleep_time = parse_dt("sleep_time")
        wakeup_time = parse_dt("wakeup_time")

        # date はモデルの default=timezone.localdate に任せる
        log = Log(
            date=date_val,
            good_1=good_1,
            good_2=good_2,
            good_3=good_3,
            growth=growth,
            mood=mood,
            sleep_time=sleep_time,
            wakeup_time=wakeup_time,
        )
        # sleep_duration は models.Log.save() で自動計算される
        log.save()

        return redirect("logs:index")

    # GET
    date_str = request.GET.get("date")  # "YYYY-MM-DD" or None
    display_date = date_str or timezone.localdate().isoformat()  # 表示用
    return render(request, "logs/create_log.html", {
        "mood_scale": range(1, 11),
        "prefill_date": display_date,   # 表示＆hidden でPOST
    })


def delete_log(request, log_id):
    log = get_object_or_404(Log, id=log_id)
    log.delete()
    return redirect("logs:index")
