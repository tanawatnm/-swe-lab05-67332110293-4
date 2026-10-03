# SWE Inventory Management - Lab 04: AI-Assisted Coding & UX

**รหัสวิชา:** วิศวกรรมซอฟต์แวร์ในยุค AI (Software Engineering in AI Era)  
**ชื่อ-นามสกุล:** นายธนวัฒน์ น้ำเง่า (Mr. Tanawat Namngao)  
**รหัสนักศึกษา:** 67332110293-4  
**GitHub Username:** [tanawatnm](https://github.com/tanawatnm)  
**Repository:** [swe-inventory-67332110293-4](https://github.com/tanawatnm/swe-inventory-67332110293-4)

---

## 📌 สรุปงานส่ง Lab 04 (Checklist of Deliverables)

งานทั้งหมดของ Lab 4 รวบรวมไว้ในโฟลเดอร์ `lab04-ai-coding-ux/` ตามข้อกำหนด:

### ส่วนที่ 1: UX แบบย่อ และ UI Mockup (Sub-CLO 3.4, 3.5)
- [x] [findings-lab04.md](file:///c:/Users/next5/Desktop/LAB4/lab04-ai-coding-ux/findings-lab04.md) - บันทึกการสัมภาษณ์ผู้ใช้ สรุป Needs, Pain Points, Surprises และ Point of View (1 ประโยค) ที่ชี้เป้าไปยังหน้าจอที่ต้องแก้ไข
- [x] [persona.md](file:///c:/Users/next5/Desktop/LAB4/lab04-ai-coding-ux/persona.md) - Persona ตัวละคร "สมหมาย รักงาน" พร้อมระบุระดับทักษะเทคโนโลยี (2/5) และ Journey Map 5 ขั้นตอนระบุจุดสะดุดและแนวทางแก้ไข
- [x] [assets/wireframe-ai.md](file:///c:/Users/next5/Desktop/LAB4/lab04-ai-coding-ux/assets/wireframe-ai.md) - Text Wireframe (ASCII Layout) จาก AI รวม 3 หน้าจอ: Login, Dashboard, และ Add Product พร้อมคำอธิบาย Usability & Accessibility
- [x] [assets/inventory-mockup.drawio](file:///c:/Users/next5/Desktop/LAB4/lab04-ai-coding-ux/assets/inventory-mockup.drawio) - UI Mockup ฉบับสมบูรณ์สำหรับเปิดดูและแก้ไขใน draw.io / diagrams.net ตามชุดสี WCAG AA
- [x] [assets/mockup-link.txt](file:///c:/Users/next5/Desktop/LAB4/lab04-ai-coding-ux/assets/mockup-link.txt) - ลิงก์และคำอธิบายการเข้าถึงไฟล์ Mockup
- [x] [accessibility-review.md](file:///c:/Users/next5/Desktop/LAB4/lab04-ai-coding-ux/accessibility-review.md) - ผลการตรวจ Accessibility Checklist ตามเกณฑ์ WCAG 2.1 AA และระบุจุดที่ AI ออกแบบพลาด 3 จุดพร้อมวิธีแก้ไขด้วยตนเอง

### ส่วนที่ 2: Prompt vs Context Engineering & Code Review (Sub-CLO 3.6)
- [x] [prompt-vs-context.md](file:///c:/Users/next5/Desktop/LAB4/lab04-ai-coding-ux/prompt-vs-context.md) - การทดลองเปรียบเทียบผลลัพธ์ระหว่าง Prompt ธรรมดากับ Prompt ที่มี Context ครบถ้วน (Invariants, Exceptions, Constraints, Tests)
- [x] [code-review.md](file:///c:/Users/next5/Desktop/LAB4/lab04-ai-coding-ux/code-review.md) - รายงาน Code Review ละเอียดครบ 4 องค์ประกอบ สำหรับ PR โมดูล `inventory_service.py`, ตารางสรุป 7 จุดบกพร่อง, การเปรียบเทียบกับ AI Reviewer และคำตอบแบบฝึกหัดส่งท้าย

### ส่วนที่ 3: Evidence-Based Debugging (Sub-CLO 3.6)
- [x] [debug-log.md](file:///c:/Users/next5/Desktop/LAB4/lab04-ai-coding-ux/debug-log.md) - บันทึกการ Debug 5 ขั้นตอน (Reproduce, Traceback, Hypothesis, Confirmation, Fix & Re-run) สำหรับทุก Test ที่ไม่ผ่าน พร้อมการวิเคราะห์ Trap ใน `test_apply_discount_zero`
- [x] [discount.py](file:///c:/Users/next5/Desktop/LAB4/lab04-ai-coding-ux/discount.py) - โค้ดที่ได้รับการแก้ไข Root cause ครบถ้วน
- [x] [tests/test_discount.py](file:///c:/Users/next5/Desktop/LAB4/lab04-ai-coding-ux/tests/test_discount.py) - ชุดทดสอบทางการ รันผ่านครบ 6/6 tests (100% PASSED)

---

## 🚀 วิธีการทดสอบรัน Test Suite

เปิด Terminal และรันคำสั่งต่อไปนี้:

```bash
cd lab04-ai-coding-ux
python -m pytest tests/test_discount.py -v
```

ผลการทดสอบ:
```text
tests/test_discount.py::test_apply_discount_basic PASSED                 [ 16%]
tests/test_discount.py::test_apply_discount_zero PASSED                  [ 33%]
tests/test_discount.py::test_bulk_total PASSED                           [ 50%]
tests/test_discount.py::test_average_price PASSED                        [ 66%]
tests/test_discount.py::test_average_price_empty PASSED                  [ 83%]
tests/test_discount.py::test_cheapest_n PASSED                           [100%]

============================== 6 passed in 0.03s ==============================
```
