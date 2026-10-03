"""Unit tests for Inventory class.

Following TDD practices for Lab 05.
"""

import pytest
from inventory import Inventory


class TestLowStockItemsTDD:
    """TDD test cases for low_stock_items(threshold) method."""

    def test_case_1_all_items_above_threshold_returns_empty_list(self):
        """กรณีที่ 1: สินค้าทุกรายการมีจำนวนมากกว่า threshold -> คืน list ว่าง"""
        inv = Inventory()
        inv.add_item("สมุด", 20, 15.0)
        inv.add_item("ปากกา", 50, 10.0)
        inv.add_item("ดินสอ", 15, 5.0)

        result = inv.low_stock_items(threshold=10)
        assert result == []

    def test_case_2_item_quantity_equals_threshold_is_included(self):
        """กรณีที่ 2: มีสินค้าที่จำนวนเท่ากับ threshold พอดี -> ต้องถูกนับรวมด้วย"""
        inv = Inventory()
        inv.add_item("สมุด", 10, 15.0)
        inv.add_item("ปากกา", 25, 10.0)

        result = inv.low_stock_items(threshold=10)
        assert result == ["สมุด"]

    def test_case_3_multiple_matching_items_sorted_alphabetically(self):
        """กรณีที่ 3: มีสินค้าเข้าเกณฑ์หลายรายการ -> ผลลัพธ์เรียงตามชื่อ ไม่ใช่ตามลำดับที่เพิ่ม"""
        inv = Inventory()
        # เพิ่มตามลำดับ ยางลบ -> กรรไกร -> ไม้บรรทัด
        inv.add_item("ยางลบ", 3, 5.0)
        inv.add_item("กรรไกร", 2, 25.0)
        inv.add_item("ไม้บรรทัด", 4, 8.0)
        inv.add_item("กระดาษ A4", 100, 120.0)

        result = inv.low_stock_items(threshold=5)
        # ต้องเรียงตามตัวอักษร: กรรไกร, ยางลบ, ไม้บรรทัด
        assert result == ["กรรไกร", "ยางลบ", "ไม้บรรทัด"]

    def test_case_4_empty_inventory_returns_empty_list(self):
        """กรณีที่ 4: คลังว่าง -> คืน list ว่าง ไม่ใช่ error"""
        inv = Inventory()

        result = inv.low_stock_items(threshold=10)
        assert result == []

    def test_case_5_threshold_zero_returns_only_zero_quantity_items(self):
        """กรณีที่ 5: threshold เป็น 0 -> คืนเฉพาะสินค้าที่เหลือ 0"""
        inv = Inventory()
        inv.add_item("ปากกาหมด", 0, 10.0)
        inv.add_item("ดินสอหมด", 0, 5.0)
        inv.add_item("สมุดมีของ", 5, 20.0)

        result = inv.low_stock_items(threshold=0)
        assert result == ["ดินสอหมด", "ปากกาหมด"]

    def test_case_6_threshold_negative_returns_empty_list(self):
        """กรณีที่ 6: threshold ติดลบ -> คืน list ว่าง (เนื่องจากสต็อกสินค้า >= 0 เสมอ)"""
        inv = Inventory()
        inv.add_item("ยางลบ", 0, 5.0)
        inv.add_item("ดินสอ", 10, 5.0)

        result = inv.low_stock_items(threshold=-5)
        assert result == []


class TestSellAIShallow:
    """ชุด Test ที่ AI มักสร้างให้จาก Prompt ทั่วไป (มักครอบคลุมเฉพาะ Happy Path ปกติ)."""

    def test_sell_basic_happy_path(self):
        """กรณีทั่วไป: ขายสินค้าสำเร็จเมื่อสต็อกมีเพียงพอ."""
        inv = Inventory()
        inv.add_item("ปากกา", 10, 15.0)
        remaining = inv.sell("ปากกา", 3)
        assert remaining == 7


class TestSellEdgeCases:
    """ชุด Test เสริมความปลอดภัย (Edge Cases & Boundaries) ที่เราเขียนเพิ่มเพื่อปิดช่องโหว่."""

    def test_sell_exact_boundary_stock_to_zero(self):
        """กลุ่มค่าขอบ: ขายสินค้าเท่ากับจำนวนคงเหลือทั้งหมดพอดี (สต็อกต้องกลายเป็น 0)."""
        inv = Inventory()
        inv.add_item("สมุดบันทึก", 5, 50.0)

        remaining = inv.sell("สมุดบันทึก", 5)

        assert remaining == 0
        assert inv._items["สมุดบันทึก"].quantity == 0
        assert inv.get_total_value() == 0.0

    def test_sell_zero_quantity_raises_value_error(self):
        """กลุ่มค่าที่ไม่ควรรับ: ขายจำนวน 0 ชิ้น ต้อง raise ValueError พร้อมข้อความที่ถูกต้อง."""
        inv = Inventory()
        inv.add_item("ดินสอ 2B", 10, 8.0)

        with pytest.raises(ValueError) as exc_info:
            inv.sell("ดินสอ 2B", 0)

        assert "จำนวนที่ขายต้องมากกว่าศูนย์" in str(exc_info.value)
        # ตรวจสอบว่าสต็อกไม่ถูกแก้ไข
        assert inv._items["ดินสอ 2B"].quantity == 10

    def test_sell_negative_quantity_raises_value_error(self):
        """กลุ่มค่าที่ไม่ควรรับ: ขายจำนวนติดลบ ต้อง raise ValueError ป้องกันสต็อกเพิ่มผิดธรรมชาติ."""
        inv = Inventory()
        inv.add_item("ยางลบ", 15, 5.0)

        with pytest.raises(ValueError) as exc_info:
            inv.sell("ยางลบ", -3)

        assert "จำนวนที่ขายต้องมากกว่าศูนย์" in str(exc_info.value)
        assert inv._items["ยางลบ"].quantity == 15

    def test_sell_insufficient_stock_raises_value_error_with_details(self):
        """กลุ่มค่าที่ไม่ควรรับ: ขายเกินจำนวนคงเหลือ ต้อง raise ValueError พร้อมระบุสต็อกและจำนวนที่ขอ."""
        inv = Inventory()
        inv.add_item("แฟ้มเอกสาร", 4, 35.0)

        with pytest.raises(ValueError) as exc_info:
            inv.sell("แฟ้มเอกสาร", 10)

        error_msg = str(exc_info.value)
        assert "สินค้า 'แฟ้มเอกสาร' คงเหลือ 4 ชิ้น" in error_msg
        assert "ไม่เพียงพอสำหรับการขาย 10 ชิ้น" in error_msg
        assert inv._items["แฟ้มเอกสาร"].quantity == 4

    def test_sell_non_existent_item_raises_key_error(self):
        """กลุ่มเส้นทาง error: ขายสินค้าที่ไม่มีในคลัง ต้อง raise KeyError พร้อมชื่อสินค้าที่หาไม่พบ."""
        inv = Inventory()
        inv.add_item("ไม้บรรทัด", 5, 12.0)

        with pytest.raises(KeyError) as exc_info:
            inv.sell("กาวสองหน้า", 1)

        assert "ไม่พบสินค้า 'กาวสองหน้า' ในระบบ" in str(exc_info.value)

    def test_sell_total_inventory_value_updates_correctly(self):
        """กลุ่มความสอดคล้องของสถานะ: ขายสินค้าแล้วมูลค่ารวมของคลังสินค้า (Total Value) ต้องลดลงถูกต้อง."""
        inv = Inventory()
        inv.add_item("สินค้า A", 10, 100.0)  # 1000
        inv.add_item("สินค้า B", 5, 200.0)   # 1000
        initial_value = inv.get_total_value()
        assert initial_value == 2000.0

        inv.sell("สินค้า A", 4)  # ขาย 4 ชิ้น = 400
        assert inv.get_total_value() == 1600.0
