from django.contrib import admin

from .models import (Argument,
                     Keyword,
                     KeywordStatus,
                     Message,
                     Suite,
                     SuiteStatus,
                     Tag,
                     TagStatus,
                     TestRunError,
                     TestRun,
                     Test,
                     TestStatus,
                     TestRunStatus)


# Register your models here.
@admin.register(Argument)
class ArgumentAdmin(admin.ModelAdmin):
    list_display = ("id", 'keyword', 'content', )


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ("id", 'name', 'type', 'parent_keyword', 'doc')


@admin.register(KeywordStatus)
class KeywordStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "keyword", "status", 'test_run')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", 'keyword', 'level', 'content',)


@admin.register(Suite)
class SuiteAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "doc", "source", "xml_id", "parent_suite")


@admin.register(SuiteStatus)
class SuiteStatusAdmin(admin.ModelAdmin):
    list_display = ("id", 'test_run', 'suite', 'status', 'passed', 'failed')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", 'test', 'content')


@admin.register(TagStatus)
class TagStatusAdmin(admin.ModelAdmin):
    list_display = ("id", 'test_run', 'name', )


@admin.register(TestRunError)
class TestRunErrorAdmin(admin.ModelAdmin):
    list_display = ("id", "test_run", 'level', 'content')


@admin.register(TestRun)
class TestRunAdmin(admin.ModelAdmin):
    list_display = ("id", "imported_at", "xml_source", 'duration', "submitted_by",)

    def duration(self, obj):
        if obj.finished_at is not None and obj.started_at is not None:
            return obj.finished_at - obj.started_at
        else:
            return "unknown"


@admin.register(TestRunStatus)
class TestRunStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "test_run", "passed", 'failed',)


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "suite", 'doc',)


@admin.register(TestStatus)
class TestStatusAdmin(admin.ModelAdmin):
    list_display = ("id", 'test_run', 'test', 'status')
