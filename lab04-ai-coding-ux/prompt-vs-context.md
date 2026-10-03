# การเปรียบเทียบ Prompt Engineering กับ Context Engineering (Lab 04)

เอกสารนี้แสดงการทดลองสั่งงาน AI Coding Assistant เพื่อพัฒนาฟังก์ชัน **การขายสินค้าหลายรายการพร้อมกัน (Batch / Multi-item Sell)** จำนวน 2 รอบ เพื่อเปรียบเทียบความแตกต่างระหว่างการสั่งงานด้วย **Prompt สั้น ๆ (Prompt Engineering)** กับการสั่งงานโดยมี **Context ครบถ้วน (Context Engineering)** พร้อมวิเคราะห์สาเหตุและสรุปผลเชิงวิศวกรรมซอฟต์แวร์

---

## 1. การทดลองรอบที่ 1: สั่งสั้น ๆ โดยไม่มี Context (Prompt-Only)

### คำสั่ง (Prompt):
```text
เขียนฟังก์ชันสำหรับขายสินค้าหลายรายการพร้อมกันในระบบ inventory ด้วยภาษา Python
```

### ผลลัพธ์ที่ AI สร้างขึ้น (Round 1 Output):
```python
def sell_multiple_items(inventory_db, items_to_sell):
    """
    ฟังก์ชันสำหรับขายสินค้าหลายชิ้นพร้อมกัน
    items_to_sell: dict เช่น {'item_a': 2, 'item_b': 5}
    """
    receipt = {}
    for item_name, quantity in items_to_sell.items():
        if item_name in inventory_db:
            if inventory_db[item_name]['stock'] >= quantity:
                inventory_db[item_name]['stock'] -= quantity
                receipt[item_name] = "Sold"
            else:
                return f"Error: {item_name} has insufficient stock"
        else:
            return f"Error: {item_name} not found"
    return receipt
```

### ข้อวิเคราะห์ข้อบกพร่องของผลลัพธ์รอบที่ 1:
1. **ไม่เข้ากับโครงสร้างระบบเดิม (Interface Incompatibility):** AI คาดเดาว่าระบบเก็บข้อมูลเป็น `dict of dicts` (`inventory_db[item_name]['stock']`) ทั้งที่ในระบบจริงเรามีคลาส `Inventory` และ `InventoryItem` ซึ่งเก็บข้อมูลผ่าน `self._items` ทำให้ไม่สามารถนำโค้ดนี้ไปใช้งานได้จริง
2. **เกิดข้อผิดพลาดด้านความคงสภาพของข้อมูล (Atomicity Failure):** หากรายการแรกขายสำเร็จ (ตัดสต็อกไปแล้ว) แต่รายการที่สองสต็อกไม่พอ ฟังก์ชันจะคืนค่า Error ทันทีโดย **ไม่มีการคืนสต็อก (Rollback) ของรายการแรก** ทำให้ข้อมูลสต็อกในคลังเพี้ยนทันที
3. **การจัดการ Exception ที่ไม่ได้มาตรฐาน:** ส่งคืนสตริงข้อความ Error (`return "Error: ..."`) แทนที่จะเป็น Exception ชนิดที่กำหนดไว้ตามมาตรฐานระบบ (`KeyError`, `ValueError`)
4. **ไม่มี Type Annotations:** ขาดการระบุประเภทตัวแปรที่ชัดเจน

---

## 2. การทดลองรอบที่ 2: สั่งงานพร้อมแนบ Context ครบถ้วน (Context Engineering)

### คำสั่งพร้อม Context (Prompt with Full Context):
```text
ปรับปรุงระบบ Inventory ด้านล่างให้รองรับการขายสินค้าหลายรายการพร้อมกัน (Batch Sell)

[บริบทโค้ดเดิม inventory.py]
class InventoryItem:
    def __init__(self, name: str, quantity: int, price: float):
        if not name or not name.strip():
            raise ValueError("ชื่อสินค้าต้องไม่ว่างเปล่า")
        if quantity < 0:
            raise ValueError("จำนวนสินค้าต้องไม่ติดลบ")
        if price <= 0:
            raise ValueError("ราคาต้องมากกว่าศูนย์")
        self.name = name.strip()
        self.quantity = quantity
        self.price = price

class Inventory:
    def __init__(self):
        self._items: dict[str, InventoryItem] = {}
    ... (แนบโค้ดคลาส Inventory ฉบับเต็ม)

[ข้อกำหนดของฟังก์ชัน (Functional & Non-Functional Requirements)]
- เพิ่มเมธอด sell_many(self, orders: dict[str, int]) -> dict[str, int] ลงในคลาส Inventory
- คืนค่าผลลัพธ์เป็น dict ของ {ชื่อสินค้า: จำนวนคงเหลือล่าสุด}
- คุณสมบัติ Atomicity (All-or-Nothing): ถ้ามีสินค้าชิ้นใดชิ้นหนึ่งสต็อกไม่เพียงพอ หรือไม่พบสินค้าในระบบ ต้องยกเลิกคำสั่งซื้อทั้งหมด และต้องไม่มีการหักสต็อกของสินค้าชิ้นอื่นเลย (Rollback)
- มาตรฐาน Exception:
  * ถ้าไม่พบสินค้าในคลัง ให้ raise KeyError(f"ไม่พบสินค้า '{name}' ในระบบ")
  * ถ้าจำนวนที่สั่งซื้อ <= 0 ให้ raise ValueError("จำนวนที่ขายต้องมากกว่าศูนย์")
  * ถ้าสินค้าคงเหลือไม่พอ ให้ raise ValueError(f"สินค้า '{name}' คงเหลือ {item.quantity} ชิ้น ไม่เพียงพอสำหรับการขาย {amount} ชิ้น")
- ข้อจำกัด: ห้ามติดตั้งหรือ import library ภายนอกเพิ่มเติม

[Test Cases ที่โค้ดต้องผ่าน]
1. ขายสินค้า 2 ชนิดสำเร็จ: ทั้งสองรายการถูกหักสต็อกถูกต้อง และคืน dict ยอดคงเหลือ
2. สินค้าที่ 2 ไม่พอ: ต้อง raise ValueError และสต็อกของสินค้าที่ 1 ต้องไม่ถูกลดลง (ต้องคงเดิม 100%)
3. สินค้าที่ 2 ไม่มีในระบบ: ต้อง raise KeyError และสินค้าที่ 1 ต้องไม่ถูกหักสต็อก
```

### ผลลัพธ์ที่ AI สร้างขึ้น (Round 2 Output):
```python
def sell_many(self, orders: dict[str, int]) -> dict[str, int]:
    """
    ขายหลายรายการพร้อมกันแบบ Atomic (All-or-Nothing)
    คืน dict ของ {ชื่อสินค้า: จำนวนคงเหลือล่าสุด}
    หากมีรายการใดล้มเหลว จะไม่มีการตัดสต็อกสินค้าใดๆ ทั้งสิ้น
    """
    if not orders:
        return {}

    # ขั้นตอนที่ 1: Validation เช็กความถูกต้องทั้งหมดล่วงหน้าก่อนทำการตัดสต็อกจริง
    for name, amount in orders.items():
        if name not in self._items:
            raise KeyError(f"ไม่พบสินค้า '{name}' ในระบบ")
        if amount <= 0:
            raise ValueError("จำนวนที่ขายต้องมากกว่าศูนย์")
        item = self._items[name]
        if item.quantity < amount:
            raise ValueError(
                f"สินค้า '{name}' คงเหลือ {item.quantity} ชิ้น "
                f"ไม่เพียงพอสำหรับการขาย {amount} ชิ้น"
            )

    # ขั้นตอนที่ 2: Mutation ดำเนินการตัดสต็อกจริงเมื่อทุกรายการผ่านการตรวจสอบครบถ้วน
    result: dict[str, int] = {}
    for name, amount in orders.items():
        self._items[name].quantity -= amount
        result[name] = self._items[name].quantity

    return result
```

### ข้อวิเคราะห์ผลลัพธ์รอบที่ 2:
1. **สอดคล้องกับสถาปัตยกรรมระบบ 100%:** เมธอดผูกเข้ากับคลาส `Inventory` เดิม ใช้ `self._items` และเข้าถึงอ็อบเจกต์ `InventoryItem` ได้อย่างถูกต้องสมบูรณ์
2. **รักษาคุณสมบัติ Atomicity ได้สมบูรณ์แบบ:** ใช้วิธี **Two-Phase Validation & Mutation** (ตรวจสอบรายการทั้งหมดในลูปแรกให้ผ่านก่อน หากไม่ผ่านจะ raise exception ทันทีโดยที่ยังไม่มีการแก้ไขค่าใน `self._items` เลย) ทำให้ไม่เกิดปัญหาข้อมูลเน่าเสีย
3. **ตรงตามข้อกำหนด Exception และ Type Hints:** ใช้ `KeyError` และ `ValueError` พร้อมข้อความที่ตรงกับเมธอด `sell()` เดิมทุกประการ

---

## 3. ตารางสรุปเปรียบเทียบผลลัพธ์

| มิติการเปรียบเทียบ | รอบที่ 1: Prompt สั้น ๆ (No Context) | รอบที่ 2: Prompt + Context ครบถ้วน |
| :--- | :--- | :--- |
| **ความเข้ากันได้กับโค้ดเดิม** | ไม่เข้ากันเลย คาดเดาโครงสร้างข้อมูลขึ้นมาเอง | เข้ากันได้อย่างสมบูรณ์ ผสานเข้ากับคลาส `Inventory` ได้ทันที |
| **ความถูกต้องของตรรกะ (Atomicity)** | ล้มเหลว ตัดสต็อกบางส่วนแล้วค้าง (Data Inconsistency) | ถูกต้อง 100% ตรวจสอบครบทุกรายการก่อนตัดสต็อกจริง |
| **การจัดการ Exception** | คืนค่าเป็น String ข้อความ Error ทั่วไป | Raise `KeyError` และ `ValueError` ตามมาตรฐานเดิม |
| **Type Annotations & Docstring** | ไม่มี Type Annotations และ Docstring ไม่ชัดเจน | มี Type Annotations และ Docstring อธิบายการทำงานละเอียด |
| **โอกาสเกิด AI Hallucination** | สูงมาก (แต่งชื่อฟิลด์และตัวแปรขึ้นมาเอง) | ต่ำมาก (AI ยึดตามบริบทและข้อจำกัดที่ส่งให้) |

---

## 4. บทสรุป: อะไรทำให้ผลลัพธ์ต่างกัน?

ความแตกต่างอย่างมหาศาลของผลลัพธ์ทั้งสองรอบชี้ให้เห็นว่า:
- **Prompt Engineering** เป็นเพียงการกำหนด **"คำสั่งและเป้าหมาย"** (What to do) หากมีเพียงคำสั่ง AI จะดึงความรู้ทั่วไปจากโมเดลมาคาดเดา ซึ่งมักไม่ตรงกับระบบที่มีอยู่จริง
- **Context Engineering** คือการจัดเตรียม **"สภาพแวดล้อม กฎเกณฑ์ ข้อจำกัด และอินเทอร์เฟซ"** (How and within what boundaries to do) การแนบโค้ดเดิม การระบุ Exception ที่ต้องใช้ และการแนบ Test Cases ทำหน้าที่เสมือน Guardrails ที่จำกัดขอบเขตการสร้างคำตอบของ AI ให้ถูกต้อง แม่นยำ และปลอดภัยต่อระบบจริงในระดับ Production
