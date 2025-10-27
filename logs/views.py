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
from datetime import timedelta
import base64
from django.core.files.base import ContentFile
import os
from django.core.files.storage import default_storage


def index(request):
    latest_log_list = Log.objects.values(
    "id", "date", "good_1", "sleep_time", "wakeup_time"
    )   
    template = loader.get_template("logs/index.html")
    context = {
        "latest_log_list_json": json.dumps(list(latest_log_list), cls=DjangoJSONEncoder),
        "latest_log_list": latest_log_list,
    }
    return HttpResponse(template.render(context, request))


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

    # 前後の日付を計算
    prev_date = d - timedelta(days=1)
    next_date = d + timedelta(days=1)
    # ログの有無をチェック
    show_prev = Log.objects.filter(date=prev_date).exists()
    show_next = Log.objects.filter(date=next_date).exists()
    return render(
        request, 
        "logs/detail2.html", 
        {
            "log": log, 
            "sleep_duration_str": sleep_duration_str, 
            "mood_scale": range(1, 11),
            "prev_date": prev_date,
            "next_date": next_date,
            "show_prev": show_prev,
            "show_next": show_next,
        }
    )


def update_log_by_date(request, yyyymmdd):
    d = _yyyymmdd_to_date(yyyymmdd)
    log = get_object_or_404(Log, date=d)

    if request.method == "POST":
        # 既存の部分更新はそのまま
        log.good_1 = (request.POST.get("good_1") or "").strip()
        log.good_2 = (request.POST.get("good_2") or "").strip()
        log.good_3 = (request.POST.get("good_3") or "").strip()
        log.growth = (request.POST.get("growth") or "").strip()
        log.comment = (request.POST.get("comment") or "").strip()

        # --- 写真（上書き保存）ここから ---
        photo_data = request.POST.get("photo_data")
        if photo_data:
            # データURL: 'data:image/png;base64,....'
            try:
                fmt, imgstr = photo_data.split(';base64,')
                mime = fmt.split(':', 1)[1]               # 'image/png'
                ext = mime.split('/')[-1].lower()         # 'png' など
            except Exception:
                mime = 'image/jpeg'
                ext = 'jpg'

            # 既存ファイルがあれば削除（これが肝！）
            if log.photo and log.photo.name:
                try:
                    log.photo.storage.delete(log.photo.name)
                except Exception:
                    # ストレージ上に無ければ無視
                    pass

            # 固定名: 例 20251025-1.jpg
            filename = f"{yyyymmdd}-1.{ext}"

            # decodeして同名でsave（upload_to配下に保存されます）
            content = ContentFile(base64.b64decode(imgstr))
            # save=False でフィールドだけ差し替え、最後に log.save()
            log.photo.save(filename, content, save=False)
        # --- 写真ここまで ---

        # 気分
        try:
            log.mood = int(request.POST.get("mood", log.mood))
        except (TypeError, ValueError):
            pass

        # 日時
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

        log.save()
        return redirect("logs:detail_by_date", yyyymmdd=yyyymmdd)

    return render(request, "logs/detail2.html", {
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

        #photo_data = request.POST.get("photo_data")
        #photo_file = None
        #if photo_data:
        #    format, imgstr = photo_data.split(';base64,')
        #    ext = format.split('/')[-1]
        #    photo_file = ContentFile(base64.b64decode(imgstr), name=f"captured.{ext}")

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
            #photo=photo_file,
        )

        # ---- 画像（カメラbase64を優先、なければFILES）----
        final_fileobj = None
        final_filename = None

        photo_data = request.POST.get("photo_data")
        if photo_data:
            # data:image/png;base64,xxxx 形式を想定
            try:
                fmt, imgstr = photo_data.split(";base64,")
                mime = fmt.split(":", 1)[1]             # e.g. image/png
                ext = mime.split("/")[-1].lower()       # png / jpeg / webp など
            except Exception:
                ext = "jpg"  # 失敗時はjpgでフォールバック
                imgstr = photo_data

            final_filename = f"{date_val.strftime('%Y%m%d')}-1.{ext}"
            final_fileobj = ContentFile(base64.b64decode(imgstr))
        else:
            uploaded = request.FILES.get("photo")
            if uploaded:
                root, up_ext = os.path.splitext(uploaded.name)
                safe_ext = (up_ext or ".jpg").lower()
                final_filename = f"{date_val.strftime('%Y%m%d')}-1{safe_ext}"
                final_fileobj = uploaded

        # ---- 同名上書き（upload_to対応）----
        if final_fileobj and final_filename:
            # フィールド取得
            photo_field = Log._meta.get_field("photo")
            # upload_to が関数/パスいずれでもOKなように、実インスタンスと一緒に解決
            storage_path = photo_field.generate_filename(log, final_filename)

            # 既存があれば削除（同名ファイルは必ず消す）
            try:
                if default_storage.exists(storage_path):
                    default_storage.delete(storage_path)
            except Exception:
                pass  # ストレージ種別によっては存在チェックで例外が出ることがあるので握りつぶす

            # フィールドにセット（save=Falseで最後にまとめて保存）
            # UploadedFile の場合 name が上書きされるよう、明示的に filename を指定して保存
            log.photo.save(final_filename, final_fileobj, save=False)

        log.save()

        return redirect("logs:index")

    # GET
    date_str = request.GET.get("date")  # "YYYY-MM-DD" or None
    display_date = date_str or timezone.localdate().isoformat()  # 表示用
    return render(request, "logs/create_log.html", {
        "mood_scale": range(1, 11),
        "prefill_date": display_date,   # 表示＆hidden でPOST
    })
