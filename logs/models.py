from django.db import models
from datetime import timedelta, date

# Create your models here.
class Log(models.Model):
    date = models.DateField(default=date.today)  # 記録の日付
    sleep_time = models.DateTimeField("sleep time", null=True, blank=True)  # 入眠時間
    wakeup_time = models.DateTimeField("wakeup time", null=True, blank=True)  # 起床時間
    log_text = models.CharField(max_length=200)  # ログ（テキスト）
    mood = models.IntegerField(default=5)  # 気分（1-10 の数値）
    sleep_duration = models.DurationField(null=True, blank=True)  # ← 追加
    
    #@property
    #def sleep_duration(self):
    #    if self.sleep_time is None or self.wakeup_time is None:
    #        return timedelta(0)
    #    return self.wakeup_time - self.sleep_time

    def save(self, *args, **kwargs):
        if self.sleep_time and self.wakeup_time:
            self.sleep_duration = self.wakeup_time - self.sleep_time
        else:
            self.sleep_duration = None
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.date)
    