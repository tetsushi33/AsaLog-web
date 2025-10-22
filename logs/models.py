from django.db import models
from datetime import timedelta, date
from django.utils import timezone   # ← 追加（重要：タイムゾーン対応）


# Create your models here.
class Log(models.Model):
    # 記録の日付
    date = models.DateField(unique=True, default=timezone.localdate)
    # 最終更新日（自動で更新される）
    updated_at = models.DateTimeField(auto_now=True)
    # 睡眠時間
    sleep_time = models.DateTimeField("sleep time", null=True, blank=True)  # 入眠時間
    wakeup_time = models.DateTimeField("wakeup time", null=True, blank=True)  # 起床時間
    sleep_duration = models.DurationField(null=True, blank=True)  # ← 追加
    # 「良かったこと」を3つ
    good_1 = models.CharField("良かったこと①", max_length=200, blank=True, default="")
    good_2 = models.CharField("良かったこと②", max_length=200, blank=True, default="")
    good_3 = models.CharField("良かったこと③", max_length=200, blank=True, default="")
    # 昨日から成長した点
    growth = models.CharField("昨日から成長した点", max_length=200, blank=True, default="")
    # コメント
    comment = models.CharField(max_length=200)  # ログ（テキスト）
    # 気分
    mood = models.IntegerField(default=5)  # 気分（1-10 の数値）

    def save(self, *args, **kwargs):
        if self.sleep_time and self.wakeup_time:
            self.sleep_duration = self.wakeup_time - self.sleep_time
        else:
            self.sleep_duration = None
        super().save(*args, **kwargs)

    #def __str__(self):
    #    return str(self.date)
    def __str__(self):
        return f"{self.date} (last updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"

    
    # 表示用の便利プロパティ（空は除外）
    @property
    def good_list(self):
        return [t for t in [self.good_1, self.good_2, self.good_3] if t.strip()]
    