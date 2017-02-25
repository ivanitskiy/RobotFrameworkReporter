
from cgi import log
from uuid import uuid4
import datetime
import os

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import models
from django.utils.encoding import force_text, force_str


def path_and_rename(instance, filename):
    ext = filename.split('.')[-1]
    if instance.pk:
        filename = '{}.{}'.format(instance.pk, ext)
    else:
        filename = '{}.{}'.format(uuid4().hex, ext)
    dirname = force_text(datetime.datetime.now().strftime(force_str('uploads/%Y/%m/%d/')))
    return os.path.join(dirname, filename)


class TestRun(models.Model):
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    xml_source = models.FileField(upload_to=path_and_rename, null=True, blank=True)
    report_file = models.FileField(upload_to='uploads/%Y/%m/%d/', null=True, blank=True)
    log_file = models.FileField(upload_to='uploads/%Y/%m/%d/', null=True, blank=True)
    hash = models.TextField(unique=True)
    imported_at = models.DateTimeField(auto_now=True)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __unicode__(self):
        return "%s" % self.imported_at

    def generate_robot_report(self):
        if self.xml_source is not None:
            from robot.reporting.resultwriter import ResultWriter
            log = os.path.splitext(self.xml_source.file.name)[0] + "_log.html"
            report = os.path.splitext(self.xml_source.file.name)[0] + "_report.html"

            if self.log_file is not None:
                self.log_file.delete()
            if self.report_file is not None:
                self.report_file.delete()
            self.log_file.save(os.path.basename(log), ContentFile('no content'))
            self.report_file.save(os.path.basename(report), ContentFile('no content'))
            writer = ResultWriter(self.xml_source.file.name)

            retval = writer.write_results(report=report, log=log, xunit=None)
            if retval == -1:
                print "failed to regenerate files"


class Suite(models.Model):
    source = models.TextField(blank=True, null=True)
    xml_id = models.TextField()
    parent_suite = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    name = models.TextField()
    doc = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = (('name', 'xml_id'),)

    def __unicode__(self):
        return "%s" % self.name


class Test(models.Model):
    doc = models.TextField(blank=True, null=True)
    xml_id = models.TextField()
    name = models.TextField()
    timeout = models.TextField(blank=True, null=True)
    suite = models.ForeignKey(Suite, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('suite', 'name'),)

    def __unicode__(self):
        return "%s" % self.name


class Keyword(models.Model):
    name = models.TextField()
    doc = models.TextField(blank=True, null=True)
    timeout = models.TextField(blank=True, null=True)
    type = models.TextField()
    parent_keyword = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, null=True, blank=True)
    suite = models.ForeignKey(Suite, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = (('name', 'type', 'doc', 'parent_keyword'),)

    def __unicode__(self):
        return "%s" % self.name


class KeywordStatus(models.Model):
    status = models.TextField()
    elapsed = models.IntegerField()
    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE)
    keyword = models.ForeignKey(Keyword, on_delete=models.CASCADE, null=True, blank=True)

    def __unicode__(self):
        return "%s %s" % (self.keyword, self.status)


class Argument(models.Model):
    content = models.TextField()
    keyword = models.ForeignKey(Keyword, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('keyword', 'content'),)

    def __unicode__(self):
        return "%s %s" % (self.keyword, self.content)


class Message(models.Model):
    content = models.TextField()
    keyword = models.ForeignKey(Keyword, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    level = models.TextField()

    class Meta:
        unique_together = (('keyword', 'level', 'content'),)

    def __unicode__(self):
        return "%s %s" % (self.level, self.content)


class SuiteStatus(models.Model):
    status = models.TextField()
    failed = models.IntegerField()
    elapsed = models.IntegerField()
    passed = models.IntegerField()
    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE)
    suite = models.ForeignKey(Suite, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('test_run', 'suite'),)

    def __unicode__(self):
        return "%s %s" % (self.test_run, self.suite)


class TagStatus(models.Model):
    name = models.TextField()
    failed = models.IntegerField()
    elapsed = models.IntegerField(blank=True, null=True)
    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE)
    critical = models.IntegerField()
    passed = models.IntegerField()

    class Meta:
        unique_together = (('test_run', 'name'),)

    def __unicode__(self):
        return "%s %s" % (self.test_run, self.name)


class Tag(models.Model):
    content = models.TextField()
    test = models.ForeignKey(Test, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('test', 'content'),)


class TestRunError(models.Model):
    content = models.TextField()
    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    level = models.TextField()

    class Meta:
        unique_together = (('test_run', 'level', 'content'),)


class TestRunStatus(models.Model):
    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE)
    passed = models.IntegerField()
    name = models.TextField()
    failed = models.IntegerField()
    elapsed = models.IntegerField(blank=True, null=True)

    class Meta:
        unique_together = (('test_run', 'name'),)

    def __unicode__(self):
        return "%s passed: %s failed:%s elapsed:%s " % (self.name, self.passed, self.failed, self.elapsed)


class TestStatus(models.Model):
    status = models.TextField()
    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    elapsed = models.IntegerField()

    class Meta:
        unique_together = (('test_run', 'test'),)

    def __unicode__(self):
        return self.status
