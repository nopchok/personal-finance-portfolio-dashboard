"""
Database and storage module for Minimalist Personal Finance & Portfolio Dashboard
Stores monthly financial snapshots, assets, liabilities, and settings using SQLite.
"""

import sqlite3
import json
import os
import math
from datetime import datetime
from typing import Dict, List, Any, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "finance_data.db")

def safe_float(val, default=0.0) -> float:
    if val is None:
        return float(default)
    try:
        if isinstance(val, float) and (math.isnan(val) or val != val):
            return float(default)
        s = str(val).strip()
        if not s or s.lower() in ('nan', 'none', 'null', ''):
            return float(default)
        return float(s.replace(',', ''))
    except (ValueError, TypeError):
        return float(default)

def safe_str(val, default="") -> str:
    if val is None:
        return default
    try:
        if isinstance(val, float) and (math.isnan(val) or val != val):
            return default
        s = str(val).strip()
        if s.lower() in ('nan', 'none', 'null'):
            return default
        return s
    except Exception:
        return default

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Assets table (Investment & Cash Holdings & Fixed Assets)
    c.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        current_value REAL NOT NULL DEFAULT 0,
        cost_basis REAL NOT NULL DEFAULT 0,
        target_allocation REAL NOT NULL DEFAULT 0,
        monthly_dca REAL NOT NULL DEFAULT 0,
        expected_roi REAL NOT NULL DEFAULT 6.0,
        platform_or_broker TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        asset_type TEXT NOT NULL DEFAULT 'investment',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Migration for existing DB
    try:
        c.execute("ALTER TABLE assets ADD COLUMN asset_type TEXT NOT NULL DEFAULT 'investment'")
    except Exception:
        pass

    # Auto tag existing fixed assets
    try:
        c.execute("""
        UPDATE assets SET asset_type = 'fixed_asset' 
        WHERE asset_type = 'investment' AND (
            category LIKE '%บ้าน%' OR category LIKE '%คอนโด%' OR category LIKE '%ที่ดิน%' 
            OR category LIKE '%อสังหา%' OR category LIKE '%สิ่งปลูกสร้าง%' OR category LIKE '%Real Estate%'
            OR category LIKE '%รถยนต์%' OR name LIKE '%บ้าน%' OR name LIKE '%คอนโด%' OR name LIKE '%ที่ดิน%'
        )
        """)
    except Exception:
        pass

    # 2. Liabilities table (Debts / Loans)
    c.execute("""
    CREATE TABLE IF NOT EXISTS liabilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        total_balance REAL NOT NULL DEFAULT 0,
        monthly_payment REAL NOT NULL DEFAULT 0,
        interest_rate REAL NOT NULL DEFAULT 0,
        notes TEXT DEFAULT '',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3. Monthly Financial Estimate Profile (Current active estimate)
    c.execute("""
    CREATE TABLE IF NOT EXISTS monthly_profile (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        salary REAL NOT NULL DEFAULT 50000,
        bonus_or_other_income REAL NOT NULL DEFAULT 0,
        passive_income REAL NOT NULL DEFAULT 0,
        fixed_expenses REAL NOT NULL DEFAULT 15000,
        variable_expense_estimate REAL NOT NULL DEFAULT 15000,
        emergency_fund_target_months INTEGER NOT NULL DEFAULT 6,
        fire_target_monthly_spend REAL NOT NULL DEFAULT 30000,
        fire_expected_return REAL NOT NULL DEFAULT 7.0,
        fire_inflation_rate REAL NOT NULL DEFAULT 2.5,
        fire_current_age INTEGER NOT NULL DEFAULT 30,
        fire_target_age INTEGER NOT NULL DEFAULT 50,
        fire_monthly_dca REAL NOT NULL DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    try:
        c.execute("ALTER TABLE monthly_profile ADD COLUMN fire_monthly_dca REAL DEFAULT 0")
    except Exception:
        pass

    # 4. Monthly Snapshots (Historic tracking)
    c.execute("""
    CREATE TABLE IF NOT EXISTS monthly_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_month TEXT UNIQUE NOT NULL, -- Format: YYYY-MM
        income REAL NOT NULL,
        expenses REAL NOT NULL,
        savings_invested REAL NOT NULL,
        total_assets REAL NOT NULL,
        total_debts REAL NOT NULL,
        net_worth REAL NOT NULL,
        notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 5. Itemized Estimated Expenses table
    c.execute("""
    CREATE TABLE IF NOT EXISTS expense_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        expense_type TEXT NOT NULL, -- 'คงที่ (Fixed)' or 'ผันแปร (Variable)'
        estimated_amount REAL NOT NULL DEFAULT 0,
        notes TEXT DEFAULT '',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 6. Itemized Estimated Income table
    c.execute("""
    CREATE TABLE IF NOT EXISTS income_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        income_type TEXT NOT NULL, -- 'ประจำ (Active / Fixed)' or 'ผันแปร/เสริม (Passive / Variable)'
        estimated_amount REAL NOT NULL DEFAULT 0,
        notes TEXT DEFAULT '',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 7. Dynamic Custom Categories table
    c.execute("""
    CREATE TABLE IF NOT EXISTS custom_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cat_type TEXT NOT NULL, -- 'income', 'expense', 'asset', 'liability'
        name TEXT NOT NULL,
        UNIQUE(cat_type, name)
    )
    """)

    # Insert default monthly profile if not exists
    c.execute("SELECT COUNT(*) FROM monthly_profile WHERE id = 1")
    if c.fetchone()[0] == 0:
        c.execute("""
        INSERT INTO monthly_profile (
            id, salary, bonus_or_other_income, passive_income,
            fixed_expenses, variable_expense_estimate,
            emergency_fund_target_months, fire_target_monthly_spend,
            fire_expected_return, fire_inflation_rate, fire_current_age, fire_target_age
        ) VALUES (1, 65000, 5000, 2000, 18000, 16000, 6, 35000, 7.0, 2.5, 29, 50)
        """)
        
    conn.commit()
    conn.close()

# Sample data seed
def seed_sample_data_if_empty():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM assets")
    asset_count = c.fetchone()[0]
    
    if asset_count == 0:
        sample_assets = [
            # กองทุนรวม (Mutual Funds)
            ("SCBAM Global Equity (SCBWORLD)", "กองทุนรวม (Mutual Funds)", 185000, 165000, 25.0, 7000, 8.0, "SCB Easy", "DCA รายเดือน"),
            ("KF-HEALTH RMF", "กองทุนรวม (Mutual Funds)", 120000, 115000, 15.0, 4000, 6.5, "Krungsri", "ลดหย่อนภาษี"),
            
            # หุ้น (Stocks)
            ("Thai Dividend Stocks (BDMS, PTT)", "หุ้น (Stocks)", 240000, 220000, 25.0, 5000, 7.0, "InnovestX", "เน้นรับเงินปันผล"),
            ("US Tech ETF (QQQ / VOO)", "หุ้น (Stocks)", 195000, 160000, 20.0, 6000, 10.0, "Dime / IBKR", "หุ้นเติบโตระยะยาว"),
            
            # คริปโตเคอร์เรนซี (Crypto)
            ("Bitcoin (BTC)", "คริปโต (Crypto)", 95000, 75000, 8.0, 2500, 12.0, "Bitkub / Binance", "HODL ระยะยาว"),
            ("Ethereum (ETH)", "คริปโต (Crypto)", 45000, 42000, 4.0, 1500, 10.0, "Binance", "Staking รับผลตอบแทน"),
            
            # เงินสด & สภาพคล่องฉุกเฉิน (Cash / Emergency Fund)
            ("เงินฝากดอกเบี้ยสูง Dime/Keep/KKP", "เงินสด/ฉุกเฉิน (Cash & Emergency)", 150000, 150000, 15.0, 2000, 1.8, "Dime Save", "เงินสำรองฉุกเฉิน 4-5 เดือน"),
            
            # สินทรัพย์อื่นๆ / ทองคำ (Others / Gold)
            ("ทองคำแท่ง (Gold)", "ทองคำ/อื่นๆ (Gold & Others)", 80000, 68000, 8.0, 1000, 5.0, "MTS Gold", "สินทรัพย์ปลอดภัย")
        ]
        c.executemany("""
        INSERT INTO assets (name, category, current_value, cost_basis, target_allocation, monthly_dca, expected_roi, platform_or_broker, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_assets)

        sample_liabilities = [
            ("ผ่อนคอนโด / บ้าน", "สินเชื่อที่อยู่อาศัย (Mortgage)", 1450000, 9500, 3.8, "หักบัญชีอัตโนมัติ"),
            ("ผ่อนรถยนต์", "สินเชื่อยานพาหนะ (Auto Loan)", 210000, 5500, 2.4, "เหลืออีก 38 งวด"),
        ]
        c.executemany("""
        INSERT INTO liabilities (name, category, total_balance, monthly_payment, interest_rate, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """, sample_liabilities)

        conn.commit()

    # Seed expense items if empty
    c.execute("SELECT COUNT(*) FROM expense_items")
    exp_count = c.fetchone()[0]
    if exp_count == 0:
        sample_expense_items = [
            ("ค่างวดคอนโด/บ้าน", "🏠 ที่อยู่อาศัย (Housing)", "คงที่ (Fixed)", 9500, "หักบัญชีเงินเดือนอัตโนมัติ"),
            ("ค่างวดผ่อนรถยนต์", "🚗 ยานพาหนะ/เดินทาง (Transport)", "คงที่ (Fixed)", 5500, "ผ่อนเดือนละ 5,500"),
            ("ประกันสุขภาพ & ประกันชีวิต", "🛡️ ประกัน/สุขภาพ (Insurance)", "คงที่ (Fixed)", 3000, "เฉลี่ยต่อเดือน"),
            ("ค่าน้ำ ค่าไฟ ค่าส่วนกลาง", "🏠 ที่อยู่อาศัย (Housing)", "ผันแปร (Variable)", 2200, "เฉลี่ยตามฤดูกาล"),
            ("ค่าโทรศัพท์ & อินเทอร์เน็ตบ้าน", "📱 สื่อสาร/บริการ (Utilities)", "คงที่ (Fixed)", 1200, "รายเดือนพร้อมเน็ต 5G"),
            ("ค่าอาหาร & เครื่องดื่มประจำวัน", "🍲 อาหาร/เครื่องดื่ม (Food & Dining)", "ผันแปร (Variable)", 9000, "ประมาณ 300 บาท/วัน"),
            ("ของใช้ส่วนตัว & ซูเปอร์มาร์เก็ต", "🛒 ของใช้ในบ้าน (Groceries)", "ผันแปร (Variable)", 2800, "ซื้อของเข้าบ้านรายสัปดาห์"),
            ("สังสรรค์ ท่องเที่ยว ช้อปปิ้ง", "🛍️ ไลฟ์สไตล์ & ท่องเที่ยว (Lifestyle)", "ผันแปร (Variable)", 4000, "หมวดงบตามใจ")
        ]
        c.executemany("""
        INSERT INTO expense_items (name, category, expense_type, estimated_amount, notes)
        VALUES (?, ?, ?, ?, ?)
        """, sample_expense_items)
        conn.commit()

    # Seed income items if empty
    c.execute("SELECT COUNT(*) FROM income_items")
    inc_count = c.fetchone()[0]
    if inc_count == 0:
        sample_income_items = [
            ("เงินเดือนประจำ (Salary)", "💼 รายได้หลักประจำ (Salary/Job)", "ประจำ (Active / Fixed)", 65000, "รับสุทธิหลังหักภาษี/ปกส."),
            ("รายได้เสริม / ฟรีแลนซ์", "💻 ฟรีแลนซ์/งานเสริม (Side Hustle)", "ผันแปร/เสริม (Passive / Variable)", 5000, "รับงานอิสระเฉลี่ยต่อเดือน"),
            ("เงินปันผล & ดอกเบี้ย", "📈 เงินปันผล/ดอกเบี้ย (Dividend/Interest)", "ผันแปร/เสริม (Passive / Variable)", 2000, "หุ้นปันผล + ดอกเบี้ยเงินฝาก Dime")
        ]
        c.executemany("""
        INSERT INTO income_items (name, category, income_type, estimated_amount, notes)
        VALUES (?, ?, ?, ?, ?)
        """, sample_income_items)
        conn.commit()

    # Seed custom categories if empty
    c.execute("SELECT COUNT(*) FROM custom_categories")
    cat_count = c.fetchone()[0]
    if cat_count == 0:
        default_cats = [
            # Income
            ("income", "💼 รายได้หลักประจำ (Salary/Job)"),
            ("income", "💻 ฟรีแลนซ์/งานเสริม (Side Hustle)"),
            ("income", "📈 เงินปันผล/ดอกเบี้ย (Dividend/Interest)"),
            ("income", "🏢 ค่าเช่า/อสังหาริมทรัพย์ (Rental)"),
            ("income", "🛍️ ธุรกิจส่วนตัว/ค้าขาย (Business/Commerce)"),
            ("income", "🎁 โบนัส/อื่นๆ (Bonus/Other)"),
            # Expense
            ("expense", "🏠 ที่อยู่อาศัย (Housing)"),
            ("expense", "🚗 ยานพาหนะ/เดินทาง (Transport)"),
            ("expense", "🍲 อาหาร/เครื่องดื่ม (Food & Dining)"),
            ("expense", "🛒 ของใช้ในบ้าน (Groceries)"),
            ("expense", "🛡️ ประกัน/สุขภาพ (Insurance)"),
            ("expense", "📱 สื่อสาร/บริการ (Utilities)"),
            ("expense", "🛍️ ไลฟ์สไตล์ & ท่องเที่ยว (Lifestyle)"),
            ("expense", "📚 พัฒนาตัวเอง & อื่นๆ (Education/Other)"),
            # Asset
            ("asset", "กองทุนรวม (Mutual Funds)"),
            ("asset", "หุ้น (Stocks)"),
            ("asset", "คริปโต (Crypto)"),
            ("asset", "เงินสด/ฉุกเฉิน (Cash & Emergency)"),
            ("asset", "ทองคำ/อื่นๆ (Gold & Others)"),
            # Liability
            ("liability", "สินเชื่อที่อยู่อาศัย (Mortgage)"),
            ("liability", "สินเชื่อยานพาหนะ (Auto Loan)"),
            ("liability", "บัตรเครดิต/สินเชื่อบุคคล (Credit Card / Personal)"),
            ("liability", "กู้ยืมเพื่อการศึกษา (Student Loan)"),
            ("liability", "หนี้สินอื่นๆ (Other Debts)"),
        ]
        c.executemany("""
        INSERT OR IGNORE INTO custom_categories (cat_type, name)
        VALUES (?, ?)
        """, default_cats)
        conn.commit()

    conn.close()

# Asset CRUD
def get_all_assets() -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM assets ORDER BY category, current_value DESC")
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

def add_asset(data: Dict[str, Any]):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO assets (name, category, current_value, cost_basis, target_allocation, monthly_dca, expected_roi, platform_or_broker, notes, asset_type)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        safe_str(data.get("name")),
        safe_str(data.get("category"), "อื่น ๆ"),
        safe_float(data.get("current_value"), 0.0),
        safe_float(data.get("cost_basis"), 0.0),
        safe_float(data.get("target_allocation"), 0.0),
        safe_float(data.get("monthly_dca"), 0.0),
        safe_float(data.get("expected_roi"), 6.0),
        safe_str(data.get("platform_or_broker"), ""),
        safe_str(data.get("notes"), ""),
        safe_str(data.get("asset_type"), "investment")
    ))
    conn.commit()
    conn.close()

def update_asset(asset_id: int, data: Dict[str, Any]):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    UPDATE assets SET
        name = ?,
        category = ?,
        current_value = ?,
        cost_basis = ?,
        target_allocation = ?,
        monthly_dca = ?,
        expected_roi = ?,
        platform_or_broker = ?,
        notes = ?,
        asset_type = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (
        safe_str(data.get("name")),
        safe_str(data.get("category"), "อื่น ๆ"),
        safe_float(data.get("current_value"), 0.0),
        safe_float(data.get("cost_basis"), 0.0),
        safe_float(data.get("target_allocation"), 0.0),
        safe_float(data.get("monthly_dca"), 0.0),
        safe_float(data.get("expected_roi"), 6.0),
        safe_str(data.get("platform_or_broker"), ""),
        safe_str(data.get("notes"), ""),
        safe_str(data.get("asset_type"), "investment"),
        asset_id
    ))
    conn.commit()
    conn.close()

def delete_asset(asset_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
    conn.commit()
    conn.close()

# Liability CRUD
def get_all_liabilities() -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM liabilities ORDER BY total_balance DESC")
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

def add_liability(data: Dict[str, Any]):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO liabilities (name, category, total_balance, monthly_payment, interest_rate, notes)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        safe_str(data.get("name")),
        safe_str(data.get("category"), "อื่น ๆ"),
        safe_float(data.get("total_balance"), 0.0),
        safe_float(data.get("monthly_payment"), 0.0),
        safe_float(data.get("interest_rate"), 0.0),
        safe_str(data.get("notes"), "")
    ))
    conn.commit()
    conn.close()

def update_liability(liability_id: int, data: Dict[str, Any]):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    UPDATE liabilities SET
        name = ?,
        category = ?,
        total_balance = ?,
        monthly_payment = ?,
        interest_rate = ?,
        notes = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (
        safe_str(data.get("name")),
        safe_str(data.get("category"), "อื่น ๆ"),
        safe_float(data.get("total_balance"), 0.0),
        safe_float(data.get("monthly_payment"), 0.0),
        safe_float(data.get("interest_rate"), 0.0),
        safe_str(data.get("notes"), ""),
        liability_id
    ))
    conn.commit()
    conn.close()

def delete_liability(liability_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM liabilities WHERE id = ?", (liability_id,))
    conn.commit()
    conn.close()

# Monthly Profile
def get_monthly_profile() -> Dict[str, Any]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM monthly_profile WHERE id = 1")
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {}

def update_monthly_profile(data: Dict[str, Any]):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    UPDATE monthly_profile SET
        salary = ?,
        bonus_or_other_income = ?,
        passive_income = ?,
        fixed_expenses = ?,
        variable_expense_estimate = ?,
        emergency_fund_target_months = ?,
        fire_target_monthly_spend = ?,
        fire_expected_return = ?,
        fire_inflation_rate = ?,
        fire_current_age = ?,
        fire_target_age = ?,
        fire_monthly_dca = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = 1
    """, (
        safe_float(data.get("salary"), 50000.0),
        safe_float(data.get("bonus_or_other_income"), 0.0),
        safe_float(data.get("passive_income"), 0.0),
        safe_float(data.get("fixed_expenses"), 15000.0),
        safe_float(data.get("variable_expense_estimate"), 15000.0),
        int(safe_float(data.get("emergency_fund_target_months"), 6)),
        safe_float(data.get("fire_target_monthly_spend"), 30000.0),
        safe_float(data.get("fire_expected_return"), 7.0),
        safe_float(data.get("fire_inflation_rate"), 2.5),
        int(safe_float(data.get("fire_current_age"), 30)),
        int(safe_float(data.get("fire_target_age"), 50)),
        safe_float(data.get("fire_monthly_dca"), 0.0)
    ))
    conn.commit()
    conn.close()

# Expense Items CRUD
def get_all_expense_items() -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM expense_items ORDER BY expense_type, category, estimated_amount DESC")
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

def add_expense_item(data: Dict[str, Any]):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO expense_items (name, category, expense_type, estimated_amount, notes)
    VALUES (?, ?, ?, ?, ?)
    """, (
        safe_str(data.get("name")),
        safe_str(data.get("category"), "อื่น ๆ"),
        safe_str(data.get("expense_type"), "คงที่ (Fixed)"),
        safe_float(data.get("estimated_amount"), 0.0),
        safe_str(data.get("notes"), "")
    ))
    conn.commit()
    conn.close()

def update_expense_item(item_id: int, data: Dict[str, Any]):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    UPDATE expense_items SET
        name = ?,
        category = ?,
        expense_type = ?,
        estimated_amount = ?,
        notes = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (
        safe_str(data.get("name")),
        safe_str(data.get("category"), "อื่น ๆ"),
        safe_str(data.get("expense_type"), "คงที่ (Fixed)"),
        safe_float(data.get("estimated_amount"), 0.0),
        safe_str(data.get("notes"), ""),
        item_id
    ))
    conn.commit()
    conn.close()

def delete_expense_item(item_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM expense_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

# Income Items CRUD
def get_all_income_items() -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM income_items ORDER BY income_type, category, estimated_amount DESC")
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

def add_income_item(data: Dict[str, Any]):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO income_items (name, category, income_type, estimated_amount, notes)
    VALUES (?, ?, ?, ?, ?)
    """, (
        safe_str(data.get("name")),
        safe_str(data.get("category"), "อื่น ๆ"),
        safe_str(data.get("income_type"), "งานประจำ (Active)"),
        safe_float(data.get("estimated_amount"), 0.0),
        safe_str(data.get("notes"), "")
    ))
    conn.commit()
    conn.close()

def update_income_item(item_id: int, data: Dict[str, Any]):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    UPDATE income_items SET
        name = ?,
        category = ?,
        income_type = ?,
        estimated_amount = ?,
        notes = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (
        safe_str(data.get("name")),
        safe_str(data.get("category"), "อื่น ๆ"),
        safe_str(data.get("income_type"), "งานประจำ (Active)"),
        safe_float(data.get("estimated_amount"), 0.0),
        safe_str(data.get("notes"), ""),
        item_id
    ))
    conn.commit()
    conn.close()

def delete_income_item(item_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM income_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

# Dynamic Category CRUD
def get_categories(cat_type: str) -> List[str]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM custom_categories WHERE cat_type = ? ORDER BY id ASC", (cat_type,))
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    if not rows:
        # Fallback defaults if empty
        defaults = {
            "income": [
                "💼 รายได้หลักประจำ (Salary/Job)",
                "💻 ฟรีแลนซ์/งานเสริม (Side Hustle)",
                "📈 เงินปันผล/ดอกเบี้ย (Dividend/Interest)",
                "🏢 ค่าเช่า/อสังหาริมทรัพย์ (Rental)",
                "🛍️ ธุรกิจส่วนตัว/ค้าขาย (Business/Commerce)",
                "🎁 โบนัส/อื่นๆ (Bonus/Other)"
            ],
            "expense": [
                "🏠 ที่อยู่อาศัย (Housing)",
                "🚗 ยานพาหนะ/เดินทาง (Transport)",
                "🍲 อาหาร/เครื่องดื่ม (Food & Dining)",
                "🛒 ของใช้ในบ้าน (Groceries)",
                "🛡️ ประกัน/สุขภาพ (Insurance)",
                "📱 สื่อสาร/บริการ (Utilities)",
                "🛍️ ไลฟ์สไตล์ & ท่องเที่ยว (Lifestyle)",
                "📚 พัฒนาตัวเอง & อื่นๆ (Education/Other)"
            ],
            "asset": [
                "กองทุนรวม (Mutual Funds)",
                "หุ้น (Stocks)",
                "คริปโต (Crypto)",
                "เงินสด/ฉุกเฉิน (Cash & Emergency)",
                "ทองคำ/อื่นๆ (Gold & Others)"
            ],
            "fixed_asset": [
                "🏠 บ้านเดี่ยว / ทาวน์โฮม (House)",
                "🏢 คอนโดมิเนียม (Condo)",
                "🏞️ ที่ดินเปล่า (Land)",
                "🚗 ยานพาหนะ / รถยนต์ (Vehicle)",
                "🏭 อาคารพาณิชย์ / สิ่งปลูกสร้าง (Commercial)",
                "💎 ของสะสมมีค่า (Collectibles)",
                "📦 สินทรัพย์ถาวรอื่น ๆ (Other Fixed Asset)"
            ],
            "liability": [
                "สินเชื่อที่อยู่อาศัย (Mortgage)",
                "สินเชื่อยานพาหนะ (Auto Loan)",
                "บัตรเครดิต/สินเชื่อบุคคล (Credit Card / Personal)",
                "กู้ยืมเพื่อการศึกษา (Student Loan)",
                "หนี้สินอื่นๆ (Other Debts)"
            ]
        }
        return defaults.get(cat_type, [])
    return rows

def add_category(cat_type: str, name: str) -> bool:
    if not name or not name.strip():
        return False
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO custom_categories (cat_type, name) VALUES (?, ?)", (cat_type, name.strip()))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def delete_category(cat_type: str, name: str) -> bool:
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM custom_categories WHERE cat_type = ? AND name = ?", (cat_type, name))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def reset_default_categories(cat_type: Optional[str] = None):
    conn = get_connection()
    c = conn.cursor()
    if cat_type:
        c.execute("DELETE FROM custom_categories WHERE cat_type = ?", (cat_type,))
    else:
        c.execute("DELETE FROM custom_categories")
        
    default_cats = [
        # Income
        ("income", "💼 รายได้หลักประจำ (Salary/Job)"),
        ("income", "💻 ฟรีแลนซ์/งานเสริม (Side Hustle)"),
        ("income", "📈 เงินปันผล/ดอกเบี้ย (Dividend/Interest)"),
        ("income", "🏢 ค่าเช่า/อสังหาริมทรัพย์ (Rental)"),
        ("income", "🛍️ ธุรกิจส่วนตัว/ค้าขาย (Business/Commerce)"),
        ("income", "🎁 โบนัส/อื่นๆ (Bonus/Other)"),
        # Expense
        ("expense", "🏠 ที่อยู่อาศัย (Housing)"),
        ("expense", "🚗 ยานพาหนะ/เดินทาง (Transport)"),
        ("expense", "🍲 อาหาร/เครื่องดื่ม (Food & Dining)"),
        ("expense", "🛒 ของใช้ในบ้าน (Groceries)"),
        ("expense", "🛡️ ประกัน/สุขภาพ (Insurance)"),
        ("expense", "📱 สื่อสาร/บริการ (Utilities)"),
        ("expense", "🛍️ ไลฟ์สไตล์ & ท่องเที่ยว (Lifestyle)"),
        ("expense", "📚 พัฒนาตัวเอง & อื่นๆ (Education/Other)"),
        # Asset
        ("asset", "กองทุนรวม (Mutual Funds)"),
        ("asset", "หุ้น (Stocks)"),
        ("asset", "คริปโต (Crypto)"),
        ("asset", "เงินสด/ฉุกเฉิน (Cash & Emergency)"),
        ("asset", "ทองคำ/อื่นๆ (Gold & Others)"),
        # Fixed Asset (Real Estate & Fixed)
        ("fixed_asset", "🏠 บ้านเดี่ยว / ทาวน์โฮม (House)"),
        ("fixed_asset", "🏢 คอนโดมิเนียม (Condo)"),
        ("fixed_asset", "🏞️ ที่ดินเปล่า (Land)"),
        ("fixed_asset", "🚗 ยานพาหนะ / รถยนต์ (Vehicle)"),
        ("fixed_asset", "🏭 อาคารพาณิชย์ / สิ่งปลูกสร้าง (Commercial)"),
        ("fixed_asset", "💎 ของสะสมมีค่า (Collectibles)"),
        ("fixed_asset", "📦 สินทรัพย์ถาวรอื่น ๆ (Other Fixed Asset)"),
        # Liability
        ("liability", "สินเชื่อที่อยู่อาศัย (Mortgage)"),
        ("liability", "สินเชื่อยานพาหนะ (Auto Loan)"),
        ("liability", "บัตรเครดิต/สินเชื่อบุคคล (Credit Card / Personal)"),
        ("liability", "กู้ยืมเพื่อการศึกษา (Student Loan)"),
        ("liability", "หนี้สินอื่นๆ (Other Debts)"),
    ]
    if cat_type:
        default_cats = [item for item in default_cats if item[0] == cat_type]

    c.executemany("INSERT OR IGNORE INTO custom_categories (cat_type, name) VALUES (?, ?)", default_cats)
    conn.commit()
    conn.close()

# Snapshots
def get_all_snapshots() -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM monthly_snapshots ORDER BY snapshot_month ASC")
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

def save_snapshot(data: Dict[str, Any]):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT OR REPLACE INTO monthly_snapshots 
    (snapshot_month, income, expenses, savings_invested, total_assets, total_debts, net_worth, notes)
    VALUES (:snapshot_month, :income, :expenses, :savings_invested, :total_assets, :total_debts, :net_worth, :notes)
    """, data)
    conn.commit()
    conn.close()

def delete_snapshot(snapshot_month: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM monthly_snapshots WHERE snapshot_month = ?", (snapshot_month,))
    conn.commit()
    conn.close()

# Export & Import
def export_all_data() -> str:
    data = {
        "monthly_profile": get_monthly_profile(),
        "categories": {
            "income": get_categories("income"),
            "expense": get_categories("expense"),
            "asset": get_categories("asset"),
            "liability": get_categories("liability")
        },
        "income_items": get_all_income_items(),
        "expense_items": get_all_expense_items(),
        "assets": get_all_assets(),
        "liabilities": get_all_liabilities(),
        "snapshots": get_all_snapshots(),
        "exported_at": datetime.now().isoformat()
    }
    return json.dumps(data, ensure_ascii=False, indent=2)

def import_all_data(json_str: str) -> bool:
    try:
        data = json.loads(json_str)
        conn = get_connection()
        c = conn.cursor()
        
        if "monthly_profile" in data and data["monthly_profile"]:
            mp = data["monthly_profile"]
            c.execute("""
            INSERT OR REPLACE INTO monthly_profile (
                id, salary, bonus_or_other_income, passive_income,
                fixed_expenses, variable_expense_estimate,
                emergency_fund_target_months, fire_target_monthly_spend,
                fire_expected_return, fire_inflation_rate, fire_current_age, fire_target_age
            ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                safe_float(mp.get("salary"), 50000),
                safe_float(mp.get("bonus_or_other_income"), 0),
                safe_float(mp.get("passive_income"), 0),
                safe_float(mp.get("fixed_expenses"), 15000),
                safe_float(mp.get("variable_expense_estimate"), 15000),
                int(safe_float(mp.get("emergency_fund_target_months"), 6)),
                safe_float(mp.get("fire_target_monthly_spend"), 30000),
                safe_float(mp.get("fire_expected_return"), 7.0),
                safe_float(mp.get("fire_inflation_rate"), 2.5),
                int(safe_float(mp.get("fire_current_age"), 30)),
                int(safe_float(mp.get("fire_target_age"), 50))
            ))

        if "categories" in data:
            c.execute("DELETE FROM custom_categories")
            for c_type, cat_list in data["categories"].items():
                for c_name in cat_list:
                    c.execute("INSERT OR IGNORE INTO custom_categories (cat_type, name) VALUES (?, ?)", (safe_str(c_type), safe_str(c_name)))

        if "income_items" in data:
            c.execute("DELETE FROM income_items")
            for i in data["income_items"]:
                c.execute("""
                INSERT INTO income_items (name, category, income_type, estimated_amount, notes)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    safe_str(i.get("name")),
                    safe_str(i.get("category"), "อื่น ๆ"),
                    safe_str(i.get("income_type"), "งานประจำ (Active)"),
                    safe_float(i.get("estimated_amount"), 0.0),
                    safe_str(i.get("notes"), "")
                ))

        if "expense_items" in data:
            c.execute("DELETE FROM expense_items")
            for e in data["expense_items"]:
                c.execute("""
                INSERT INTO expense_items (name, category, expense_type, estimated_amount, notes)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    safe_str(e.get("name")),
                    safe_str(e.get("category"), "อื่น ๆ"),
                    safe_str(e.get("expense_type"), "คงที่ (Fixed)"),
                    safe_float(e.get("estimated_amount"), 0.0),
                    safe_str(e.get("notes"), "")
                ))
            
        if "assets" in data:
            c.execute("DELETE FROM assets")
            for a in data["assets"]:
                c.execute("""
                INSERT INTO assets (name, category, current_value, cost_basis, target_allocation, monthly_dca, expected_roi, platform_or_broker, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    safe_str(a.get("name")),
                    safe_str(a.get("category"), "อื่น ๆ"),
                    safe_float(a.get("current_value"), 0.0),
                    safe_float(a.get("cost_basis"), 0.0),
                    safe_float(a.get("target_allocation"), 0.0),
                    safe_float(a.get("monthly_dca"), 0.0),
                    safe_float(a.get("expected_roi"), 6.0),
                    safe_str(a.get("platform_or_broker"), ""),
                    safe_str(a.get("notes"), "")
                ))
                
        if "liabilities" in data:
            c.execute("DELETE FROM liabilities")
            for l in data["liabilities"]:
                c.execute("""
                INSERT INTO liabilities (name, category, total_balance, monthly_payment, interest_rate, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    safe_str(l.get("name")),
                    safe_str(l.get("category"), "อื่น ๆ"),
                    safe_float(l.get("total_balance"), 0.0),
                    safe_float(l.get("monthly_payment"), 0.0),
                    safe_float(l.get("interest_rate"), 0.0),
                    safe_str(l.get("notes"), "")
                ))
                
        if "snapshots" in data:
            c.execute("DELETE FROM monthly_snapshots")
            for s in data["snapshots"]:
                c.execute("""
                INSERT INTO monthly_snapshots (snapshot_month, income, expenses, savings_invested, total_assets, total_debts, net_worth, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    safe_str(s.get("snapshot_month")),
                    safe_float(s.get("income"), 0.0),
                    safe_float(s.get("expenses"), 0.0),
                    safe_float(s.get("savings_invested"), 0.0),
                    safe_float(s.get("total_assets"), 0.0),
                    safe_float(s.get("total_debts"), 0.0),
                    safe_float(s.get("net_worth"), 0.0),
                    safe_str(s.get("notes"), "")
                ))
                
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Import error:", e)
        return False
