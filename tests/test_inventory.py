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
