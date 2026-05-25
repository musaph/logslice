"""Tests for logslice.log_watchdog."""
import pytest
from logslice.log_watchdog import (
    WatchAlert,
    WatchdogOptions,
    WatchdogResult,
    compute_watchdog_result,
    format_watchdog_result,
    watch_lines,
)


def _opts(*patterns, case_sensitive=False, max_alerts=0, stop_on_first=False):
    return WatchdogOptions(
        patterns=list(patterns),
        case_sensitive=case_sensitive,
        max_alerts=max_alerts,
        stop_on_first=stop_on_first,
    )


def _collect(lines, options):
    return list(watch_lines(lines, options))


LINES = [
    "2024-01-01 INFO  service started\n",
    "2024-01-01 ERROR disk full\n",
    "2024-01-01 WARN  high memory\n",
    "2024-01-01 ERROR connection refused\n",
    "2024-01-01 DEBUG heartbeat ok\n",
]


def test_no_patterns_yields_nothing():
    assert _collect(LINES, _opts()) == []


def test_matching_pattern_yields_alert():
    alerts = _collect(LINES, _opts("ERROR"))
    assert len(alerts) == 2


def test_alert_has_correct_line_number():
    alerts = _collect(LINES, _opts("ERROR"))
    assert alerts[0].line_number == 2
    assert alerts[1].line_number == 4


def test_alert_contains_original_line():
    alerts = _collect(LINES, _opts("disk full"))
    assert len(alerts) == 1
    assert "disk full" in alerts[0].line


def test_alert_records_pattern():
    alerts = _collect(LINES, _opts("WARN"))
    assert alerts[0].pattern == "WARN"


def test_case_insensitive_by_default():
    alerts = _collect(LINES, _opts("error"))
    assert len(alerts) == 2


def test_case_sensitive_no_match():
    alerts = _collect(LINES, _opts("error", case_sensitive=True))
    assert alerts == []


def test_stop_on_first_yields_one_alert():
    alerts = _collect(LINES, _opts("ERROR", stop_on_first=True))
    assert len(alerts) == 1


def test_max_alerts_limits_output():
    alerts = _collect(LINES, _opts("ERROR", max_alerts=1))
    assert len(alerts) == 1


def test_multiple_patterns_each_trigger():
    alerts = _collect(LINES, _opts("ERROR", "WARN"))
    assert len(alerts) == 3


def test_one_alert_per_line_even_if_two_patterns_match():
    lines = ["ERROR WARN something bad\n"]
    alerts = _collect(lines, _opts("ERROR", "WARN"))
    assert len(alerts) == 1


def test_callback_is_invoked():
    seen = []
    list(watch_lines(LINES, _opts("ERROR"), callback=seen.append))
    assert len(seen) == 2


def test_compute_watchdog_result_scanned_count():
    result = compute_watchdog_result(LINES, _opts("ERROR"))
    assert result.lines_scanned == len(LINES)


def test_compute_watchdog_result_alert_count():
    result = compute_watchdog_result(LINES, _opts("ERROR"))
    assert result.alert_count == 2


def test_format_watchdog_result_contains_header():
    result = compute_watchdog_result(LINES, _opts("ERROR"))
    text = format_watchdog_result(result)
    assert "lines_scanned=" in text
    assert "alerts=" in text


def test_format_watchdog_result_contains_alert_lines():
    result = compute_watchdog_result(LINES, _opts("disk full"))
    text = format_watchdog_result(result)
    assert "[ALERT]" in text
    assert "disk full" in text


def test_alert_str_representation():
    a = WatchAlert(line_number=3, line="ERROR boom\n", pattern="ERROR")
    assert "[ALERT]" in str(a)
    assert "line 3" in str(a)
    assert "ERROR" in str(a)
