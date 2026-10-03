"""โมดูลคำนวณราคาและส่วนลดของระบบ Inventory (ฉบับ Refactored).

โครงสร้างใหม่:
- แยกหน้าที่การทำงานตามหลัก Single Responsibility Principle (SRP)
- กำหนดค่าคงที่ชัดเจน ปราศจาก Magic Numbers
- รองรับ Type Hints และ Documentation ครบถ้วน
- รักษาพฤติกรรมเดิม (Backward Compatibility) ให้เหมือน pricing_legacy.py ทุกประการ
"""

from __future__ import annotations

import datetime
from collections.abc import Sequence
from dataclasses import dataclass

# --- ค่าคงที่ระบบ (System Constants) ---
DEFAULT_TAX_RATE = 0.07

BULK_TIER_2_MIN_QTY = 100
BULK_TIER_2_DISCOUNT_RATE = 0.10  # ลด 10% (คูณ 0.9)

BULK_TIER_1_MIN_QTY = 50
BULK_TIER_1_DISCOUNT_RATE = 0.05  # ลด 5% (คูณ 0.95)

MEMBER_DISCOUNT_RATE = 0.05  # ลด 5% (คูณ 0.95)
MEMBER_POINTS_THRESHOLD = 100  # 1 แต้มต่อทุก 100 บาท

COUPON_SAVE50_DISCOUNT = 50.0
COUPON_HALF_MULTIPLIER = 0.5
COUPON_NEWYEAR_MULTIPLIER = 0.8
COUPON_NEWYEAR_VALID_MONTH = 1  # เฉพาะเดือนมกราคม

# สถานะระดับโมดูลเพื่อความเข้ากันได้ย้อนหลัง (Backward Compatibility)
member_points: dict[str, int] = {}
LOG: list[tuple[str | None, float]] = []


@dataclass(frozen=True)
class PricingItem:
    """โครงสร้างข้อมูลสินค้าสำหรับการคิดราคา."""

    name: str
    quantity: int
    unit_price: float

    @classmethod
    def from_tuple(cls, data: tuple[str, int, float] | Sequence) -> PricingItem:
        """แปลง tuple (ชื่อ, จำนวน, ราคาต่อหน่วย) เป็น PricingItem."""
        return cls(name=str(data[0]), quantity=int(data[1]), unit_price=float(data[2]))


def calculate_item_subtotal(quantity: int, unit_price: float) -> float:
    """คำนวณราคาย่อยของสินค้าแต่ละรายการ พร้อมส่วนลดตามขั้นบันไดจำนวนซื้อ (Bulk Discount)."""
    if quantity <= 0:
        return 0.0

    raw_subtotal = quantity * unit_price

    if quantity >= BULK_TIER_2_MIN_QTY:
        return raw_subtotal * (1.0 - BULK_TIER_2_DISCOUNT_RATE)
    if quantity >= BULK_TIER_1_MIN_QTY:
        return raw_subtotal * (1.0 - BULK_TIER_1_DISCOUNT_RATE)

    return raw_subtotal


def calculate_items_total(items: Sequence[tuple[str, int, float] | PricingItem]) -> float:
    """คำนวณราคารวมของสินค้าทั้งหมดในตะกร้าหลังหักส่วนลดการซื้อจำนวนมาก."""
    total = 0.0
    for raw_item in items:
        if isinstance(raw_item, PricingItem):
            item = raw_item
        else:
            item = PricingItem.from_tuple(raw_item)

        total += calculate_item_subtotal(item.quantity, item.unit_price)
    return total


def apply_member_discount(
    total: float,
    member: str | None,
    points_repo: dict[str, int] | None = None,
) -> float:
    """คำนวณส่วนลดสมาชิก 5% และสะสมแต้ม 1 แต้มต่อทุก 100 บาท."""
    if member is None:
        return total

    if points_repo is None:
        points_repo = member_points

    if member not in points_repo:
        points_repo[member] = 0

    discounted_total = total * (1.0 - MEMBER_DISCOUNT_RATE)
    earned_points = int(discounted_total / MEMBER_POINTS_THRESHOLD)
    points_repo[member] += earned_points

    return discounted_total


def apply_coupon(
    total: float,
    coupon: str | None,
    target_date: datetime.date | None = None,
) -> float:
    """คำนวณส่วนลดจากรหัสคูปองตามเงื่อนไขทางธุรกิจ."""
    if coupon is None:
        return total

    if coupon == "SAVE50":
        return total - COUPON_SAVE50_DISCOUNT
    if coupon == "HALF":
        return total * COUPON_HALF_MULTIPLIER
    if coupon == "NEWYEAR":
        current_date = target_date if target_date is not None else datetime.date.today()
        if current_date.month == COUPON_NEWYEAR_VALID_MONTH:
            return total * COUPON_NEWYEAR_MULTIPLIER

    return total


def apply_tax_and_rounding(total: float, tax_rate: float = DEFAULT_TAX_RATE) -> float:
    """ปรับยอดไม่ให้ติดลบ บวกภาษีมูลค่าเพิ่ม และปัดเศษทศนิยม 2 ตำแหน่ง."""
    clamped_total = max(0.0, total)
    total_with_tax = clamped_total + (clamped_total * tax_rate)
    return round(total_with_tax, 2)


def calc(
    items: Sequence[tuple[str, int, float]],
    member: str | None = None,
    coupon: str | None = None,
    today: datetime.date | None = None,
) -> float:
    """ฟังก์ชันหลักสำหรับคำนวณราคาและส่วนลด (คง Interface เดิมทุกประการ).

    Parameters:
        items: list ของ tuple (ชื่อสินค้า, จำนวน, ราคาต่อหน่วย)
        member: ชื่อสมาชิก (ถ้ามี)
        coupon: รหัสคูปอง (ถ้ามี)
        today: วันที่สำหรับการประเมินเงื่อนไขเวลาของคูปอง (ถ้าไม่ระบุใช้วันนี้)

    Returns:
        ยอดเงินรวมสุทธิหลังหักส่วนลดและรวมภาษีมูลค่าเพิ่ม (ปัดเศษ 2 ตำแหน่ง)
    """
    total = calculate_items_total(items)
    total = apply_member_discount(total, member, points_repo=member_points)
    total = apply_coupon(total, coupon, target_date=today)
    final_total = apply_tax_and_rounding(total, tax_rate=DEFAULT_TAX_RATE)

    LOG.append((member, final_total))
    return final_total
