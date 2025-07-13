# 🎲 Sic Bo Oracle (v1.0.0)

โปรเจกต์นี้คือระบบวิเคราะห์ผลไฮโลที่พัฒนาด้วย Python และ Streamlit โดยมีเป้าหมายเพื่อช่วยวิเคราะห์สถิติ, ระบุรูปแบบที่เกิดขึ้นบ่อย และให้คำแนะนำในการทำนายผลลัพธ์การทอยไฮโลครั้งถัดไป ระบบนี้ถูกออกแบบมาให้เป็นโมดูลาร์ (Modular) ทำให้ง่ายต่อการเพิ่มหรือปรับปรุง "สูตร" การทำนายต่างๆ ในอนาคต

---

## การปรับปรุงในเวอร์ชันนี้ (v1.0.0)

เวอร์ชันนี้ได้รวมเอาแนวคิดและโครงสร้างการทำนายที่ซับซ้อนจากระบบ Oracle Baccarat (v3.7) มาปรับใช้กับไฮโล ทำให้มีความสามารถในการวิเคราะห์และทำนายที่ลึกซึ้งยิ่งขึ้น:

* **โมดูลทำนายใหม่:** เพิ่ม "ผู้เชี่ยวชาญ" การทำนายใหม่ 4 โมดูล (ปรับจาก Baccarat Oracle):
    * `TrendPredictor`: วิเคราะห์แนวโน้มหลักของผล สูง/ต่ำ ในช่วงล่าสุด
    * `TwoTwoPatternPredictor`: ตรวจจับรูปแบบ 2-2 (เช่น สูง-สูง-ต่ำ-ต่ำ)
    * `SniperPatternPredictor`: ค้นหารูปแบบที่ซับซ้อนและเฉพาะเจาะจงมากขึ้นจากชุดรูปแบบที่กำหนดไว้
    * `SmartPredictor`: ผสมผสานการจดจำรูปแบบและการวิเคราะห์เทรนด์ เพื่อการทำนายที่ยืดหยุ่น
* **Logic การทำนายที่ซับซ้อนขึ้น:**
    * **การรอข้อมูล:** ระบบจะเริ่มทำนายเมื่อมีข้อมูล สูง/ต่ำ ที่ไม่ใช่ตอง สะสมครบ 20 ครั้ง (`min_non_triplet_history_for_prediction`) เพื่อให้การทำนายมีความน่าเชื่อถือ
    * **การหยุดระบบชั่วคราว:** หากทำนายพลาดติดต่อกัน 6 ครั้ง (`current_miss_streak >= 6`) ระบบจะหยุดให้คำแนะนำชั่วคราว เพื่อป้องกันการสูญเสียที่อาจเกิดขึ้น
    * **กลยุทธ์การฟื้นฟู (Recovery Logic):** เมื่อทำนายพลาดติดต่อกัน 3-5 ครั้ง (`current_miss_streak in [3, 4, 5]`) ระบบจะพยายามระบุโมดูลที่ทำนายได้ดีที่สุดในช่วงล่าสุด (โดยมีลำดับความสำคัญของโมดูลกู้คืน) และใช้คำทำนายจากโมดูลนั้น เพื่อพยายามกลับมาทำนายถูก พร้อมเพิ่มความมั่นใจเล็กน้อย

---

## คุณสมบัติ

* **การบันทึกผลสด:** สามารถบันทึกผลลูกเต๋า 3 ลูกของการทอยแต่ละครั้งได้
* **การวิเคราะห์สถิติ:** แสดงสถิติพื้นฐานของผลลัพธ์ที่ผ่านมา เช่น ความถี่ของ สูง/ต่ำ, คู่/คี่, แต้มรวม และจำนวนตอง
* **ระบบทำนายแบบ Ensemble:** รวบรวมคำทำนายจาก "โมดูลผู้เชี่ยวชาญ" หลายตัวที่ใช้ Logic ต่างกัน (เช่น กฎพื้นฐาน, การจดจำรูปแบบ)
* **การถ่วงน้ำหนักตามประสิทธิภาพ:** ระบบจะประเมินความแม่นยำของแต่ละโมดูลในอดีต และนำมาใช้เป็นน้ำหนักในการให้คำทำนายสุดท้าย
* **การแสดงผล Big Road:** แสดงประวัติผล สูง/ต่ำ ในรูปแบบ Big Road ที่คุ้นเคย
* **ความมั่นใจในการทำนาย:** แสดงระดับความมั่นใจของคำทำนายที่แนะนำ
* **การจัดการประวัติ:** สามารถลบผลล่าสุด หรือรีเซ็ตประวัติทั้งหมดได้
* **การบันทึกข้อมูล:** ประวัติการทอยจะถูกบันทึกในไฟล์ CSV เพื่อให้ข้อมูลคงอยู่แม้ปิดแอปไป

---

## โครงสร้างโปรเจกต์

sicbo-analyzer/
├── .streamlit/
│   └── config.toml           # การตั้งค่าธีมสำหรับ Streamlit
├── data/
│   └── sicbo_data.csv        # ไฟล์สำหรับบันทึกประวัติผลการทอย (จะถูกสร้างอัตโนมัติ)
├── src/                      # โฟลเดอร์สำหรับ Logic การทำงานหลัก
│   ├── data_generator.py     # โมดูลสำหรับสร้าง/โหลด/บันทึกข้อมูล
│   ├── analyzer.py           # โมดูลสำหรับวิเคราะห์สถิติและสร้างกราฟ
│   ├── prediction_modules/   # โฟลเดอร์สำหรับเก็บโมดูลทำนายผลแต่ละตัว
│   │   ├── init.py
│   │   ├── base_predictor.py # คลาสพื้นฐานสำหรับโมดูลทำนาย
│   │   ├── rule_based_predictor.py # โมดูลทำนายตามกฎพื้นฐาน
│   │   ├── pattern_predictor.py    # โมดูลทำนายตามการจดจำรูปแบบ
│   │   ├── trend_predictor.py      # โมดูลวิเคราะห์เทรนด์ใหม่
│   │   ├── two_two_pattern_predictor.py # โมดูลรูปแบบ 2-2 ใหม่
│   │   ├── sniper_pattern_predictor.py  # โมดูลรูปแบบ Sniper ใหม่
│   │   └── smart_predictor.py       # โมดูลทำนายแบบ Smart ใหม่
│   ├── scorer.py             # โมดูลสำหรับถ่วงน้ำหนักและให้คะแนนคำทำนาย
│   ├── sicbo_oracle.py       # คลาสหลักที่จัดการประวัติ, โมดูลทำนาย และการให้คำทำนายสุดท้าย
│   └── init.py
├── app.py                    # ไฟล์หลักของ Streamlit Application (ส่วนติดต่อผู้ใช้)
├── requirements.txt          # รายชื่อไลบรารี Python ที่จำเป็น
└── README.md                 # ไฟล์อธิบายโปรเจกต์

---

## การติดตั้งและการใช้งาน (บนมือถือผ่าน GitHub และ Streamlit Cloud)

เนื่องจากคุณต้องการทำบนมือถือโดยตรง เราจะใช้ GitHub.com ผ่านเว็บเบราว์เซอร์ในการสร้างและจัดการไฟล์ทั้งหมด จากนั้นจึง Deploy ไปยัง Streamlit Cloud

### ขั้นตอนที่ 1: สร้าง GitHub Repository ใหม่

1.  เปิดเบราว์เซอร์บนมือถือของคุณ ไปที่ [https://github.com/](https://github.com/) และเข้าสู่ระบบ
2.  แตะที่ไอคอนเมนู (มักจะเป็นขีดสามขีด หรือรูปโปรไฟล์ของคุณ) เพื่อเปิดเมนูด้านข้าง
3.  มองหาและแตะที่ **"Your repositories"**
4.  แตะที่ปุ่ม **"New"** (หรือเครื่องหมาย `+` ที่มุมขวาบน แล้วเลือก "New repository")
5.  **Repository name:** พิมพ์ `sicbo-oracle`
6.  **Description (Optional):** ใส่คำอธิบายสั้นๆ เช่น `Sic Bo prediction and analysis tool`
7.  **Public/Private:** เลือก `Public`
8.  **สำคัญมาก:** **อย่าติ๊ก** ช่อง "Add a README file", "Add .gitignore", "Choose a license"
9.  แตะปุ่ม **"Create repository"**

 ### ขั้นตอนที่ 2: สร้างโครงสร้างโฟลเดอร์และไฟล์บน GitHub

บน GitHub คุณต้องสร้างไฟล์ภายในโฟลเดอร์นั้นๆ GitHub ถึงจะสร้างโฟลเดอร์ให้

1.  **สร้างโฟลเดอร์ `.streamlit/` และไฟล์ `config.toml`:**
    * บนหน้า Repository `sicbo-oracle` ของคุณ แตะที่ปุ่ม **"Add file"** แล้วเลือก **"Create new file"**
    * ในช่อง "Name your file..." ให้พิมพ์: `.streamlit/config.toml`
    * คัดลอกโค้ดสำหรับ `config.toml` ที่ผมให้ไว้ด้านบน แล้ววางลงในช่องเนื้อหาไฟล์
    * เลื่อนลงมาด้านล่าง แตะปุ่ม **"Commit new file"**

2.  **สร้างโฟลเดอร์ `data/`:**
    * ทำซ้ำขั้นตอนเดิม: แตะ **"Add file"** > **"Create new file"**
    * ในช่อง "Name your file..." ให้พิมพ์: `data/.gitkeep` (ไฟล์เปล่าๆ เพื่อให้ Git สร้างโฟลเดอร์)
    * **ไม่ต้องใส่เนื้อหาอะไรในไฟล์นี้**
    * แตะปุ่ม **"Commit new file"**

3.  **สร้างโฟลเดอร์ `src/` และไฟล์ `src/__init__.py`:**
    * ทำซ้ำขั้นตอนเดิม: แตะ **"Add file"** > **"Create new file"**
    * ในช่อง "Name your file..." ให้พิมพ์: `src/__init__.py`
    * **ไม่ต้องใส่เนื้อหาอะไรในไฟล์นี้**
    * แตะปุ่ม **"Commit new file"**

4.  **สร้างโฟลเดอร์ `src/prediction_modules/` และไฟล์ `src/prediction_modules/__init__.py`:**
    * ทำซ้ำขั้นตอนเดิม: แตะ **"Add file"** > **"Create new file"**
    * ในช่อง "Name your file..." ให้พิมพ์: `src/prediction_modules/__init__.py`
    * **ไม่ต้องใส่เนื้อหาอะไรในไฟล์นี้**
    * แตะปุ่ม **"Commit new file"**

5.  **สร้างไฟล์ `requirements.txt`:**
    * ทำซ้ำขั้นตอนเดิม: แตะ **"Add file"** > **"Create new file"**
    * ในช่อง "Name your file..." ให้พิมพ์: `requirements.txt`
    * คัดลอกโค้ดสำหรับ `requirements.txt` ที่ผมให้ไว้ด้านบน แล้ววางลงในช่องเนื้อหาไฟล์
    * แตะปุ่ม **"Commit new file"**

6.  **สร้างไฟล์ `README.md`:**
    * ทำซ้ำขั้นตอนเดิม: แตะ **"Add file"** > **"Create new file"**
    * ในช่อง "Name your file..." ให้พิมพ์: `README.md`
    * คัดลอกโค้ดสำหรับ `README.md` ที่ผมให้ไว้ด้านบน แล้ววางลงในช่องเนื้อหาไฟล์
    * แตะปุ่ม **"Commit new file"**

7.  **สร้างไฟล์ `app.py`:**
    * ทำซ้ำขั้นตอนเดิม: แตะ **"Add file"** > **"Create new file"**
    * ในช่อง "Name your file..." ให้พิมพ์: `app.py`
    * คัดลอกโค้ดสำหรับ `app.py` ที่ผมให้ไว้ด้านบน แล้ววางลงในช่องเนื้อหาไฟล์
    * แตะปุ่ม **"Commit new file"**

8.  **สร้างไฟล์ Python ที่เหลือในโฟลเดอร์ `src/` และ `src/prediction_modules/`:**
    * **สำหรับ `src/analyzer.py`:**
        * แตะ **"Add file"** > **"Create new file"**
        * พิมพ์: `src/analyzer.py`
        * คัดลอกโค้ดสำหรับ `analyzer.py` ที่ผมให้ไว้ด้านบน แล้ววางลงในช่องเนื้อหาไฟล์
        * แตะ **"Commit new file"**
    * **สำหรับ `src/data_generator.py`:**
        * แตะ **"Add file"** > **"Create new file"**
        * พิมพ์: `src/data_generator.py`
        * คัดลอกโค้ดสำหรับ `data_generator.py` ที่ผมให้ไว้ด้านบน แล้ววางลงในช่องเนื้อหาไฟล์
        * แตะ **"Commit new file"**
    * **สำหรับ `src/scorer.py`:**
        * แตะ **"Add file"** > **"Create new file"**
        * พิมพ์: `src/scorer.py`
        * คัดลอกโค้ดสำหรับ `scorer.py` ที่ผมให้ไว้ด้านบน แล้ววางลงในช่องเนื้อหาไฟล์
        * แตะ **"Commit new file"**
    * **สำหรับ `src/sicbo_oracle.py`:**
        * แตะ **"Add file"** > **"Create new file"**
        * พิมพ์: `src/sicbo_oracle.py`
        * คัดลอกโค้ดสำหรับ `sicbo_oracle.py` ที่ผมให้ไว้ด้านบน แล้ววางลงในช่องเนื้อหาไฟล์
        * แตะ **"Commit new file"**
     * **สำหรับ `src/prediction_modules/base_predictor.py`:**
        * แตะ **"Add file"** > **"Create new file"**
        * พิมพ์: `src/prediction_modules/base_predictor.py`
        * คัดลอกโค้ดสำหรับ `base_predictor.py` ที่ผมให้ไว้ด้านบน แล้ววางลงในช่องเนื้อหาไฟล์
        * แตะ **"Commit new file"**
    * **สำหรับ `src/prediction_modules/rule_based_predictor.py`:**
        * แตะ **"Add file"** > **"Create new file"**
        * พิมพ์: `src/prediction_modules/rule_based_predictor.py`
        * คัดลอกโค้ดสำหรับ `rule_based_predictor.py` ที่ผมให้ไว้ด้านบน แล้ววางลงในช่องเนื้อหาไฟล์
        * แตะ **"Commit new file"**
    * **สำหรับ `src/prediction_modules/pattern_predictor.py`:**
        * แตะ **"Add file"** > **"Create new file"**
        * พิมพ์: `src/prediction_modules/pattern_predictor.py`
        * คัดลอกโค้ดสำหรับ `pattern_predictor.py` ที่ผมให้ไว้ด้านบน แล้ววางลงในช่องเนื้อหาไฟล์
        * แตะ **"Commit new file"**
    * **สำหรับ `src/prediction_modules/trend_predictor.py`:**
        * แตะ **"Add file"** > **"Create new file"**
        * พิมพ์: `src/prediction_modules/trend_predictor.py`
        * คัดลอกโค้ดสำหรับ `trend_predictor.py` ที่ผมให้ไว้ด้านบน แล้ววางลงในช่องเนื้อหาไฟล์
        * แตะ **"Commit new file"**
    * **สำหรับ `src/prediction_modules/two_two_pattern_predictor.py`:**
        * แตะ **"Add file"** > **"Create new file"**
        * พิมพ์: `src/prediction_modules/two_two_pattern_predictor.py`
        * คัดลอกโค้ดสำหรับ `two_two_pattern_predictor.py` ที่ผมให้ไว้ด้านบน แล้ววางลงในช่องเนื้อหาไฟล์
        * แตะ **"Commit new file"**
    * **สำหรับ `src/prediction_modules/sniper_pattern_predictor.py`:**
        * แตะ **"Add file"** > **"Create new file"**
        * พิมพ์: `src/prediction_modules/sniper_pattern_predictor.py`
        * คัดลอกโค้ดสำหรับ `sniper_pattern_predictor.py` ที่ผมให้ไว้ด้านบน แล้ววางลงในช่องเนื้อหาไฟล์
        * แตะ **"Commit new file"**
    * **สำหรับ `src/prediction_modules/smart_predictor.py`:**
        * แตะ **"Add file"** > **"Create new file"**
        * พิมพ์: `src/prediction_modules/smart_predictor.py`
        * คัดลอกโค้ดสำหรับ `smart_predictor.py` ที่ผมให้ไว้ด้านบน แล้ววางลงในช่องเนื้อหาไฟล์
        * แตะ **"Commit new file"**

### ขั้นตอนที่ 3: Deploy แอปพลิเคชันบน Streamlit Cloud

1.  **ไปที่ Streamlit Cloud:**
    * เปิดเบราว์เซอร์บนมือถือของคุณ
    * ไปที่ [https://share.streamlit.io/](https://share.streamlit.io/)
2.  **เข้าสู่ระบบ:**
    * แตะ **"Continue with GitHub"** และอนุญาตให้ Streamlit Cloud เข้าถึงบัญชี GitHub ของคุณ (หากยังไม่ได้ทำ)
3.  **Deploy แอปใหม่:**
    * เมื่อเข้ามาใน Dashboard ของ Streamlit Cloud ให้มองหาปุ่ม **"New app"** (หรือ "Deploy an app")
    * **"Repository"**: แตะที่ช่องนี้ แล้วเลือก Repository ของคุณจากรายการ (เช่น `YOUR_USERNAME/sicbo-oracle`)
    * **"Branch"**: แตะที่ช่องนี้ แล้วเลือก **`main`** (หรือ `master` หากคุณใช้ชื่อนั้น)
    * **"Main file path"**: พิมพ์ `app.py`
    * **"App URL"**: (ไม่บังคับ) คุณสามารถกำหนดชื่อ URL ที่จำง่ายได้ เช่น `sicbo-oracle-yourusername`
    * แตะปุ่ม **"Deploy!"**

4.  **รอการ Deploy:**
    * Streamlit Cloud จะใช้เวลาสักครู่ในการดึงโค้ดของคุณ, ติดตั้งไลบรารีจาก `requirements.txt`, และรันแอปพลิเคชัน
    * คุณจะเห็น Log การทำงานในระหว่างนี้
    * เมื่อเสร็จสิ้น แอปพลิเคชันของคุณจะปรากฏขึ้นบนเว็บ และคุณจะได้รับ URL ที่สามารถแชร์ให้ผู้อื่นใช้งานได้
