"""Unit and characterization tests for the refactored pricing.py module.

พิสูจน์ว่าโมเดล pricing.py ที่ผ่านการ Refactor ให้ผลลัพธ์เหมือนกับ pricing_legacy.py ทุกประการ
และทดสอบฟังก์ชันย่อยที่แยกออกมาตามหลัก Modular Design.
"""

import datetime

import pytest

import pricing


@pytest.fixture(autouse=True)
def reset_global_state():
    """ล้างสถานะตัวแปรส่วนกลาง ทั้งก่อนและหลังการทดสอบแต่ละข้อ."""
    pricing.member_points.clear()
    pricing.LOG.clear()
    yield
    pricing.member_points.clear()
    pricing.LOG.clear()


class TestRefactoredPricingCharacterization:
    """ยืนยันพฤติกรรมของ calc ใน pricing.py ว่าตรงกับ Characterization Test เดิม 100%."""

    def test_group_1_normal_price_single_item(self):
        items = [("สมุด", 1, 100.0)]
        result = pricing.calc(items)
        assert result == 107.0
        assert pricing.LOG == [(None, 107.0)]

    def test_group_1_normal_price_multiple_items(self):
        items = [("ปากกา", 10, 20.0), ("ดินสอ", 5, 10.0)]
        result = pricing.calc(items)
        assert result == 267.5
        assert pricing.LOG == [(None, 267.5)]

    def test_group_2_bulk_purchase_threshold_49_no_discount(self):
        items = [("ปากกา", 49, 10.0)]
        result = pricing.calc(items)
        assert result == 524.3

    def test_group_2_bulk_purchase_threshold_50_discount_5_percent(self):
        items = [("ปากกา", 50, 10.0)]
        result = pricing.calc(items)
        assert result == 508.25

    def test_group_2_bulk_purchase_threshold_99_discount_5_percent(self):
        items = [("ปากกา", 99, 10.0)]
        result = pricing.calc(items)
        assert result == 1006.34

    def test_group_2_bulk_purchase_threshold_100_discount_10_percent(self):
        items = [("ปากกา", 100, 10.0)]
        result = pricing.calc(items)
        assert result == 963.0

    def test_group_3_zero_quantity_item(self):
        items = [("สมุด", 0, 100.0)]
        result = pricing.calc(items)
        assert result == 0.0
        assert pricing.LOG == [(None, 0.0)]

    def test_group_3_negative_quantity_item(self):
        items = [("สมุด", -5, 100.0)]
        result = pricing.calc(items)
        assert result == 0.0

    def test_group_3_mixed_zero_and_valid_quantity(self):
        items = [("ของแถมหมด", 0, 200.0), ("สินค้าปกติ", 2, 50.0)]
        result = pricing.calc(items)
        assert result == 107.0

    def test_group_4_member_discount_and_points_accumulation(self):
        items = [("สินค้า", 1, 1000.0)]
        result = pricing.calc(items, member="Somchai")
        assert result == 1016.5
        assert pricing.member_points["Somchai"] == 9
        assert pricing.LOG == [("Somchai", 1016.5)]

    def test_group_4_member_points_cumulative_across_multiple_purchases(self):
        items = [("สินค้า", 1, 1000.0)]
        pricing.calc(items, member="Somchai")
        assert pricing.member_points["Somchai"] == 9

        pricing.calc(items, member="Somchai")
        assert pricing.member_points["Somchai"] == 18
        assert len(pricing.LOG) == 2

    def test_group_4_member_under_100_baht_gets_zero_points(self):
        items = [("สินค้าเล็ก", 1, 100.0)]
        result = pricing.calc(items, member="Bob")
        assert result == 101.65
        assert pricing.member_points["Bob"] == 0

    def test_group_5_coupon_save50(self):
        items = [("สินค้า", 1, 200.0)]
        result = pricing.calc(items, coupon="SAVE50")
        assert result == 160.5

    def test_group_5_coupon_half(self):
        items = [("สินค้า", 1, 200.0)]
        result = pricing.calc(items, coupon="HALF")
        assert result == 107.0

    def test_group_5_coupon_newyear_in_january(self):
        items = [("สินค้า", 1, 200.0)]
        jan_date = datetime.date(2026, 1, 15)
        result = pricing.calc(items, coupon="NEWYEAR", today=jan_date)
        assert result == 171.2

    def test_group_5_coupon_newyear_outside_january(self):
        items = [("สินค้า", 1, 200.0)]
        feb_date = datetime.date(2026, 2, 1)
        result = pricing.calc(items, coupon="NEWYEAR", today=feb_date)
        assert result == 214.0

    def test_group_5_coupon_unknown_has_no_effect(self):
        items = [("สินค้า", 1, 200.0)]
        result = pricing.calc(items, coupon="NOT_EXIST")
        assert result == 214.0

    def test_group_6_negative_clamping_when_discount_exceeds_price(self):
        items = [("สินค้าชิ้นเล็ก", 1, 30.0)]
        result = pricing.calc(items, coupon="SAVE50")
        assert result == 0.0
        assert pricing.LOG == [(None, 0.0)]

    def test_group_7_stored_state_logged_each_call(self):
        assert len(pricing.LOG) == 0

        pricing.calc([("สินค้า 1", 1, 100.0)], member="User1")
        pricing.calc([("สินค้า 2", 1, 200.0)], member=None)

        assert pricing.LOG == [
            ("User1", 101.65),
            (None, 214.0),
        ]


class TestModularComponents:
    """ทดสอบฟังก์ชันย่อยที่แตกออกมาในการ Refactor แยกตามหน้าที่ (Unit Testing)."""

    def test_pricing_item_dataclass(self):
        item = pricing.PricingItem.from_tuple(("เมาส์", 2, 250.0))
        assert item.name == "เมาส์"
        assert item.quantity == 2
        assert item.unit_price == 250.0

    def test_calculate_item_subtotal_negative_qty(self):
        assert pricing.calculate_item_subtotal(-1, 100.0) == 0.0

    def test_apply_member_discount_with_custom_repo(self):
        custom_points = {}
        total = pricing.apply_member_discount(1000.0, "Charlie", points_repo=custom_points)
        assert total == 950.0
        assert custom_points["Charlie"] == 9

    def test_apply_tax_and_rounding(self):
        assert pricing.apply_tax_and_rounding(-50.0) == 0.0
        assert pricing.apply_tax_and_rounding(100.0, tax_rate=0.07) == 107.0
