'''
Created on Jan 28, 2017

@author: ivanitskiy
'''
from datetime import datetime
from hashlib import sha1
# from io import BytesIO
from StringIO import StringIO
from django.core.files.base import File, ContentFile
import logging

from robot.result.executionresult import Result
from robot.result.resultbuilder import ExecutionResultBuilder
from robot.utils.etreewrapper import ETSource


from report.models import (TestRun,
                           TestRunError,
                           TagStatus,
                           TestRunStatus,
                           KeywordStatus,
                           Message,
                           Argument,
                           Suite,
                           SuiteStatus,
                           Test, TestStatus, Tag, Keyword)
import xml.etree.ElementTree as ET
from _io import BytesIO
import six
from django.utils.encoding import force_bytes
from robot.reporting.resultwriter import ResultWriter
import tempfile
import os


LOG = logging.getLogger()


def _hash(xml_file, block_size=68157440):
    hasher = sha1()
    for chunk in xml_file.chunks():
        hasher.update(chunk)
    return hasher.hexdigest()


def _parse_suite_status(test_run, suite_obj, suite):
    SuiteStatus.objects.get_or_create(test_run=test_run,
                                      suite=suite_obj,
                                      passed=suite.statistics.all.passed,
                                      failed=suite.statistics.all.failed,
                                      elapsed=suite.elapsedtime,
                                      status=suite.status
                                      )


def _format_robot_timestamp(timestamp):
    return datetime.strptime(timestamp, '%Y%m%d %H:%M:%S.%f')


def _parse_arguments(args, keyword):
    for arg in args:
        Argument.objects.get_or_create(keyword=keyword,
                                       content=arg)


def _parse_messages(messages, keyword):
    for message in messages:
        Message.objects.get_or_create(keyword=keyword,
                                      level=message.level,
                                      timestamp=_format_robot_timestamp(message.timestamp),
                                      content=message.message)


def _parse_keyword_status(test_run, parent_keyword, keyword):
    KeywordStatus.objects.get_or_create(status=keyword.status,
                                        elapsed=keyword.elapsedtime,
                                        test_run=test_run,
                                        keyword=parent_keyword,
                                        )


def _parse_tags(tags, test_id):
    for tag in tags:
        Tag.objects.get_or_create(test=test_id, content=tag)


def _parse_test_status(test_run, test_id, test):
    TestStatus.objects.get_or_create(test_run=test_run,
                                     test=test_id,
                                     status=test.status,
                                     elapsed=test.elapsedtime
                                     )


def _parse_test_run_stats(stat, test_run):
    TestRunStatus.objects.get_or_create(test_run=test_run,
                                        name=stat.name,
                                        elapsed=getattr(stat, 'elapsed', None),
                                        failed=stat.failed,
                                        passed=stat.passed
                                        )


def _parse_tag_stats(stat, test_run):
    TagStatus.objects.get_or_create(test_run=test_run,
                                    name=stat.name,
                                    critical=stat.critical,
                                    elapsed=getattr(stat, 'elapsed', None),
                                    failed=stat.failed,
                                    passed=stat.passed)


def _parse_test_run_statistics(test_run_statistics, test_run):
    LOG.info('`--> Parsing test run statistics')
    [_parse_test_run_stats(stat, test_run) for stat in test_run_statistics]


def _parse_tag_statistics(tag_statistics, test_run):
    LOG.info('  `--> Parsing tag statistics')
    [_parse_tag_stats(stat, test_run) for stat in tag_statistics.tags.values()]


def _parse_statistics(statistics, test_run):
    _parse_test_run_statistics(statistics.total, test_run)
    _parse_tag_statistics(statistics.tags, test_run)


def _parse_errors(errors, test_run):
    for error in errors:
        TestRunError.objects.get_or_create(test_run=test_run,
                                           content=error.message,
                                           timestamp=_format_robot_timestamp(error.timestamp),
                                           level=error.level)


def _parse_suite(suite_el, test_run, parent_suite=None):
    LOG.info('`--> Parsing suite: %s' % suite_el.name)
    suite_obj, __ = Suite.objects.get_or_create(parent_suite=parent_suite,
                                                xml_id=suite_el.id,
                                                name=suite_el.name,
                                                source=suite_el.source,
                                                doc=suite_el.doc)
    _parse_suite_status(test_run, suite_obj, suite_el)
    _parse_suites(suite_el, test_run, parent_suite=suite_obj)
    _parse_tests(suite_el.tests, test_run, suite_obj)
    _parse_keywords(suite_el.keywords, test_run, suite_obj, None)


def _parse_suites(suite, test_run, parent_suite):
    for subsuite in suite.suites:
        _parse_suite(subsuite, test_run, parent_suite)


def _parse_tests(tests, test_run, suite):
    for test in tests:
        _parse_test(test, test_run, suite)


def _parse_test(test, test_run, suite_obj):
    LOG.info('  `--> Parsing test: %s' % test.name)
    test_obj, __ = Test.objects.get_or_create(suite=suite_obj,
                                              xml_id=test.id,
                                              name=test.name,
                                              timeout=test.timeout,
                                              doc=test.doc)
    _parse_test_status(test_run, test_obj, test)
    _parse_tags(test.tags, test_obj)
    _parse_keywords(test.keywords, test_run, None, test_obj)


def _parse_keywords(keywords, test_run, suite_id, test_id, keyword_id=None):
    for keyword in keywords:
        _parse_keyword(keyword, test_run, suite_id, test_id, keyword_id)


def _parse_keyword(keyword, test_run, suite_id, test_id, parent_keyword):
    kw, __ = Keyword.objects.get_or_create(suite=suite_id,
                                           test=test_id,
                                           parent_keyword=parent_keyword,
                                           name=keyword.name,
                                           type=keyword.type,
                                           timeout=keyword.timeout,
                                           doc=keyword.doc)

    _parse_keyword_status(test_run, kw, keyword)
    _parse_messages(keyword.messages, kw)
    _parse_arguments(keyword.args, kw)
    _parse_keywords(keyword.keywords, test_run, None, None, kw)


def _extarct_only_robot(xmlfile):
    """remove from file not robot's elements
    robot elements are: 'suite' 'statistics' 'errors'
    """

    original_doc = ET.parse(xmlfile)
    root = original_doc.getroot()
    devices = root.find("devices")
    if devices is not None:
        root.remove(devices)

    source = StringIO(ET.tostring(root))
    ets = ETSource(source)
    execution_result = ExecutionResultBuilder(ets).build(Result())
    patched_file = File(BytesIO(force_bytes(source.getvalue())), name=xmlfile.name)
    return (execution_result, patched_file)


def handle_uploaded_file(request):
    f = request.FILES['xmlfile']
    execution_result, patched_report = _extarct_only_robot(f)
    started_at = None
    finished_at = None
    if execution_result.suite.starttime:
        started_at = _format_robot_timestamp(execution_result.suite.starttime)
    if execution_result.suite.starttime:
        finished_at = _format_robot_timestamp(execution_result.suite.endtime)
    test_run, created = TestRun.objects.get_or_create(started_at=started_at,
                                                      finished_at=finished_at,
                                                      xml_source=patched_report,
                                                      hash=_hash(patched_report),
                                                      submitted_by=request.user)

    if created:
        test_run.generate_robot_report()
        _parse_errors(execution_result.errors.messages, test_run)
        _parse_statistics(execution_result.statistics, test_run)
        _parse_suite(execution_result.suite, test_run)
