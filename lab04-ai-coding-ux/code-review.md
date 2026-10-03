# เอกสาร Code Review: โมดูล `inventory_service.py` (Lab 04)

**ผู้จัดทำ Review:** นายธนวัฒน์ น้ำเง่า (Mr. Tanawat Namngao)  
**รหัสนักศึกษา:** 67332110293-4  
**เป้าหมาย:** ตรวจสอบโค้ดใน Pull Request (PR) ของโมดูล `inventory_service.py` ที่สร้างโดย AI Coding Assistant ซึ่งสามารถรันผ่านและโครงสร้างโค้ดดูเรียบร้อย แต่มีข้อบกพร่องและ Bug แฝงอยู่หลายจุดตามเกณฑ์ Code Review คุณภาพสูง

---

## 1. รายละเอียด Review Comments รายเมธอด (ครบ 4 องค์ประกอบ)

---

### จุดที่ 1: เมธอด `sell_batch()` (บรรทัดที่ 421 - 427)

```python
421:     def sell_batch(self, orders: dict[str, int]) -> dict[str, int]:
422:         """ขายหลายรายการพร้อมกัน คืน {ชื่อสินค้า: จำนวนคงเหลือ}"""
423:         result = {}
424:         for name, amount in orders.items():
425:             remaining = self._inv.sell(name, amount)
426:             result[name] = remaining
427:         return result
```

- **ตำแหน่ง:** เมธอด `sell_batch()`, บรรทัดที่ 424 - 426
- **ปัญหาคืออะไร (Why it is wrong):**  
  ขาดคุณสมบัติ **Atomicity (All-or-Nothing Transaction)** โค้ดวนลูปตัดสต็อกสินค้าทีละรายการผ่าน `self._inv.sell(name, amount)` ทันที หากรายการแรกตัดสต็อกสำเร็จแล้ว แต่รายการถัดไปล้มเหลว (เช่น สินค้าไม่พอ หรือไม่พบสินค้า) เมธอด `sell()` จะ raise `ValueError` หรือ `KeyError` ทำให้คำสั่งหยุดกลางคัน ส่งผลให้สินค้าในรายการแรกถูกหักสต็อกไปแล้วโดยไม่มีการกู้คืน (Rollback) ข้อมูลสต็อกในคลังจึงเพี้ยนและไม่ตรงกับความเป็นจริง
- **กรณีที่ทำให้พัง (Failing Scenario & Input):**  
  สมมติในคลังมี:
  - "สมุดบันทึก" เหลือ 10 เล่ม
  - "ปากกาลูกลื่น" เหลือ 2 ด้าม  
  ลูกค้าสั่งซื้อแบบ Batch: `orders = {"สมุดบันทึก": 5, "ปากกาลูกลื่น": 10}`  
  **พฤติกรรม:** ระบบจะตัดสต็อก "สมุดบันทึก" สำเร็จ เหลือ 5 เล่ม จากนั้นเมื่อถึง "ปากกาลูกลื่น" จะเกิด `ValueError` คำสั่งหยุดทำงานทันที คำสั่งซื้อของลูกค้าล้มเหลว แต่สต็อกของ "สมุดบันทึก" หายไป 5 เล่มฟรี ๆ ในระบบ
- **ข้อเสนอแนะในการแก้ไข (Proposed Solution):**  
  ใช้แนวทาง **Two-Phase Validation & Mutation** โดยวนลูปตรวจสอบความพร้อมของสินค้าทุกรายการก่อน (ว่ามีสินค้าและมีจำนวนพอหรือไม่) หากผ่านครบทุกรายการจึงค่อยวนลูปตัดสต็อกจริง หรือทำ Rollback กู้คืนสต็อกเมื่อเกิดข้อผิดพลาด

```python
def sell_batch(self, orders: dict[str, int]) -> dict[str, int]:
    # Phase 1: Validate all items first
    for name, amount in orders.items():
        if name not in self._inv._items:
            raise KeyError(f"ไม่พบสินค้า '{name}' ในระบบ")
        if amount <= 0:
            raise ValueError("จำนวนที่ขายต้องมากกว่าศูนย์")
        if self._inv._items[name].quantity < amount:
            raise ValueError(f"สินค้า '{name}' มีไม่พอสำหรับการขาย {amount} ชิ้น")
            
    # Phase 2: Deduct stock atomically
    result = {}
    for name, amount in orders.items():
        result[name] = self._inv.sell(name, amount)
    return result
```

---

### จุดที่ 2: เมธอด `reserve()` (บรรทัดที่ 430 - 436)

```python
430:     def reserve(self, name: str, amount: int) -> int:
431:         """จองสินค้าไว้ก่อนชำระเงิน คืนจำนวนที่ยังจองได้"""
432:         item = self._inv._items[name]
433:         already = self._reserved.get(name, 0)
434:         if amount <= item.quantity - already:
435:             self._reserved[name] = already + amount
436:         return item.quantity - self._reserved[name]
```

- **ตำแหน่ง:** เมธอด `reserve()`, บรรทัดที่ 432 - 436
- **ปัญหาคืออะไร (Why it is wrong):**
  1. **เงื่อนไขกับการคืนค่าไม่สอดคล้องกัน (Inconsistent State & Silent Failure):** หากสต็อกที่เหลือไม่พอให้จอง (`amount > item.quantity - already`) เงื่อนไขใน `if` จะเป็นเท็จและไม่เกิดการจอง แต่บรรทัดที่ 436 กลับพยายามเข้าถึง `self._reserved[name]`
     - ถ้าสินค้าชิ้นนี้ **ไม่เคยถูกจองมาก่อนเลย** จะเกิดข้อผิดพลาด `KeyError: name` ที่บรรทัด 436 ทันที
     - ถ้าเคยมีการจองมาก่อน จะคืนค่าตัวเลขสต็อกเดิมออกมา โดยที่ผู้เรียกเข้าใจว่าการจองสำเร็จ ทั้งที่ระบบไม่ได้จองเพิ่มให้เลย (Silent Failure)
  2. **ไม่มีการตรวจสอบความถูกต้องของอินพุต:** ไม่ได้ตรวจว่า `amount <= 0` หรือไม่ หากส่งค่าติดลบเข้าไปจะทำให้สต็อกที่ถูกจองลดลงโดยไม่ได้รับอนุญาต
- **กรณีที่ทำให้พัง (Failing Scenario & Input):**  
  - กรณีแครช: สินค้า "เมาส์ไร้สาย" มี 3 ชิ้น ยังไม่เคยมีใครจอง (`_reserved` ยังไม่มีคีย์นี้) ผู้ใช้เรียก `reserve("เมาส์ไร้สาย", 5)` เงื่อนไขใน if เป็นเท็จ โปรแกรมกระโดดไปบรรทัด 436 และแครชด้วย `KeyError: 'เมาส์ไร้สาย'`
  - กรณีข้อมูลเพี้ยนเงียบ: สินค้าเดิมถูกจองไว้แล้ว 2 ชิ้น ผู้ใช้พยายามจองเพิ่ม 10 ชิ้น ฟังก์ชันคืนค่าคงเหลือเดิมกลับมา ผู้เรียกเข้าใจว่าจองได้ 10 ชิ้น
- **ข้อเสนอแนะในการแก้ไข (Proposed Solution):**  
  ตรวจสอบความถูกต้องของสินค้าและจำนวน, ตรวจสอบว่ามีสต็อกเพียงพอหรือไม่ หากไม่พอให้ raise `ValueError` และคำนวณค่าคืนอย่างปลอดภัยผ่าน `self._reserved.get(name, 0)`

```python
def reserve(self, name: str, amount: int) -> int:
    if name not in self._inv._items:
        raise KeyError(f"ไม่พบสินค้า '{name}' ในระบบ")
    if amount <= 0:
        raise ValueError("จำนวนที่จองต้องมากกว่าศูนย์")
    item = self._inv._items[name]
    already = self._reserved.get(name, 0)
    available = item.quantity - already
    if amount > available:
        raise ValueError(f"สินค้า '{name}' เหลือให้จองเพียง {available} ชิ้น")
    self._reserved[name] = already + amount
    return item.quantity - self._reserved[name]
```

---

### จุดที่ 3: เมธอด `items_in_price_range()` (บรรทัดที่ 439 - 445)

```python
439:     def items_in_price_range(self, low: float, high: float) -> list:
440:         """คืนรายชื่อสินค้าที่ราคาอยู่ในช่วง [low, high]"""
441:         names = []
442:         for name, item in self._inv._items.items():
443:             if low < item.price < high:
444:                 names.append(name)
445:         return names
```

- **ตำแหน่ง:** เมธอด `items_in_price_range()`, บรรทัดที่ 443
- **ปัญหาคืออะไร (Why it is wrong):**  
  **ข้อผิดพลาดเรื่องขอบเขต (Off-by-boundary / Exclusive vs Inclusive):** ใน Docstring ระบุชัดเจนว่าต้องการค้นหาสินค้าที่ราคาอยู่ในช่วง `[low, high]` ซึ่งตามหลักคณิตศาสตร์ วงเล็บเหลี่ยมหมายถึง **ช่วงปิด (Closed Interval)** ที่ต้องรวมค่าขอบปลายทั้งสองข้าง (`low` และ `high`) ด้วย แต่โค้ดกลับใช้ตัวดำเนินการ `<` (Strict Inequality) ทำให้สินค้าที่มีราคาเท่ากับ `low` หรือเท่ากับ `high` พอดีจะตกหล่นไป ไม่ถูกนำมารวมในผลลัพธ์
- **กรณีที่ทำให้พัง (Failing Scenario & Input):**  
  ในคลังมีสินค้า "ปากกา" ราคา 50.00 บาท และ "สมุด" ราคา 100.00 บาท  
  ผู้ใช้เรียก `items_in_price_range(50.0, 100.0)`  
  **ผลลัพธ์ที่ได้:** คืนค่าเป็น `[]` (ลิสต์ว่าง) สินค้าทั้งสองชิ้นหายไปอย่างเงียบ ๆ ทั้งที่ควรได้ `["ปากกา", "สมุด"]`
- **ข้อเสนอแนะในการแก้ไข (Proposed Solution):**  
  เปลี่ยนตัวดำเนินการเปรียบเทียบเป็นช่วงปิด `<=`:

```python
def items_in_price_range(self, low: float, high: float) -> list:
    names = []
    for name, item in self._inv._items.items():
        if low <= item.price <= high:
            names.append(name)
    return names
```

---

### จุดที่ 4: เมธอด `low_stock_report()` (บรรทัดที่ 448 - 454)

```python
448:     def low_stock_report(self) -> list:
449:         """คืนรายชื่อสินค้าที่ stock ต่ำกว่าหรือเท่ากับเกณฑ์"""
450:         report = []
451:         for name, item in self._inv._items.items():
452:             if item.quantity < self.LOW_STOCK_THRESHOLD:
453:                 report.append(name)
454:         return report
```

- **ตำแหน่ง:** เมธอด `low_stock_report()`, บรรทัดที่ 452
- **ปัญหาคืออะไร (Why it is wrong):**  
  **เงื่อนไขไม่ตรงกับข้อกำหนด (Off-by-one / Boundary Logic):** Docstring ระบุว่า *"คืนรายชื่อสินค้าที่ stock ต่ำกว่าหรือเท่ากับเกณฑ์"* (`<=`) แต่บรรทัดที่ 452 โค้ดกลับเขียนเงื่อนไข `if item.quantity < self.LOW_STOCK_THRESHOLD:` ซึ่งหมายถึงน้อยกว่าเกณฑ์เท่านั้น สินค้าที่มีจำนวนเท่ากับ 5 ชิ้นพอดีจึงไม่ถูกรายงาน ทำให้ฝ่ายจัดซื้อไม่ได้รับการแจ้งเตือน
- **กรณีที่ทำให้พัง (Failing Scenario & Input):**  
  สินค้า "สายแลน CAT6" มีคงเหลือในคลัง 5 ชิ้น (ซึ่งตรงกับเกณฑ์ `LOW_STOCK_THRESHOLD = 5`)  
  เมื่อเรียก `low_stock_report()` สินค้านี้จะไม่ปรากฏในรายงาน ทำให้ไม่มีใครสั่งของมาเติมจนสินค้าหมดเกลี้ยงในที่สุด
- **ข้อเสนอแนะในการแก้ไข (Proposed Solution):**  
  เปลี่ยนเครื่องหมาย `<` เป็น `<=` ให้ตรงตามข้อกำหนด:

```python
def low_stock_report(self) -> list:
    report = []
    for name, item in self._inv._items.items():
        if item.quantity <= self.LOW_STOCK_THRESHOLD:
            report.append(name)
    return report
```

---

### จุดที่ 5: เมธอด `concurrent_restock()` (บรรทัดที่ 457 - 463)

```python
457:     def concurrent_restock(self, name: str, amount: int) -> int:
458:         """เติม stock โดยป้องกัน race condition"""
459:         current = self._inv._items[name].quantity
460:         with self._lock:
461:             self._inv._items[name].quantity = current + amount
462:         return self._inv._items[name].quantity
```

- **ตำแหน่ง:** เมธอด `concurrent_restock()`, บรรทัดที่ 459 - 461
- **ปัญหาคืออะไร (Why it is wrong):**  
  **อ่านค่านอกล็อกแล้วนำมาเขียนในล็อก (Race Condition: Lost Update):** บรรทัดที่ 459 มีการอ่านค่า `current` ออกมาก่อนที่จะเข้าบล็อก `with self._lock:` หากมี 2 เธรดทำงานพร้อมกัน เธรด A และเธรด B จะอ่านได้ค่า `current` เดิมค่าเดียวกัน จากนั้นเธรดแรกเข้าล็อกและอัปเดตค่าเสร็จ เมื่อเธรดสองเข้าล็อกต่อ จะนำค่า `current` เก่าที่จำไว้มาบวก ทำให้ยอดการเติมสต็อกของเธรดแรกถูกเขียนทับและสูญหายไปทันที (Lost Update Bug)
- **กรณีที่ทำให้พัง (Failing Scenario & Input):**  
  สินค้า "USB Hub" มีคงเหลือเริ่มต้น 10 ชิ้น  
  - เธรด 1 สั่งเติม 5 ชิ้น (อ่าน `current = 10` ที่บรรทัด 459)
  - เธรด 2 สั่งเติม 10 ชิ้น (อ่าน `current = 10` ที่บรรทัด 459 พร้อมกัน)
  - เธรด 1 เข้าล็อก: ตั้งค่าเป็น `10 + 5 = 15`
  - เธรด 2 เข้าล็อก: นำค่า `10 + 10 = 20` ไปเขียนทับ  
  **ผลลัพธ์:** สต็อกปลายทางกลายเป็น 20 ชิ้น ทั้งที่ความเป็นจริงควรจะเป็น `10 + 5 + 10 = 25` ชิ้น (ของหายไป 5 ชิ้นในระบบ)
- **ข้อเสนอแนะในการแก้ไข (Proposed Solution):**  
  ย้ายการอ่านค่าเข้าไปอยู่ในบล็อก `with self._lock:` หรือเรียกใช้เมธอด `restock()` ของ Inventory ภายใต้ Lock:

```python
def concurrent_restock(self, name: str, amount: int) -> int:
    if name not in self._inv._items:
        raise KeyError(f"ไม่พบสินค้า '{name}' ในระบบ")
    if amount <= 0:
        raise ValueError("จำนวนที่เติมต้องมากกว่าศูนย์")
    with self._lock:
        return self._inv.restock(name, amount)
```

---

### จุดที่ 6: เมธอด `average_unit_value()` (บรรทัดที่ 465 - 470)

```python
465:     def average_unit_value(self) -> float:
466:         """คืนมูลค่าเฉลี่ยต่อชิ้นของสินค้าทั้งคลัง"""
467:         total_value = self._inv.get_total_value()
468:         total_items = len(self._inv._items)
469:         return total_value / total_items
```

- **ตำแหน่ง:** เมธอด `average_unit_value()`, บรรทัดที่ 468 - 469
- **ปัญหาคืออะไร (Why it is wrong):**
  1. **สูตรคำนวณและตัวหารผิดความหมาย (Incorrect Metric / Wrong Denominator):** Docstring ระบุว่าต้องการหา *"มูลค่าเฉลี่ยต่อชิ้น"* (Average value per unit/piece) แต่โค้ดกลับหารด้วย `len(self._inv._items)` ซึ่งเป็น **จำนวนชนิดสินค้า (SKU count)** ไม่ใช่จำนวนชิ้นทั้งหมด ทำให้ค่าเฉลี่ยที่ได้ผิดความจริงอย่างสิ้นเชิง
  2. **ไม่ดักกรณีคลังสินค้าว่างเปล่า (Unhandled ZeroDivisionError):** หากในคลังยังไม่มีสินค้าอยู่เลย (`len(self._inv._items) == 0`) การหารด้วย `total_items` จะทำให้เกิด `ZeroDivisionError: division by zero` และโปรแกรมจะแครชทันที
- **กรณีที่ทำให้พัง (Failing Scenario & Input):**  
  - กรณีแครช: ระบบเพิ่งเริ่มต้น คลังยังว่างเปล่า (`_items = {}`) เมื่อเรียก `average_unit_value()` จะเกิด `ZeroDivisionError` ทันที
  - กรณีคำนวณผิด: ในคลังมี 2 ชนิดสินค้า คือ
    - ดินสอ 100 แท่ง ราคาแท่งละ 10 บาท (มูลค่า 1,000 บาท)
    - โต๊ะทำงาน 1 ตัว ราคาตัวละ 9,000 บาท (มูลค่า 9,000 บาท)  
    มูลค่ารวม = 10,000 บาท, จำนวนชิ้นรวม = 101 ชิ้น  
    มูลค่าเฉลี่ยต่อชิ้นที่แท้จริงคือ `10,000 / 101 = 99.01` บาท  
    แต่โค้ดคำนวณ: `10,000 / 2 = 5,000.00` บาท (คลาดเคลื่อนไป 50 เท่า!)
- **ข้อเสนอแนะในการแก้ไข (Proposed Solution):**  
  คำนวณจำนวนชิ้นรวมของสินค้าทั้งหมด (`sum(item.quantity)`) และตรวจสอบว่าหากไม่มีสินค้าหรือจำนวนชิ้นรวมเป็น 0 ให้คืนค่า `0.0`:

```python
def average_unit_value(self) -> float:
    total_quantity = sum(item.quantity for item in self._inv._items.values())
    if total_quantity == 0:
        return 0.0
    return self._inv.get_total_value() / total_quantity
```

---

### จุดที่ 7: ปัญหาการละเมิดหลักการ Encapsulation ข้ามชั้น (Design Smell)

- **ตำแหน่ง:** ตลอดทั้งคลาส `InventoryService` (บรรทัดที่ 432, 442, 451, 459, 461, 468)
- **ปัญหาคืออะไร (Why it is wrong):**  
  คลาส `InventoryService` เข้าถึงตัวแปรภายใน `self._inv._items` ซึ่งขึ้นต้นด้วยเครื่องหมายขีดล่าง `_` (Private/Internal attribute) ของคลาส `Inventory` โดยตรง หากในอนาคตคลาส `Inventory` มีการปรับปรุงโครงสร้างภายใน (เช่น เปลี่ยนไปใช้ Database หรือปรับโครงสร้าง Dictionary) จะส่งผลให้ `InventoryService` พังทันทีโดยไม่มีการแจ้งเตือน
- **ข้อเสนอแนะในการแก้ไข:**  
  เพิ่มเมธอดสาธารณะ (Public APIs) ในคลาส `Inventory` เช่น `get_item()`, `get_all_items()`, `has_item()` แล้วให้ `InventoryService` เรียกใช้ผ่านอินเทอร์เฟซดังกล่าว

---

## 2. ตารางสรุปการจัดหมวดหมู่และระดับความรุนแรงของ Bug

| # | เมธอด | หมวด (Category) | ระดับ (Severity) | สรุปปัญหา | กรณีที่ทำให้พัง |
| :-: | :--- | :--- | :--- | :--- | :--- |
| **1** | `sell_batch()` | `correctness` / `atomicity` | `high` | ขาดคุณสมบัติ Atomicity หากรายการหลังพัง รายการแรกจะถูกหักสต็อกค้างไว้ | รายการที่ 2 สต็อกไม่พอ แต่รายการที่ 1 ถูกหักสต็อกไปแล้ว ข้อมูลเพี้ยน |
| **2** | `reserve()` | `correctness` | `high` | เงื่อนไขกับค่าที่คืนไม่สัมพันธ์กัน เกิด KeyError เมื่อของไม่พอและไม่เคยจอง | จองสินค้าใหม่เกินยอดคงเหลือ โปรแกรมแครชด้วย `KeyError` ทันที |
| **3** | `items_in_price_range()` | `correctness` | `medium` | ข้อผิดพลาดช่วงขอบเขต ใช้ `<` แทนที่จะเป็นช่วงปิด `<=` ตามที่ระบุใน docstring | สินค้าที่ราคาเท่ากับ `low` หรือ `high` พอดีจะตกหล่น ไม่ปรากฏในลิสต์ |
| **4** | `low_stock_report()` | `correctness` | `medium` | ข้อผิดพลาดช่วงขอบเขต ใช้ `<` แทนที่จะเป็น `<=` ทำให้ไม่เตือนของที่เหลือ 5 ชิ้น | สินค้าที่เหลือคงเหลือ 5 ชิ้นพอดีไม่ปรากฏในรายงานสต็อกต่ำ |
| **5** | `concurrent_restock()` | `concurrency` | `high` | อ่านค่านอกล็อกแล้วนำมาเขียนในล็อก เกิด Race Condition: Lost Update | 2 เธรดอ่านค่า 10 พร้อมกัน แล้วเขียนทับ ยอดสต็อกหายไป 1 รายการ |
| **6** | `average_unit_value()` | `correctness` | `high` | ตัวหารผิดความหมาย (ใช้จน. SKU แทนจน.ชิ้น) และเกิด ZeroDivisionError เมื่อคลังว่าง | เรียกฟังก์ชันขณะคลังว่างแครชทันที, คำนวณค่าเฉลี่ยต่อชิ้นผิดมหาศาล |
| **7** | ทุกเมธอดในคลาส | `style` | `low` | เข้าถึงตัวแปร private `_items` ของคลาสอื่นข้ามชั้น ละเมิด Encapsulation | คลาส Inventory มีการเปลี่ยนโครงสร้างข้อมูลภายใน โค้ดจะพังทั้งหมด |

---

## 3. การเปรียบเทียบผลการ Review ระหว่างมนุษย์กับ AI Reviewer (Phase 2B ขั้นที่ 4)

จากการนำโค้ด `inventory_service.py` ไปให้ AI Reviewer ตรวจสอบ พบข้อสังเกตที่น่าสนใจดังนี้:
1. **สิ่งที่ AI Reviewer จับได้ดี:**
   - จุดที่ 6 (`average_unit_value` หารด้วยศูนย์) AI ตรวจจับได้อย่างรวดเร็วเพราะเป็น Pattern ทั่วไปของ Static Analysis
   - จุดที่ 3 และ 4 (เรื่อง off-by-boundary ใน `low < item.price < high`) AI สามารถจับคู่ข้อความใน Docstring กับเครื่องหมายในโค้ดได้ดี
2. **สิ่งที่ AI Reviewer มองข้ามหรือวิเคราะห์ผิด:**
   - **Concurrency Bug ใน `concurrent_restock()`:** AI มองเห็นว่ามีบล็อก `with self._lock:` จึงสรุปว่า "โค้ดมีการป้องกัน Race Condition เรียบร้อยแล้ว" โดยไม่ได้สังเกตว่าบรรทัด `current = ...` ที่อ่านค่านั้นอยู่นอกบล็อกล็อก ซึ่งเป็นข้อผิดพลาดที่ร้ายแรงมาก
   - **Atomicity ใน `sell_batch()`:** AI มักไม่ทักท้วงเรื่อง All-or-Nothing เว้นแต่จะสั่งให้อ่านในบริบทของ Transaction อย่างเจาะจง
3. **สรุปแนวทางการแบ่งงานระหว่างคนกับ AI:**
   - ใช้ AI ช่วยกวาดหา Linting, Syntax, Null-check, Zero-division และ Style เบื้องต้น
   - วิศวกรซอฟต์แวร์ต้องเป็นผู้ตรวจสอบด้าน **Business Invariants, Transaction Atomicity, Concurrency Synchronization และ Architectural Boundary** เพื่อความปลอดภัยสูงสุดของระบบ

---

## 4. คำตอบแบบฝึกหัดส่งท้าย (Post-Lab Exercise Analysis)

### ข้อ 1: วิเคราะห์ Bug ที่ทำงานได้ปกติในกรณีทั่วไป แต่พังเฉพาะใน Edge Case หรือ Concurrency (ยกตัวอย่าง 2 ข้อ)
1. **`concurrent_restock()` (Concurrency / Lost Update):**
   - *ทำไมรันปกติได้:* หากรันใน Single Thread แบบธรรมดา ฟังก์ชันจะทำงานและคืนค่าสต็อกที่ถูกต้องเสมอ ทำให้ Unit Test ทั่วไปที่ไม่ได้จำลองมัลติเธรดรันผ่าน 100%
   - *ทำไมพัง:* พังเฉพาะเมื่อมีหลาย Thread เรียกพร้อมกันในจังหวะพอดี (Microsecond Interleaving) โดย Thread 1 และ Thread 2 อ่านค่า `current` ตัวเดิมก่อนเข้าล็อก ทำให้เกิด Lost Update ยอดสต็อกหายไปเงียบ ๆ
2. **`items_in_price_range()` และ `low_stock_report()` (Edge Case / Off-by-boundary):**
   - *ทำไมรันปกติได้:* ถ้าทดสอบด้วยราคากลาง ๆ เช่น ช่วง [50, 100] แต่สินค้ามีราคา 60, 80 โค้ดจะคืนค่าถูกต้องทุกครั้ง
   - *ทำไมพัง:* พังเฉพาะค่าที่ตรงกับขอบพอดี เช่น สินค้าราคา 50 หรือ 100 พอดี หรือสต็อกเหลือ 5 ชิ้นพอดี โค้ดจะคัดทิ้งทันทีเพราะใช้เครื่องหมาย `<` ซึ่ง Unit Test ทั่วไปมักไม่ได้เลือก Boundary Values มาทดสอบอย่างครอบคลุม

### ข้อ 2: ออกแบบ Test Case สำหรับตรวจจับ Concurrency Bug ใน `concurrent_restock()`
```python
import threading
import pytest
from inventory import Inventory
from inventory_service import InventoryService


def test_concurrent_restock_race_condition():
    """
    จำลอง 10 Threads เติมสต็อกสินค้าเดียวกันพร้อมกัน คนละ 5 ชิ้น
    ยอดเริ่มต้น = 0 ชิ้น -> ยอดสุดท้ายที่ถูกต้องต้องเป็น 50 ชิ้นพอดี
    """
    inv = Inventory()
    inv.add_item("Mouse", 0, 150.0)
    service = InventoryService(inv)
    
    threads = []
    num_threads = 10
    restock_per_thread = 5

    # Barrier ช่วยบังคับให้ทุกเธรดเริ่มทำงานพร้อมกันในเสี้ยววินาทีเดียวกัน
    barrier = threading.Barrier(num_threads)

    def worker():
        barrier.wait()  # รอให้ทุกเธรดพร้อมแล้วปล่อยพร้อมกันเพื่อบีบให้เกิด Race Condition
        service.concurrent_restock("Mouse", restock_per_thread)

    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # หากมี Lost Update ยอดจะน้อยกว่า 50 (เช่น ได้ 10, 15 หรือ 20)
    assert inv._items["Mouse"].quantity == 50, (
        f"เกิด Lost Update! คาดหวัง 50 แต่ได้ {inv._items['Mouse'].quantity}"
    )
```

### ข้อ 3: การประเมิน AI และการแบ่งงานระหว่างคนกับ AI ให้ปลอดภัยที่สุด
- **จุดเด่นของ AI:** รวดเร็วมากในการสแกนโครงสร้างไวยากรณ์ (Syntax), รูปแบบการตั้งชื่อ (Naming conventions), การตรวจจับข้อผิดพลาดคลาสสิกที่เห็นชัดเจน เช่น Null/None Check และการหารด้วยศูนย์ (Zero Division)
- **ข้อจำกัดของ AI:** มักเชื่อมั่นว่าตนเองเขียนโค้ดถูกต้อง มองข้ามความสัมพันธ์เชิงบริบทของเวลา (Time/Concurrency), การรับประกันความคงสภาพของธุรกรรม (Transaction Atomicity) และความเข้ากันได้ของโดเมนระบบ
- **แนวทางแบ่งงาน:** กำหนดให้ AI ทำหน้าที่เป็น **First-pass Reviewer** กวาดตรวจ Syntax, Style และ Clean Code เบื้องต้น จากนั้นวิศวกรซอฟต์แวร์ทำหน้าที่เป็น **Final Decision Maker** ตรวจสอบ Logic Invariants, Business Rules, Concurrency Safety และ Security Permissions ก่อนอนุมัติ Merge ทุกครั้ง

### ข้อ 4: การสะท้อนคิด (Reflection: 100 - 150 คำ)
ในยุคที่ AI สามารถสร้างโค้ดทั้งโมดูลเสร็จสิ้นภายในไม่กี่วินาที ทักษะที่สำคัญและมีมูลค่าสูงสุดของวิศวกรซอฟต์แวร์ไม่ใช่ความเร็วในการพิมพ์โค้ดอีกต่อไป แต่เป็น **"ความละเอียดรอบคอบในการตรวจสอบและประเมินคุณภาพของโค้ด (Critical Evaluation & Code Review)"** ดังที่เห็นได้อย่างชัดเจนใน Lab 4 นี้ โค้ด `inventory_service.py` และ `discount.py` ที่ AI สร้างขึ้นนั้นสามารถรันผ่าน คอมไพล์ได้ และดูสะอาดเรียบร้อย แต่กลับแฝงข้อผิดพลาดร้ายแรงทั้งการตัดสต็อกไม่สำเร็จครึ่งทาง (Atomicity), การหารด้วยศูนย์, การตัดข้อมูลตกหล่น (Off-by-one), และ Race Condition ที่ทำให้ข้อมูลในระบบสูญหาย หากวิศวกรขาดความเข้าใจอย่างลึกซึ้งและนำโค้ดไปใช้งานโดยไม่ตรวจสอบ จะสร้างความเสียหายมหาศาลต่อระบบจริง ดังนั้นบทบาทของมนุษย์ในฐานะผู้กำกับดูแลและตรวจสอบจึงเป็นด่านสุดท้ายที่ขาดไม่ได้

