from django.contrib import admin

from .models import Log

class LogAdmin(admin.ModelAdmin):
    list_display = ("date", "sleep_time", "wakeup_time", "log_text", "mood")
    list_filter = ("date", "mood")
    search_fields = ("log_text",)
    date_hierarchy = "date"

admin.site.register(Log, LogAdmin)