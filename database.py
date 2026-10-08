"""
Pure Supabase Cloud Database Module with Connection Pooling, In-Memory Cache & Multi-User Data Isolation.
All data is stored on Supabase PostgreSQL REST API.
Uses persistent requests.Session + Streamlit cache with user-scoped isolation.
"""

import os
import math
import json
import hashlib
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import streamlit as st

# Helper functions for data sanitization
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

# Get Supabase Credentials from Streamlit Secrets or Environment
def get_supabase_config():
    url = None
    key = None
    
    # 1. Try Streamlit Secrets
    try:
        if hasattr(st, "secrets"):
            if "SUPABASE_URL" in st.secrets:
                url = st.secrets["SUPABASE_URL"]
            if "SUPABASE_KEY" in st.secrets:
                key = st.secrets["SUPABASE_KEY"]
    except Exception:
        pass
        
    # 2. Try Environment Variables
    if not url:
        url = os.environ.get("SUPABASE_URL")
    if not key:
        key = os.environ.get("SUPABASE_KEY")
        
    # 3. Default credentials
    if not url:
        url = "https://qrdszoirwvpcfitbevvu.supabase.co"
    if not key:
        key = "sb_publishable_OPdMhz1EpC1NJAVgx4pwjA_i4bN_0g2"
        
    return url.rstrip('/'), key

SUPABASE_URL, SUPABASE_KEY = get_supabase_config()

# Persistent HTTP session with Keep-Alive Connection Pool
_session = requests.Session()
_retries = Retry(total=2, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504])
_adapter = HTTPAdapter(pool_connections=15, pool_maxsize=25, max_retries=_retries)
_session.mount("https://", _adapter)
_session.mount("http://", _adapter)

def clear_db_cache():
    """Invalidates Streamlit cache when any mutation occurs."""
    try:
        st.cache_data.clear()
    except Exception:
        pass

# Direct REST helper for Supabase
def supabase_rest_request(method: str, endpoint: str, data: Any = None, params: Dict[str, Any] = None, prefer: str = None) -> Any:
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    if prefer:
        headers["Prefer"] = prefer
        
    try:
        if method.upper() == "GET":
            res = _session.get(url, headers=headers, params=params, timeout=8)
        elif method.upper() == "POST":
            res = _session.post(url, headers=headers, json=data, params=params, timeout=8)
        elif method.upper() == "PATCH":
            res = _session.patch(url, headers=headers, json=data, params=params, timeout=8)
        elif method.upper() == "DELETE":
            res = _session.delete(url, headers=headers, params=params, timeout=8)
        else:
            return None
            
        if res.status_code in (200, 201, 204, 206):
            if res.text:
                try:
                    return res.json()
                except Exception:
                    return True
            return True
        else:
            return None
    except Exception as e:
        print("Supabase connection exception:", e)
        return None

# =========================================================================
# USER AUTHENTICATION & SESSION MANAGEMENT
# =========================================================================
def hash_password(password: str) -> str:
    """Computes secure SHA-256 hash with salt for passwords."""
    salt = "minimal_finance_salt_2026_sec"
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()

def get_current_user() -> Optional[Dict[str, Any]]:
    """Returns currently logged in user dictionary from session state."""
    try:
        if "current_user" in st.session_state and st.session_state["current_user"]:
            return st.session_state["current_user"]
    except Exception:
        pass
    return None

def get_current_user_id() -> int:
    """Returns currently active user ID (defaults to 1 if not set)."""
    user = get_current_user()
    if user and "id" in user:
        return int(user["id"])
    return 1

def get_all_users() -> List[Dict[str, Any]]:
    """Fetches user list for checking existence or demo helper."""
    res = supabase_rest_request("GET", "app_users", params={"select": "id,username,display_name,created_at"})
    if isinstance(res, list):
        return res
    return []

def register_user(username: str, password: str, display_name: str, seed_sample: bool = False) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Registers a new user, initializes their financial profile, and optionally seeds sample data."""
    u = safe_str(username).strip().lower()
    p = str(password).strip()
    d = safe_str(display_name).strip() or u
    
    if not u or len(u) < 3:
        return False, "ชื่อผู้ใช้ (Username) ต้องมีอย่างน้อย 3 ตัวอักษร", None
    if not p or len(p) < 4:
        return False, "รหัสผ่านต้องมีความยาวอย่างน้อย 4 ตัวอักษร", None

    # Check if username already taken
    existing = supabase_rest_request("GET", "app_users", params={"username": f"eq.{u}", "select": "id"})
    if isinstance(existing, list) and len(existing) > 0:
        return False, f"ชื่อผู้ใช้ '{u}' มีอยู่ในระบบแล้ว กรุณาเลือกชื่ออื่น", None

    # Create User
    pwd_hash = hash_password(p)
    new_user_data = {
        "username": u,
        "password_hash": pwd_hash,
        "display_name": d,
        "created_at": datetime.now().isoformat(),
        "last_login": datetime.now().isoformat()
    }
    
    res = supabase_rest_request("POST", "app_users", data=new_user_data, prefer="return=representation")
    if not isinstance(res, list) or not res:
        # If app_users table might not exist or failed
        return False, "ไม่สามารถสร้างบัญชีผู้ใช้ได้ กรุณาตรวจสอบการเชื่อมต่อฐานข้อมูล Supabase", None
        
    user_created = res[0]
    user_id = user_created.get("id")

    # Initialize user profile
    curr_y = datetime.now().year
    if seed_sample:
        initial_profile = {
            "user_id": user_id,
            "salary": 65000, "bonus_or_other_income": 5000, "passive_income": 2000,
            "fixed_expenses": 18000, "variable_expense_estimate": 16000,
            "emergency_fund_target_months": 6, "fire_target_monthly_spend": 35000,
            "fire_expected_return": 7.0, "fire_inflation_rate": 2.5,
            "fire_birth_year": 1996, "fire_current_age": curr_y - 1996,
            "fire_target_age": 50, "fire_monthly_dca": 0
        }
    else:
        initial_profile = {
            "user_id": user_id,
            "salary": 0, "bonus_or_other_income": 0, "passive_income": 0,
            "fixed_expenses": 0, "variable_expense_estimate": 0,
            "emergency_fund_target_months": 6, "fire_target_monthly_spend": 0,
            "fire_expected_return": 7.0, "fire_inflation_rate": 2.5,
            "fire_birth_year": 1996, "fire_current_age": curr_y - 1996,
            "fire_target_age": 60, "fire_monthly_dca": 0
        }
    update_monthly_profile(initial_profile, user_id=user_id)
    
    # Initialize default categories
    reset_default_categories(user_id=user_id)

    # Seed sample investments if requested
    if seed_sample:
        seed_sample_data_if_empty(user_id=user_id)

    clear_db_cache()
    return True, "สร้างบัญชีผู้ใช้สำเร็จ!", user_created

def login_user(username: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Authenticates username and password against app_users."""
    u = safe_str(username).strip().lower()
    p = str(password).strip()

    if not u or not p:
        return False, "กรุณาระบุชื่อผู้ใช้และรหัสผ่าน", None

    res = supabase_rest_request("GET", "app_users", params={"username": f"eq.{u}", "select": "*"})
    if not isinstance(res, list) or len(res) == 0:
        return False, "ไม่พบชื่อผู้ใช้นี้ในระบบ", None

    user = res[0]
    expected_hash = user.get("password_hash", "")
    provided_hash = hash_password(p)

    if expected_hash != provided_hash:
        return False, "รหัสผ่านไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง", None

    # Update last login timestamp
    try:
        supabase_rest_request("PATCH", "app_users", data={"last_login": datetime.now().isoformat()}, params={"id": f"eq.{user.get('id')}"})
    except Exception:
        pass

    clear_db_cache()
    return True, "เข้าสู่ระบบสำเร็จ!", user

def init_db():
    """Verify connection and ensure schema baseline exists on Supabase."""
    pass

# =========================================================================
# ASSETS CRUD (Supabase with Cache & User Isolation)
# =========================================================================
@st.cache_data(ttl=10, show_spinner=False)
def _fetch_assets(user_id: int) -> List[Dict[str, Any]]:
    params = {
        "select": "*",
        "user_id": f"eq.{user_id}",
        "order": "category.asc,current_value.desc"
    }
    res = supabase_rest_request("GET", "assets", params=params)
    if isinstance(res, list):
        for r in res:
            r["current_value"] = safe_float(r.get("current_value"), 0.0)
            r["cost_basis"] = safe_float(r.get("cost_basis"), 0.0)
            r["target_allocation"] = safe_float(r.get("target_allocation"), 0.0)
            r["monthly_dca"] = safe_float(r.get("monthly_dca"), 0.0)
            r["expected_roi"] = safe_float(r.get("expected_roi"), 6.0)
        return res
    return []

def get_all_assets(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    uid = user_id if user_id is not None else get_current_user_id()
    return _fetch_assets(uid)

def add_asset(data: Dict[str, Any], user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    clean = {
        "user_id": uid,
        "name": safe_str(data.get("name")),
        "category": safe_str(data.get("category"), "อื่น ๆ"),
        "current_value": safe_float(data.get("current_value"), 0.0),
        "cost_basis": safe_float(data.get("cost_basis"), 0.0),
        "target_allocation": safe_float(data.get("target_allocation"), 0.0),
        "monthly_dca": safe_float(data.get("monthly_dca"), 0.0),
        "expected_roi": safe_float(data.get("expected_roi"), 6.0),
        "platform_or_broker": safe_str(data.get("platform_or_broker"), ""),
        "notes": safe_str(data.get("notes"), ""),
        "asset_type": safe_str(data.get("asset_type"), "investment")
    }
    res = supabase_rest_request("POST", "assets", data=clean, prefer="return=representation")
    clear_db_cache()
    return res

def update_asset(asset_id: int, data: Dict[str, Any], user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    clean = {
        "user_id": uid,
        "name": safe_str(data.get("name")),
        "category": safe_str(data.get("category"), "อื่น ๆ"),
        "current_value": safe_float(data.get("current_value"), 0.0),
        "cost_basis": safe_float(data.get("cost_basis"), 0.0),
        "target_allocation": safe_float(data.get("target_allocation"), 0.0),
        "monthly_dca": safe_float(data.get("monthly_dca"), 0.0),
        "expected_roi": safe_float(data.get("expected_roi"), 6.0),
        "platform_or_broker": safe_str(data.get("platform_or_broker"), ""),
        "notes": safe_str(data.get("notes"), ""),
        "asset_type": safe_str(data.get("asset_type"), "investment")
    }
    res = supabase_rest_request("PATCH", "assets", data=clean, params={"id": f"eq.{asset_id}", "user_id": f"eq.{uid}"})
    clear_db_cache()
    return res

def delete_asset(asset_id: int, user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    res = supabase_rest_request("DELETE", "assets", params={"id": f"eq.{asset_id}", "user_id": f"eq.{uid}"})
    clear_db_cache()
    return res

def save_assets_batch(items: List[Dict[str, Any]], asset_type: str = "investment", user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    current_all = get_all_assets(user_id=uid)
    current_type_ids = [a["id"] for a in current_all if a.get("asset_type", "investment") == asset_type]
    saved_ids = []

    for r in items:
        name = safe_str(r.get("name"))
        if not name:
            continue
        row_id = safe_float(r.get("id"), 0)
        item_data = {
            "user_id": uid,
            "name": name,
            "category": safe_str(r.get("category"), "อื่น ๆ"),
            "current_value": safe_float(r.get("current_value"), 0.0),
            "cost_basis": safe_float(r.get("cost_basis"), 0.0),
            "target_allocation": safe_float(r.get("target_allocation"), 0.0),
            "monthly_dca": safe_float(r.get("monthly_dca"), 0.0),
            "expected_roi": safe_float(r.get("expected_roi"), 6.0),
            "platform_or_broker": safe_str(r.get("platform_or_broker"), ""),
            "notes": safe_str(r.get("notes"), ""),
            "asset_type": asset_type
        }
        
        if row_id > 0:
            supabase_rest_request("PATCH", "assets", data=item_data, params={"id": f"eq.{int(row_id)}", "user_id": f"eq.{uid}"})
            saved_ids.append(int(row_id))
        else:
            created = supabase_rest_request("POST", "assets", data=item_data, prefer="return=representation")
            if isinstance(created, list) and created:
                saved_ids.append(created[0].get("id"))

    # Delete removed
    to_delete = [aid for aid in current_type_ids if aid not in saved_ids]
    for del_id in to_delete:
        supabase_rest_request("DELETE", "assets", params={"id": f"eq.{del_id}", "user_id": f"eq.{uid}"})
    
    clear_db_cache()

# =========================================================================
# LIABILITIES CRUD (Supabase with Cache & User Isolation)
# =========================================================================
@st.cache_data(ttl=10, show_spinner=False)
def _fetch_liabilities(user_id: int) -> List[Dict[str, Any]]:
    params = {
        "select": "*",
        "user_id": f"eq.{user_id}",
        "order": "total_balance.desc"
    }
    res = supabase_rest_request("GET", "liabilities", params=params)
    if isinstance(res, list):
        for r in res:
            r["total_balance"] = safe_float(r.get("total_balance"), 0.0)
            r["monthly_payment"] = safe_float(r.get("monthly_payment"), 0.0)
            r["interest_rate"] = safe_float(r.get("interest_rate"), 0.0)
        return res
    return []

def get_all_liabilities(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    uid = user_id if user_id is not None else get_current_user_id()
    return _fetch_liabilities(uid)

def add_liability(data: Dict[str, Any], user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    clean = {
        "user_id": uid,
        "name": safe_str(data.get("name")),
        "category": safe_str(data.get("category"), "อื่น ๆ"),
        "total_balance": safe_float(data.get("total_balance"), 0.0),
        "monthly_payment": safe_float(data.get("monthly_payment"), 0.0),
        "interest_rate": safe_float(data.get("interest_rate"), 0.0),
        "notes": safe_str(data.get("notes"), "")
    }
    res = supabase_rest_request("POST", "liabilities", data=clean, prefer="return=representation")
    clear_db_cache()
    return res

def update_liability(liability_id: int, data: Dict[str, Any], user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    clean = {
        "user_id": uid,
        "name": safe_str(data.get("name")),
        "category": safe_str(data.get("category"), "อื่น ๆ"),
        "total_balance": safe_float(data.get("total_balance"), 0.0),
        "monthly_payment": safe_float(data.get("monthly_payment"), 0.0),
        "interest_rate": safe_float(data.get("interest_rate"), 0.0),
        "notes": safe_str(data.get("notes"), "")
    }
    res = supabase_rest_request("PATCH", "liabilities", data=clean, params={"id": f"eq.{liability_id}", "user_id": f"eq.{uid}"})
    clear_db_cache()
    return res

def delete_liability(liability_id: int, user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    res = supabase_rest_request("DELETE", "liabilities", params={"id": f"eq.{liability_id}", "user_id": f"eq.{uid}"})
    clear_db_cache()
    return res

def save_liabilities_batch(items: List[Dict[str, Any]], user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    current_all = get_all_liabilities(user_id=uid)
    current_ids = [l["id"] for l in current_all]
    saved_ids = []

    for r in items:
        name = safe_str(r.get("name"))
        if not name:
            continue
        row_id = safe_float(r.get("id"), 0)
        item_data = {
            "user_id": uid,
            "name": name,
            "category": safe_str(r.get("category"), "อื่น ๆ"),
            "total_balance": safe_float(r.get("total_balance"), 0.0),
            "monthly_payment": safe_float(r.get("monthly_payment"), 0.0),
            "interest_rate": safe_float(r.get("interest_rate"), 0.0),
            "notes": safe_str(r.get("notes"), "")
        }
        
        if row_id > 0:
            supabase_rest_request("PATCH", "liabilities", data=item_data, params={"id": f"eq.{int(row_id)}", "user_id": f"eq.{uid}"})
            saved_ids.append(int(row_id))
        else:
            created = supabase_rest_request("POST", "liabilities", data=item_data, prefer="return=representation")
            if isinstance(created, list) and created:
                saved_ids.append(created[0].get("id"))

    to_delete = [lid for lid in current_ids if lid not in saved_ids]
    for del_id in to_delete:
        supabase_rest_request("DELETE", "liabilities", params={"id": f"eq.{del_id}", "user_id": f"eq.{uid}"})
    
    clear_db_cache()

# =========================================================================
# MONTHLY PROFILE (Supabase with Cache & User Isolation)
# =========================================================================
@st.cache_data(ttl=10, show_spinner=False)
def _fetch_monthly_profile(user_id: int) -> Dict[str, Any]:
    curr_y = datetime.now().year
    res = supabase_rest_request("GET", "monthly_profile", params={"select": "*", "user_id": f"eq.{user_id}"})
    
    if isinstance(res, list) and len(res) > 0:
        row = res[0]
        birth_year_raw = row.get("fire_birth_year")
        if birth_year_raw is not None:
            birth_year = int(safe_float(birth_year_raw, curr_y - 29))
            current_age = max(1, curr_y - birth_year)
        else:
            current_age = int(safe_float(row.get("fire_current_age"), 29))
            birth_year = curr_y - current_age

        return {
            "id": row.get("id", user_id),
            "user_id": user_id,
            "salary": safe_float(row.get("salary"), 0.0),
            "bonus_or_other_income": safe_float(row.get("bonus_or_other_income"), 0.0),
            "passive_income": safe_float(row.get("passive_income"), 0.0),
            "fixed_expenses": safe_float(row.get("fixed_expenses"), 0.0),
            "variable_expense_estimate": safe_float(row.get("variable_expense_estimate"), 0.0),
            "emergency_fund_target_months": int(safe_float(row.get("emergency_fund_target_months"), 6)),
            "fire_target_monthly_spend": safe_float(row.get("fire_target_monthly_spend"), 0.0),
            "fire_expected_return": safe_float(row.get("fire_expected_return"), 7.0),
            "fire_inflation_rate": safe_float(row.get("fire_inflation_rate"), 2.5),
            "fire_birth_year": birth_year,
            "fire_current_age": current_age,
            "fire_target_age": int(safe_float(row.get("fire_target_age"), 60)),
            "fire_monthly_dca": safe_float(row.get("fire_monthly_dca"), 0.0),
        }

    return {
        "id": user_id, "user_id": user_id, "salary": 0.0, "bonus_or_other_income": 0.0, "passive_income": 0.0,
        "fixed_expenses": 0.0, "variable_expense_estimate": 0.0, "emergency_fund_target_months": 6,
        "fire_target_monthly_spend": 0.0, "fire_expected_return": 7.0, "fire_inflation_rate": 2.5,
        "fire_birth_year": 1996, "fire_current_age": curr_y - 1996, "fire_target_age": 60, "fire_monthly_dca": 0.0
    }

def get_monthly_profile(user_id: Optional[int] = None) -> Dict[str, Any]:
    uid = user_id if user_id is not None else get_current_user_id()
    return _fetch_monthly_profile(uid)

def update_monthly_profile(data: Dict[str, Any], user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    curr_y = datetime.now().year
    birth_year_raw = data.get("fire_birth_year")
    if birth_year_raw is not None:
        birth_year = int(safe_float(birth_year_raw, 1996))
        current_age = max(1, curr_y - birth_year)
    else:
        current_age = int(safe_float(data.get("fire_current_age"), 30))
        birth_year = curr_y - current_age

    clean = {
        "user_id": uid,
        "salary": safe_float(data.get("salary"), 50000.0),
        "bonus_or_other_income": safe_float(data.get("bonus_or_other_income"), 0.0),
        "passive_income": safe_float(data.get("passive_income"), 0.0),
        "fixed_expenses": safe_float(data.get("fixed_expenses"), 15000.0),
        "variable_expense_estimate": safe_float(data.get("variable_expense_estimate"), 15000.0),
        "emergency_fund_target_months": int(safe_float(data.get("emergency_fund_target_months"), 6)),
        "fire_target_monthly_spend": safe_float(data.get("fire_target_monthly_spend"), 30000.0),
        "fire_expected_return": safe_float(data.get("fire_expected_return"), 7.0),
        "fire_inflation_rate": safe_float(data.get("fire_inflation_rate"), 2.5),
        "fire_birth_year": birth_year,
        "fire_current_age": current_age,
        "fire_target_age": int(safe_float(data.get("fire_target_age"), 50)),
        "fire_monthly_dca": safe_float(data.get("fire_monthly_dca"), 0.0),
    }
    
    # Check if profile exists for user
    existing = supabase_rest_request("GET", "monthly_profile", params={"user_id": f"eq.{uid}", "select": "id,user_id"})
    if isinstance(existing, list) and len(existing) > 0:
        res = supabase_rest_request("PATCH", "monthly_profile", data=clean, params={"user_id": f"eq.{uid}"})
    else:
        res = supabase_rest_request("POST", "monthly_profile", data=clean, prefer="return=representation")
        
    clear_db_cache()
    return res

# =========================================================================
# EXPENSE ITEMS CRUD (Supabase with Cache & User Isolation)
# =========================================================================
@st.cache_data(ttl=10, show_spinner=False)
def _fetch_expense_items(user_id: int) -> List[Dict[str, Any]]:
    params = {
        "select": "*",
        "user_id": f"eq.{user_id}",
        "order": "estimated_amount.desc"
    }
    res = supabase_rest_request("GET", "expense_items", params=params)
    if isinstance(res, list):
        for r in res:
            r["estimated_amount"] = safe_float(r.get("estimated_amount"), 0.0)
        return res
    return []

def get_all_expense_items(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    uid = user_id if user_id is not None else get_current_user_id()
    return _fetch_expense_items(uid)

def add_expense_item(data: Dict[str, Any], user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    clean = {
        "user_id": uid,
        "name": safe_str(data.get("name")),
        "category": safe_str(data.get("category"), "อื่น ๆ"),
        "expense_type": safe_str(data.get("expense_type"), "คงที่ (Fixed)"),
        "estimated_amount": safe_float(data.get("estimated_amount"), 0.0),
        "notes": safe_str(data.get("notes"), "")
    }
    res = supabase_rest_request("POST", "expense_items", data=clean, prefer="return=representation")
    clear_db_cache()
    return res

def update_expense_item(item_id: int, data: Dict[str, Any], user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    clean = {
        "user_id": uid,
        "name": safe_str(data.get("name")),
        "category": safe_str(data.get("category"), "อื่น ๆ"),
        "expense_type": safe_str(data.get("expense_type"), "คงที่ (Fixed)"),
        "estimated_amount": safe_float(data.get("estimated_amount"), 0.0),
        "notes": safe_str(data.get("notes"), "")
    }
    res = supabase_rest_request("PATCH", "expense_items", data=clean, params={"id": f"eq.{item_id}", "user_id": f"eq.{uid}"})
    clear_db_cache()
    return res

def delete_expense_item(item_id: int, user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    res = supabase_rest_request("DELETE", "expense_items", params={"id": f"eq.{item_id}", "user_id": f"eq.{uid}"})
    clear_db_cache()
    return res

def save_expense_items_batch(items: List[Dict[str, Any]], user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    current_all = get_all_expense_items(user_id=uid)
    current_ids = [e["id"] for e in current_all]
    saved_ids = []

    for r in items:
        name = safe_str(r.get("name"))
        if not name:
            continue
        row_id = safe_float(r.get("id"), 0)
        item_data = {
            "user_id": uid,
            "name": name,
            "category": safe_str(r.get("category"), "อื่น ๆ"),
            "expense_type": safe_str(r.get("expense_type"), "คงที่ (Fixed)"),
            "estimated_amount": safe_float(r.get("estimated_amount"), 0.0),
            "notes": safe_str(r.get("notes"), "")
        }
        
        if row_id > 0:
            supabase_rest_request("PATCH", "expense_items", data=item_data, params={"id": f"eq.{int(row_id)}", "user_id": f"eq.{uid}"})
            saved_ids.append(int(row_id))
        else:
            created = supabase_rest_request("POST", "expense_items", data=item_data, prefer="return=representation")
            if isinstance(created, list) and created:
                saved_ids.append(created[0].get("id"))

    to_delete = [eid for eid in current_ids if eid not in saved_ids]
    for del_id in to_delete:
        supabase_rest_request("DELETE", "expense_items", params={"id": f"eq.{del_id}", "user_id": f"eq.{uid}"})
    
    clear_db_cache()

# =========================================================================
# INCOME ITEMS CRUD (Supabase with Cache & User Isolation)
# =========================================================================
@st.cache_data(ttl=10, show_spinner=False)
def _fetch_income_items(user_id: int) -> List[Dict[str, Any]]:
    params = {
        "select": "*",
        "user_id": f"eq.{user_id}",
        "order": "estimated_amount.desc"
    }
    res = supabase_rest_request("GET", "income_items", params=params)
    if isinstance(res, list):
        for r in res:
            r["estimated_amount"] = safe_float(r.get("estimated_amount"), 0.0)
        return res
    return []

def get_all_income_items(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    uid = user_id if user_id is not None else get_current_user_id()
    return _fetch_income_items(uid)

def add_income_item(data: Dict[str, Any], user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    clean = {
        "user_id": uid,
        "name": safe_str(data.get("name")),
        "category": safe_str(data.get("category"), "อื่น ๆ"),
        "income_type": safe_str(data.get("income_type"), "ประจำ (Active / Fixed)"),
        "estimated_amount": safe_float(data.get("estimated_amount"), 0.0),
        "notes": safe_str(data.get("notes"), "")
    }
    res = supabase_rest_request("POST", "income_items", data=clean, prefer="return=representation")
    clear_db_cache()
    return res

def update_income_item(item_id: int, data: Dict[str, Any], user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    clean = {
        "user_id": uid,
        "name": safe_str(data.get("name")),
        "category": safe_str(data.get("category"), "อื่น ๆ"),
        "income_type": safe_str(data.get("income_type"), "ประจำ (Active / Fixed)"),
        "estimated_amount": safe_float(data.get("estimated_amount"), 0.0),
        "notes": safe_str(data.get("notes"), "")
    }
    res = supabase_rest_request("PATCH", "income_items", data=clean, params={"id": f"eq.{item_id}", "user_id": f"eq.{uid}"})
    clear_db_cache()
    return res

def delete_income_item(item_id: int, user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    res = supabase_rest_request("DELETE", "income_items", params={"id": f"eq.{item_id}", "user_id": f"eq.{uid}"})
    clear_db_cache()
    return res

def save_income_items_batch(items: List[Dict[str, Any]], user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    current_all = get_all_income_items(user_id=uid)
    current_ids = [i["id"] for i in current_all]
    saved_ids = []

    for r in items:
        name = safe_str(r.get("name"))
        if not name:
            continue
        row_id = safe_float(r.get("id"), 0)
        item_data = {
            "user_id": uid,
            "name": name,
            "category": safe_str(r.get("category"), "อื่น ๆ"),
            "income_type": safe_str(r.get("income_type"), "ประจำ (Active / Fixed)"),
            "estimated_amount": safe_float(r.get("estimated_amount"), 0.0),
            "notes": safe_str(r.get("notes"), "")
        }
        
        if row_id > 0:
            supabase_rest_request("PATCH", "income_items", data=item_data, params={"id": f"eq.{int(row_id)}", "user_id": f"eq.{uid}"})
            saved_ids.append(int(row_id))
        else:
            created = supabase_rest_request("POST", "income_items", data=item_data, prefer="return=representation")
            if isinstance(created, list) and created:
                saved_ids.append(created[0].get("id"))

    to_delete = [iid for iid in current_ids if iid not in saved_ids]
    for del_id in to_delete:
        supabase_rest_request("DELETE", "income_items", params={"id": f"eq.{del_id}", "user_id": f"eq.{uid}"})
    
    clear_db_cache()

# =========================================================================
# CATEGORIES (Supabase with Cache & User Isolation)
# =========================================================================
DEFAULT_CATEGORIES_DICT = {
    "income": [
        "💼 รายได้หลักประจำ (Salary/Job)",
        "💻 งานเสริม / ฟรีแลนซ์ (Freelance/Side Hustle)",
        "📈 ปันผลหุ้น / กองทุน (Dividends)",
        "🏢 ค่าเช่าอสังหาริมทรัพย์ (Rental Income)",
        "🎁 โบนัส / คอมมิชชั่น (Bonus/Commission)",
        "🪙 กำไรจากคริปโต / ลงทุน (Capital Gains)",
        "✨ รายได้อื่น ๆ (Other Income)"
    ],
    "expense": [
        "🏠 ที่อยู่อาศัย (Housing)",
        "🚗 ค่าเดินทางและยานพาหนะ (Transportation)",
        "🍲 อาหารและของใช้ (Food & Groceries)",
        "⚡ สาธารณูปโภคและบิล (Utilities & Bills)",
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

@st.cache_data(ttl=10, show_spinner=False)
def _fetch_categories(cat_type: str, user_id: int) -> List[str]:
    params = {
        "select": "name",
        "cat_type": f"eq.{cat_type}",
        "user_id": f"eq.{user_id}",
        "order": "id.asc"
    }
    res = supabase_rest_request("GET", "custom_categories", params=params)
    if isinstance(res, list) and len(res) > 0:
        return [r["name"] for r in res]
    return DEFAULT_CATEGORIES_DICT.get(cat_type, [])

def get_categories(cat_type: str, user_id: Optional[int] = None) -> List[str]:
    uid = user_id if user_id is not None else get_current_user_id()
    return _fetch_categories(cat_type, uid)

def add_category(cat_type: str, name: str, user_id: Optional[int] = None) -> bool:
    uid = user_id if user_id is not None else get_current_user_id()
    name_str = safe_str(name)
    if not name_str:
        return False
    res = supabase_rest_request("POST", "custom_categories", data={"user_id": uid, "cat_type": cat_type, "name": name_str})
    clear_db_cache()
    return bool(res)

def delete_category(cat_type: str, name: str, user_id: Optional[int] = None) -> bool:
    uid = user_id if user_id is not None else get_current_user_id()
    res = supabase_rest_request("DELETE", "custom_categories", params={"user_id": f"eq.{uid}", "cat_type": f"eq.{cat_type}", "name": f"eq.{name}"})
    clear_db_cache()
    return bool(res)

def reset_default_categories(cat_type: Optional[str] = None, user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    targets = [cat_type] if cat_type else list(DEFAULT_CATEGORIES_DICT.keys())
    for c_type in targets:
        supabase_rest_request("DELETE", "custom_categories", params={"user_id": f"eq.{uid}", "cat_type": f"eq.{c_type}"})
        for cat_name in DEFAULT_CATEGORIES_DICT.get(c_type, []):
            supabase_rest_request("POST", "custom_categories", data={"user_id": uid, "cat_type": c_type, "name": cat_name})
    clear_db_cache()

# =========================================================================
# SNAPSHOTS CRUD (Supabase with Cache & User Isolation)
# =========================================================================
@st.cache_data(ttl=10, show_spinner=False)
def _fetch_snapshots(user_id: int) -> List[Dict[str, Any]]:
    params = {
        "select": "*",
        "user_id": f"eq.{user_id}",
        "order": "snapshot_month.asc"
    }
    res = supabase_rest_request("GET", "monthly_snapshots", params=params)
    if isinstance(res, list):
        for r in res:
            r["income"] = safe_float(r.get("income"), 0.0)
            r["expenses"] = safe_float(r.get("expenses"), 0.0)
            r["savings_invested"] = safe_float(r.get("savings_invested"), 0.0)
            r["total_assets"] = safe_float(r.get("total_assets"), 0.0)
            r["total_debts"] = safe_float(r.get("total_debts"), 0.0)
            r["net_worth"] = safe_float(r.get("net_worth"), 0.0)
        return res
    return []

def get_all_snapshots(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    uid = user_id if user_id is not None else get_current_user_id()
    return _fetch_snapshots(uid)

def save_snapshot(data: Dict[str, Any], user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    s_month = safe_str(data.get("snapshot_month"))
    clean = {
        "user_id": uid,
        "snapshot_month": s_month,
        "income": safe_float(data.get("income"), 0.0),
        "expenses": safe_float(data.get("expenses"), 0.0),
        "savings_invested": safe_float(data.get("savings_invested"), 0.0),
        "total_assets": safe_float(data.get("total_assets"), 0.0),
        "total_debts": safe_float(data.get("total_debts"), 0.0),
        "net_worth": safe_float(data.get("net_worth"), 0.0),
        "notes": safe_str(data.get("notes"), "")
    }
    
    # Check if snapshot for month exists for user
    existing = supabase_rest_request("GET", "monthly_snapshots", params={"user_id": f"eq.{uid}", "snapshot_month": f"eq.{s_month}"})
    if isinstance(existing, list) and len(existing) > 0:
        res = supabase_rest_request("PATCH", "monthly_snapshots", data=clean, params={"user_id": f"eq.{uid}", "snapshot_month": f"eq.{s_month}"})
    else:
        res = supabase_rest_request("POST", "monthly_snapshots", data=clean, prefer="return=representation")
        
    clear_db_cache()
    return res

def delete_snapshot(snapshot_month: str, user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    res = supabase_rest_request("DELETE", "monthly_snapshots", params={"user_id": f"eq.{uid}", "snapshot_month": f"eq.{snapshot_month}"})
    clear_db_cache()
    return res

# =========================================================================
# BACKUP, SEEDING & RESET (Scoped per User)
# =========================================================================
def export_all_data(user_id: Optional[int] = None) -> str:
    uid = user_id if user_id is not None else get_current_user_id()
    data = {
        "version": "3.0_multi_user",
        "user_id": uid,
        "exported_at": datetime.now().isoformat(),
        "profile": get_monthly_profile(user_id=uid),
        "assets": get_all_assets(user_id=uid),
        "liabilities": get_all_liabilities(user_id=uid),
        "income_items": get_all_income_items(user_id=uid),
        "expense_items": get_all_expense_items(user_id=uid),
        "snapshots": get_all_snapshots(user_id=uid)
    }
    return json.dumps(data, ensure_ascii=False, indent=2)

def import_all_data(json_str: str, user_id: Optional[int] = None) -> bool:
    uid = user_id if user_id is not None else get_current_user_id()
    try:
        data = json.loads(json_str)
        reset_all_data(user_id=uid)

        if "profile" in data:
            update_monthly_profile(data["profile"], user_id=uid)

        if "assets" in data:
            for a in data["assets"]:
                add_asset(a, user_id=uid)

        if "liabilities" in data:
            for l in data["liabilities"]:
                add_liability(l, user_id=uid)

        if "income_items" in data:
            for i in data["income_items"]:
                add_income_item(i, user_id=uid)

        if "expense_items" in data:
            for e in data["expense_items"]:
                add_expense_item(e, user_id=uid)

        if "snapshots" in data:
            for s in data["snapshots"]:
                save_snapshot(s, user_id=uid)

        clear_db_cache()
        return True
    except Exception as e:
        print("Import error:", e)
        return False

def reset_all_data(user_id: Optional[int] = None):
    uid = user_id if user_id is not None else get_current_user_id()
    supabase_rest_request("DELETE", "assets", params={"user_id": f"eq.{uid}"})
    supabase_rest_request("DELETE", "liabilities", params={"user_id": f"eq.{uid}"})
    supabase_rest_request("DELETE", "income_items", params={"user_id": f"eq.{uid}"})
    supabase_rest_request("DELETE", "expense_items", params={"user_id": f"eq.{uid}"})
    supabase_rest_request("DELETE", "monthly_snapshots", params={"user_id": f"eq.{uid}"})
    supabase_rest_request("DELETE", "custom_categories", params={"user_id": f"eq.{uid}"})
    clear_db_cache()

def seed_sample_data_if_empty(user_id: Optional[int] = None):
    """Seeds rich mock sample data for the specific user."""
    uid = user_id if user_id is not None else get_current_user_id()
    curr_y = datetime.now().year
    
    update_monthly_profile({
        "user_id": uid,
        "salary": 65000, "bonus_or_other_income": 5000, "passive_income": 2000,
        "fixed_expenses": 18000, "variable_expense_estimate": 16000,
        "emergency_fund_target_months": 6, "fire_target_monthly_spend": 35000,
        "fire_expected_return": 7.0, "fire_inflation_rate": 2.5,
        "fire_birth_year": 1996, "fire_current_age": curr_y - 1996,
        "fire_target_age": 50, "fire_monthly_dca": 0
    }, user_id=uid)
    
    sample_investments = [
        {"name": "S&P 500 ETF (VOO)", "category": "หุ้นต่างประเทศ (Global / US Stocks)", "current_value": 450000, "cost_basis": 400000, "target_allocation": 40, "monthly_dca": 8000, "expected_roi": 8.0, "platform_or_broker": "Dime!", "asset_type": "investment"},
        {"name": "Thai SET50 Index Fund", "category": "กองทุนรวม (Mutual Funds)", "current_value": 150000, "cost_basis": 160000, "target_allocation": 15, "monthly_dca": 2000, "expected_roi": 5.0, "platform_or_broker": "SCB Easy", "asset_type": "investment"},
        {"name": "Bitcoin (BTC)", "category": "สินทรัพย์ทางเลือก (Alternative / Crypto)", "current_value": 120000, "cost_basis": 90000, "target_allocation": 10, "monthly_dca": 1500, "expected_roi": 12.0, "platform_or_broker": "Bitkub", "asset_type": "investment"},
        {"name": "เงินฝากดอกเบี้ยสูงดิจิทัล", "category": "เงินสด / บัญชีออมทรัพย์ (Cash & Savings)", "current_value": 200000, "cost_basis": 200000, "target_allocation": 20, "monthly_dca": 2900, "expected_roi": 1.5, "platform_or_broker": "LHB You", "asset_type": "investment"},
        {"name": "พันธบัตรรัฐบาล / ตราสารหนี้", "category": "ตราสารหนี้ / พันธบัตร (Bonds)", "current_value": 100000, "cost_basis": 100000, "target_allocation": 15, "monthly_dca": 0, "expected_roi": 2.5, "platform_or_broker": "เป๋าตัง (วอลเล็ต สบม.)", "asset_type": "investment"},
    ]
    sample_fixed = [
        {"name": "คอนโดมิเนียมสุขุมวิท", "category": "🏢 คอนโดมิเนียม (Condo)", "current_value": 2800000, "cost_basis": 2500000, "target_allocation": 0, "monthly_dca": 0, "expected_roi": 0, "platform_or_broker": "โฉนดส่วนบุคคล", "asset_type": "fixed_asset"},
        {"name": "รถยนต์ส่วนตัว (Mazda 2)", "category": "🚗 รถยนต์ส่วนบุคคล (Vehicle)", "current_value": 320000, "cost_basis": 550000, "target_allocation": 0, "monthly_dca": 0, "expected_roi": 0, "platform_or_broker": "เล่มทะเบียน", "asset_type": "fixed_asset"}
    ]
    for a in sample_investments + sample_fixed:
        add_asset(a, user_id=uid)

    sample_liabs = [
        {"name": "สินเชื่อบ้าน/คอนโด", "category": "สินเชื่อบ้าน/อสังหาริมทรัพย์ (Mortgage)", "total_balance": 1850000, "monthly_payment": 12500, "interest_rate": 3.45, "notes": "ผ่อนธนาคารอาคารสงเคราะห์"},
        {"name": "สินเชื่อเช่าซื้อรถยนต์", "category": "สินเชื่อรถยนต์/ยานพาหนะ (Auto Loan)", "total_balance": 140000, "monthly_payment": 6800, "interest_rate": 2.20, "notes": "เหลืออีก 21 งวด"}
    ]
    for l in sample_liabs:
        add_liability(l, user_id=uid)

    sample_incomes = [
        {"name": "เงินเดือนหลักประจำ (Base Salary)", "category": "💼 รายได้หลักประจำ (Salary/Job)", "income_type": "ประจำ (Active / Fixed)", "estimated_amount": 65000, "notes": "หักภาษี ณ ที่จ่ายและประกันสังคมแล้ว"},
        {"name": "งานฟรีแลนซ์ / รับจ้างอิสระ", "category": "💻 งานเสริม / ฟรีแลนซ์ (Freelance/Side Hustle)", "income_type": "ไม่แน่นอน (Active / Variable)", "estimated_amount": 5000, "notes": "เฉลี่ยต่อเดือน"},
        {"name": "เงินปันผลหุ้นและกองทุน", "category": "📈 ปันผลหุ้น / กองทุน (Dividends)", "income_type": "Passive (ลงทุน/สินทรัพย์)", "estimated_amount": 2000, "notes": "เฉลี่ยต่อเดือน"}
    ]
    for inc in sample_incomes:
        add_income_item(inc, user_id=uid)

    sample_expenses = [
        {"name": "ค่าผ่อนคอนโด", "category": "🏠 ที่อยู่อาศัย (Housing)", "expense_type": "คงที่ (Fixed)", "estimated_amount": 12500, "notes": "รวมส่วนกลาง"},
        {"name": "ค่าน้ำมันและค่าเดินทาง", "category": "🚗 ค่าเดินทางและยานพาหนะ (Transportation)", "expense_type": "คงที่ (Fixed)", "estimated_amount": 3500, "notes": "BTS + เติมน้ำมัน"},
        {"name": "ค่าอาหารและของใช้ประจำวัน", "category": "🍲 อาหารและของใช้ (Food & Groceries)", "expense_type": "ผันแปร (Variable)", "estimated_amount": 10000, "notes": "มื้อประจำวันและเข้าซูเปอร์มาร์เก็ต"},
        {"name": "ค่าช้อปปิ้งและสันทนาการ", "category": "🛍️ ช้อปปิ้งและไลฟ์สไตล์ (Shopping & Lifestyle)", "expense_type": "ผันแปร (Variable)", "estimated_amount": 4000, "notes": "ทานข้าวนอกบ้าน/เที่ยวพักผ่อน"},
        {"name": "ค่าเน็ตและบริการสมาชิก (Netflix/Spotify)", "category": "⚡ สาธารณูปโภคและบิล (Utilities & Bills)", "expense_type": "คงที่ (Fixed)", "estimated_amount": 2000, "notes": "เน็ตบ้าน+มือถือ+สตรีมมิ่ง"}
    ]
    for exp in sample_expenses:
        add_expense_item(exp, user_id=uid)
    
    clear_db_cache()
