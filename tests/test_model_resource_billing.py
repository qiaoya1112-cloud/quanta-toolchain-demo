import re
import unittest
from datetime import date
from unittest.mock import patch

import toolchain_demo


class DemoDate(date):
    @classmethod
    def today(cls):
        return cls(2026, 9, 10)


def read_usage(client, **query):
    response = client.get("/model/resources", query_string=query)
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    panel = page.split('data-resource-panel="usage">', 1)[1].split('data-resource-panel="exclusive">', 1)[0]
    values = re.findall(r'class="model-resource-stat"[^>]*><span>[^<]+</span><b>([^<]+)</b>', panel)
    return panel, values


class ResourceBillingTests(unittest.TestCase):
    def setUp(self):
        date_patch = patch.object(toolchain_demo, "date", DemoDate)
        date_patch.start()
        self.addCleanup(date_patch.stop)
        self.client = toolchain_demo.app.test_client()

    def test_presets_filter_usage_and_recharges_but_keep_prior_balance(self):
        for period, recharge, hours, cost in [
            ("all", "5,000.00", "585.5", "3410.00"),
            ("today", "0.00", "45.5", "280.00"),
            ("7", "500.00", "205.5", "1220.00"),
            ("30", "1,500.00", "425.5", "2470.00"),
        ]:
            with self.subTest(period=period):
                panel, values = read_usage(self.client, period=period)
                self.assertEqual(values, ["1,590.00", recharge, "318.0", hours])
                rows = re.findall(r'<tr>(.*?)</tr>', panel.split('<tbody>', 1)[1], re.S)
                totals = [re.findall(r'class="mono">([^<]+)', row) for row in rows]
                self.assertEqual(sum(toolchain_demo.Decimal(row[2].replace(",", "")) for row in totals), toolchain_demo.Decimal(cost))
                self.assertNotIn("本月", panel)
                self.assertNotIn("<tfoot>", panel)

    def test_custom_range_includes_both_bounds_and_uses_closing_balance(self):
        _, values = read_usage(self.client, period="custom", start="2026-08-21", end="2026-08-21")
        self.assertEqual(values, ["2,310.00", "1,000.00", "462.0", "220.0"])

    def test_remaining_hours_change_with_gpu_and_preserve_range(self):
        panel, values = read_usage(self.client, period="custom", start="2026-08-21", end="2026-08-21", gpu="H800-80G")
        self.assertEqual(values, ["2,310.00", "1,000.00", "231.0", "220.0"])
        self.assertIn('<option value="H800-80G" selected>', panel)
        self.assertIn('value="custom" checked', panel)

    def test_empty_range_returns_zero_usage_without_resetting_balance(self):
        _, values = read_usage(self.client, period="custom", start="2026-09-01", end="2026-09-02")
        self.assertEqual(values, ["2,310.00", "0.00", "462.0", "0.0"])

    def test_invalid_dates_show_error_and_restore_all_range(self):
        for start, end in [("invalid", ""), ("2026-09-10", "2026-09-01"), ("2026-09-01", "2026-09-11")]:
            with self.subTest(start=start, end=end):
                panel, values = read_usage(self.client, period="custom", start=start, end=end)
                self.assertIn('role="alert"', panel)
                self.assertIn('value="all" checked', panel)
                self.assertEqual(values, ["1,590.00", "5,000.00", "318.0", "585.5"])
