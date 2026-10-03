# บันทึกการ Debug แบบมีหลักฐาน (Evidence-Based Debugging Log) - Lab 04

**ผู้จัดทำ:** นายธนวัฒน์ น้ำเง่า (Mr. Tanawat Namngao)  
**รหัสนักศึกษา:** 67332110293-4  
**ไฟล์เป้าหมาย:** `discount.py` และ `tests/test_discount.py`  
**แนวทางการทำงาน:** ปฏิบัติตามกระบวนการ 5 ขั้นตอน (Reproduce -> Traceback -> Hypothesis -> Confirmation -> Fix & Re-run) ห้ามเดาสุ่มหรือแก้โค้ดโดยไม่ยืนยันสมมติฐาน

---

## สรุปภาพรวมผลการรัน Test ครั้งแรก (Initial Test Run)

คำสั่งที่ใช้รัน:
```bash
python -m pytest tests/test_discount.py -v
```

ผลลัพธ์: **4 Failed, 2 Passed**
- `test_apply_discount_basic` -> **FAILED** (AssertionError: 99.9 != 90.0)
- `test_apply_discount_zero` -> **PASSED** (ผ่านโดยบังเอิญจากกับดักที่วางไว้)
- `test_bulk_total` -> **FAILED** (AssertionError: 299.9 != 270.0)
- `test_average_price` -> **PASSED**
- `test_average_price_empty` -> **FAILED** (ZeroDivisionError: division by zero)
- `test_cheapest_n` -> **FAILED** (AssertionError: [20.0] != [10.0, 20.0])

---

## บันทึกการ Debug รายจุดอย่างละเอียด (5 ขั้นตอน)

---

### จุดที่ 1: `test_apply_discount_basic`

#### 1. Reproduce
- **คำสั่งที่รัน:** `python -m pytest tests/test_discount.py -k test_apply_discount_basic -v`
- **ผลลัพธ์ Failure:**
  ```text
  E   AssertionError: assert 99.9 == 90.0
  E    +  where 99.9 = apply_discount(100.0, 10)
  ```

#### 2. Traceback
- **บรรทัดที่เกิดข้อผิดพลาด:** `tests/test_discount.py`, บรรทัดที่ 8
  ```python
  def test_apply_discount_basic():
      # ลด 10% จาก 100 บาท ควรเหลือ 90 บาท
  >   assert apply_discount(100.0, 10) == 90.0
  ```
- **ตำแหน่งโค้ด:** `discount.py`, บรรทัดที่ 5
  ```python
  def apply_discount(price: float, percent: float) -> float:
      return price - percent / 100
  ```

#### 3. สมมติฐาน (Hypothesis)
ฟังก์ชัน `apply_discount` มีสูตรคำนวณทางคณิตศาสตร์ผิดพลาด โดยนำราคาตั้งต้น `price` มาลบออกด้วยค่าสัดส่วนเปอร์เซ็นต์โดยตรง (`percent / 100`) โดยลืมนำสัดส่วนนั้นไปคูณกับราคาต้นทาง `price` ก่อน ทำให้การคำนวณกลายเป็น `100.0 - (10 / 100) = 100.0 - 0.1 = 99.9` แทนที่จะเป็น `100.0 - (100.0 * 10 / 100) = 90.0`

#### 4. การยืนยัน (Confirmation)
ทดลองพิมพ์ค่าคำนวณผ่าน Python REPL:
```python
price = 100.0
percent = 10.0
print("โค้ดเดิม:", price - percent / 100)           # แสดงผล: 99.9
print("ตามสมมติฐาน:", price * (1 - percent / 100))   # แสดงผล: 90.0
```
ค่าที่ได้จากการพิสูจน์ตรงกับผลลัพธ์ที่ Test คาดหวังทุกประการ ยืนยันว่าสมมติฐานถูกต้อง

#### 5. Root Cause และการแก้ (Fix)
- **Root Cause:** ใช้ตัวดำเนินการผิดความหมายและตกหล่นตัวแปร `price` ในเทอมของการลดราคา (Mathematical Formulation Error)
- **การแก้ไข:** แก้ไขบรรทัดที่ 5 ของ `discount.py` เป็น:
  ```python
  def apply_discount(price: float, percent: float) -> float:
      """ลดราคาตาม percent (0-100) คืนราคาหลังลด"""
      return price * (1 - percent / 100)
  ```

---

### จุดที่ 2: `test_bulk_total`

#### 1. Reproduce
- **คำสั่งที่รัน:** `python -m pytest tests/test_discount.py -k test_bulk_total -v`
- **ผลลัพธ์ Failure:**
  ```text
  E   AssertionError: assert 299.9 == 270.0
  E    +  where 299.9 = bulk_total([100.0, 100.0, 100.0], 10)
  ```

#### 2. Traceback
- **บรรทัดที่เกิดข้อผิดพลาด:** `tests/test_discount.py`, บรรทัดที่ 18
  ```python
  def test_bulk_total():
      # (100 + 100 + 100) = 300 ลด 10% ควรเหลือ 270
  >   assert bulk_total([100.0, 100.0, 100.0], 10) == 270.0
  ```
- **ตำแหน่งโค้ด:** `discount.py`, บรรทัดที่ 13
  ```python
  def bulk_total(prices: list, discount_percent: float) -> float:
      total = 0
      for p in prices:
          total += p
      return apply_discount(total, discount_percent)
  ```

#### 3. สมมติฐาน (Hypothesis)
ฟังก์ชัน `bulk_total` มีการรวมราคาสินค้าถูกต้อง (`total = 100 + 100 + 100 = 300.0`) แต่การคำนวณล้มเหลวเนื่องจากได้รับผลกระทบสืบเนื่อง (Cascading Failure) มาจากบั๊กในฟังก์ชัน `apply_discount` ซึ่งเมื่อส่ง `total = 300.0` และ `discount_percent = 10` เข้าไป ฟังก์ชันเดิมจะคำนวณ `300.0 - 10 / 100 = 299.9` แทนที่จะเป็น `270.0`

#### 4. การยืนยัน (Confirmation)
ทดสอบตรวจสอบค่า `total` ก่อนส่งเข้า `apply_discount`:
```python
prices = [100.0, 100.0, 100.0]
total = sum(prices)
print("Total sum:", total)  # แสดงผล 300.0
```
และเมื่อเรียก `apply_discount(300.0, 10)` ด้วยสูตรใหม่ที่แก้ในจุดที่ 1 จะได้ `300.0 * 0.9 = 270.0` ถูกต้องตามที่ test ต้องการทันที

#### 5. Root Cause และการแก้ (Fix)
- **Root Cause:** Cascading Error จากฟังก์ชันย่อย `apply_discount` ที่ให้ผลลัพธ์ผิดพลาด
- **การแก้ไข:** เมื่อแก้ไข `apply_discount` เรียบร้อยแล้ว ข้อนี้จะผ่านทันที และเพื่อปรับปรุงโค้ดให้สะอาดขึ้น จึงเปลี่ยนการวนลูปบวกทีละตัวมาใช้ `sum(prices)`:
  ```python
  def bulk_total(prices: list, discount_percent: float) -> float:
      """รวมราคาหลายรายการแล้วลดส่วนลดรวมทีเดียว"""
      total = sum(prices)
      return apply_discount(total, discount_percent)
  ```

---

### จุดที่ 3: `test_average_price_empty`

#### 1. Reproduce
- **คำสั่งที่รัน:** `python -m pytest tests/test_discount.py -k test_average_price_empty -v`
- **ผลลัพธ์ Failure:**
  ```text
  E   ZeroDivisionError: division by zero
  ```

#### 2. Traceback
- **บรรทัดที่เกิดข้อผิดพลาด:** `tests/test_discount.py`, บรรทัดที่ 28
  ```python
  def test_average_price_empty():
  >   assert average_price([]) == 0.0
  ```
- **ตำแหน่งโค้ด:** `discount.py`, บรรทัดที่ 18
  ```python
  def average_price(prices: list) -> float:
  >   return sum(prices) / len(prices)
  ```

#### 3. สมมติฐาน (Hypothesis)
ฟังก์ชัน `average_price` นำ `len(prices)` มาเป็นตัวหารโดยตรง โดยไม่มีการตรวจสอบกรณีลิสต์ว่าง (`prices = []`) ซึ่ง `len([])` มีค่าเท่ากับ `0` ทำให้เกิดข้อผิดพลาดร้ายแรง `ZeroDivisionError: division by zero`

#### 4. การยืนยัน (Confirmation)
ทดสอบรันคำสั่งใน Python:
```python
prices = []
print(len(prices))  # ได้ 0
```
การนำตัวเลขใด ๆ หารด้วย 0 ใน Python จะเกิด Exception ทันที และเมื่อทดลองใส่เงื่อนไข Guard Clause: `if not prices: return 0.0` พบว่าฟังก์ชันคืนค่า `0.0` ผ่านการทดสอบ

#### 5. Root Cause และการแก้ (Fix)
- **Root Cause:** ขาด Input Validation สำหรับ Edge Case ข้อมูลคลังว่างเปล่า (Empty Collection)
- **การแก้ไข:** เพิ่มการตรวจสอบกรณีลิสต์ว่างที่ต้นฟังก์ชัน:
  ```python
  def average_price(prices: list) -> float:
      """คืนราคาเฉลี่ยของรายการสินค้า"""
      if not prices:
          return 0.0
      return sum(prices) / len(prices)
  ```

---

### จุดที่ 4: `test_cheapest_n`

#### 1. Reproduce
- **คำสั่งที่รัน:** `python -m pytest tests/test_discount.py -k test_cheapest_n -v`
- **ผลลัพธ์ Failure:**
  ```text
  E   assert [20.0] == [10.0, 20.0]
  E   At index 0 diff: 20.0 != 10.0
  E   Right contains one more item: 20.0
  ```

#### 2. Traceback
- **บรรทัดที่เกิดข้อผิดพลาด:** `tests/test_discount.py`, บรรทัดที่ 33
  ```python
  def test_cheapest_n():
      # ถูกสุด 2 รายการของ [50, 10, 30, 20] = [10, 20]
  >   assert cheapest_n([50.0, 10.0, 30.0, 20.0], 2) == [10.0, 20.0]
  ```
- **ตำแหน่งโค้ด:** `discount.py`, บรรทัดที่ 24
  ```python
  def cheapest_n(prices: list, n: int) -> list:
      ordered = sorted(prices)
      return ordered[1:n]
  ```

#### 3. สมมติฐาน (Hypothesis)
ฟังก์ชันตัดข้อมูลด้วยคำสั่ง Slice ผิดพลาด โดยเขียน `ordered[1:n]` ซึ่งเริ่มต้นที่ index 1 ทำให้ข้ามสมาชิกตัวแรกที่ถูกที่สุด (index 0) ไป และยังทำให้ได้จำนวนสมาชิกเพียง `n - 1` ตัว แทนที่จะได้ `n` ตัว

#### 4. การยืนยัน (Confirmation)
ทดลองเรียงลำดับและตัด slice ใน Python:
```python
prices = [50.0, 10.0, 30.0, 20.0]
ordered = sorted(prices)
print("เรียงแล้ว:", ordered)          # [10.0, 20.0, 30.0, 50.0]
print("โค้ดเดิม [1:2]:", ordered[1:2]) # ได้ [20.0] (ผิด)
print("โค้ดใหม่ [:2]:", ordered[:2])   # ได้ [10.0, 20.0] (ถูกต้อง)
```
ผลลัพธ์ยืนยันว่า `ordered[:n]` ได้รายการสินค้าที่ถูกที่สุด `n` รายการครบถ้วนตั้งแต่ตัวแรก

#### 5. Root Cause และการแก้ (Fix)
- **Root Cause:** ข้อผิดพลาดเรื่องการตัดช่วงข้อมูล (Off-by-one / Slice Boundary Error) สับสนเรื่อง Zero-based Indexing
- **การแก้ไข:** แก้ไขการตัด slice ให้เริ่มจากตำแหน่งแรก:
  ```python
  def cheapest_n(prices: list, n: int) -> list:
      """คืน n รายการที่ราคาถูกที่สุด เรียงจากถูกไปแพง"""
      ordered = sorted(prices)
      return ordered[:n]
  ```

---

## 3. วิเคราะห์กับดักที่ตั้งใจวางไว้: `test_apply_discount_zero`

ในชุด Test มีกรณีทดสอบหนึ่งที่ **ผ่าน (PASSED)** ตั้งแต่แรกทั้งที่ฟังก์ชัน `apply_discount` มีบั๊ก:
```python
def test_apply_discount_zero():
    # ลด 0% ควรได้ราคาเดิม
    assert apply_discount(250.0, 0) == 250.0
```
- **สาเหตุที่ผ่าน:** โค้ดเดิมคือ `price - percent / 100` เมื่อแทนค่า `percent = 0` จะได้ `250.0 - 0 / 100 = 250.0 - 0 = 250.0` ซึ่งเท่ากับ `250.0` พอดี
- **บทเรียนเชิงวิศวกรรมซอฟต์แวร์:**  
  การที่ Test รันผ่าน ไม่ได้แปลว่าโค้ดนั้นถูกต้องเสมอไป (False Sense of Security) หาก Test Cases ไม่ครอบคลุมกรณีทั่วไป (Equivalence Partitioning) หรือพึ่งพาเพียงค่าขอบที่เป็น 0 เพียงตัวเดียว ดังนั้นวิศวกรซอฟต์แวร์จะต้องอ่าน Requirement และทำความเข้าใจตรรกะของฟังก์ชันร่วมด้วยเสมอ

---

## 4. ตารางสรุปการ Debug ครบทุกจุด

| Test ที่ไม่ผ่าน | Traceback / Assertion ที่พบ | สมมติฐาน Root Cause | วิธียืนยัน | การแก้ที่ถูกต้อง |
| :--- | :--- | :--- | :--- | :--- |
| `test_apply_discount_basic` | `AssertionError: assert 99.9 == 90.0` | สูตรคำนวณผิด ลืมคูณ `price` กับสัดส่วนเปอร์เซ็นต์ | รันคำนวณเปรียบเทียบใน REPL | `return price * (1 - percent / 100)` |
| `test_bulk_total` | `AssertionError: assert 299.9 == 270.0` | Cascading failure จากฟังก์ชัน `apply_discount` | เช็กค่า `total` ก่อนส่งเข้าฟังก์ชัน | แก้ไข `apply_discount` และใช้ `sum(prices)` |
| `test_average_price_empty` | `ZeroDivisionError: division by zero` | ขาด Guard Clause ดักกรณีลิสต์ว่าง | ทดสอบเรียก `len([])` แล้วหาร | เพิ่ม `if not prices: return 0.0` |
| `test_cheapest_n` | `AssertionError: [20.0] != [10.0, 20.0]` | ตัด slice ผิด `ordered[1:n]` ข้าม index 0 | ทดลอง print slice `ordered[:n]` | เปลี่ยนเป็น `return ordered[:n]` |
