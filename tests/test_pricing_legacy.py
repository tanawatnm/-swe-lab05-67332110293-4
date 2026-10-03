"""Characterization tests for pricing_legacy.py.

บันทึกพฤติกรรมจริงของฟังก์ชัน calc เดิม เพื่อใช้เป็น Safety Net ก่อนการ Refactor.
"""

import datetime
import pytest
import pricing_legacy


@pytest.fixture(autouse=True)
def reset_global_state():
    """ล้างสถานะตัวแปรส่วนกลาง (member_points และ LOG) ทั้งก่อนและหลังการทดสอบแต่ละข้อ."""
    pricing_legacy.member_points.clear()
    pricing_legacy.LOG.clear()
    yield
    pricing_legacy.member_points.clear()
    pricing_legacy.LOG.clear()


class TestPricingCharacterization:
    """ชุด Characterization Tests ครอบคลุมทุกกลุ่มตามข้อกำหนดใน Lab 05 ขั้นที่ 7."""

    def test_group_1_normal_price_single_item(self):
        """กลุ่มราคาปกติ: สินค้าหนึ่งรายการ จำนวนน้อย ไม่ใช้สิทธิ์ใดๆ."""
        items = [("สมุด", 1, 100.0)]
        result = pricing_legacy.calc(items)
        # 100 + 7% vat = 107.0
        assert result == 107.0
        assert pricing_legacy.LOG == [(None, 107.0)]

    def test_group_1_normal_price_multiple_items(self):
        """กลุ่มราคาปกติ: สินค้าหลายรายการ จำนวนน้อย ไม่ใช้สิทธิ์ใดๆ."""
        items = [("ปากกา", 10, 20.0), ("ดินสอ", 5, 10.0)]
        result = pricing_legacy.calc(items)
        # (200 + 50) = 250 + 7% vat = 267.5
        assert result == 267.5
        assert pricing_legacy.LOG == [(None, 267.5)]

    def test_group_2_bulk_purchase_threshold_49_no_discount(self):
        """กลุ่มซื้อจำนวนมาก: ค่าขอบที่ 49 ชิ้น (ยังไม่เข้าเกณฑ์ลดราคา)."""
        items = [("ปากกา", 49, 10.0)]
        result = pricing_legacy.calc(items)
        # 490 + 7% vat = 524.3
        assert result == 524.3

    def test_group_2_bulk_purchase_threshold_50_discount_5_percent(self):
        """กลุ่มซื้อจำนวนมาก: ค่าขอบที่ 50 ชิ้นพอดี (ได้ลด 5%)."""
        items = [("ปากกา", 50, 10.0)]
        result = pricing_legacy.calc(items)
        # 500 * 0.95 = 475, 475 + 7% vat = 508.25
        assert result == 508.25

    def test_group_2_bulk_purchase_threshold_99_discount_5_percent(self):
        """กลุ่มซื้อจำนวนมาก: ค่าขอบที่ 99 ชิ้น (ยังอยู่ในขั้นลด 5%)."""
        items = [("ปากกา", 99, 10.0)]
        result = pricing_legacy.calc(items)
        # 990 * 0.95 = 940.5, 940.5 + 7% vat = 1006.335 -> round(2) = 1006.34
        assert result == 1006.34

    def test_group_2_bulk_purchase_threshold_100_discount_10_percent(self):
        """กลุ่มซื้อจำนวนมาก: ค่าขอบที่ 100 ชิ้นพอดี (ได้ลด 10%)."""
        items = [("ปากกา", 100, 10.0)]
        result = pricing_legacy.calc(items)
        # 1000 * 0.9 = 900, 900 + 7% vat = 963.0
        assert result == 963.0

    def test_group_3_zero_quantity_item(self):
        """กลุ่มจำนวนเป็นศูนย์: รายการสินค้าจำนวน 0 ชิ้น ข้ามการคิดราคา คืน 0.0."""
        items = [("สมุด", 0, 100.0)]
        result = pricing_legacy.calc(items)
        assert result == 0.0
        assert pricing_legacy.LOG == [(None, 0.0)]

    def test_group_3_negative_quantity_item(self):
        """กลุ่มจำนวนเป็นศูนย์/ติดลบ: รายการสินค้าจำนวนติดลบ ข้ามการคิดราคา คืน 0.0."""
        items = [("สมุด", -5, 100.0)]
        result = pricing_legacy.calc(items)
        assert result == 0.0

    def test_group_3_mixed_zero_and_valid_quantity(self):
        """กลุ่มจำนวนเป็นศูนย์: มีทั้งสินค้าจำนวน 0 และสินค้าที่มีจำนวนปกติ."""
        items = [("ของแถมหมด", 0, 200.0), ("สินค้าปกติ", 2, 50.0)]
        result = pricing_legacy.calc(items)
        # 100 + 7% vat = 107.0
        assert result == 107.0

    def test_group_4_member_discount_and_points_accumulation(self):
        """กลุ่มสมาชิก: สมาชิกลด 5% และสะสมแต้ม 1 แต้มต่อทุก 100 บาท."""
        items = [("สินค้า", 1, 1000.0)]
        result = pricing_legacy.calc(items, member="Somchai")
        # 1000 * 0.95 = 950.0, points = int(950 / 100) = 9
        # vat = 950 + (950 * 0.07) = 1016.5
        assert result == 1016.5
        assert pricing_legacy.member_points["Somchai"] == 9
        assert pricing_legacy.LOG == [("Somchai", 1016.5)]

    def test_group_4_member_points_cumulative_across_multiple_purchases(self):
        """กลุ่มสมาชิก: แต้มสะสมของสมาชิกต้องบวกทบต่อเนื่องข้ามการซื้อหลายครั้ง."""
        items = [("สินค้า", 1, 1000.0)]
        pricing_legacy.calc(items, member="Somchai")
        assert pricing_legacy.member_points["Somchai"] == 9

        pricing_legacy.calc(items, member="Somchai")
        assert pricing_legacy.member_points["Somchai"] == 18
        assert len(pricing_legacy.LOG) == 2

    def test_group_4_member_under_100_baht_gets_zero_points(self):
        """กลุ่มสมาชิก: ยอดเงินหลังหักส่วนลดไม่ถึง 100 บาท ได้รับ 0 แต้ม."""
        items = [("สินค้าเล็ก", 1, 100.0)]
        result = pricing_legacy.calc(items, member="Bob")
        # 100 * 0.95 = 95, int(95/100) = 0
        # 95 + 7% vat = 101.65
        assert result == 101.65
        assert pricing_legacy.member_points["Bob"] == 0

    def test_group_5_coupon_save50(self):
        """กลุ่มคูปอง: คูปอง SAVE50 หักลด 50 บาท."""
        items = [("สินค้า", 1, 200.0)]
        result = pricing_legacy.calc(items, coupon="SAVE50")
        # 200 - 50 = 150, 150 + 7% vat = 160.5
        assert result == 160.5

    def test_group_5_coupon_half(self):
        """กลุ่มคูปอง: คูปอง HALF ลด 50%."""
        items = [("สินค้า", 1, 200.0)]
        result = pricing_legacy.calc(items, coupon="HALF")
        # 200 * 0.5 = 100, 100 + 7% vat = 107.0
        assert result == 107.0

    def test_group_5_coupon_newyear_in_january(self):
        """กลุ่มคูปอง: คูปอง NEWYEAR ใช้ในเดือนมกราคม ลด 20%."""
        items = [("สินค้า", 1, 200.0)]
        jan_date = datetime.date(2026, 1, 15)
        result = pricing_legacy.calc(items, coupon="NEWYEAR", today=jan_date)
        # 200 * 0.8 = 160, 160 + 7% vat = 171.2
        assert result == 171.2

    def test_group_5_coupon_newyear_outside_january(self):
        """กลุ่มคูปอง: คูปอง NEWYEAR ใช้นอกเดือนมกราคม (กุมภาพันธ์) ไม่ได้รับส่วนลด."""
        items = [("สินค้า", 1, 200.0)]
        feb_date = datetime.date(2026, 2, 1)
        result = pricing_legacy.calc(items, coupon="NEWYEAR", today=feb_date)
        # ไม่ลด: 200 + 7% vat = 214.0
        assert result == 214.0

    def test_group_5_coupon_unknown_has_no_effect(self):
        """กลุ่มคูปอง: คูปองที่ไม่รู้จัก ไม่มีผลใดๆ คิดราคาปกติ."""
        items = [("สินค้า", 1, 200.0)]
        result = pricing_legacy.calc(items, coupon="NOT_EXIST")
        assert result == 214.0

    def test_group_6_negative_clamping_when_discount_exceeds_price(self):
        """กลุ่มยอดติดลบ: ส่วนลดคูปองมากกว่าราคาสินค้า ต้องปรับเป็น 0 ไม่คิดภาษีติดลบ."""
        items = [("สินค้าชิ้นเล็ก", 1, 30.0)]
        result = pricing_legacy.calc(items, coupon="SAVE50")
        # 30 - 50 = -20 -> clamp เป็น 0, 0 + vat = 0.0
        assert result == 0.0
        assert pricing_legacy.LOG == [(None, 0.0)]

    def test_group_7_stored_state_logged_each_call(self):
        """กลุ่มค่าที่ฟังก์ชันเก็บไว้: ยืนยันว่า LOG เก็บประวัติการเรียกทุกครั้งทั้ง member และยอดเงิน."""
        assert len(pricing_legacy.LOG) == 0

        pricing_legacy.calc([("สินค้า 1", 1, 100.0)], member="User1")
        pricing_legacy.calc([("สินค้า 2", 1, 200.0)], member=None)

        assert pricing_legacy.LOG == [
            ("User1", 101.65),
            (None, 214.0),
        ]
