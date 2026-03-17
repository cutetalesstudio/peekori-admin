import os
from fastapi import FastAPI, Depends, HTTPException, Query, APIRouter, BackgroundTasks, Body, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
import requests
from jose import jwt, JWTError
from fastapi import status
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional, Union, Literal, Tuple
from datetime import datetime, timezone, timedelta, date
from zoneinfo import ZoneInfo
from pymongo import MongoClient
from pymongo.collection import Collection
import pytz
from dateutil import parser as date_parser
from collections import Counter
from fastapi.middleware.cors import CORSMiddleware
import re
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from google.oauth2.service_account import Credentials as _GoogleCredentials
from pydantic import BaseModel, EmailStr, Field, ConfigDict
import gspread
import json
from decimal import Decimal
from bson import ObjectId
from google.oauth2.service_account import Credentials as _GoogleCredentials
from dateutil import parser
from fastapi.encoders import jsonable_encoder
import tempfile
import csv
from dateutil import parser as dateutil_parser
import io
import pandas as pd
import logging
import xlsxwriter
import openpyxl
from botocore.exceptions import BotoCoreError, ClientError
import httpx
import html
from email.message import EmailMessage
import smtplib
from app.routers.reconcile import router as vlookup_router
from app.routers.reconcile import _auto_reconcile_and_sign_once
from app.routers.razorpay_export import router as razorpay_router
from app.routers.cloudprinter_webhook import router as cloudprinter_router
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from app.routers.cloudprinter_produce_webhook import router as cp_produce_router
from app.routers.shiprocket_webhook import router as shiprocket_router
import asyncio
from apscheduler.triggers.cron import CronTrigger
from io import BytesIO
from collections import defaultdict
import builtins
from pymongo import ReturnDocument
import hashlib
import PyPDF2
from pathlib import Path

load_dotenv()


RangeKey = Literal["1d", "1w", "1m", "6m", "this_month"] 
MONGO_URI = os.getenv("MONGO_URI")
UTC = timezone.utc
TZ_IST = ZoneInfo("Asia/Kolkata")
IST_TZ = pytz.timezone("Asia/Kolkata")
MONGO_URI_df = os.getenv("MONGO_URI_df")
client_df = MongoClient(MONGO_URI_df)
df_db = client_df["df-db"]
collection_df = df_db["user-data"]
client = MongoClient(MONGO_URI, tz_aware=True)
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "candyman")
db = client[MONGO_DB_NAME]
shipping_collection = db["shipping_details"]
orders_collection = db["user_details"]
campaigns_collection = db["marketing_campaigns"]
creators_collection = db["marketing_creators"]
landing_pages_collection = db["marketing_landing_pages"]
commission_ledger_collection = db["commission_ledger"]
creator_payouts_collection = db["creator_payouts"]
withdrawal_requests_collection = db["withdrawal_requests"]
creator_signup_otps_collection = db["creator_signup_otps"]
PREVIEW_URL_FIELD = "preview_url"
JOBS_CREATED_AT_FIELD = "created_at"
PAID_FIELD = "paid"
s3 = boto3.client('s3')

BUCKET_NAME = "replicacomfy"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = timedelta(hours=1)
JWT_SECRET = "abc123"
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL") or ADMIN_USERNAME
ADMIN_JWT_SECRET = os.getenv("ADMIN_JWT_SECRET", JWT_SECRET)
ADMIN_JWT_TTL_HOURS = int(os.getenv("ADMIN_JWT_TTL_HOURS", "24"))
CREATOR_JWT_SECRET = os.getenv("CREATOR_JWT_SECRET", ADMIN_JWT_SECRET)
CREATOR_JWT_TTL_HOURS = int(os.getenv("CREATOR_JWT_TTL_HOURS", "720"))
CUTETALES_FRONTEND_BASE_URL = (os.getenv("CUTETALES_FRONTEND_BASE_URL") or "http://localhost:3005").rstrip("/")
CUTETALES_REPO_PATH = Path(
    os.getenv("CUTETALES_REPO_PATH")
    or (Path(__file__).resolve().parents[2] / "cutetales-storybook")
).resolve()
CUTETALES_CONFIG_DIR = CUTETALES_REPO_PATH / "config"
CUTETALES_PUBLIC_DIR = CUTETALES_REPO_PATH / "frontend" / "public"
CUTETALES_BOOKS_PUBLIC_DIR = CUTETALES_PUBLIC_DIR / "books"
CUTETALES_STORYBOOK_PREVIEW_LAYOUT_DIR = CUTETALES_PUBLIC_DIR / "preview_layout" / "storybook"
CUTETALES_PREVIEW_PUBLIC_DIR = CUTETALES_PUBLIC_DIR / "preview"


# Genesis SHEETS INTEGRATION BLOCK STARTS HERE
SPREADSHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_SHEET_ENABLED = os.getenv("GOOGLE_SHEET_ENABLED", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
WORKSHEET_NAME = os.getenv("GOOGLE_SHEET_WORKSHEET", "Order Placement")
VALUE_INPUT_OPTION = os.getenv("GOOGLE_VALUE_INPUT_OPTION", "USER_ENTERED")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
SERVICE_ACCOUNT_JSON = os.getenv(
    "GOOGLE_SERVICE_ACCOUNT_JSON")  # optional fallback
_SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
           "https://www.googleapis.com/auth/drive.file"]

## YARA SHEET INTEGRATION BLOCK STARTS HERE ##
SPREADSHEET_ID_YARA = os.getenv("GOOGLE_SHEET_ID_YARA")
WORKSHEET_NAME_YARA = os.getenv(
    "GOOGLE_SHEET_WORKSHEET_YARA", "Order Placement Yara")
VALUE_INPUT_OPTION_YARA = os.getenv(
    "GOOGLE_VALUE_INPUT_OPTION_YARA", "USER_ENTERED")
SERVICE_ACCOUNT_FILE_YARA = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE_YARA")
SERVICE_ACCOUNT_JSON = os.getenv(
    "GOOGLE_SERVICE_ACCOUNT_JSON")  # optional fallback
_SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
           "https://www.googleapis.com/auth/drive.file"]
SHIPROCKET_BASE = os.getenv(
    "SHIPROCKET_BASE", "https://apiv2.shiprocket.in"
).rstrip("/")
SHIPROCKET_EMAIL = os.getenv("SHIPROCKET_EMAIL")
SHIPROCKET_PASSWORD = os.getenv("SHIPROCKET_PASSWORD")
IST = timezone(timedelta(hours=5, minutes=30))
TIMESTAMP_FIELD = "time_req_recieved"
IST_OFFSET = timedelta(hours=5, minutes=30)
AWS_REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
API_BASE = os.getenv("NEXT_PUBLIC_API_BASE_URL", "http://127.0.0.1:8001")
VLOOKUP_PATH = "/api/reconcile/vlookup-payment-to-orders/auto"
DETAILS_PATH = "/api/reconcile/na-payment-details"
EMAIL_USER = os.getenv("EMAIL_ADDRESS")
EMAIL_PASS = os.getenv("EMAIL_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USER)
EMAIL_TO_RAW = os.getenv("EMAIL_TO", "")
EMAIL_TO = [e.strip() for e in EMAIL_TO_RAW.split(",") if e.strip()]
SMTP_USER = os.getenv("SMTP_USER", EMAIL_USER)
SMTP_PASS = os.getenv("SMTP_PASS", EMAIL_PASS)
NUDGE_MIN_WORKFLOWS = int(os.getenv("NUDGE_MIN_WORKFLOWS", "13"))
SHIPPED_STATUSES = {
    "PICKED UP",
    "IN TRANSIT",
    "OUT FOR DELIVERY",
    "DELIVERED",
    "REACHED AT DESTINATION HUB",
}
COUNTRY_CODES = {
    "India": "IN",
    "United States": "US",
    "United Kingdom": "GB",
    # Add more countries as needed
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger = logging.getLogger("xlsx_cron")

INSTANCE_IDS = [
    "i-0b1f98e12f9344f9f",
    "i-071c197c88296ab8a",
    "i-03dbcc37d0a59609d",
    "i-00de64646abb34ad2",
    "i-0e9f5ac83b77815a0",
    "i-0e6c27e8b058676f8",
    "i-0bfbcb4615bc6b3e3",
    "i-0b1f98e12f9344f9f",
    "i-071c197c88296ab8a",
    "i-03dbcc37d0a59609d",
    "i-00de64646abb34ad2",
]

MONGO_URI_YIPPEE = os.getenv("MONGO_URI_YIPPEE")
client_yippee = MongoClient(MONGO_URI_YIPPEE)
yippee_db = client_yippee["yippee-db"]
collection_yippee = yippee_db["user-data"]

scheduler = BackgroundScheduler(timezone=IST_TZ)

class CloudprinterWebhookBase(BaseModel):
    apikey: str
    type: str
    order: Optional[str] = None
    item: Optional[str] = None
    order_reference: str
    item_reference: Optional[str] = None
    datetime: str


class ItemProducedPayload(CloudprinterWebhookBase):
    pass


class ItemErrorPayload(CloudprinterWebhookBase):
    error_code: str
    error_message: str


class ItemValidatedPayload(CloudprinterWebhookBase):
    pass


class ItemCanceledPayload(CloudprinterWebhookBase):
    pass


class CloudprinterOrderCanceledPayload(CloudprinterWebhookBase):
    pass


class ItemDeletePayload(CloudprinterWebhookBase):
    pass


class ItemShippedPayload(CloudprinterWebhookBase):
    tracking: str
    shipping_option: str


class UnapproveRequest(BaseModel):
    job_ids: List[str]


class ShippingAddressUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    address1: Optional[str] = None
    address2: Optional[str] = None
    city:   Optional[str] = None
    state:  Optional[str] = None
    country: Optional[str] = None
    zip:    Optional[str] = Field(None, alias="postal_code")


class TimelineUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    created_at:    Optional[str] = None
    processed_at:  Optional[str] = None
    approved_at:   Optional[str] = None
    print_sent_at: Optional[str] = None
    shipped_at:    Optional[str] = None


class OrderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name:   Optional[str] = None
    age:    Optional[Union[str, int]] = None
    gender: Optional[str] = None
    book_id:        Optional[str] = None
    job_id:         Optional[str] = None
    locale:        Optional[str] = None
    book_style:     Optional[str] = None
    discount_code:  Optional[str] = None
    quantity:       Optional[int] = None
    preview_url:    Optional[str] = None
    total_price:        Optional[Union[str, float, int]] = None
    transaction_id:     Optional[str] = None
    paypal_capture_id:  Optional[str] = None
    paypal_order_id:    Optional[str] = None
    cover_url:          Optional[str] = None
    book_url:           Optional[str] = None
    user_name: Optional[str] = None
    email:     Optional[EmailStr] = None
    phone:     Optional[str] = None
    current_status: Optional[str] = None
    printer:   Optional[str] = None
    shipping_address: Optional[ShippingAddressUpdate] = None
    timeline:         Optional[TimelineUpdate] = None
    order_id: Optional[str] = None
    tracking_code: Optional[str] = None
    remarks: Optional[str] = None   # ✅ ADD

class OrderStatusUpdatePayload(BaseModel):
    order_status: str
    order_status_remarks: str

class IssueOriginUpdatePayload(BaseModel):
    issue_origin: str


class ProductConfigUpdatePayload(BaseModel):
    content: Dict[str, Any]


class BookManagerValidationPayload(BaseModel):
    book_key: str
    image_src: Optional[str] = None
    hover_image_src: Optional[str] = None
    hero_images: List[str] = []
    enabled_countries: List[str] = []
    prices: Dict[str, Dict[str, Dict[str, str]]] = {}


class NonStoryManagerValidationPayload(BaseModel):
    product_id: str
    item_id: str
    image_src: Optional[str] = None
    hero_images: List[str] = []
    enabled_countries: List[str] = []
    prices: Dict[str, Dict[str, Dict[str, str]]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        if not scheduler.running:
            scheduler.start()

        loop = asyncio.get_running_loop()

        def _kick_auto_reconcile():
            asyncio.run_coroutine_threadsafe(
                _auto_reconcile_and_sign_once(), loop
            )

        scheduler.add_job(
            _kick_auto_reconcile,
            trigger=CronTrigger(minute="*/5", timezone=IST_TZ),
            id="auto_reconcile_every_5m",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )

        scheduler.add_job(
            _run_export_and_email,
            trigger=CronTrigger(
                hour="0,3,6,9,12,15,18,21",
                minute="0",
                timezone=IST_TZ,
            ),
            id="xlsx_export_fixed_ist_times",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )

        def _kick_feedback_emails():
            asyncio.run_coroutine_threadsafe(
                _run_feedback_emails_once(), loop
            )

        scheduler.add_job(
            _kick_feedback_emails,
            trigger=CronTrigger(hour="12", minute="00", timezone=IST_TZ),
            id="feedback_emails_job",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )

        def _kick_send_nudges():
            asyncio.run_coroutine_threadsafe(
                send_nudge_batches(batch_size=200, days_window=7), loop
            )
        '''
        scheduler.add_job(
            _kick_send_nudges,
            trigger=CronTrigger(hour="12", minute="45", timezone=IST_TZ),
            id="send_nudges_job",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
        '''
    except Exception:
        logger.exception("Failed to start APScheduler")

    yield

    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
    except Exception:
        logger.exception("Failed to stop APScheduler")

app = FastAPI(lifespan=lifespan)
app.include_router(vlookup_router)
app.include_router(razorpay_router)
app.include_router(cloudprinter_router)

app.include_router(cp_produce_router)
app.include_router(shiprocket_router)
origins = [
    "http://localhost:3000",  # Allow the frontend to make requests to backend
    "http://127.0.0.1:3000", # Allow requests from other local frontend URLs
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "https://admin.peekori.com", # Allow requests from production frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows frontend domains to send requests
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


class BulkPrintRequest(BaseModel):
    order_ids: List[str]
    print_sent_by: Optional[EmailStr] = None

class OrderStatusUpdatePayload(BaseModel):
    order_status: str
    order_status_remarks: str


from fastapi import Header

def require_auth(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format")

    token = authorization.split(" ")[1]

    try:
        claims = jwt.decode(
            token,
            ADMIN_JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_aud": False},
        )
        return claims
    except JWTError as e:
        print("JWT VERIFY FAILED:", e)
        raise HTTPException(status_code=401, detail="Invalid or expired token")


PRODUCT_CONFIG_FILES = {
    "catalog": "catalog.json",
    "products": "products.json",
    "discounts": "discounts.json",
}


def _resolve_product_config_path(config_name: str, *, draft: bool = False) -> Path:
    file_name = PRODUCT_CONFIG_FILES.get((config_name or "").strip().lower())
    if not file_name:
        raise HTTPException(status_code=404, detail="Unknown product config")
    if draft:
        file_name = file_name.replace(".json", ".draft.json")
    path = (CUTETALES_CONFIG_DIR / file_name).resolve()
    try:
        path.relative_to(CUTETALES_CONFIG_DIR.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Resolved config path escaped config directory") from exc
    return path


def _load_product_config(config_name: str, *, draft: bool = False, fallback_to_live: bool = True) -> Dict[str, Any]:
    path = _resolve_product_config_path(config_name, draft=draft)
    if draft and not path.exists() and fallback_to_live:
        path = _resolve_product_config_path(config_name, draft=False)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Config file not found: {path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in {path.name}: {exc}") from exc


def _write_product_config(config_name: str, content: Dict[str, Any], *, draft: bool = False) -> Dict[str, Any]:
    path = _resolve_product_config_path(config_name, draft=draft)
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(content, indent=2, ensure_ascii=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(serialized + "\n", encoding="utf-8")
    tmp_path.replace(path)
    return {
        "config_name": config_name,
        "draft": draft,
        "path": str(path),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _product_config_status(config_name: str) -> Dict[str, Any]:
    live_path = _resolve_product_config_path(config_name, draft=False)
    draft_path = _resolve_product_config_path(config_name, draft=True)
    return {
        "config_name": config_name,
        "live_path": str(live_path),
        "draft_path": str(draft_path),
        "has_draft": draft_path.exists(),
        "live_updated_at": datetime.fromtimestamp(live_path.stat().st_mtime, tz=timezone.utc).isoformat() if live_path.exists() else None,
        "draft_updated_at": datetime.fromtimestamp(draft_path.stat().st_mtime, tz=timezone.utc).isoformat() if draft_path.exists() else None,
    }


def _publish_product_config(config_name: str) -> Dict[str, Any]:
    draft_path = _resolve_product_config_path(config_name, draft=True)
    if not draft_path.exists():
        raise HTTPException(status_code=404, detail="No draft exists to publish")
    content = _load_product_config(config_name, draft=True, fallback_to_live=False)
    result = _write_product_config(config_name, content, draft=False)
    return {
        **result,
        "published_from": str(draft_path),
    }


def _discard_product_config_draft(config_name: str) -> Dict[str, Any]:
    draft_path = _resolve_product_config_path(config_name, draft=True)
    if draft_path.exists():
        draft_path.unlink()
    return {
        "config_name": config_name,
        "draft": True,
        "discarded": True,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _summarize_product_config(config_name: str, content: Dict[str, Any]) -> Dict[str, Any]:
    if config_name == "catalog":
        books = content.get("books") or {}
        countries = content.get("countries") or {}
        return {
            "book_count": len(books) if isinstance(books, dict) else 0,
            "country_count": len(countries) if isinstance(countries, dict) else 0,
        }
    if config_name == "products":
        products = content.get("products") or {}
        product_count = len(products) if isinstance(products, dict) else 0
        item_count = 0
        if isinstance(products, dict):
            for product in products.values():
                items = (product or {}).get("items") or []
                if isinstance(items, list):
                    item_count += len(items)
        return {
            "product_count": product_count,
            "item_count": item_count,
            "default_product_id": content.get("default_product_id"),
        }
    if config_name == "discounts":
        codes = content.get("codes") or {}
        platform_offer = content.get("platform_offer") or {}
        by_product = platform_offer.get("by_product") or {}
        by_book = platform_offer.get("by_book") or {}
        return {
            "code_count": len(codes) if isinstance(codes, dict) else 0,
            "product_offer_count": len(by_product) if isinstance(by_product, dict) else 0,
            "book_offer_count": len(by_book) if isinstance(by_book, dict) else 0,
            "default_product_id": content.get("default"),
        }
    return {}


def _normalize_country_code(value: str) -> str:
    text = str(value or "").strip().upper()
    if text == "UK":
        return "GB"
    if text in {"UAE", "ARE"}:
        return "AE"
    return text


def _sanitize_filename(name: str) -> str:
    file_name = Path(str(name or "").strip()).name
    if not file_name:
        raise HTTPException(status_code=400, detail="Filename is required")
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", file_name)
    safe = safe.strip("._")
    if not safe:
        raise HTTPException(status_code=400, detail="Filename produced an empty safe value")
    return safe


def _resolve_public_path_from_web_path(web_path: str) -> Path:
    relative = str(web_path or "").strip().lstrip("/").replace("\\", "/")
    if not relative:
        raise HTTPException(status_code=400, detail="Asset path is empty")
    path = (CUTETALES_PUBLIC_DIR / relative).resolve()
    try:
        path.relative_to(CUTETALES_PUBLIC_DIR.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Asset path escaped public directory") from exc
    return path


def _storybook_layout_required_files(book_key: str) -> List[str]:
    layout_dir = CUTETALES_STORYBOOK_PREVIEW_LAYOUT_DIR / book_key
    if not layout_dir.exists():
        return ["frontcover.png"]
    front_cover = layout_dir / "frontcover.png"
    spread_files = sorted(layout_dir.glob("pg*.png"))
    required = []
    if not front_cover.exists():
        required.append("frontcover.png")
    if not spread_files:
        required.append("pgXX-YY.png")
    return required


def _build_book_validation_checks(payload: BookManagerValidationPayload) -> List[Dict[str, str]]:
    checks: List[Dict[str, str]] = []
    book_key = str(payload.book_key or "").strip()
    if not book_key:
        return [{
            "level": "error",
            "code": "missing_book_key",
            "message": "Book key is required before assets and validations can be resolved.",
        }]

    for field_name, web_path, level_if_missing in (
        ("cover image", payload.image_src, "error"),
        ("hover image", payload.hover_image_src, "warning"),
    ):
        text = str(web_path or "").strip()
        if not text:
            checks.append({
                "level": level_if_missing,
                "code": f"missing_{field_name.replace(' ', '_')}",
                "message": f"{field_name.capitalize()} path is empty.",
            })
            continue
        try:
            file_path = _resolve_public_path_from_web_path(text)
            if not file_path.exists():
                checks.append({
                    "level": "error" if field_name == "cover image" else "warning",
                    "code": f"{field_name.replace(' ', '_')}_not_found",
                    "message": f"{field_name.capitalize()} file does not exist at {text}.",
                })
            else:
                checks.append({
                    "level": "success",
                    "code": f"{field_name.replace(' ', '_')}_found",
                    "message": f"{field_name.capitalize()} file exists at {text}.",
                })
        except HTTPException:
            checks.append({
                "level": "error",
                "code": f"invalid_{field_name.replace(' ', '_')}_path",
                "message": f"{field_name.capitalize()} path is invalid: {text}.",
            })

    hero_images = [str(item or "").strip() for item in payload.hero_images if str(item or "").strip()]
    if hero_images:
        for index, web_path in enumerate(hero_images, start=1):
            try:
                file_path = _resolve_public_path_from_web_path(web_path)
                if not file_path.exists():
                    checks.append({
                        "level": "warning",
                        "code": f"gallery_image_{index}_not_found",
                        "message": f"Gallery image {index} does not exist at {web_path}.",
                    })
                else:
                    checks.append({
                        "level": "success",
                        "code": f"gallery_image_{index}_found",
                        "message": f"Gallery image {index} exists at {web_path}.",
                    })
            except HTTPException:
                checks.append({
                    "level": "warning",
                    "code": f"invalid_gallery_image_{index}",
                    "message": f"Gallery image {index} path is invalid: {web_path}.",
                })
    else:
        checks.append({
            "level": "info",
            "code": "gallery_images_missing",
            "message": "No custom gallery images configured. Storybook page will fall back to /books/<book>/<country>/<book>-book-1..5 assets.",
        })

    missing_layout_files = _storybook_layout_required_files(book_key)
    if missing_layout_files:
        checks.append({
            "level": "warning",
            "code": "missing_preview_layout_assets",
            "message": f"Preview layout is incomplete for {book_key}. Missing: {', '.join(missing_layout_files)}.",
        })
    else:
        checks.append({
            "level": "success",
            "code": "preview_layout_ready",
            "message": f"Preview layout assets exist for {book_key}.",
        })

    for country_code in payload.enabled_countries:
        normalized = _normalize_country_code(country_code)
        style_map = payload.prices.get(country_code) or payload.prices.get(normalized) or {}
        has_any_price = False
        for fields in style_map.values():
            price = str((fields or {}).get("price") or "").strip()
            if price:
                has_any_price = True
                break
        if has_any_price:
            checks.append({
                "level": "success",
                "code": f"price_present_{normalized.lower()}",
                "message": f"At least one price is configured for {normalized}.",
            })
        else:
            checks.append({
                "level": "warning",
                "code": f"missing_price_{normalized.lower()}",
                "message": f"No price is configured for enabled country {normalized}.",
            })

    preview_dir = CUTETALES_PREVIEW_PUBLIC_DIR
    sample_hits = list(preview_dir.glob(f"*/{book_key}/*"))
    if sample_hits:
        checks.append({
            "level": "success",
            "code": "sample_preview_found",
            "message": f"Sample preview assets exist for {book_key}.",
        })
    else:
        checks.append({
            "level": "info",
            "code": "sample_preview_missing",
            "message": f"No sample preview assets found for {book_key}. This is optional.",
        })

    return checks


def _non_story_preview_required_files(product_id: str, item_id: str) -> List[str]:
    product = str(product_id or "").strip().lower()
    item = str(item_id or "").strip().lower()
    if not product or not item:
      return ["preview asset"]
    folder = "frames" if product == "frame" else "stickers"
    layout_dir = CUTETALES_PUBLIC_DIR / "preview_layout" / folder / item
    if not layout_dir.exists():
        return ["frontcover.png" if product == "frame" else "pg1.png"]
    required_file = layout_dir / ("frontcover.png" if product == "frame" else "pg1.png")
    return [] if required_file.exists() else [required_file.name]


def _build_non_story_validation_checks(payload: NonStoryManagerValidationPayload) -> List[Dict[str, str]]:
    checks: List[Dict[str, str]] = []
    product_id = str(payload.product_id or "").strip().lower()
    item_id = str(payload.item_id or "").strip().lower()
    if product_id not in {"frame", "sticker"}:
        return [{
            "level": "error",
            "code": "invalid_product_id",
            "message": "Product id must be 'frame' or 'sticker'.",
        }]
    if not item_id:
        return [{
            "level": "error",
            "code": "missing_item_id",
            "message": "Item id is required before assets and validations can be resolved.",
        }]

    image_src = str(payload.image_src or "").strip()
    if not image_src:
        checks.append({
            "level": "warning",
            "code": "missing_item_image",
            "message": "Main image path is empty.",
        })
    else:
        try:
            file_path = _resolve_public_path_from_web_path(image_src)
            checks.append({
                "level": "success" if file_path.exists() else "warning",
                "code": "item_image_found" if file_path.exists() else "item_image_missing",
                "message": f"Main image {'exists' if file_path.exists() else 'does not exist'} at {image_src}.",
            })
        except HTTPException:
            checks.append({
                "level": "warning",
                "code": "invalid_item_image",
                "message": f"Main image path is invalid: {image_src}.",
            })

    hero_images = [str(item or "").strip() for item in payload.hero_images if str(item or "").strip()]
    if hero_images:
        for index, web_path in enumerate(hero_images, start=1):
            try:
                file_path = _resolve_public_path_from_web_path(web_path)
                checks.append({
                    "level": "success" if file_path.exists() else "warning",
                    "code": f"hero_image_{index}_{'found' if file_path.exists() else 'missing'}",
                    "message": f"Gallery image {index} {'exists' if file_path.exists() else 'does not exist'} at {web_path}.",
                })
            except HTTPException:
                checks.append({
                    "level": "warning",
                    "code": f"invalid_hero_image_{index}",
                    "message": f"Gallery image {index} path is invalid: {web_path}.",
                })
    else:
        checks.append({
            "level": "info",
            "code": "hero_images_missing",
            "message": "No gallery images configured for this item.",
        })

    missing_layout_files = _non_story_preview_required_files(product_id, item_id)
    if missing_layout_files:
        checks.append({
            "level": "warning",
            "code": "missing_preview_layout_assets",
            "message": f"Preview layout is incomplete for {product_id}/{item_id}. Missing: {', '.join(missing_layout_files)}.",
        })
    else:
        checks.append({
            "level": "success",
            "code": "preview_layout_ready",
            "message": f"Preview layout assets exist for {product_id}/{item_id}.",
        })

    for country_code in payload.enabled_countries:
        normalized = _normalize_country_code(country_code)
        style_map = payload.prices.get(country_code) or payload.prices.get(normalized) or {}
        has_any_price = False
        for fields in style_map.values():
            price = str((fields or {}).get("price") or "").strip()
            if price:
                has_any_price = True
                break
        checks.append({
            "level": "success" if has_any_price else "warning",
            "code": f"{'price_present' if has_any_price else 'missing_price'}_{normalized.lower()}",
            "message": f"{'At least one price is configured' if has_any_price else 'No price is configured'} for enabled country {normalized}.",
        })

    return checks


def _target_upload_path(
    *,
    book_key: str,
    asset_kind: str,
    country: str,
    sample_variant: str,
    filename: str,
) -> Tuple[Path, str]:
    book_key = str(book_key or "").strip()
    if not book_key:
        raise HTTPException(status_code=400, detail="book_key is required")
    asset_kind = str(asset_kind or "").strip().lower()
    safe_filename = _sanitize_filename(filename)
    normalized_country = _normalize_country_code(country or "IN") or "IN"
    variant = str(sample_variant or "").strip().lower() or "boy"

    if asset_kind in {"cover", "hover", "gallery"}:
        target = CUTETALES_BOOKS_PUBLIC_DIR / book_key / normalized_country / safe_filename
        public_path = "/" + str(target.relative_to(CUTETALES_PUBLIC_DIR)).replace("\\", "/")
        return target, public_path
    if asset_kind == "preview_layout":
        target = CUTETALES_STORYBOOK_PREVIEW_LAYOUT_DIR / book_key / safe_filename
        public_path = "/" + str(target.relative_to(CUTETALES_PUBLIC_DIR)).replace("\\", "/")
        return target, public_path
    if asset_kind == "sample_preview":
        target = CUTETALES_PREVIEW_PUBLIC_DIR / normalized_country / book_key / variant / safe_filename
        public_path = "/" + str(target.relative_to(CUTETALES_PUBLIC_DIR)).replace("\\", "/")
        return target, public_path

    raise HTTPException(status_code=400, detail="Unsupported asset_kind")


def _target_non_story_upload_path(*, product_id: str, item_id: str, asset_kind: str, filename: str) -> Tuple[Path, str]:
    product = str(product_id or "").strip().lower()
    item = str(item_id or "").strip().lower()
    if product not in {"frame", "sticker"}:
        raise HTTPException(status_code=400, detail="product_id must be frame or sticker")
    if not item:
        raise HTTPException(status_code=400, detail="item_id is required")
    safe_filename = _sanitize_filename(filename)
    asset_kind = str(asset_kind or "").strip().lower()
    if asset_kind in {"main_image", "gallery_image"}:
        target = CUTETALES_PUBLIC_DIR / "products" / product / item / safe_filename
        public_path = "/" + str(target.relative_to(CUTETALES_PUBLIC_DIR)).replace("\\", "/")
        return target, public_path
    if asset_kind == "preview_layout":
        folder = "frames" if product == "frame" else "stickers"
        target = CUTETALES_PUBLIC_DIR / "preview_layout" / folder / item / safe_filename
        public_path = "/" + str(target.relative_to(CUTETALES_PUBLIC_DIR)).replace("\\", "/")
        return target, public_path
    raise HTTPException(status_code=400, detail="Unsupported asset_kind")


class LoginPayload(BaseModel):
    username: str
    password: str


class CampaignPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    slug: str
    platform: str = "meta"
    product_type: Optional[str] = None
    landing_page_slug: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    active: bool = True
    commission_type: Optional[str] = None
    commission_rate: Optional[float] = None
    notes: Optional[str] = None


class CreatorPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    slug: str
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    country: Optional[str] = None
    instagram_handle: Optional[str] = None
    youtube_channel: Optional[str] = None
    handle: Optional[str] = None
    ref_code: Optional[str] = None
    coupon_code: Optional[str] = None
    payout_type: Optional[str] = None
    payout_rate: Optional[float] = None
    active: bool = True
    default_campaign_slug: Optional[str] = None
    approval_status: Optional[str] = None
    approval_notes: Optional[str] = None
    notes: Optional[str] = None


class LandingPagePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slug: str
    title: str
    product_type: Optional[str] = None
    hero_heading: Optional[str] = None
    hero_media_url: Optional[str] = None
    target_path: Optional[str] = None
    active: bool = True
    notes: Optional[str] = None


class CreatorLoginPayload(BaseModel):
    email: EmailStr
    password: str


class CreatorSignupStartPayload(BaseModel):
    email: EmailStr
    password: str
    name: str
    country: str
    instagram_handle: Optional[str] = None
    youtube_channel: Optional[str] = None


class CreatorSignupVerifyPayload(BaseModel):
    email: EmailStr
    otp: str


class CreatorApprovalPayload(BaseModel):
    notes: Optional[str] = None


class CreatorChangePasswordPayload(BaseModel):
    current_password: str
    new_password: str


class CommissionSyncPayload(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = Field(default=500, ge=1, le=5000)


class CreatePayoutPayload(BaseModel):
    creator_id: str
    ledger_ids: Optional[List[str]] = None
    payout_reference: Optional[str] = None
    notes: Optional[str] = None


class CreatorPayoutProfilePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    preferred_method: Optional[str] = None
    account_holder_name: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    upi_id: Optional[str] = None
    paypal_email: Optional[EmailStr] = None
    notes: Optional[str] = None


class WithdrawalRequestPayload(BaseModel):
    notes: Optional[str] = None


class ApproveWithdrawalPayload(BaseModel):
    payout_reference: Optional[str] = None
    notes: Optional[str] = None


def _clean_marketing_text(value: Any, *, max_length: int = 240) -> str:
    if value is None:
        return ""
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text[:max_length] if text else ""


def _normalize_slug(value: Any) -> str:
    slug = _clean_marketing_text(value, max_length=120).lower()
    slug = re.sub(r"[^a-z0-9\-_]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-_")
    return slug


def _serialize_marketing_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    out = {k: v for k, v in doc.items() if k not in {"_id", "password_hash"}}
    out["id"] = str(doc.get("_id"))
    return out


def _hash_secret(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _generate_otp_code() -> str:
    return str(builtins.__import__("random").randint(100000, 999999))


def _send_creator_otp_email(email: str, otp_code: str) -> None:
    if not (SMTP_HOST and SMTP_PORT and SMTP_USER and SMTP_PASS and EMAIL_FROM):
        logger.warning("Creator OTP email skipped because SMTP is not configured")
        return
    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = email
    msg["Subject"] = "Peekori Creator OTP"
    msg.set_content(f"Your Peekori creator signup OTP is {otp_code}. It expires in 10 minutes.")
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except Exception:
        logger.exception("Failed to send creator OTP email")


def _make_creator_token(creator_doc: Dict[str, Any]) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(creator_doc.get("_id")),
        "email": str(creator_doc.get("email") or "").strip().lower(),
        "slug": str(creator_doc.get("slug") or "").strip().lower(),
        "scope": "creator",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=CREATOR_JWT_TTL_HOURS)).timestamp()),
    }
    return jwt.encode(payload, CREATOR_JWT_SECRET, algorithm=JWT_ALGORITHM)


def require_creator_auth(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing creator authorization")
    token = authorization.split(" ", 1)[1]
    try:
        claims = jwt.decode(
            token,
            CREATOR_JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_aud": False},
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired creator token")
    if claims.get("scope") != "creator":
        raise HTTPException(status_code=403, detail="Invalid creator session")
    return claims


def _get_creator_doc_from_claims(claims: Dict[str, Any]) -> Dict[str, Any]:
    creator_id = str(claims.get("sub") or "").strip()
    if not ObjectId.is_valid(creator_id):
        raise HTTPException(status_code=401, detail="Invalid creator session")
    creator_doc = creators_collection.find_one({
        "_id": ObjectId(creator_id),
        "active": True,
    })
    approval_status = _clean_marketing_text((creator_doc or {}).get("approval_status"), max_length=40).lower()
    if creator_doc and not approval_status:
        approval_status = "active"
    if creator_doc and approval_status != "active":
        creator_doc = None
    if not creator_doc:
        raise HTTPException(status_code=401, detail="Creator not found or inactive")
    return creator_doc


def _build_creator_primary_link(creator_doc: Dict[str, Any]) -> str:
    default_campaign_slug = _normalize_slug(creator_doc.get("default_campaign_slug"))
    campaign_doc = campaigns_collection.find_one({"slug": default_campaign_slug}) if default_campaign_slug else None
    landing_slug = _normalize_slug((campaign_doc or {}).get("landing_page_slug")) or "storybook-meta-lp"
    ref_code = _clean_marketing_text(creator_doc.get("ref_code"), max_length=80)
    utm_campaign = _clean_marketing_text((campaign_doc or {}).get("utm_campaign"), max_length=120) or default_campaign_slug or _normalize_slug(creator_doc.get("slug"))
    params = {
        "utm_source": "instagram",
        "utm_medium": "influencer",
        "utm_campaign": utm_campaign,
        "ref": ref_code,
        "lp": landing_slug,
    }
    query = "&".join(
        f"{k}={requests.utils.quote(v)}"
        for k, v in params.items()
        if v
    )
    return f"{CUTETALES_FRONTEND_BASE_URL}/?{query}"


def _resolve_commission_targets(
    order_doc: Dict[str, Any],
    creators: List[Dict[str, Any]],
    campaigns: List[Dict[str, Any]],
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], float, str]:
    campaign_by_slug = {_normalize_slug(doc.get("slug")): doc for doc in campaigns}
    campaign_by_utm = {
        _clean_marketing_text(doc.get("utm_campaign"), max_length=120): doc
        for doc in campaigns
        if _clean_marketing_text(doc.get("utm_campaign"), max_length=120)
    }
    creator_by_ref = {
        _clean_marketing_text(doc.get("ref_code"), max_length=80).lower(): doc
        for doc in creators
        if _clean_marketing_text(doc.get("ref_code"), max_length=80)
    }
    creator_by_coupon = {
        _clean_marketing_text(doc.get("coupon_code"), max_length=80).upper(): doc
        for doc in creators
        if _clean_marketing_text(doc.get("coupon_code"), max_length=80)
    }

    ref_code = _clean_marketing_text(order_doc.get("ref_code"), max_length=80).lower()
    coupon_code = _clean_marketing_text(order_doc.get("discount_code"), max_length=80).upper()
    landing_slug = _normalize_slug(order_doc.get("landing_page_slug"))
    utm_campaign = _clean_marketing_text(order_doc.get("utm_campaign"), max_length=120)

    creator = creator_by_ref.get(ref_code) or creator_by_coupon.get(coupon_code)
    campaign = campaign_by_slug.get(landing_slug) or campaign_by_utm.get(utm_campaign)
    amount = _compute_commission_amount(float(order_doc.get("total_price") or 0), creator, campaign)

    if creator and creator.get("payout_type"):
        rule = f"creator:{creator.get('payout_type')}:{creator.get('payout_rate')}"
    elif campaign and campaign.get("commission_type"):
        rule = f"campaign:{campaign.get('commission_type')}:{campaign.get('commission_rate')}"
    else:
        rule = ""
    return creator, campaign, amount, rule


def _prepare_campaign_doc(payload: CampaignPayload) -> Dict[str, Any]:
    data = payload.model_dump()
    now = datetime.now(timezone.utc)
    return {
        "name": _clean_marketing_text(data["name"]),
        "slug": _normalize_slug(data["slug"] or data["name"]),
        "platform": _clean_marketing_text(data.get("platform") or "meta", max_length=40).lower(),
        "product_type": _clean_marketing_text(data.get("product_type"), max_length=40).lower() or None,
        "landing_page_slug": _normalize_slug(data.get("landing_page_slug")),
        "utm_source": _clean_marketing_text(data.get("utm_source"), max_length=80).lower() or None,
        "utm_medium": _clean_marketing_text(data.get("utm_medium"), max_length=80).lower() or None,
        "utm_campaign": _clean_marketing_text(data.get("utm_campaign"), max_length=120) or None,
        "utm_content": _clean_marketing_text(data.get("utm_content"), max_length=120) or None,
        "active": bool(data.get("active", True)),
        "commission_type": _clean_marketing_text(data.get("commission_type"), max_length=40).lower() or None,
        "commission_rate": float(data["commission_rate"]) if data.get("commission_rate") is not None else None,
        "notes": _clean_marketing_text(data.get("notes"), max_length=500) or None,
        "updated_at": now,
    }


def _prepare_creator_doc(payload: CreatorPayload) -> Dict[str, Any]:
    data = payload.model_dump()
    now = datetime.now(timezone.utc)
    doc = {
        "name": _clean_marketing_text(data["name"]),
        "slug": _normalize_slug(data["slug"] or data["name"]),
        "email": _clean_marketing_text(data.get("email"), max_length=160).lower() or None,
        "country": _clean_marketing_text(data.get("country"), max_length=80).upper() or None,
        "instagram_handle": _clean_marketing_text(data.get("instagram_handle"), max_length=120) or None,
        "youtube_channel": _clean_marketing_text(data.get("youtube_channel"), max_length=240) or None,
        "handle": _clean_marketing_text(data.get("handle"), max_length=120) or None,
        "ref_code": _clean_marketing_text(data.get("ref_code"), max_length=80) or None,
        "coupon_code": _clean_marketing_text(data.get("coupon_code"), max_length=80).upper() or None,
        "payout_type": _clean_marketing_text(data.get("payout_type"), max_length=40).lower() or None,
        "payout_rate": float(data["payout_rate"]) if data.get("payout_rate") is not None else None,
        "active": bool(data.get("active", True)),
        "default_campaign_slug": _normalize_slug(data.get("default_campaign_slug")),
        "approval_status": _clean_marketing_text(data.get("approval_status"), max_length=40).lower() or ("active" if bool(data.get("active", True)) else "pending_admin_approval"),
        "approval_notes": _clean_marketing_text(data.get("approval_notes"), max_length=500) or None,
        "notes": _clean_marketing_text(data.get("notes"), max_length=500) or None,
        "updated_at": now,
    }
    password_hash = _hash_secret(str(data.get("password") or ""))
    if password_hash:
        doc["password_hash"] = password_hash
    return doc


def _sanitize_payout_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "preferred_method": _clean_marketing_text(data.get("preferred_method"), max_length=40).lower() or None,
        "account_holder_name": _clean_marketing_text(data.get("account_holder_name"), max_length=120) or None,
        "bank_name": _clean_marketing_text(data.get("bank_name"), max_length=120) or None,
        "account_number": _clean_marketing_text(data.get("account_number"), max_length=64) or None,
        "ifsc_code": _clean_marketing_text(data.get("ifsc_code"), max_length=32).upper() or None,
        "upi_id": _clean_marketing_text(data.get("upi_id"), max_length=120) or None,
        "paypal_email": _clean_marketing_text(data.get("paypal_email"), max_length=160).lower() or None,
        "notes": _clean_marketing_text(data.get("notes"), max_length=500) or None,
    }


def _is_creator_payout_profile_complete(creator: Dict[str, Any]) -> bool:
    profile = creator.get("payout_profile") or {}
    country = _clean_marketing_text(creator.get("country"), max_length=80).upper()
    method = _clean_marketing_text(profile.get("preferred_method"), max_length=40).lower()
    account_holder_name = _clean_marketing_text(profile.get("account_holder_name"), max_length=120)

    if not account_holder_name or not country:
        return False

    if country == "IN":
        if method == "upi":
            return bool(_clean_marketing_text(profile.get("upi_id"), max_length=120))
        if method == "bank":
            return bool(
                _clean_marketing_text(profile.get("bank_name"), max_length=120)
                and _clean_marketing_text(profile.get("account_number"), max_length=64)
                and _clean_marketing_text(profile.get("ifsc_code"), max_length=32)
            )
        return False

    if method != "paypal":
        return False
    return bool(_clean_marketing_text(profile.get("paypal_email"), max_length=160))


def _prepare_landing_page_doc(payload: LandingPagePayload) -> Dict[str, Any]:
    data = payload.model_dump()
    now = datetime.now(timezone.utc)
    return {
        "slug": _normalize_slug(data["slug"] or data["title"]),
        "title": _clean_marketing_text(data["title"]),
        "product_type": _clean_marketing_text(data.get("product_type"), max_length=40).lower() or None,
        "hero_heading": _clean_marketing_text(data.get("hero_heading"), max_length=240) or None,
        "hero_media_url": _clean_marketing_text(data.get("hero_media_url"), max_length=500) or None,
        "target_path": _clean_marketing_text(data.get("target_path"), max_length=240) or None,
        "active": bool(data.get("active", True)),
        "notes": _clean_marketing_text(data.get("notes"), max_length=500) or None,
        "updated_at": now,
    }


def _compute_commission_amount(
    order_total: float,
    creator: Optional[Dict[str, Any]],
    campaign: Optional[Dict[str, Any]],
) -> float:
    if creator:
        payout_type = _clean_marketing_text(creator.get("payout_type"), max_length=40).lower()
        payout_rate = float(creator.get("payout_rate") or 0)
        if payout_type == "percent":
            return round(order_total * payout_rate / 100.0, 2)
        if payout_type in {"fixed", "per_order"}:
            return round(payout_rate, 2)
    if campaign:
        commission_type = _clean_marketing_text(campaign.get("commission_type"), max_length=40).lower()
        commission_rate = float(campaign.get("commission_rate") or 0)
        if commission_type == "percent":
            return round(order_total * commission_rate / 100.0, 2)
        if commission_type in {"fixed", "per_order"}:
            return round(commission_rate, 2)
    return 0.0


def _compute_creator_wallet(creator_id: str) -> Dict[str, float]:
    ledger_docs = list(commission_ledger_collection.find({"creator_id": creator_id}))
    pending = round(sum(float(doc.get("commission_amount") or 0) for doc in ledger_docs if doc.get("status") == "pending"), 2)
    paid = round(sum(float(doc.get("commission_amount") or 0) for doc in ledger_docs if doc.get("status") == "paid"), 2)
    requested = round(
        sum(
            float(doc.get("amount") or 0)
            for doc in withdrawal_requests_collection.find({"creator_id": creator_id, "status": "requested"})
        ),
        2,
    )
    available = round(max(0.0, pending - requested), 2)
    return {
        "pending_commission": pending,
        "paid_commission": paid,
        "requested_amount": requested,
        "available_to_withdraw": available,
    }


def _create_payout_for_creator(
    creator_id: str,
    *,
    payout_reference: Optional[str] = None,
    notes: Optional[str] = None,
    withdrawal_request_id: Optional[str] = None,
) -> Dict[str, Any]:
    if not ObjectId.is_valid(creator_id):
        raise HTTPException(status_code=400, detail="Invalid creator_id")
    creator = creators_collection.find_one({"_id": ObjectId(creator_id)})
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")

    ledger_docs = list(commission_ledger_collection.find({"creator_id": creator_id, "status": "pending"}))
    if not ledger_docs:
        raise HTTPException(status_code=400, detail="No pending commission entries found")

    total_amount = round(sum(float(doc.get("commission_amount") or 0) for doc in ledger_docs), 2)
    currency = next((str(doc.get("currency") or "") for doc in ledger_docs if doc.get("currency")), "")
    ledger_ids = [doc["_id"] for doc in ledger_docs]
    now = datetime.now(timezone.utc)

    payout_doc = {
        "creator_id": creator_id,
        "creator_name": creator.get("name", ""),
        "currency": currency,
        "amount": total_amount,
        "ledger_ids": [str(x) for x in ledger_ids],
        "payout_reference": _clean_marketing_text(payout_reference, max_length=120) or None,
        "notes": _clean_marketing_text(notes, max_length=500) or None,
        "created_at": now,
        "updated_at": now,
        "status": "paid",
        "withdrawal_request_id": withdrawal_request_id or None,
    }
    result = creator_payouts_collection.insert_one(payout_doc)
    payout_id = str(result.inserted_id)
    commission_ledger_collection.update_many(
        {"_id": {"$in": ledger_ids}},
        {"$set": {
            "status": "paid",
            "paid_at": now,
            "payout_id": payout_id,
            "updated_at": now,
        }},
    )
    if withdrawal_request_id and ObjectId.is_valid(withdrawal_request_id):
        withdrawal_requests_collection.update_one(
            {"_id": ObjectId(withdrawal_request_id)},
            {"$set": {
                "status": "paid",
                "paid_at": now,
                "payout_id": payout_id,
                "updated_at": now,
            }},
        )
    else:
        withdrawal_requests_collection.update_many(
            {"creator_id": creator_id, "status": "requested"},
            {"$set": {
                "status": "paid",
                "paid_at": now,
                "payout_id": payout_id,
                "updated_at": now,
            }},
        )
    created = creator_payouts_collection.find_one({"_id": result.inserted_id})
    return _serialize_marketing_doc(created or payout_doc)


def _make_admin_token(username: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=ADMIN_JWT_TTL_HOURS)).timestamp()),
    }
    return jwt.encode(payload, ADMIN_JWT_SECRET, algorithm=JWT_ALGORITHM)


@app.post("/api/auth/login")
def admin_login(payload: LoginPayload):
    if not ADMIN_PASSWORD:
        raise HTTPException(status_code=500, detail="ADMIN_PASSWORD is not configured")

    if payload.username != ADMIN_USERNAME or payload.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = _make_admin_token(ADMIN_USERNAME, ADMIN_EMAIL)
    return {"token": token, "email": ADMIN_EMAIL}


@app.post("/api/creator/auth/signup/start")
def creator_signup_start(payload: CreatorSignupStartPayload):
    email = str(payload.email or "").strip().lower()
    if len(str(payload.password or "").strip()) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if not _clean_marketing_text(payload.name):
        raise HTTPException(status_code=400, detail="Name is required")
    if not _clean_marketing_text(payload.country, max_length=80):
        raise HTTPException(status_code=400, detail="Country is required")
    if not (
        _clean_marketing_text(payload.instagram_handle, max_length=120)
        or _clean_marketing_text(payload.youtube_channel, max_length=240)
    ):
        raise HTTPException(status_code=400, detail="Add your Instagram handle or YouTube channel")
    if creators_collection.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="Creator email already exists")

    otp_code = _generate_otp_code()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=10)
    creator_signup_otps_collection.update_one(
        {"email": email},
        {"$set": {
            "email": email,
            "otp_hash": _hash_secret(otp_code),
            "signup_payload": {
                "name": _clean_marketing_text(payload.name),
                "slug": _normalize_slug(payload.name),
                "email": email,
                "password_hash": _hash_secret(payload.password),
                "country": _clean_marketing_text(payload.country, max_length=80).upper(),
                "instagram_handle": _clean_marketing_text(payload.instagram_handle, max_length=120) or None,
                "youtube_channel": _clean_marketing_text(payload.youtube_channel, max_length=240) or None,
            },
            "expires_at": expires_at,
            "updated_at": now,
        }},
        upsert=True,
    )
    _send_creator_otp_email(email, otp_code)
    response: Dict[str, Any] = {"success": True, "message": "OTP sent"}
    if os.getenv("ENV", "").strip().lower() in {"local", "dev", "development"}:
        response["otp_debug"] = otp_code
    return response


@app.post("/api/creator/auth/signup/verify")
def creator_signup_verify(payload: CreatorSignupVerifyPayload):
    email = str(payload.email or "").strip().lower()
    otp_doc = creator_signup_otps_collection.find_one({"email": email})
    if not otp_doc:
        raise HTTPException(status_code=400, detail="OTP request not found")
    expires_at = otp_doc.get("expires_at")
    if not expires_at or expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP expired")
    if _hash_secret(payload.otp) != str(otp_doc.get("otp_hash") or ""):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    signup_payload = otp_doc.get("signup_payload") or {}
    if creators_collection.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="Creator email already exists")
    now = datetime.now(timezone.utc)
    creator_doc = {
        "name": signup_payload.get("name") or "Creator",
        "slug": _normalize_slug(signup_payload.get("slug") or signup_payload.get("name") or email.split("@")[0]),
        "email": email,
        "password_hash": signup_payload.get("password_hash"),
        "country": signup_payload.get("country"),
        "instagram_handle": signup_payload.get("instagram_handle"),
        "youtube_channel": signup_payload.get("youtube_channel"),
        "handle": signup_payload.get("instagram_handle") or signup_payload.get("youtube_channel") or None,
        "ref_code": None,
        "coupon_code": None,
        "payout_type": None,
        "payout_rate": None,
        "active": False,
        "approval_status": "pending_admin_approval",
        "approval_notes": None,
        "created_at": now,
        "updated_at": now,
    }
    result = creators_collection.insert_one(creator_doc)
    creator_signup_otps_collection.delete_one({"email": email})
    created = creators_collection.find_one({"_id": result.inserted_id}) or creator_doc
    return {
        "success": True,
        "creator": _serialize_marketing_doc(created),
        "message": "Signup complete. Awaiting admin approval.",
    }


@app.get("/api/auth/me")
def auth_me(claims=Depends(require_auth)):
    email = (claims.get("email") or "").strip().lower()
    username = claims.get("sub") or ""
    if not email:
        raise HTTPException(status_code=401, detail="Invalid session")
    return {
        "email": email,
        "allowed": True,
        "username": username,
    }


@app.get("/api/admin/product-config")
def list_product_configs(claims=Depends(require_auth)):
    items = []
    for config_name in PRODUCT_CONFIG_FILES:
        content = _load_product_config(config_name, draft=True)
        items.append({
            "config_name": config_name,
            **_product_config_status(config_name),
            "summary": _summarize_product_config(config_name, content),
        })
    return {
        "repo_path": str(CUTETALES_REPO_PATH),
        "items": items,
    }


@app.get("/api/admin/product-config/{config_name}")
def get_product_config(config_name: str, draft: bool = True, claims=Depends(require_auth)):
    content = _load_product_config(config_name, draft=draft)
    draft_path = _resolve_product_config_path(config_name, draft=True)
    path = draft_path if draft and draft_path.exists() else _resolve_product_config_path(config_name, draft=False)
    return {
        "config_name": config_name,
        "draft": draft,
        "path": str(path),
        "status": _product_config_status(config_name),
        "summary": _summarize_product_config(config_name, content),
        "content": content,
    }


@app.put("/api/admin/product-config/{config_name}")
def update_product_config(
    config_name: str,
    payload: ProductConfigUpdatePayload,
    draft: bool = True,
    claims=Depends(require_auth),
):
    result = _write_product_config(config_name, payload.content, draft=draft)
    return {**result, "status": _product_config_status(config_name)}


@app.get("/api/admin/product-config/{config_name}/status")
def get_product_config_status(config_name: str, claims=Depends(require_auth)):
    return _product_config_status(config_name)


@app.post("/api/admin/product-config/{config_name}/publish")
def publish_product_config(config_name: str, claims=Depends(require_auth)):
    result = _publish_product_config(config_name)
    return {**result, "status": _product_config_status(config_name)}


@app.delete("/api/admin/product-config/{config_name}/draft")
def discard_product_config_draft(config_name: str, claims=Depends(require_auth)):
    result = _discard_product_config_draft(config_name)
    return {**result, "status": _product_config_status(config_name)}


@app.post("/api/admin/book-manager/validate")
def validate_book_manager(
    payload: BookManagerValidationPayload,
    claims=Depends(require_auth),
):
    return {
        "book_key": str(payload.book_key or "").strip(),
        "checks": _build_book_validation_checks(payload),
    }


@app.post("/api/admin/book-manager/upload")
async def upload_book_manager_asset(
    book_key: str = Form(...),
    asset_kind: str = Form(...),
    country: str = Form("IN"),
    sample_variant: str = Form("boy"),
    file: UploadFile = File(...),
    claims=Depends(require_auth),
):
    target_path, public_path = _target_upload_path(
        book_key=book_key,
        asset_kind=asset_kind,
        country=country,
        sample_variant=sample_variant,
        filename=file.filename or "",
    )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    target_path.write_bytes(content)
    return {
        "book_key": str(book_key).strip(),
        "asset_kind": str(asset_kind).strip().lower(),
        "public_path": public_path,
        "filename": target_path.name,
        "saved_path": str(target_path),
        "size_bytes": len(content),
    }


@app.post("/api/admin/non-story-manager/validate")
def validate_non_story_manager(
    payload: NonStoryManagerValidationPayload,
    claims=Depends(require_auth),
):
    return {
        "product_id": str(payload.product_id or "").strip().lower(),
        "item_id": str(payload.item_id or "").strip().lower(),
        "checks": _build_non_story_validation_checks(payload),
    }


@app.post("/api/admin/non-story-manager/upload")
async def upload_non_story_asset(
    product_id: str = Form(...),
    item_id: str = Form(...),
    asset_kind: str = Form(...),
    file: UploadFile = File(...),
    claims=Depends(require_auth),
):
    target_path, public_path = _target_non_story_upload_path(
        product_id=product_id,
        item_id=item_id,
        asset_kind=asset_kind,
        filename=file.filename or "",
    )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    target_path.write_bytes(content)
    return {
        "product_id": str(product_id).strip().lower(),
        "item_id": str(item_id).strip().lower(),
        "asset_kind": str(asset_kind).strip().lower(),
        "public_path": public_path,
        "filename": target_path.name,
        "saved_path": str(target_path),
        "size_bytes": len(content),
    }


@app.get("/api/admin/campaigns")
def list_campaigns(claims=Depends(require_auth)):
    docs = list(campaigns_collection.find({}, {"created_at": 0}).sort("updated_at", -1))
    return {"items": [_serialize_marketing_doc(doc) for doc in docs]}


@app.post("/api/admin/campaigns")
def create_campaign(payload: CampaignPayload, claims=Depends(require_auth)):
    doc = _prepare_campaign_doc(payload)
    if not doc["name"] or not doc["slug"]:
        raise HTTPException(status_code=400, detail="name and slug are required")
    if campaigns_collection.find_one({"slug": doc["slug"]}):
        raise HTTPException(status_code=409, detail="Campaign slug already exists")
    doc["created_at"] = doc["updated_at"]
    result = campaigns_collection.insert_one(doc)
    created = campaigns_collection.find_one({"_id": result.inserted_id})
    return {"item": _serialize_marketing_doc(created or doc)}


@app.patch("/api/admin/campaigns/{item_id}")
def update_campaign(item_id: str, payload: CampaignPayload, claims=Depends(require_auth)):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid campaign id")
    doc = _prepare_campaign_doc(payload)
    existing = campaigns_collection.find_one({"slug": doc["slug"], "_id": {"$ne": ObjectId(item_id)}})
    if existing:
        raise HTTPException(status_code=409, detail="Campaign slug already exists")
    result = campaigns_collection.find_one_and_update(
        {"_id": ObjectId(item_id)},
        {"$set": doc},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"item": _serialize_marketing_doc(result)}


@app.delete("/api/admin/campaigns/{item_id}")
def delete_campaign(item_id: str, claims=Depends(require_auth)):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid campaign id")
    result = campaigns_collection.delete_one({"_id": ObjectId(item_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"success": True}


@app.get("/api/admin/creators")
def list_creators(claims=Depends(require_auth)):
    docs = list(creators_collection.find({}, {"created_at": 0}).sort("updated_at", -1))
    return {"items": [_serialize_marketing_doc(doc) for doc in docs]}


@app.post("/api/admin/creators")
def create_creator(payload: CreatorPayload, claims=Depends(require_auth)):
    doc = _prepare_creator_doc(payload)
    if not doc["name"] or not doc["slug"]:
        raise HTTPException(status_code=400, detail="name and slug are required")
    if creators_collection.find_one({"slug": doc["slug"]}):
        raise HTTPException(status_code=409, detail="Creator slug already exists")
    if doc.get("email") and creators_collection.find_one({"email": doc["email"]}):
        raise HTTPException(status_code=409, detail="Creator email already exists")
    doc["created_at"] = doc["updated_at"]
    result = creators_collection.insert_one(doc)
    created = creators_collection.find_one({"_id": result.inserted_id})
    return {"item": _serialize_marketing_doc(created or doc)}


@app.patch("/api/admin/creators/{item_id}")
def update_creator(item_id: str, payload: CreatorPayload, claims=Depends(require_auth)):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid creator id")
    doc = _prepare_creator_doc(payload)
    existing = creators_collection.find_one({"slug": doc["slug"], "_id": {"$ne": ObjectId(item_id)}})
    if existing:
        raise HTTPException(status_code=409, detail="Creator slug already exists")
    if doc.get("email"):
        existing_email = creators_collection.find_one({"email": doc["email"], "_id": {"$ne": ObjectId(item_id)}})
        if existing_email:
            raise HTTPException(status_code=409, detail="Creator email already exists")
    result = creators_collection.find_one_and_update(
        {"_id": ObjectId(item_id)},
        {"$set": doc},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Creator not found")
    return {"item": _serialize_marketing_doc(result)}


@app.delete("/api/admin/creators/{item_id}")
def delete_creator(item_id: str, claims=Depends(require_auth)):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid creator id")
    result = creators_collection.delete_one({"_id": ObjectId(item_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Creator not found")
    return {"success": True}


@app.post("/api/admin/creators/{item_id}/approve")
def approve_creator(item_id: str, payload: CreatorApprovalPayload, claims=Depends(require_auth)):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid creator id")
    result = creators_collection.find_one_and_update(
        {"_id": ObjectId(item_id)},
        {"$set": {
            "active": True,
            "approval_status": "active",
            "approval_notes": _clean_marketing_text(payload.notes, max_length=500) or None,
            "updated_at": datetime.now(timezone.utc),
        }},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Creator not found")
    return {"item": _serialize_marketing_doc(result)}


@app.post("/api/admin/creators/{item_id}/reject")
def reject_creator(item_id: str, payload: CreatorApprovalPayload, claims=Depends(require_auth)):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid creator id")
    result = creators_collection.find_one_and_update(
        {"_id": ObjectId(item_id)},
        {"$set": {
            "active": False,
            "approval_status": "rejected",
            "approval_notes": _clean_marketing_text(payload.notes, max_length=500) or None,
            "updated_at": datetime.now(timezone.utc),
        }},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Creator not found")
    return {"item": _serialize_marketing_doc(result)}


@app.get("/api/admin/landing-pages")
def list_landing_pages(claims=Depends(require_auth)):
    docs = list(landing_pages_collection.find({}, {"created_at": 0}).sort("updated_at", -1))
    return {"items": [_serialize_marketing_doc(doc) for doc in docs]}


@app.post("/api/admin/landing-pages")
def create_landing_page(payload: LandingPagePayload, claims=Depends(require_auth)):
    doc = _prepare_landing_page_doc(payload)
    if not doc["title"] or not doc["slug"]:
        raise HTTPException(status_code=400, detail="title and slug are required")
    if landing_pages_collection.find_one({"slug": doc["slug"]}):
        raise HTTPException(status_code=409, detail="Landing page slug already exists")
    doc["created_at"] = doc["updated_at"]
    result = landing_pages_collection.insert_one(doc)
    created = landing_pages_collection.find_one({"_id": result.inserted_id})
    return {"item": _serialize_marketing_doc(created or doc)}


@app.patch("/api/admin/landing-pages/{item_id}")
def update_landing_page(item_id: str, payload: LandingPagePayload, claims=Depends(require_auth)):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid landing page id")
    doc = _prepare_landing_page_doc(payload)
    existing = landing_pages_collection.find_one({"slug": doc["slug"], "_id": {"$ne": ObjectId(item_id)}})
    if existing:
        raise HTTPException(status_code=409, detail="Landing page slug already exists")
    result = landing_pages_collection.find_one_and_update(
        {"_id": ObjectId(item_id)},
        {"$set": doc},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Landing page not found")
    return {"item": _serialize_marketing_doc(result)}


@app.delete("/api/admin/landing-pages/{item_id}")
def delete_landing_page(item_id: str, claims=Depends(require_auth)):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid landing page id")
    result = landing_pages_collection.delete_one({"_id": ObjectId(item_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Landing page not found")
    return {"success": True}


@app.get("/api/admin/commissions/report")
def commission_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    claims=Depends(require_auth),
):
    query: Dict[str, Any] = {"paid": True}
    date_filter: Dict[str, Any] = {}
    if start_date:
        date_filter["$gte"] = dateutil_parser.parse(start_date)
    if end_date:
        date_filter["$lte"] = dateutil_parser.parse(end_date) + timedelta(days=1)
    if date_filter:
        query["processed_at"] = date_filter

    projection = {
        "_id": 0,
        "order_id": 1,
        "job_id": 1,
        "name": 1,
        "processed_at": 1,
        "total_price": 1,
        "currency": 1,
        "discount_code": 1,
        "utm_source": 1,
        "utm_medium": 1,
        "utm_campaign": 1,
        "ref_code": 1,
        "landing_page_slug": 1,
    }
    orders = list(orders_collection.find(query, projection).sort("processed_at", -1).limit(500))
    campaigns = list(campaigns_collection.find({}))
    creators = list(creators_collection.find({}))
    campaign_by_slug = {_normalize_slug(doc.get("slug")): doc for doc in campaigns}
    campaign_by_utm = {
        _clean_marketing_text(doc.get("utm_campaign"), max_length=120): doc
        for doc in campaigns
        if _clean_marketing_text(doc.get("utm_campaign"), max_length=120)
    }
    creator_by_ref = {
        _clean_marketing_text(doc.get("ref_code"), max_length=80).lower(): doc
        for doc in creators
        if _clean_marketing_text(doc.get("ref_code"), max_length=80)
    }
    creator_by_coupon = {
        _clean_marketing_text(doc.get("coupon_code"), max_length=80).upper(): doc
        for doc in creators
        if _clean_marketing_text(doc.get("coupon_code"), max_length=80)
    }

    rows: List[Dict[str, Any]] = []
    total_revenue = 0.0
    total_commission = 0.0
    for order in orders:
        order_total = float(order.get("total_price") or 0)
        ref_code = _clean_marketing_text(order.get("ref_code"), max_length=80).lower()
        coupon_code = _clean_marketing_text(order.get("discount_code"), max_length=80).upper()
        landing_slug = _normalize_slug(order.get("landing_page_slug"))
        utm_campaign = _clean_marketing_text(order.get("utm_campaign"), max_length=120)

        creator = creator_by_ref.get(ref_code) or creator_by_coupon.get(coupon_code)
        campaign = campaign_by_slug.get(landing_slug) or campaign_by_utm.get(utm_campaign)
        commission_amount = _compute_commission_amount(order_total, creator, campaign)

        total_revenue += order_total
        total_commission += commission_amount
        rows.append({
            "order_id": order.get("order_id", ""),
            "job_id": order.get("job_id", ""),
            "name": order.get("name", ""),
            "processed_at": order.get("processed_at"),
            "currency": order.get("currency", ""),
            "revenue": round(order_total, 2),
            "utm_source": order.get("utm_source", ""),
            "utm_medium": order.get("utm_medium", ""),
            "utm_campaign": utm_campaign,
            "ref_code": order.get("ref_code", ""),
            "landing_page_slug": order.get("landing_page_slug", ""),
            "creator_name": creator.get("name", "") if creator else "",
            "campaign_name": campaign.get("name", "") if campaign else "",
            "commission_amount": round(commission_amount, 2),
            "commission_rule": (
                f"{creator.get('payout_type')}:{creator.get('payout_rate')}"
                if creator and creator.get("payout_type")
                else (
                    f"{campaign.get('commission_type')}:{campaign.get('commission_rate')}"
                    if campaign and campaign.get("commission_type")
                    else ""
                )
            ),
        })

    return {
        "items": rows,
        "summary": {
            "orders": len(rows),
            "revenue": round(total_revenue, 2),
            "commission": round(total_commission, 2),
        },
    }


@app.post("/api/admin/commissions/sync")
def sync_commission_ledger(payload: CommissionSyncPayload, claims=Depends(require_auth)):
    query: Dict[str, Any] = {"paid": True}
    date_filter: Dict[str, Any] = {}
    if payload.start_date:
        date_filter["$gte"] = dateutil_parser.parse(payload.start_date)
    if payload.end_date:
        date_filter["$lte"] = dateutil_parser.parse(payload.end_date) + timedelta(days=1)
    if date_filter:
        query["processed_at"] = date_filter

    projection = {
        "_id": 0,
        "order_id": 1,
        "job_id": 1,
        "name": 1,
        "processed_at": 1,
        "total_price": 1,
        "currency": 1,
        "discount_code": 1,
        "utm_source": 1,
        "utm_medium": 1,
        "utm_campaign": 1,
        "ref_code": 1,
        "landing_page_slug": 1,
        "product_type": 1,
        "book_id": 1,
    }
    orders = list(orders_collection.find(query, projection).sort("processed_at", -1).limit(payload.limit))
    creators = list(creators_collection.find({"active": True}))
    campaigns = list(campaigns_collection.find({"active": True}))

    created_count = 0
    skipped_count = 0
    for order in orders:
        order_id = _clean_marketing_text(order.get("order_id"), max_length=120)
        if not order_id:
            skipped_count += 1
            continue
        if commission_ledger_collection.find_one({"order_id": order_id}):
            skipped_count += 1
            continue

        creator, campaign, amount, rule = _resolve_commission_targets(order, creators, campaigns)
        if amount <= 0:
            skipped_count += 1
            continue

        now = datetime.now(timezone.utc)
        commission_ledger_collection.insert_one({
            "order_id": order_id,
            "job_id": order.get("job_id", ""),
            "creator_id": str(creator.get("_id")) if creator else "",
            "creator_name": creator.get("name", "") if creator else "",
            "campaign_id": str(campaign.get("_id")) if campaign else "",
            "campaign_name": campaign.get("name", "") if campaign else "",
            "status": "pending",
            "currency": order.get("currency", ""),
            "order_total": round(float(order.get("total_price") or 0), 2),
            "commission_amount": round(amount, 2),
            "rule_snapshot": rule,
            "attribution_snapshot": {
                "utm_source": order.get("utm_source", ""),
                "utm_medium": order.get("utm_medium", ""),
                "utm_campaign": order.get("utm_campaign", ""),
                "ref_code": order.get("ref_code", ""),
                "landing_page_slug": order.get("landing_page_slug", ""),
            },
            "product_type": order.get("product_type", ""),
            "book_id": order.get("book_id", ""),
            "processed_at": order.get("processed_at"),
            "created_at": now,
            "updated_at": now,
        })
        created_count += 1

    return {"created": created_count, "skipped": skipped_count}


@app.get("/api/admin/commissions/ledger")
def list_commission_ledger(
    creator_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    claims=Depends(require_auth),
):
    query: Dict[str, Any] = {}
    if creator_id:
        query["creator_id"] = creator_id
    if status:
        query["status"] = status
    docs = list(commission_ledger_collection.find(query).sort("processed_at", -1).limit(1000))
    return {"items": [_serialize_marketing_doc(doc) for doc in docs]}


@app.get("/api/admin/payouts")
def list_creator_payouts(claims=Depends(require_auth)):
    docs = list(creator_payouts_collection.find({}).sort("created_at", -1).limit(500))
    return {"items": [_serialize_marketing_doc(doc) for doc in docs]}


@app.post("/api/admin/payouts/create")
def create_payout(payload: CreatePayoutPayload, claims=Depends(require_auth)):
    item = _create_payout_for_creator(
        str(payload.creator_id or "").strip(),
        payout_reference=payload.payout_reference,
        notes=payload.notes,
    )
    return {"item": item}


@app.get("/api/admin/withdrawal-requests")
def list_withdrawal_requests(claims=Depends(require_auth)):
    docs = list(withdrawal_requests_collection.find({}).sort("created_at", -1).limit(500))
    return {"items": [_serialize_marketing_doc(doc) for doc in docs]}


@app.post("/api/admin/withdrawal-requests/{request_id}/approve")
def approve_withdrawal_request(request_id: str, payload: ApproveWithdrawalPayload, claims=Depends(require_auth)):
    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid withdrawal request id")
    request_doc = withdrawal_requests_collection.find_one({"_id": ObjectId(request_id)})
    if not request_doc:
        raise HTTPException(status_code=404, detail="Withdrawal request not found")
    if request_doc.get("status") != "requested":
        raise HTTPException(status_code=400, detail="Withdrawal request is not pending")
    item = _create_payout_for_creator(
        str(request_doc.get("creator_id") or ""),
        payout_reference=payload.payout_reference,
        notes=payload.notes or request_doc.get("notes"),
        withdrawal_request_id=request_id,
    )
    return {"item": item}


@app.post("/api/creator/auth/login")
def creator_login(payload: CreatorLoginPayload):
    email = str(payload.email or "").strip().lower()
    password_hash = _hash_secret(payload.password)
    creator = creators_collection.find_one({
        "email": email,
        "password_hash": password_hash,
    })
    if not creator:
        raise HTTPException(status_code=401, detail="Invalid creator credentials")
    approval_status = _clean_marketing_text(creator.get("approval_status"), max_length=40).lower() or ("active" if bool(creator.get("active")) else "pending_admin_approval")
    if approval_status != "active" or not bool(creator.get("active")):
        raise HTTPException(status_code=403, detail="Your creator account is pending admin approval")
    token = _make_creator_token(creator)
    return {
        "token": token,
        "creator": {
            "id": str(creator.get("_id")),
            "name": creator.get("name", ""),
            "slug": creator.get("slug", ""),
            "email": creator.get("email", ""),
        },
    }


@app.get("/api/creator/me")
def creator_me(claims=Depends(require_creator_auth)):
    creator = _get_creator_doc_from_claims(claims)
    return {
        "id": str(creator.get("_id")),
        "name": creator.get("name", ""),
        "slug": creator.get("slug", ""),
        "email": creator.get("email", ""),
        "handle": creator.get("handle", ""),
        "ref_code": creator.get("ref_code", ""),
        "coupon_code": creator.get("coupon_code", ""),
        "payout_profile": creator.get("payout_profile") or {},
        "country": creator.get("country", ""),
        "instagram_handle": creator.get("instagram_handle", ""),
        "youtube_channel": creator.get("youtube_channel", ""),
    }


@app.post("/api/creator/change-password")
def creator_change_password(payload: CreatorChangePasswordPayload, claims=Depends(require_creator_auth)):
    creator = _get_creator_doc_from_claims(claims)
    current_hash = _hash_secret(payload.current_password)
    if current_hash != str(creator.get("password_hash") or ""):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(str(payload.new_password or "").strip()) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    new_hash = _hash_secret(payload.new_password)
    if not new_hash:
        raise HTTPException(status_code=400, detail="New password is required")
    creators_collection.update_one(
        {"_id": creator["_id"]},
        {"$set": {"password_hash": new_hash, "updated_at": datetime.now(timezone.utc)}},
    )
    return {"success": True}


@app.get("/api/creator/dashboard")
def creator_dashboard(claims=Depends(require_creator_auth)):
    creator = _get_creator_doc_from_claims(claims)
    creator_id = str(creator.get("_id"))
    ledger_docs = list(commission_ledger_collection.find({"creator_id": creator_id}))
    payout_docs = list(creator_payouts_collection.find({"creator_id": creator_id}))
    wallet = _compute_creator_wallet(creator_id)
    orders_count = len({str(doc.get("order_id") or "") for doc in ledger_docs if doc.get("order_id")})
    last_payout = payout_docs[0].get("created_at") if payout_docs else None
    return {
        "creator": {
            "name": creator.get("name", ""),
            "slug": creator.get("slug", ""),
        },
        "summary": {
            "orders": orders_count,
            **wallet,
            "last_payout_at": last_payout,
        },
    }


@app.get("/api/creator/orders")
def creator_orders(claims=Depends(require_creator_auth)):
    creator = _get_creator_doc_from_claims(claims)
    creator_id = str(creator.get("_id"))
    docs = list(commission_ledger_collection.find({"creator_id": creator_id}).sort("processed_at", -1).limit(500))
    return {"items": [_serialize_marketing_doc(doc) for doc in docs]}


@app.get("/api/creator/payouts")
def creator_payouts(claims=Depends(require_creator_auth)):
    creator = _get_creator_doc_from_claims(claims)
    creator_id = str(creator.get("_id"))
    docs = list(creator_payouts_collection.find({"creator_id": creator_id}).sort("created_at", -1).limit(200))
    return {"items": [_serialize_marketing_doc(doc) for doc in docs]}


@app.get("/api/creator/payout-profile")
def creator_payout_profile(claims=Depends(require_creator_auth)):
    creator = _get_creator_doc_from_claims(claims)
    return {
        "profile": creator.get("payout_profile") or {},
        "wallet": _compute_creator_wallet(str(creator.get("_id"))),
        "country": creator.get("country", ""),
        "profile_complete": _is_creator_payout_profile_complete(creator),
    }


@app.put("/api/creator/payout-profile")
def update_creator_payout_profile(payload: CreatorPayoutProfilePayload, claims=Depends(require_creator_auth)):
    creator = _get_creator_doc_from_claims(claims)
    creator_id = str(creator.get("_id"))
    profile = _sanitize_payout_profile(payload.model_dump())
    country = _clean_marketing_text(creator.get("country"), max_length=80).upper()
    if country == "IN":
        if profile.get("preferred_method") not in {"upi", "bank"}:
            raise HTTPException(status_code=400, detail="Indian creators can use only UPI or bank transfer")
        profile["paypal_email"] = None
    else:
        if profile.get("preferred_method") != "paypal":
            raise HTTPException(status_code=400, detail="Non-India creators can use only PayPal payout")
        profile["upi_id"] = None
        profile["bank_name"] = None
        profile["account_number"] = None
        profile["ifsc_code"] = None
    creators_collection.update_one(
        {"_id": ObjectId(creator_id)},
        {"$set": {"payout_profile": profile, "updated_at": datetime.now(timezone.utc)}},
    )
    updated = creators_collection.find_one({"_id": ObjectId(creator_id)}) or {}
    return {
        "profile": updated.get("payout_profile") or {},
        "country": updated.get("country", ""),
        "profile_complete": _is_creator_payout_profile_complete(updated),
    }


@app.get("/api/creator/withdrawals")
def creator_withdrawals(claims=Depends(require_creator_auth)):
    creator = _get_creator_doc_from_claims(claims)
    creator_id = str(creator.get("_id"))
    docs = list(withdrawal_requests_collection.find({"creator_id": creator_id}).sort("created_at", -1).limit(200))
    return {"items": [_serialize_marketing_doc(doc) for doc in docs]}


@app.post("/api/creator/withdrawals/request")
def request_withdrawal(payload: WithdrawalRequestPayload, claims=Depends(require_creator_auth)):
    creator = _get_creator_doc_from_claims(claims)
    creator_id = str(creator.get("_id"))
    profile = creator.get("payout_profile") or {}
    if not _is_creator_payout_profile_complete(creator):
        raise HTTPException(status_code=400, detail="Complete your payout profile before requesting withdrawal")
    existing = withdrawal_requests_collection.find_one({"creator_id": creator_id, "status": "requested"})
    if existing:
        raise HTTPException(status_code=400, detail="A withdrawal request is already pending")
    wallet = _compute_creator_wallet(creator_id)
    amount = float(wallet.get("available_to_withdraw") or 0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="No amount available to withdraw")
    now = datetime.now(timezone.utc)
    doc = {
        "creator_id": creator_id,
        "creator_name": creator.get("name", ""),
        "amount": round(amount, 2),
        "currency": next((str(x.get("currency") or "") for x in commission_ledger_collection.find({"creator_id": creator_id, "status": "pending"}) if x.get("currency")), ""),
        "status": "requested",
        "notes": _clean_marketing_text(payload.notes, max_length=500) or None,
        "payout_profile_snapshot": profile,
        "created_at": now,
        "updated_at": now,
    }
    result = withdrawal_requests_collection.insert_one(doc)
    created = withdrawal_requests_collection.find_one({"_id": result.inserted_id})
    return {"item": _serialize_marketing_doc(created or doc)}


@app.get("/api/creator/link")
def creator_link(claims=Depends(require_creator_auth)):
    creator = _get_creator_doc_from_claims(claims)
    return {
        "primary_link": _build_creator_primary_link(creator),
        "ref_code": creator.get("ref_code", ""),
        "coupon_code": creator.get("coupon_code", ""),
    }

def _send_email_with_attachment(subject: str, body_html: str, attachment_name: str, attachment_bytes: bytes):
    """
    Sends an email with XLSX attachment via SMTP (STARTTLS).
    """
    if not (SMTP_HOST and SMTP_PORT and SMTP_USER and SMTP_PASS and EMAIL_FROM):
        logger.error("Email env vars missing; cannot send export email.")
        return
    if not EMAIL_TO:
        logger.error(
            "EMAIL_TO is empty after parsing. Set EMAIL_TO='a@x.com,b@y.com'.")
        return

    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(EMAIL_TO)
    msg["Subject"] = subject
    msg.set_content(
        "This email contains HTML content. Please view in an HTML-capable client.")
    msg.add_alternative(body_html, subtype="html")

    msg.add_attachment(
        attachment_bytes,
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=attachment_name,
    )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            # STARTTLS path (most common). If you use port 465, switch to SMTP_SSL.
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        logger.info(
            f"SMTP: host={SMTP_HOST}:{SMTP_PORT} as={SMTP_USER} to={EMAIL_TO}")

        logger.info("📧 Export email sent.")
    except Exception as e:
        logger.exception("Failed to send export email")


def _run_export_and_email():
    try:
        # IST-aligned window
        now_ist = datetime.now(IST_TZ)  # use your single pytz timezone object
        to_ist = now_ist.replace(minute=0, second=0, microsecond=0)
        from_ist = to_ist - timedelta(days=3)   # <-- last 3 days

        # Convert IST -> naive UTC for Mongo (if DB stores UTC)
        from_utc = from_ist.astimezone(pytz.utc).replace(tzinfo=None)
        to_utc = to_ist.astimezone(pytz.utc).replace(tzinfo=None)

        xlsx_bytes, fname = _export_xlsx_bytes(from_utc, to_utc)

        subject = f"[Peekori Admin] Export (IST {from_ist:%Y-%m-%d %H:%M} → {to_ist:%Y-%m-%d %H:%M})"
        body_html = f"""
        <html><body style="font-family: Arial, sans-serif;">
          <p>Attached export for the <b>last 3 days</b> (IST).</p>
          <ul>
            <li><b>Window (IST):</b> {from_ist:%Y-%m-%d %H:%M} → {to_ist:%Y-%m-%d %H:%M}</li>
          </ul>
        </body></html>
        """
        _send_email_with_attachment(subject, body_html, fname, xlsx_bytes)
        logger.info("✅ Scheduled export completed")
    except Exception:
        logger.exception("Scheduled export failed")

async def _run_feedback_emails_once():
    try:
        cron_feedback_emails(limit=200)
    except Exception:
        logger.exception("Feedback email cron failed")
@app.get("/api/orders/meta/by-job/{job_id}")
def order_meta_by_job(job_id: str):
    doc = orders_collection.find_one(
        {"job_id": job_id},
        {"_id": 0, "book_id": 1, "book_style": 1}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    # normalize keys if you want
    return {
        "book_id": doc.get("book_id"),
        "book_style": doc.get("book_style")
    }


def chunked_iterable(items: List, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


async def send_nudge_batches(batch_size: int = 200, days_window: int = 7):
    ist = ZoneInfo("Asia/Kolkata")
    now_ist = datetime.now(ist)
    logger.info(f"Starting nudge batch job (snapshot {now_ist.isoformat()})")

    try:
        candidates = await asyncio.to_thread(
            _fetch_nudge_candidates_compact, days_window
        )
    except Exception as e:
        logger.exception("Failed to fetch nudge candidates: %s", e)
        return

    total = len(candidates)
    if total == 0:
        logger.info("No nudge candidates found (last %d days).", days_window)
        return

    logger.info(
        f"Found {total} eligible nudge candidates — batching {batch_size} per run."
    )

    for batch in chunked_iterable(candidates, batch_size):
        for user in batch:
            email = user.get("email")
            user_name = user.get("user_name")
            child_name = user.get("name")
            job_id = user.get("job_id")
            book_id = user.get("book_id")
            days = user.get("days_since_created")
            current_stage = int(user.get("nudge_stage", 0))

            # Decide which stage to send
            desired_stage = None
            if days == 1 and current_stage == 0:
                desired_stage = 1
            elif days == 2 and current_stage == 1:
                desired_stage = 2

            if desired_stage is None:
                logger.debug(
                    f"Skipping {email} (job_id={job_id}) days={days} stage={current_stage}"
                )
                continue

            preview_link = (
                user.get("preview_url")
                or f"https://peekori.com/preview?job_id={job_id}&name={child_name}&book_id={book_id}"
            )

            # ---- retry cap check ----
            history = user.get("nudge_history", [])
            stage_entry = next(
                (h for h in history if h.get("stage") == desired_stage),
                None
            )

            if stage_entry and stage_entry.get("status") == "failed":
                attempts = stage_entry.get("attempts", 0)
                if attempts >= 5:
                    logger.warning(
                        f"Skipping job_id={job_id} stage={desired_stage} after {attempts} failures"
                    )
                    continue

            def _send_and_record():
                try:
                    # ---- send mail ----
                    if desired_stage == 1:
                        send_stage1_nudge_email(
                            email=email,
                            user_name=user_name,
                            child_name=child_name,
                            preview_link=preview_link,
                        )
                    elif desired_stage == 2:
                        send_stage2_nudge_email(
                            email=email,
                            user_name=user_name,
                            child_name=child_name,
                            preview_link=preview_link,
                        )
                    else:
                        return

                    # ---- advance stage atomically ----
                    res = orders_collection.update_one(
                        {"job_id": job_id, "nudge_stage": current_stage},
                        {
                            "$set": {
                                "nudge_stage": desired_stage,
                                "nudge_last_sent_at": datetime.now(timezone.utc),
                            }
                        }
                    )

                    if res.matched_count == 0:
                        logger.warning(
                            "Race condition: order %s stage changed, skipping update",
                            job_id,
                        )
                        return

                    # ---- mark history as sent ----
                    upsert_nudge_history(
                        job_id=job_id,
                        stage=desired_stage,
                        status="sent",
                        error=None,
                    )

                    logger.info(
                        f"✅ Sent stage {desired_stage} nudge to {email} (job_id={job_id})"
                    )

                except Exception as exc:
                    # ---- overwrite failure state ----
                    upsert_nudge_history(
                        job_id=job_id,
                        stage=desired_stage,
                        status="failed",
                        error=str(exc),
                    )

                    logger.exception(
                        f"❌ Failed sending stage {desired_stage} to {email}: {exc}"
                    )

            await asyncio.to_thread(_send_and_record)

    logger.info("Completed all nudge batches.")

def upsert_nudge_history(
    job_id: str,
    stage: int,
    status: str,
    error: str | None = None,
):
    now = datetime.now(timezone.utc)

    # Try updating existing stage entry
    res = orders_collection.update_one(
        {"job_id": job_id, "nudge_history.stage": stage},
        {
            "$set": {
                "nudge_history.$.status": status,
                "nudge_history.$.at": now,
                "nudge_history.$.error": error[:1000] if error else None,
            },
            "$inc": {
                "nudge_history.$.attempts": 1
            },
        }
    )

    # If stage entry does not exist, insert once
    if res.matched_count == 0:
        orders_collection.update_one(
            {"job_id": job_id},
            {
                "$push": {
                    "nudge_history": {
                        "stage": stage,
                        "status": status,
                        "via": "email",
                        "attempts": 1,
                        "at": now,
                        "error": error[:1000] if error else None,
                    }
                }
            }
        )



def send_stage1_nudge_email(
    email: str,
    user_name: str | None,
    child_name: str | None,
    preview_link: str
):
    user_name = ((user_name or "").strip().title()) or "there"
    child_name = ((child_name or "").strip().title()) or "your child"

    subject = f"{child_name}'s Peekori Storybook is waiting!"

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <p>Hi <strong>{user_name}</strong>,</p>

        <p>
          We noticed you began crafting a personalized storybook for
          <strong>{child_name}</strong> — and it’s already looking magical!
        </p>

        <p>
          Just one more step to bring it to life:
          preview the story and place your order whenever you’re ready.
        </p>

        <p style="margin: 32px 0;">
          <a href="{preview_link}"
             style="background-color: #5784ba; color: white;
                    padding: 14px 28px; border-radius: 6px;
                    text-decoration: none; font-weight: bold;">
            Preview & Continue
          </a>
        </p>

        <p>
          Your story is safe and waiting.
          We’d love for <strong>{child_name}</strong> to see themselves in a story
          made just for them.
        </p>

        <p>
          Warm wishes,<br>
          <strong>The Peekori Team</strong>
        </p>
      </body>
    </html>
    """

    _send_html_email(email, subject, html)


def send_stage2_nudge_email(
    email: str,
    user_name: str | None,
    child_name: str | None,
    preview_link: str
):
    user_name = ((user_name or "").strip().title()) or "there"
    child_name = ((child_name or "").strip().title()) or "your child"

    subject = f"Final reminder — {child_name}'s storybook is still waiting"

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #222;">
        <p>Hi <strong>{user_name}</strong>,</p>

        <p>
          {child_name}’s personalised story is ready —
          over 300 parents completed their orders within 48 hours
          and loved the results.
        </p>

        <p>
          Complete the order now for faster dispatch
          and a keepsake {child_name} will treasure.
        </p>

        <p style="margin: 22px 0;">
          <a href="{preview_link}"
             style="display: inline-block;
                    padding: 12px 20px;
                    border-radius: 6px;
                    text-decoration: none;
                    font-weight: 600;">
            Finish & Order Now
          </a>
        </p>

        <p>
          Use code <strong>FAST10</strong> for 10% off —
          valid for the next 24 hours only.
        </p>

        <p>
          Need help finishing up?
          Reply to this email and we’ll take care of the last steps.
        </p>

        <p>
          Warmly,<br>
          <strong>The Peekori Team</strong>
        </p>
      </body>
    </html>
    """

    _send_html_email(email, subject, html)



def _fetch_nudge_candidates_compact(days_window: int = 7) -> List[Dict]:

    ist = ZoneInfo("Asia/Kolkata")
    now_ist = datetime.now(ist)
    cutoff_ist = now_ist - timedelta(days=days_window)
    cutoff_utc = cutoff_ist.astimezone(timezone.utc)

    pipeline = [
        {"$match": {
            "created_at": {"$gte": cutoff_utc},
            "email": {"$exists": True, "$ne": None, "$not": {"$regex": "@lhmm\\.in$", "$options": "i"}},
            "workflows": {"$exists": True}
        }},
        {"$group": {
            "_id": "$email",
            "docs": {"$push": "$$ROOT"},
            "has_paid_order": {"$max": {"$cond": [{"$eq": ["$paid", True]}, 1, 0]}},
            "latest_created_at": {"$max": "$created_at"}
        }},
        {"$match": {"has_paid_order": 0}},
        {"$project": {
            "email": "$_id",
            "latest_doc": {
                "$arrayElemAt": [
                    {"$filter": {"input": "$docs", "as": "doc", "cond": {
                        "$eq": ["$$doc.created_at", "$latest_created_at"]}}}, 0
                ]
            }
        }},
        {"$replaceRoot": {"newRoot": "$latest_doc"}},
        {"$match": {
            "paid": False,
            "$or": [{"nudge_stage": {"$exists": False}}, {"nudge_stage": {"$in": [0, 1]}}]
        }},
        {"$addFields": {
            "wf_array": {"$objectToArray": "$workflows"},
            "wf_count": {"$size": {"$objectToArray": "$workflows"}}
        }},
        {"$match": {"wf_count": 13}},
        {"$match": {
            "$expr": {
                "$allElementsTrue": {
                    "$map": {"input": "$wf_array", "as": "w", "in": {"$eq": ["$$w.v.status", "completed"]}}
                }
            }
        }},
        {"$project": {
            "_id": 0,
            "email": 1,
            "name": 1,
            "user_name": 1,
            "job_id": 1,
            "created_at": 1,
            "nudge_stage": {"$ifNull": ["$nudge_stage", 0]},
            "nudge_history": {"$ifNull": ["$nudge_history", []]}
        }}
    ]

    results = list(orders_collection.aggregate(pipeline))

    filtered = []
    for r in results:
        ca = r.get("created_at")
        if isinstance(ca, datetime):
            days = (now_ist.date() - ca.astimezone(ist).date()).days
            r["days_since_created"] = days
        else:
            r["days_since_created"] = None

        # skip same day
        if r["days_since_created"] is None or r["days_since_created"] == 0:
            continue

        filtered.append(r)
    return filtered

def personalize_pronoun(gender: str) -> str:
    gender = gender.strip().lower()
    if gender == "boy":
        return "his"
    elif gender == "girl":
        return "her"
    else:
        return "their"  # fallback to original if gender is unknown


@app.post("/api/send-feedback-email/{job_id}")
def send_feedback_email(job_id: str, background_tasks: BackgroundTasks):
    # 1) Find the order
    order = orders_collection.find_one({"job_id": job_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    recipient_email = order.get("email", "")
    if not recipient_email:
        raise HTTPException(
            status_code=400, detail="No email found for this order"
        )
    # 2) Check if feedback email was already sent for this email
    already_sent_for_email = orders_collection.find_one(
        {"email": recipient_email, "feedback_email_sent": True}
    )
    if already_sent_for_email:
        logger.info(
            f"⚠️ Feedback email already sent earlier for {recipient_email}, skipping."
        )
        return {
            "status": "already_sent",
            "message": "Feedback email already sent for this customer",
            "email": recipient_email,
        }

    try:
        # 3) Build HTML (unchanged)
        html_content = f"""
        <html>
        <head>
        <meta charset="UTF-8">
        <meta name="color-scheme" content="light">
        <meta name="supported-color-schemes" content="light">
        <title>We'd love your feedback</title>
        <style>
        @keyframes shine-sweep {{
          0%   {{ transform: translateX(-100%) rotate(45deg); }}
          50%  {{ transform: translateX(100%)  rotate(45deg); }}
          100% {{ transform: translateX(100%)  rotate(45deg); }}
        }}
        .review-btn {{
          position: relative;
          display: inline-block;
          border-radius: 20px;
          font-family: Arial, Helvetica, sans-serif;
          font-weight: bold;
          text-decoration: none;
          color: #ffffff !important;
          background-color: #5784ba;
          overflow: hidden;
          padding: 12px 24px;
          font-size: 16px;
        }}
        .review-btn::before {{
          content: "";
          position: absolute;
          top: 0;
          left: -50%;
          height: 100%;
          width: 200%;
          background: linear-gradient(120deg, transparent 0%, rgba(255,255,255,0.6) 50%, transparent 100%);
          animation: shine-sweep 4s infinite;
        }}
        @media only screen and (max-width: 480px) {{
            h2 {{ font-size: 15px !important; }}
            p {{ font-size: 15px !important; }}
            a {{ font-size: 15px !important; }}
            .title-text {{ font-size: 18px !important; }}
            .small-text {{ font-size: 12px !important; }}
            .logo-img {{ width: 300px !important; }}
            .review-btn {{ font-size: 13px !important; padding: 10px 16px !important; width: 100% !important; text-align: center !important; }}
            .browse-now-btn {{
              font-size: 12px !important;
              padding: 8px 12px !important;
            }}
        }}
        </style>

        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f7f7f7; padding: 20px; margin: 0;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff" style="max-width: 600px; margin: 0 auto; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
            <tr>
            <td style="padding: 20px;">
                <div style="text-align: left; margin-bottom: 20px;">
                <img src="https://peekori.com/peekori-meta.png" alt="Peekori" class="logo-img" style="max-width: 100px;">
                </div>

                <h2 style="color: #333; font-size: 15px;">Hey {order.get("user_name")},</h2>

                <p style="font-size: 14px; color: #555;">
                We truly hope {order.get("name", "")} is enjoying {personalize_pronoun(order.get("gender", "   "))} magical storybook, <strong>{generate_book_title(order.get("book_id"), order.get("name"))}</strong>! 
                At Peekori, we are dedicated to crafting personalized storybooks that inspire joy, imagination, and lasting memories for every child. 
                Your feedback means the world to us. We'd be grateful if you could share your experience.
                </p>

                <p style="font-size: 14px; color: #555;">Please share your feedback with us:</p>

                <p style="text-align: left; margin: 30px 0;">
                <a href="https://search.google.com/local/writereview?placeid=ChIJn5mGENoTrjsRPHxH86vgui0"
                    class="review-btn"
                    style="background-color: #5784ba; color: #ffffff; text-decoration: none; border-radius: 20px;">
                    Leave a Google Review
                </a>
                </p>

                <p style="font-size: 14px; color: #555; text-align: left;">
                Thanks,<br>Team Peekori
                </p>

                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">

                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top: 30px;">
                <tr>
                    <td colspan="2" style="padding: 10px 0; text-align: left;">
                    <p class="title-text" style="font-size: 18px; margin: 0; font-weight: bold; color: #000;">
                            {generate_book_title(order.get("book_id"), order.get("name"))}
                            </p>
                    </td>
                </tr>

                <tr>
                    <td style="padding: 0; vertical-align: top; font-size: 12px; color: #333; font-weight: 500;">
                    Order reference ID: <span>{order.get("order_id", "N/A")}</span>
                    </td>
                    <td style="padding: 0; text-align: right; font-size: 12px; color: #333; font-weight: 500;">
                    Ordered: <span>{format_date(order.get("approved_at", ""))}</span>
                    </td>
                </tr>

                <tr>
                    <td colspan="2" style="padding: 0; margin: 0; background-color: #f7f6cf;">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse: collapse; padding: 0; margin: 0;">
                        <tr>
                        <td style="padding: 20px; vertical-align: middle; margin: 0;">
                            
                            <p style="font-size: 15px; margin: 0;">
                        Explore more magical books in our growing collection &nbsp;
                        <button class="browse-now-btn" style="background-color:#5784ba; margin-top: 20px; border-radius: 30px;border: none;padding:10px 15px"><a href="https://peekori.com" style="color:white; font-weight: bold; text-decoration: none;">
                        Browse Now
                        </a></button>
                    </p>
                        </td>

                        <td width="300" style="padding: 0; margin: 0; vertical-align: middle;">
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse: collapse;">
                            <tr>
                                <td align="right" style="padding: 0; margin: 0;">
                                <img src="https://peekori.com/peekori-meta.png" 
                                    alt="Cover Image" 
                                    width="300" 
                                    style="display: block; border-radius: 0; margin: 0; padding: 0;">
                                </td>
                            </tr>
                            </table>
                        </td>
                        </tr>
                    </table>
                    </td>
                </tr>

                </table>

            </td>
            </tr>
        </table>
        </body>
        </html>
        """

        msg = EmailMessage()
        msg["Subject"] = f"We'd love your feedback on {order.get('name', '')}'s Storybook!"
        msg["From"] = f"Peekori Team <{os.getenv('EMAIL_ADDRESS')}>"
        msg["To"] = recipient_email
        msg.set_content("This email contains HTML content.")
        msg.add_alternative(html_content, subtype="html")

        # 4) Actually send
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            EMAIL_USER = os.getenv("EMAIL_ADDRESS")
            EMAIL_PASS = os.getenv("EMAIL_PASSWORD")
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)

        logger.info(f"✅ Feedback email sent to {recipient_email}")

        # 5) Mark ALL orders for this email as feedback_email_sent
        orders_collection.update_many(
            {"email": recipient_email},
            {"$set": {"feedback_email_sent": True}},
        )

    except Exception as e:
        logger.error(f"❌ Failed to send feedback email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email.")

    # 6) Consistent response for both cron and manual call
    return {
        "status": "sent",
        "message": "Feedback email sent",
        "email": recipient_email,
    }


@app.post("/cron/feedback-emails")
def cron_feedback_emails(limit: int = 200):

    blocked_emails = orders_collection.distinct(
        "email",
        {
            "$or": [
                {"feedback_email_sent": True},
                {"feedback_email": True},
            ]
        }
    )

    pipeline = [
        {
            "$match": {
                "email": {"$exists": True, "$ne": "", "$nin": blocked_emails},
                "feedback_email_sent": {"$ne": True},
                "feedback_email": {"$ne": True},
                "processed_at": {"$exists": True, "$ne": None},
            }
        },
        {
            "$lookup": {
                "from": "shipping_details",
                "localField": "order_id",
                "foreignField": "order_id",
                "as": "shipping_docs",
            }
        },
        {"$unwind": "$shipping_docs"},
        {
            "$match": {
                "$or": [
                    {"shipping_docs.shiprocket_data.current_status": "DELIVERED"},
                    {"shipping_docs.shiprocket_data.shipment_status": "DELIVERED"},
                ],
                "shipping_docs.shiprocket_data.current_timestamp_iso": {
                    "$exists": True,
                    "$ne": None,
                },
            }
        },
        {
            "$addFields": {
                "processed_dt": {"$toDate": "$processed_at"},
                "delivered_dt": {
                    "$toDate": "$shipping_docs.shiprocket_data.current_timestamp_iso"
                },
            }
        },
        {
            "$addFields": {
                "processing_to_delivery_days": {
                    "$dateDiff": {
                        "startDate": "$processed_dt",
                        "endDate": "$delivered_dt",
                        "unit": "day",
                        "timezone": "Asia/Kolkata",
                    }
                }
            }
        },
        {
            "$match": {
                "$expr": {
                    "$and": [
                        {"$gte": ["$processing_to_delivery_days", 0]},
                        {"$lte": ["$processing_to_delivery_days", 8]},
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$email",
                "sample": {"$first": "$$ROOT"},
            }
        },
        {"$replaceRoot": {"newRoot": "$sample"}},
        {"$limit": int(limit)},
    ]

    candidates = list(orders_collection.aggregate(pipeline))

    results = {
        "total": len(candidates),
        "sent": 0,
        "skipped": 0,
        "errors": 0,
    }

    for c in candidates:
        try:
            res = send_feedback_email(c["job_id"], BackgroundTasks())
            if res.get("status") == "sent":
                results["sent"] += 1
            else:
                results["skipped"] += 1
        except Exception:
            results["errors"] += 1

    return results

def _format_ec2_status_table(rows: List[dict]) -> pd.DataFrame:
    """
    Shape EC2 rows into the exact table:
    Name, InstanceId, State, OnOff('on'/'off'), InstanceStatus, SystemStatus,
    PublicIP, PrivateIP, LaunchTime_ISO (YYYY-MM-DD), CheckedAt_IST (YYYY-MM-DD)
    """
    df = pd.DataFrame(rows or [])
    if df.empty:
        # return empty frame with expected columns so Excel writer doesn't choke
        return pd.DataFrame(columns=[
            "Name", "InstanceId", "State", "OnOff", "InstanceStatus", "SystemStatus",
            "PublicIP", "PrivateIP", "LaunchTime_ISO", "CheckedAt_IST"
        ])

    # Map OnOff 1/0 -> "on"/"off"
    df["OnOff"] = df.get("OnOff", 0).map({1: "on", 0: "off"}).fillna("off")

    # Resolve statuses from DescribeInstanceStatus (include stopped)
    status_map = {}
    ec2 = get_ec2_client()
    ids = [i for i in df.get("InstanceId", []).tolist(
    ) if isinstance(i, str) and i.startswith("i-")]
    for i in range(0, len(ids), 100):
        chunk = ids[i:i+100]
        try:
            resp = ec2.describe_instance_status(
                InstanceIds=chunk, IncludeAllInstances=True)
            for st in resp.get("InstanceStatuses", []):
                iid = st.get("InstanceId", "")
                inst_status = (st.get("InstanceStatus", {}) or {}).get(
                    "Status", "not-applicable")
                sys_status = (st.get("SystemStatus", {}) or {}
                              ).get("Status", "not-applicable")
                status_map[iid] = (
                    inst_status or "not-applicable", sys_status or "not-applicable")
        except ClientError as e:
            logging.warning(
                "describe_instance_status failed for %s: %s", chunk, e)

    df["InstanceStatus"] = df["InstanceId"].map(
        lambda x: status_map.get(x, ("not-applicable", "not-applicable"))[0])
    df["SystemStatus"] = df["InstanceId"].map(
        lambda x: status_map.get(x, ("not-applicable", "not-applicable"))[1])

    # LaunchTime -> UTC date string (YYYY-MM-DD), safe for Excel
    def _to_naive_utc(x):
        if isinstance(x, datetime):
            return x.astimezone(timezone.utc).replace(tzinfo=None) if x.tzinfo else x
        return x
    launch_col = "LaunchTime" if "LaunchTime" in df.columns else "LaunchTime_ISO"
    df["LaunchTime_ISO"] = df.get(launch_col, "").apply(_to_naive_utc).apply(
        lambda d: d.strftime("%Y-%m-%d") if isinstance(d,
                                                       datetime) else (str(d) if d else "")
    )

    # CheckedAt_IST = today's IST date
    df["CheckedAt_IST"] = datetime.now(IST_TZ).date().isoformat()

    # Select & order columns
    out = df.reindex(columns=[
        "Name", "InstanceId", "State", "OnOff", "InstanceStatus", "SystemStatus",
        "PublicIP", "PrivateIP", "LaunchTime_ISO", "CheckedAt_IST"
    ])
    # Fill NAs with empty string
    return out.fillna("")


def _export_xlsx_bytes(from_dt_utc: datetime, to_dt_utc: datetime) -> Tuple[bytes, str]:
    # ---- helpers ----
    def _load_df_for_collection(mongo_collection) -> pd.DataFrame:
        mongo_filter = {TIMESTAMP_FIELD: {
            "$gte": from_dt_utc, "$lte": to_dt_utc}}
        projection = {"_id": 0}
        data = list(mongo_collection.find(mongo_filter, projection))
        rows_out = []
        if data:
            for row in data:
                r = dict(row)
                base_ts = _parse_dt(r.get(TIMESTAMP_FIELD))
                r["date"] = ""
                r["hour"] = ""
                r["date-hour"] = ""
                r["ist-date"] = ""
                r["ist-hour"] = ""
                if base_ts is not None:
                    ist_ts = base_ts + IST_OFFSET
                    r["date"] = base_ts.strftime("%d/%m/%Y")
                    r["hour"] = base_ts.strftime("%H")
                    r["date-hour"] = ist_ts.strftime("%Y-%m-%d %H:%M:%S")
                    r["ist-date"] = ist_ts.strftime("%d/%m/%Y")
                    r["ist-hour"] = ist_ts.strftime("%H")
                rows_out.append(r)
            df = pd.DataFrame(rows_out)
        else:
            df = pd.DataFrame(columns=["ist-date", "ist-hour"])

        for col in ["ist-date", "ist-hour", "room_id"]:
            if col not in df.columns:
                df[col] = ""
        if "ist-hour" in df.columns:
            df["ist-hour"] = df["ist-hour"].astype(str)
        return df

    def _build_pivot(df: pd.DataFrame) -> pd.DataFrame:
        hours = [f"{h:02d}" for h in range(24)]
        if df.empty:
            return pd.DataFrame([{"error": "No data in range"}])
        try:
            piv = pd.pivot_table(
                df, index="ist-date", columns="ist-hour",
                values="room_id", aggfunc="count", fill_value=0
            )
            piv = piv.reindex(columns=hours, fill_value=0)

            def _date_key(x):
                try:
                    return datetime.strptime(x, "%d/%m/%Y")
                except Exception:
                    return x
            piv = piv.sort_index(key=lambda idx: [_date_key(x) for x in idx])
            piv["Total"] = piv.sum(axis=1)
            piv.loc["Total"] = piv.sum(numeric_only=True)
            return piv
        except Exception as e:
            return pd.DataFrame([{"error": f"pivot build failed: {e}"}])

    def _slice_last_n_days(piv: pd.DataFrame, n_days: int) -> pd.DataFrame:
        if piv.empty or "error" in piv.columns:
            return piv
        base = piv.copy()
        if "Total" in base.index:
            base = base.drop(index="Total")
        # sort by real date

        def _parse_date_idx(idx: pd.Index) -> list:
            out = []
            for v in idx:
                try:
                    out.append(datetime.strptime(v, "%d/%m/%Y"))
                except Exception:
                    out.append(v)
            return out
        sort_pairs = sorted(zip(_parse_date_idx(base.index),
                            base.index), key=lambda x: x[0])
        keep_labels = [lbl for _, lbl in sort_pairs[-n_days:]]
        section = base.loc[keep_labels].copy()
        hours = [f"{h:02d}" for h in range(24)]
        for h in hours:
            if h not in section.columns:
                section[h] = 0
        section = section.reindex(columns=hours, fill_value=0)
        section["Total"] = section.sum(axis=1)
        section.loc[f"Total ({n_days}d)"] = section.sum(numeric_only=True)
        return section

    # ---- main & yippee pivots ----
    df_main = _load_df_for_collection(collection_df)
    pivot_main_full = _build_pivot(df_main)

    # filename
    filename = (
        f"export_{from_dt_utc.strftime('%Y%m%d_%H%M%S')}_to_{to_dt_utc.strftime('%Y%m%d_%H%M%S')}.xlsx"
        if not df_main.empty
        else f"export_empty_{from_dt_utc.date()}_{to_dt_utc.date()}.xlsx"
    )

    df_yip = _load_df_for_collection(collection_yippee)
    pivot_yip_full = _build_pivot(df_yip)

    # keep full main block as-is; yippee = last 4 IST days
    pivot_main = pivot_main_full.copy()
    pivot_yippee = _slice_last_n_days(pivot_yip_full, 4)

    # ---- combined (DF + Yippee) hour-wise sums per day ----
    def _strip_totals(piv: pd.DataFrame) -> pd.DataFrame:
        if piv.empty or "error" in piv.columns:
            return pd.DataFrame()
        if "Total" in piv.index:
            piv = piv.drop(index="Total")
        hours = [f"{h:02d}" for h in range(24)]
        cols = [c for c in piv.columns if c in hours]
        return piv[cols].copy()

    hours = [f"{h:02d}" for h in range(24)]
    m_hours = _strip_totals(pivot_main_full)
    y_hours = _strip_totals(pivot_yip_full)

    # union of dates
    all_days = sorted(set(m_hours.index) | set(y_hours.index),
                      key=lambda x: datetime.strptime(x, "%d/%m/%Y") if isinstance(x, str) else x)
    combined = pd.DataFrame(0, index=all_days, columns=hours)
    if not m_hours.empty:
        m_aligned = m_hours.reindex(
            index=all_days, columns=hours, fill_value=0)
        combined = combined.add(m_aligned, fill_value=0)
    if not y_hours.empty:
        y_aligned = y_hours.reindex(
            index=all_days, columns=hours, fill_value=0)
        combined = combined.add(y_aligned, fill_value=0)
    # totals
    if not combined.empty:
        combined["Total"] = combined.sum(axis=1)
        combined.loc["Total (COMBINED)"] = combined.sum(numeric_only=True)
    else:
        combined = pd.DataFrame([{"info": "No data to combine"}])

    # ---- Write workbook with headings and blocks ----
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        ws_name = "pivot"
        start_row = 0

        # Heading 1
        pd.DataFrame({"Dark fantasy": []}).to_excel(
            writer, sheet_name=ws_name, index=False, header=True, startrow=start_row
        )
        start_row += 1

        # DF block
        pivot_main.to_excel(writer, sheet_name=ws_name, startrow=start_row)
        start_row += (pivot_main.shape[0] + 4)  # leave some space

        # Heading 2
        pd.DataFrame({"Yippee": []}).to_excel(
            writer, sheet_name=ws_name, index=False, header=True, startrow=start_row
        )
        start_row += 1

        # Yippee block
        pivot_yippee.to_excel(writer, sheet_name=ws_name, startrow=start_row)
        start_row += (pivot_yippee.shape[0] + 4)

        # Heading 3
        pd.DataFrame({"Combined (DF + Yippee)": []}).to_excel(
            writer, sheet_name=ws_name, index=False, header=True, startrow=start_row
        )
        start_row += 1

        # Combined block
        combined.to_excel(writer, sheet_name=ws_name, startrow=start_row)

        # EC2 status sheet
        ec2_rows, ec2_err = _get_ec2_status_rows()
        if ec2_err:
            ec2_df = pd.DataFrame([{"error": ec2_err}])
            ec2_sheet_name = "ec2_status_error"
        else:
            ec2_df = _format_ec2_status_table(ec2_rows)
            if not ec2_df.empty:
                ec2_df["__on__"] = (ec2_df["OnOff"] == "on").astype(int)
                ec2_df = ec2_df.sort_values(["__on__", "Name", "InstanceId"], ascending=[
                                            False, True, True]).drop(columns="__on__")
            ec2_sheet_name = "ec2_status"
        ec2_df.to_excel(writer, index=False, sheet_name=ec2_sheet_name)

        # Freeze panes (optional: top headings won’t freeze across all blocks cleanly)
        ws2 = writer.sheets.get(ec2_sheet_name)
        if ws2 is not None:
            ws2.freeze_panes = "A2"

        # Basic formatting for headings (bold) via openpyxl
        ws = writer.sheets.get(ws_name)
        if ws is not None:
            for r in [1,                     # "Dark fantasy"
                      1 + pivot_main.shape[0] + 4 + 1,  # "Yippee"
                      # "Combined"
                      1 + pivot_main.shape[0] + 4 + 1 + pivot_yippee.shape[0] + 4 + 1]:
                try:
                    ws.cell(row=r, column=1).font = ws.cell(
                        row=r, column=1).font.copy(bold=True)
                except Exception:
                    pass

    buf.seek(0)
    return buf.read(), filename



def _build_loc_match(loc: str) -> dict:
    loc = (loc or "IN").upper()

    # CURRENT BEHAVIOUR (your existing India behaviour) → use this for "ALL"
    if loc in ("ALL", "IN"):
        in_clause = {"$or": [{"locale": "IN"}, {"LOC": "IN"}]}
        empty_or_missing = {
            "$or": [
                {"locale": {"$exists": False}},
                {"locale": None},
                {"locale": ""},
                {"LOC": {"$exists": False}},
                {"LOC": None},
                {"LOC": ""},
            ]
        }
        return {"$or": [in_clause, empty_or_missing]}

    # STRICT INDIA ONLY
    if loc in ("IN_ONLY", "INDIA"):
        return {"$or": [{"locale": "IN"}, {"LOC": "IN"}]}

    # everything else – simple exact match
    return {"$or": [{"locale": loc}, {"LOC": loc}]}

def _periods_custom(start_date: str, end_date: str) -> Tuple[datetime, datetime, datetime, datetime, str]:
    start_ist = _ist_midnight(_parse_ymd_ist(start_date))
    # inclusive end_date → exclusive next midnight
    end_ist = _ist_midnight(_parse_ymd_ist(end_date)) + timedelta(days=1)
    if end_ist <= start_ist:
        raise HTTPException(
            status_code=400, detail="start_date must be before or equal to end_date")

    # previous window: immediately preceding the current window, same length
    span_days = (end_ist - start_ist).days
    prev_end_ist = start_ist
    prev_start_ist = prev_end_ist - timedelta(days=span_days)

    return (
        start_ist.astimezone(UTC),
        end_ist.astimezone(UTC),
        prev_start_ist.astimezone(UTC),
        prev_end_ist.astimezone(UTC),
        "day",
    )

def _ist_midnight(dt_ist: datetime) -> datetime:
    return dt_ist.replace(hour=0, minute=0, second=0, microsecond=0)

def _parse_ymd_ist(d: str) -> datetime:
    try:
        y, m, dd = map(int, d.split("-"))
        return datetime(y, m, dd, tzinfo=TZ_IST)
    except Exception:
        raise HTTPException(
            status_code=400, detail=f"Invalid date: {d}. Use YYYY-MM-DD")

def _labels_for(range_key: RangeKey, start_utc: datetime, end_utc: datetime) -> List[str]:
    if range_key == "1d":
        labels = []
        cur = start_utc.astimezone(TZ_IST)
        for _ in range(24):
            labels.append(cur.strftime("%Y-%m-%d %H:00"))
            cur += timedelta(hours=1)
        return labels
    out = []
    cur = start_utc.astimezone(TZ_IST)
    end = end_utc.astimezone(TZ_IST)
    while cur < end:
        out.append(cur.strftime("%Y-%m-%d"))
        cur += timedelta(days=1)
    return out

def _periods(range_key: RangeKey, _now_utc_ignored: datetime) -> Tuple[datetime, datetime, datetime, datetime, str]:
    now_ist = _now_ist()

    if range_key == "1d":
        end_curr_ist = now_ist.replace(
            minute=0, second=0, microsecond=0) + timedelta(hours=1)
        start_curr_ist = end_curr_ist - timedelta(hours=24)
        end_prev_ist = end_curr_ist - timedelta(days=7)
        start_prev_ist = start_curr_ist - timedelta(days=7)
        gran = "hour"

    elif range_key == "this_month":
        # current: [1st of this month 00:00 IST, 1st of next month 00:00 IST)
        first_curr = _ist_midnight(now_ist).replace(day=1)
        # compute 1st of next month
        if first_curr.month == 12:
            first_next = first_curr.replace(year=first_curr.year + 1, month=1)
        else:
            first_next = first_curr.replace(month=first_curr.month + 1)
        start_curr_ist = first_curr
        end_curr_ist = first_next

        # previous: [1st of prev month 00:00 IST, 1st of this month 00:00 IST)
        if first_curr.month == 1:
            first_prev = first_curr.replace(year=first_curr.year - 1, month=12)
        else:
            first_prev = first_curr.replace(month=first_curr.month - 1)
        start_prev_ist = first_prev
        end_prev_ist = first_curr

        gran = "day"

    else:
        end_curr_ist = _ist_midnight(
            now_ist) + timedelta(days=1)  # next IST midnight
        span = {"1w": 7, "1m": 30, "6m": 182}.get(range_key)
        if not span:
            raise HTTPException(status_code=400, detail="invalid range")
        start_curr_ist = end_curr_ist - timedelta(days=span)
        end_prev_ist = start_curr_ist
        start_prev_ist = end_prev_ist - timedelta(days=span)
        gran = "day"

    return (
        start_curr_ist.astimezone(UTC),
        end_curr_ist.astimezone(UTC),
        start_prev_ist.astimezone(UTC),
        end_prev_ist.astimezone(UTC),
        gran,
    )

def _fetch_counts(
    col: Collection,
    start_utc: datetime,
    end_utc: datetime,
    exclude_codes: List[str],
    granularity: str,
    loc_match: dict,                      # <-- NEW
) -> Dict[str, int]:
    discount_ne = [{"discount_code": {"$ne": code}} for code in exclude_codes]
    base_match = {
        "paid": True,
        "order_id": {"$regex": r"^#\d+(_\d+)?$"},
        "processed_at": {"$exists": True, "$ne": None},
    }

    # merge AND conditions safely
    ands = []
    if discount_ne:
        ands.extend(discount_ne)
    if loc_match:
        ands.append(loc_match)
    if ands:
        base_match["$and"] = ands

    pipeline = [
        {"$match": base_match},
        {"$addFields": {"processed_dt": {"$toDate": "$processed_at"}}},
        {"$match": {"processed_dt": {"$gte": start_utc, "$lt": end_utc}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d %H:00" if granularity == "hour" else "%Y-%m-%d",
                        "date": "$processed_dt",
                        "timezone": "Asia/Kolkata",
                    }
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    rows = list(col.aggregate(pipeline))
    return {r["_id"]: int(r["count"]) for r in rows}

def _now_ist():
    return datetime.now(IST_TZ)

def _fetch_jobs_created_with_preview_per_bucket(
    col: Collection,
    start_utc: datetime,
    end_utc: datetime,
    granularity: str,
    loc_match: dict,                      # <-- NEW
) -> Dict[str, int]:
    base_match = {
        PREVIEW_URL_FIELD: {"$exists": True, "$nin": [None, ""]},
        JOBS_CREATED_AT_FIELD: {"$exists": True, "$ne": None},
    }
    if loc_match:
        base_match = {"$and": [base_match, loc_match]}

    pipeline = [
        {"$match": base_match},
        {"$addFields": {
            "_dt": {
                "$cond": [
                    {"$eq": [{"$type": f"${JOBS_CREATED_AT_FIELD}"}, "date"]},
                    f"${JOBS_CREATED_AT_FIELD}",
                    {"$toDate": f"${JOBS_CREATED_AT_FIELD}"},
                ]
            }
        }},
        {"$match": {"_dt": {"$gte": start_utc, "$lt": end_utc}}},
        {"$group": {
            "_id": {
                "$dateToString": {
                    "format": "%Y-%m-%d %H:00" if granularity == "hour" else "%Y-%m-%d",
                    "date": "$_dt",
                    "timezone": "Asia/Kolkata",
                }
            },
            "count": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]
    return {r["_id"]: int(r["count"]) for r in col.aggregate(pipeline)}

def _fetch_paid_orders_per_bucket(
    col: Collection,
    start_utc: datetime,
    end_utc: datetime,
    granularity: str,
    loc_match: dict,                      # <-- NEW
) -> Dict[str, int]:
    base_match = {
        PAID_FIELD: True,
        "$or": [
            {"processed_at": {"$exists": True, "$ne": None}},
            {"created_at": {"$exists": True, "$ne": None}},
        ],
    }
    if loc_match:
        base_match = {"$and": [base_match, loc_match]}

    pipeline = [
        {"$match": base_match},
        {"$addFields": {
            "_dt": {"$toDate": {"$ifNull": ["$processed_at", "$created_at"]}}}},
        {"$match": {"_dt": {"$gte": start_utc, "$lt": end_utc}}},
        {"$group": {
            "_id": {
                "$dateToString": {
                    "format": "%Y-%m-%d %H:00" if granularity == "hour" else "%Y-%m-%d",
                    "date": "$_dt",
                    "timezone": "Asia/Kolkata",
                }
            },
            "count": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]
    return {r["_id"]: int(r["count"]) for r in col.aggregate(pipeline)}

def _fetch_revenue_per_bucket(
    col: Collection,
    start_utc: datetime,
    end_utc: datetime,
    granularity: str,
    loc_match: dict,
) -> Dict[str, float]:
    base_match = {PAID_FIELD: True}
    if loc_match:
        base_match = {"$and": [base_match, loc_match]}

    value_expr = {
        "$toDouble": {
            "$ifNull": [
                "$total_amount",
                {"$ifNull": [
                    "$total_price",
                    {"$ifNull": [
                        "$amount",
                        {"$ifNull": ["$price", 0]}
                    ]}
                ]}
            ]
        }
    }

    pipeline = [
        {"$match": base_match},
        {"$addFields": {
            "_dt": {"$toDate": {"$ifNull": ["$processed_at", "$created_at"]}}}},
        {"$match": {"_dt": {"$gte": start_utc, "$lt": end_utc}}},
        {"$group": {
            "_id": {
                "$dateToString": {
                    "format": "%Y-%m-%d %H:00" if granularity == "hour" else "%Y-%m-%d",
                    "date": "$_dt",
                    "timezone": "Asia/Kolkata",
                }
            },
            "revenue": {"$sum": value_expr},
        }},
        {"$sort": {"_id": 1}},
    ]
    rows = list(col.aggregate(pipeline))
    return {r["_id"]: float(r["revenue"]) for r in rows}


@app.get("/api/stats/orders")
def stats_orders(
    range: RangeKey = Query(
        "1w", description="1d | 1w | 1m | 6m | this_month"),
    start_date: Optional[str] = Query(
        None, description="YYYY-MM-DD (only when using custom)"),
    end_date: Optional[str] = Query(
        None, description="YYYY-MM-DD (only when using custom)"),
    exclude_codes: List[str] = Query(["TEST", "COLLAB", "REJECTED"]),
    loc: str = Query(
        "IN", description="Country code; IN includes empty/missing"),
):
    now_utc = datetime.now(tz=UTC)
    if start_date and end_date:
        curr_start_utc, curr_end_utc, prev_start_utc, prev_end_utc, gran = _periods_custom(
            start_date, end_date)
    else:
        curr_start_utc, curr_end_utc, prev_start_utc, prev_end_utc, gran = _periods(
            range, now_utc)

    labels = _labels_for("1d" if gran == "hour" else range,
                         curr_start_utc, curr_end_utc)
    prev_labels = _labels_for(
        "1d" if gran == "hour" else range, prev_start_utc, prev_end_utc)

    loc_match = _build_loc_match(loc)

    curr_map = _fetch_counts(
        orders_collection, curr_start_utc, curr_end_utc,  exclude_codes, gran, loc_match)
    prev_map = _fetch_counts(
        orders_collection, prev_start_utc, prev_end_utc, exclude_codes, gran, loc_match)

    current = [int(curr_map.get(k, 0)) for k in labels]
    previous = [int(prev_map.get(k, 0)) for k in prev_labels]

    return {
        "labels": labels,
        "current": current,
        "previous": previous,
        "exclusions": exclude_codes,
        "granularity": gran,
    }

@app.get("/api/stats/revenue", tags=["stats"])
def stats_revenue(
    range: RangeKey = Query("1w"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    loc: str = Query(
        "IN", description="Country code; IN includes empty/missing"),
):
    now_utc = datetime.now(tz=UTC)
    if start_date and end_date:
        cs, ce, ps, pe, gran = _periods_custom(start_date, end_date)
    else:
        cs, ce, ps, pe, gran = _periods(range, now_utc)

    labels = _labels_for("1d" if gran == "hour" else range, cs, ce)
    prev_labels = _labels_for("1d" if gran == "hour" else range, ps, pe)

    loc_match = _build_loc_match(loc)

    rev_curr = _fetch_revenue_per_bucket(
        orders_collection, cs, ce, gran, loc_match)
    rev_prev = _fetch_revenue_per_bucket(
        orders_collection, ps, pe, gran, loc_match)

    current = [float(rev_curr.get(k, 0.0)) for k in labels]
    previous = [float(rev_prev.get(k, 0.0)) for k in prev_labels]

    return {
        "labels": labels,
        "current": current,
        "previous": previous,
        "granularity": gran,
        "currency_hint": "mixed",  # you can switch to currency-specific buckets later if needed
    }



@app.get("/api/stats/ship-status")
def stats_ship_status(
    range: str = Query(
        "1w", description="range key like 1d, 1w, 1m, 6m, this_month, custom"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    printer: Optional[str] = Query("all", description="genesis | yara | all"),
    loc: Optional[str] = Query("IN", description="country code"),
):
    """
    Dynamic-activity version (batched, STRICT) – **always day-level**:

    - For each date (labels) we take paid orders whose processed_at (IST) falls into the date.
    - We select only orders routed to 'genesis' or 'yara' (or filtered by top-level printer param).
    - total = number of genesis|yara orders for that date.
    - We fetch shipping docs in a single batched query for all candidate orders.
    - For each order we look ONLY at shiprocket_data.scans and take the LAST element's 'activity' field.
    - We count occurrences of each distinct activity string per date.
    """
    order_totals_by_date: Dict[str, int] = {}

    try:
        loc_match = _build_loc_match(loc)
    except Exception:
        loc_match = None

    # ---- 1) Choose the time window & labels ----
    now_utc = datetime.now(timezone.utc)

    # We **never** want hourly buckets for this endpoint.
    # Treat '1d' as '1w' for shipment status.
    effective_range = "1w" if range == "1d" else range

    try:
        if start_date and end_date:
            # Respect custom dates (regardless of 'range' query value)
            cs, ce, ps, pe, _gran = _periods_custom(start_date, end_date)
            # Any range_key != '1d' gives day-wise labels
            labels = _labels_for("custom", cs, ce)
        else:
            cs, ce, ps, pe, gran = _periods(effective_range, now_utc)
            # gran from _periods may be "hour" for 1d, but we have already
            # normalised 1d -> 1w above, so this is always day-level here.
            labels = _labels_for(effective_range, cs, ce)

        exclude_codes = ["TEST", "COLLAB", "REJECTED"]
        if cs and ce:
            order_totals_by_date = _fetch_counts(
                orders_collection,
                cs,
                ce,
                exclude_codes,
                "day",        # ship-status is always day-level
                loc_match or {},  # may be None if _build_loc_match failed
            )

    except Exception:
        # Fallback: last 7 calendar days in IST
        today = datetime.now(timezone.utc)
        labels = []
        for i in range(6, -1, -1):
            d = (today - timedelta(days=i)).astimezone(IST_TZ)
            labels.append(d.strftime("%Y-%m-%d"))

        # ---- 2) Base order query (unchanged apart from loc filter reuse) ----
    base_match = {"paid": True, "processed_at": {"$exists": True, "$ne": None}}
    if loc_match:
        base_match = {"$and": [base_match, loc_match]}

    projection = {"order_id": 1, "processed_at": 1, "printer": 1, "_id": 0}
    cursor = orders_collection.find(base_match, projection)

    # group orders by IST date and remember printer
    orders_by_date = {k.split(" ")[0]: [] for k in labels}
    order_printer_map: dict = {}
    all_printer_candidates: set = set()

    for doc in cursor:
        try:
            dt = doc.get("processed_at")
            if isinstance(dt, str):
                dt = date_parser.isoparse(dt)
            if not dt:
                continue

            ist_d = dt.astimezone(IST_TZ).strftime("%Y-%m-%d")
            if ist_d not in orders_by_date:
                continue

            oid = doc.get("order_id")
            doc_printer = (doc.get("printer") or "").strip().lower()
            order_printer_map[oid] = doc_printer

            # respect top-level printer filter if provided
            if printer and printer.lower() not in ("all", ""):
                if doc_printer != printer.lower():
                    continue

            orders_by_date[ist_d].append(oid)

            # only genesis / yara to be considered for shipment status
            if doc_printer in ("genesis", "yara"):
                all_printer_candidates.add(oid)
        except Exception:
            continue

        # no printer candidates at all
    if not all_printer_candidates:
        rows = []
        for lbl in labels:
            date_key = lbl.split(" ")[0]
            total_orders = int(order_totals_by_date.get(date_key, 0))
            rows.append({
                "date": date_key,
                # NEW: total orders for the day (loc-filtered)
                "total": total_orders,
                "sent_to_print": 0,      # no genesis/yara orders
                "counts": {},
            })
        return {
            "labels": labels,
            "activities": [],
            "rows": rows,
            "printer": printer or "all",
        }

    # ---- 3) Fetch shiprocket scans for all candidate orders ----
    shipping_docs = list(
        shipping_collection.find(
            {"order_id": {"$in": list(all_printer_candidates)}},
            {"order_id": 1, "shiprocket_data.scans": 1},
        )
    )
    sh_map = {s.get("order_id"): s for s in shipping_docs}

    global_activity_set = set()
    rows = []

    # ---- 4) Build per-day rows ----
    for lbl in labels:
        date_key = lbl.split(" ")[0]
        order_ids = orders_by_date.get(date_key, [])

        # total orders for that day (Orders graph style, loc-filtered)
        total_orders = int(order_totals_by_date.get(date_key, 0))

        if not order_ids:
            rows.append({
                "date": date_key,
                "total": total_orders,
                "sent_to_print": 0,
                "counts": {},
            })
            continue

        # only genesis|yara for this date (sent to print)
        printer_candidates = [
            oid
            for oid in order_ids
            if (order_printer_map.get(oid) or "").lower() in ("genesis", "yara")
        ]

        sent_to_print_count = len(printer_candidates)
        counts = Counter()

        if printer_candidates:
            for oid in printer_candidates:
                s = sh_map.get(oid)
                last_activity_str = None

                if s:
                    sr_data = s.get("shiprocket_data")
                    scans = sr_data.get("scans") if isinstance(
                        sr_data, dict) else None

                    if isinstance(scans, list) and scans:
                        last = scans[-1]
                        # STRICT: only activity field
                        last_activity_str = last.get("sr-status-label")

                # if no activity or no scans/doc → mark as NEW
                act_label = str(last_activity_str).strip(
                ) if last_activity_str else "NEW"

                counts[act_label] += 1
                global_activity_set.add(act_label)

        rows.append({
            "date": date_key,
            "total": total_orders,               # NEW column value
            "sent_to_print": sent_to_print_count,
            "counts": dict(counts),
        })

    # sorted list of activity labels (NO_SCAN last)
    activities = sorted(global_activity_set,
                        key=lambda s: (s == "NEW", s.lower()))

    return {
        "labels": labels,
        "activities": activities,
        "rows": rows,
        "printer": printer or "all",
    }

@app.get("/api/stats/preview-vs-orders", tags=["stats"])
def stats_preview_vs_orders(
    range: RangeKey = Query("1w"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    loc: str = Query(
        "IN", description="Country code; IN includes empty/missing"),
):
    now_utc = datetime.now(tz=UTC)
    if start_date and end_date:
        cs, ce, ps, pe, gran = _periods_custom(start_date, end_date)
    else:
        cs, ce, ps, pe, gran = _periods(range, now_utc)

    labels = _labels_for("1d" if gran == "hour" else range, cs, ce)
    prev_labels = _labels_for("1d" if gran == "hour" else range, ps, pe)

    loc_match = _build_loc_match(loc)

    jobs_map_curr = _fetch_jobs_created_with_preview_per_bucket(
        orders_collection, cs, ce, granularity=gran, loc_match=loc_match)
    paid_map_curr = _fetch_paid_orders_per_bucket(
        orders_collection, cs, ce, granularity=gran, loc_match=loc_match)
    jobs_map_prev = _fetch_jobs_created_with_preview_per_bucket(
        orders_collection, ps, pe, granularity=gran, loc_match=loc_match)
    paid_map_prev = _fetch_paid_orders_per_bucket(
        orders_collection, ps, pe, granularity=gran, loc_match=loc_match)

    current_jobs = [int(jobs_map_curr.get(k, 0)) for k in labels]
    current_orders = [int(paid_map_curr.get(k, 0)) for k in labels]
    previous_jobs = [int(jobs_map_prev.get(k, 0)) for k in prev_labels]
    previous_orders = [int(paid_map_prev.get(k, 0)) for k in prev_labels]

    conversion_current = [(o * 100 / j) if j > 0 else 0 for o,
                          j in zip(current_orders, current_jobs)]
    conversion_previous = [(o * 100 / j) if j > 0 else 0 for o,
                           j in zip(previous_orders, previous_jobs)]

    return {
        "labels": labels,
        "current_jobs": current_jobs,
        "previous_jobs": previous_jobs,
        "current_orders": current_orders,
        "previous_orders": previous_orders,
        "conversion_current": conversion_current,
        "conversion_previous": conversion_previous,
        "granularity": gran,
    }

@app.get("/api/orders_api")
def get_orders(
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    sort_dir: Optional[str] = Query("asc", description="asc or desc"),
    filter_status: Optional[str] = Query(None),
    filter_book_style: Optional[str] = Query(None),
    filter_print_approval: Optional[str] = Query(None),
    filter_discount_code: Optional[str] = Query(None),
    exclude_discount_code: Optional[List[str]] = Query(None),
    discount_not_empty: Optional[bool] = Query(False),
    q: Optional[str] = Query(
        None, description="Search by job_id, order_id, email, name, discount_code, city, locale, book_id"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=1000),
):
    # Base query
    query: Dict[str, Any] = {}
    ex_values: List[str] = []

    # --- Filters (same as before) ---
    if filter_status == "approved":
        query["approved"] = True
    elif filter_status == "uploaded":
        query["approved"] = False

    if filter_book_style:
        query["book_style"] = filter_book_style

    if filter_print_approval == "yes":
        query["print_approval"] = True
    elif filter_print_approval == "no":
        query["print_approval"] = False
    elif filter_print_approval == "not_found":
        query["print_approval"] = {"$exists": False}

    if filter_discount_code:
        print(f"[DEBUG] Filter discount code: {filter_discount_code}")
        if filter_discount_code.lower() == "none":
            query["discount_amount"] = 0
            query["paid"] = True
        else:
            query["discount_code"] = filter_discount_code.upper()

    # Exclude discount codes
    if exclude_discount_code:
        if isinstance(exclude_discount_code, list):
            ex_values = exclude_discount_code
        else:
            ex_values = [p.strip()
                         for p in str(exclude_discount_code).split(",")]

    ex_values = [v for v in (s.strip() for s in ex_values) if v]
    if ex_values:
        regexes = [re.compile(rf"^{re.escape(v)}$", re.IGNORECASE)
                   for v in ex_values]
        existing = query.pop("discount_code", None)
        exclude_cond = {"discount_code": {"$nin": regexes}}
        if existing is None:
            query["discount_code"] = exclude_cond["discount_code"]
        else:
            query["$and"] = [{"discount_code": existing}, exclude_cond]

    # Optional: remove empty discount codes (only if frontend asks)
    if discount_not_empty:
        query.setdefault("$and", []).append({
            "discount_code": {
                "$nin": ["", None]
            }
        })

    # --- Extended free-text search ---
    if q:
        term = q.strip()
        if term:
            rx = re.compile(re.escape(term), re.IGNORECASE)
            query.setdefault("$and", []).append({
                "$or": [
                    {"order_id": {"$regex": rx}},
                    {"job_id": {"$regex": rx}},
                    {"email": {"$regex": rx}},
                    {"name": {"$regex": rx}},
                    {"user_name": {"$regex": rx}},
                    {"discount_code": {"$regex": rx}},
                    {"book_id": {"$regex": rx}},
                    {"locale": {"$regex": rx}},
                    {"shipping_address.city": {"$regex": rx}},
                ]
            })

    query = _with_paid_fallback(query)
    skip = (page - 1) * limit
    total_count = orders_collection.count_documents(query)

    # Sorting
    sort_field = sort_by if sort_by else "created_at"
    sort_order = 1 if sort_dir == "asc" else -1

    # Projection
    projection = {
        "order_id": 1,
        "job_id": 1,
        "cover_url": 1,
        "book_url": 1,
        "preview_url": 1,
        "name": 1,
        "shipping_address": 1,
        "created_at": 1,
        "processed_at": 1,
        "approved_at": 1,
        "approved": 1,
        "book_id": 1,
        "book_style": 1,
        "print_status": 1,
        "price": 1,
        "total_price": 1,
        "amount": 1,
        "total_amount": 1,
        "feedback_email": 1,
        "print_approval": 1,
        "discount_code": 1,
        "currency": 1,
        "locale": 1,
        "quantity": 1,
        "_id": 0,
        "shipped_at": 1,
        "cust_status": 1,
        "printer": 1,
        "locked": 1,
        "locked_by": 1,
        "unlock_by": 1,
        "print_sent_by": 1,
        "utm_source": 1,
        "utm_medium": 1,
        "utm_campaign": 1,
        "utm_content": 1,
        "utm_term": 1,
        "ref_code": 1,
        "landing_page_slug": 1,
    }

    cursor = orders_collection.find(query, projection).sort(
        sort_field, sort_order).skip(skip).limit(limit)
    records = list(cursor)
    result = []

    for doc in records:
        result.append({
            "order_id": _order_id_fallback(doc),
            "job_id": doc.get("job_id", ""),
            "coverPdf": _first_non_empty(doc, ["cover_url", "cover_pdf", "cover_image"], default=""),
            "interiorPdf": _first_non_empty(doc, ["book_url", "interior_pdf", "interior_url"], default=""),
            "previewUrl": _first_non_empty(doc, ["preview_url", "preview"], default=""),
            "name": doc.get("name", ""),
            "city": doc.get("shipping_address", {}).get("city", ""),
            "price": doc.get("price", doc.get("total_price", doc.get("amount", doc.get("total_amount", 0)))),
            "paymentDate": doc.get("processed_at", ""),
            "approvalDate": doc.get("approved_at", ""),
            "status": _derive_status(doc),
            "bookId": doc.get("book_id", ""),
            "bookStyle": _first_non_empty(doc, ["book_style", "binding", "cover_type"], default=""),
            "printStatus": doc.get("print_status", ""),
            "feedback_email": doc.get("feedback_email", False),
            "print_approval": doc.get("print_approval", None),
            "discount_code": doc.get("discount_code", ""),
            "currency": _first_non_empty(doc, ["currency", "currency_code"], default=""),
            "locale": doc.get("locale", ""),
            "shippedAt": doc.get("shipped_at"),
            "quantity": doc.get("quantity", 1),
            "cust_status": doc.get("cust_status", ""),
            "printer": doc.get("printer", ""),
            "locked": bool(doc.get("locked", False)),
            "locked_by": doc.get("locked_by", ""),
            "unlock_by": doc.get("unlock_by", ""),
            "print_sent_by": doc.get("print_sent_by", ""),
            "utm_source": doc.get("utm_source", ""),
            "utm_medium": doc.get("utm_medium", ""),
            "utm_campaign": doc.get("utm_campaign", ""),
            "utm_content": doc.get("utm_content", ""),
            "utm_term": doc.get("utm_term", ""),
            "ref_code": doc.get("ref_code", ""),
            "landing_page_slug": doc.get("landing_page_slug", ""),

        })

    return {
        "orders": result,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": (total_count + limit - 1) // limit
        }
    }

def _first_non_empty(d: Dict[str, Any], keys: List[str], default=None):
    for k in keys:
        val = d.get(k)
        if val not in (None, "", []):
            return val
    return default

def _with_paid_fallback(query: Dict[str, Any]) -> Dict[str, Any]:
    paid_clause = {"$or": [{"paid": True}, {"paid": {"$exists": False}}]}
    if not query:
        return paid_clause
    return {"$and": [paid_clause, query]}

def _derive_status(doc: Dict[str, Any]) -> str:
    if doc.get("approved") is True:
        return "Approved"
    if doc.get("approved") is False:
        return "Uploaded"
    for key in ("status", "job_state", "job_phase"):
        val = doc.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return "Uploaded"

def _order_id_fallback(doc: Dict[str, Any]) -> str:
    return _first_non_empty(
        doc,
        ["order_id", "order_id_long", "payment_order_id", "job_id"],
        default="",
    )

def _find_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
    if not order_id:
        return None
    order = orders_collection.find_one({"order_id": order_id})
    if order:
        return order
    order = orders_collection.find_one({"reprint_order_id": order_id})
    if order:
        return order
    order = orders_collection.find_one({"order_id_long": order_id})
    if order:
        return order
    order = orders_collection.find_one({"job_id": order_id})
    if order:
        return order
    return None

def _pick_image_list(doc: Dict[str, Any]) -> List[str]:

    candidate_keys = [
        "saved_files",
    ]

    # helper to normalize a value to a list of basenames
    def _norm(x: Any) -> List[str]:
        if isinstance(x, list):
            items = x
        elif isinstance(x, str) and x.strip():
            items = [x.strip()]
        else:
            return []
        # keep basenames (in case a full path/key was stored)
        return [os.path.basename(s) for s in items if isinstance(s, str) and s.strip()]

    # 1) check keys at the root
    for key in candidate_keys:
        v = doc.get(key)
        lst = _norm(v)
        if lst:
            return lst[:3]

    # 2) check nested under "child" if present
    child = doc.get("child")
    if isinstance(child, dict):
        for key in candidate_keys:
            v = child.get(key)
            lst = _norm(v)
            if lst:
                return lst[:3]

    return []

def get_aws_region() -> str:
    region = (os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "").strip()
    if not region:
        raise HTTPException(status_code=500, detail="AWS region not configured")
    return region


def _get_s3_client() -> Tuple[boto3.client, str]:
    bucket = os.getenv("REPLICACOMFY_BUCKET", "").strip()
    region = get_aws_region()
    return boto3.client(
        "s3",
        region_name=region,
        config=Config(
            retries={"max_attempts": 3, "mode": "standard"}
        )
    )

def _s3_key_for_input(filename: str) -> str:
    base = os.path.basename(filename).strip()
    return f"input/{base}"

def _generate_presigned_url(s3, bucket: str, key: str, expires_in: int = 3600) -> str:
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )

def _presigned_urls_for_saved_files(files: List[str], expires_in: int = 3600) -> List[str]:
    if not files:
        return []
    try:
        bucket = os.getenv("REPLICACOMFY_BUCKET")
        s3 = _get_s3_client()
    except HTTPException:
        raise

    urls: List[str] = []
    for f in files[:3]:
        key = _s3_key_for_input(f)
        try:
            # Verify the object exists before signing
            s3.head_object(Bucket=bucket, Key=key)
            urls.append(_generate_presigned_url(
                s3, bucket, key, expires_in=expires_in))
        except NoCredentialsError:
            raise HTTPException(
                status_code=500, detail="AWS credentials not available")
        except PartialCredentialsError:
            raise HTTPException(
                status_code=500, detail="AWS credentials are incomplete")
        except ClientError as e:
            code = getattr(e, "response", {}).get("Error", {}).get("Code")
            if code in ("404", "NoSuchKey", "NotFound", "AccessDenied"):
                # Skip silently—don’t break the whole order response
                continue
            raise HTTPException(
                status_code=502, detail="S3 error while generating image URLs")
        except Exception:
            raise HTTPException(
                status_code=502, detail="Unexpected error while generating image URLs")
    return urls

def _is_twin_book(book_id: str) -> bool:
    b = (book_id or "").strip().lower()
    # Adjust the identifiers below to your catalog if needed
    return any(k in b for k in ("twin", "bb", "bg", "gg", "twin_boy_girl", "twin_girl_girl", "twin_boy_boy"))

def _coerce_list(v: Any) -> List[str]:
    if not v:
        return []
    if isinstance(v, list):
        return [str(x) for x in v if x is not None and str(x).strip()]
    return [str(v)]

def _get_s3_client_generic():
    region = (os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "").strip()
    if not region:
        raise HTTPException(
            status_code=500,
            detail="AWS region not configured"
        )

    return boto3.client(
        "s3",
        region_name=region,
        config=Config(
            retries={"max_attempts": 3, "mode": "standard"}
        ),
    )

def _list_objects_with_prefix(s3, bucket: str, prefix: str, max_collect: int = 1000) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    token: Optional[str] = None
    while True:
        kwargs = {"Bucket": bucket, "Prefix": prefix, "MaxKeys": 1000}
        if token:
            kwargs["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kwargs)
        out.extend(resp.get("Contents", []) or [])
        if not resp.get("IsTruncated") or len(out) >= max_collect:
            break
        token = resp.get("NextContinuationToken")
    return out



def _find_cover_image_url_from_generations(job_id: str, expires_in: int = 3600) -> Optional[str]:
    bucket = (os.getenv("DIFFRUN_GENERATIONS_BUCKET") or "").strip()
    if not bucket or not job_id:
        return None

    s3 = _get_s3_client_generic()
    prefix = f"jpg_output/{job_id}_pg0_"

    try:
        objs = _list_objects_with_prefix(s3, bucket, prefix, max_collect=2000)
    except ClientError:
        return None

    if not objs:
        return None

    preferred = [o for o in objs if str(
        o.get("Key", "")).lower().endswith("_001.jpg")]
    chosen = min(preferred or objs, key=lambda o: o.get("LastModified"))

    try:
        return s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket,
                "Key": chosen["Key"],
                # Force browser-friendly headers for inline display
                "ResponseContentType": "image/jpeg",
                "ResponseContentDisposition": "inline",
            },
            ExpiresIn=expires_in,
        )
    except ClientError:
        return None

def _iso(dt: Any) -> Optional[str]:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    if isinstance(dt, str):
        return dt
    try:
        return datetime.fromtimestamp(dt).isoformat()
    except Exception:
        return str(dt)

def _build_order_response(order: Dict[str, Any]) -> Dict[str, Any]:
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    job_id = _first_non_empty(order, ["job_id", "JobId", "jobID"], default="")
    current_status = order.get("current_status") 

    user_doc = {}
    if job_id:
        user_doc = orders_collection.find_one({"job_id": job_id}) or {}

    child_name = _first_non_empty(
        order, ["name"],   default=_first_non_empty(user_doc, ["name"]))
    child_age = _first_non_empty(
        order, ["age"],    default=_first_non_empty(user_doc, ["age"]))
    child_gender = _first_non_empty(
        order, ["gender"], default=_first_non_empty(user_doc, ["gender"]))

    saved_files = _pick_image_list(order) or _pick_image_list(user_doc)

    saved_file_urls: list[str] = []
    if saved_files:
        saved_file_urls = _presigned_urls_for_saved_files(
            saved_files, expires_in=3600)

    book_id = _first_non_empty(
        order, ["book_id"], default=_first_non_empty(user_doc, ["book_id"])) or ""
    is_twin = _is_twin_book(book_id)

    child1_age = _first_non_empty(
        order, ["child1_age"], default=_first_non_empty(user_doc, ["child1_age"]))
    child2_age = _first_non_empty(
        order, ["child2_age"], default=_first_non_empty(user_doc, ["child2_age"]))

    child1_files = _coerce_list(order.get(
        "child1_image_filenames") or user_doc.get("child1_image_filenames"))[:3]
    child2_files = _coerce_list(order.get(
        "child2_image_filenames") or user_doc.get("child2_image_filenames"))[:3]

    child1_input_urls: list[str] = _presigned_urls_for_saved_files(
        child1_files, expires_in=3600) if child1_files else []
    child2_input_urls: list[str] = _presigned_urls_for_saved_files(
        child2_files, expires_in=3600) if child2_files else []

    child_details = {
        "name": (child_name or ""),
        "age":  (child_age or ""),
        "gender": (child_gender or "").lower(),
        "saved_files": saved_files[:3],
        "saved_file_urls": saved_file_urls,
        "is_twin": bool(is_twin),
        "child1_age": child1_age if child1_age not in (None, "") else None,
        "child2_age": child2_age if is_twin and child2_age not in (None, "") else None,
        # as stored in DB (for traceability)
        "child1_image_filenames": child1_files,
        "child2_image_filenames": child2_files,
        # presigned URLs from replicacomfy/input/<filename>
        "child1_input_images": child1_input_urls,
        "child2_input_images": child2_input_urls,
    }

    # customer details
    customer_email = _first_non_empty(
        order, ["email", "customer_email", "paypal_email"], default="")
    ship = order.get("shipping_address", {}) or order.get("shipping", {}) or {}
    phone_number = _first_non_empty(
        order, ["phone_number", "phone"], default=_first_non_empty(ship, ["phone"], default=""))
    customer_details = {
        "user_name": order.get("user_name", ""),
        "email": customer_email or "",
        "phone_number": phone_number or "",
    }

    cover_url_from_gen = _find_cover_image_url_from_generations(
        job_id, expires_in=3600)

    # order financials/ids
    order_details = {
        "order_id": _order_id_fallback(order),
        "discount_code": order.get("discount_code", ""),
        "total_price": _first_non_empty(order, ["total_price", "amount", "total", "price", "total_amount"], default=""),
        "transaction_id": _first_non_empty(order, ["transaction_id", "razorpay_payment_id", "payment_id"], default=""),
        "cover_url": _first_non_empty(order, ["cover_url", "cover_pdf", "cover_image"], default=""),
        "book_url": _first_non_empty(order, ["book_url", "interior_pdf", "interior_url"], default=""),
        "paypal_capture_id": order.get("paypal_capture_id", ""),
        "paypal_order_id": order.get("paypal_order_id", ""),
        "cover_image": cover_url_from_gen or "",
        "tracking_code": order.get("tracking_code") or order.get("tracking_number"),
        "printer": order.get("printer", "")
    }

    attribution = {
        "utm_source": order.get("utm_source", "") or user_doc.get("utm_source", ""),
        "utm_medium": order.get("utm_medium", "") or user_doc.get("utm_medium", ""),
        "utm_campaign": order.get("utm_campaign", "") or user_doc.get("utm_campaign", ""),
        "utm_content": order.get("utm_content", "") or user_doc.get("utm_content", ""),
        "utm_term": order.get("utm_term", "") or user_doc.get("utm_term", ""),
        "ref_code": order.get("ref_code", "") or user_doc.get("ref_code", ""),
        "landing_page_slug": order.get("landing_page_slug", "") or user_doc.get("landing_page_slug", ""),
    }

    # timeline
    timeline = {
        "created_at": _iso(order.get("created_at")),
        "processed_at": _iso(order.get("processed_at")),
        "approved_at": _iso(order.get("approved_at")),
        "print_sent_at": _iso(order.get("print_sent_at")),
        "shipped_at": _iso(order.get("shipped_at")),
    }

    # base legacy fields (preserved)
    response = {
        "order_id": _order_id_fallback(order),
        "name": order.get("name", ""),
        "book_id": order.get("book_id", ""),
        "book_style": _first_non_empty(order, ["book_style", "binding", "cover_type"], default=""),
        "preview_url": _first_non_empty(order, ["preview_url", "preview"], default=""),
        "gender": order.get("gender", ""),
        "user_name": order.get("user_name", ""),
        "email": order.get("email", ""),
        "discount_code": order.get("discount_code", ""),
        "quantity": order.get("quantity", 1),
        "phone": order.get("phone_number"),
        "shipping_address": {
            "address1": ship.get("address1", "") or ship.get("street", "") or "",
            "address2": ship.get("address2", "") or ship.get("street2", "") or "",
            "city": ship.get("city", "") or "",
            "state": ship.get("province", "") or ship.get("state", "") or "",
            "country": ship.get("country", "") or "",
            "zip": ship.get("zip", "") or ship.get("postal_code", "") or "",
            "phone": ship.get("phone", "") or "",
        },
    }

    # enrich
    response.update({
        "job_id": job_id,
        "book_style": _first_non_empty(order, ["book_style", "binding", "cover_type"], default=""),
        "book_id": order.get("book_id", ""),
        "preview_url": _first_non_empty(order, ["preview_url", "preview"], default=""),
        "locale": order.get("locale", ""),
        "child": child_details,
        "customer": customer_details,
        "order": order_details,
        "timeline": timeline,
        "printer": order.get("printer", ""),
        "current_status": current_status,
        "remarks": order.get("remarks", ""),   # ✅ ADD
        "order_status": order.get("order_status"),
        "order_status_remarks": order.get("order_status_remarks"),
        "reprint_order_id": order.get("reprint_order_id", ""),
        "issue_origin": order.get("issue_origin", ""),
        "reprint_meta": order.get("reprint_meta", {}),
        "attribution": attribution,
    })
    return response

def get_gspread_client_yara():
    """
    Return authenticated gspread client. Preference:
      1) SERVICE_ACCOUNT_FILE path
      2) SERVICE_ACCOUNT_JSON content (full JSON string)
    """

    creds = None
    if SERVICE_ACCOUNT_FILE_YARA and os.path.exists(SERVICE_ACCOUNT_FILE_YARA):
        creds = _GoogleCredentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE_YARA, scopes=_SCOPES)
    elif SERVICE_ACCOUNT_JSON:
        info = json.loads(SERVICE_ACCOUNT_JSON)
        creds = _GoogleCredentials.from_service_account_info(
            info, scopes=_SCOPES)
    else:
        raise RuntimeError(
            "Google service account credentials not configured. Set GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_SERVICE_ACCOUNT_JSON")

    return gspread.authorize(creds)

def get_gspread_client():
    """
    Return authenticated gspread client. Preference:
      1) SERVICE_ACCOUNT_FILE path
      2) SERVICE_ACCOUNT_JSON content (full JSON string)
    """

    creds = None
    if SERVICE_ACCOUNT_FILE and os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = _GoogleCredentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=_SCOPES)
    elif SERVICE_ACCOUNT_JSON:
        info = json.loads(SERVICE_ACCOUNT_JSON)
        creds = _GoogleCredentials.from_service_account_info(
            info, scopes=_SCOPES)
    else:
        raise RuntimeError(
            "Google service account credentials not configured. Set GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_SERVICE_ACCOUNT_JSON")

    return gspread.authorize(creds)

def _ensure_quantity_header(worksheet):
    """Ensure the header 'Quantity' exists in column L (index 12)."""
    try:
        header = worksheet.row_values(1)
        if len(header) < 12 or header[11].strip() == "":
            worksheet.update_cell(1, 12, "Quantity")
            print("[SHEETS] Added missing 'Quantity' header in column L")
    except Exception as e:
        print(f"[SHEETS][WARN] Could not verify Quantity header: {e}")


def append_row_to_google_sheet(row: list):

    try:
        client = get_gspread_client()
        sh = client.open_by_key(SPREADSHEET_ID)
        worksheet = sh.worksheet(WORKSHEET_NAME)

        _ensure_quantity_header(worksheet)

        worksheet.insert_row(row, index=2, value_input_option="USER_ENTERED")
        print(f"[SHEETS] appended row for order {row[1]}")
    except Exception as exc:
        print(
            f"[SHEETS][ERROR] failed to append row for order {row[1]}: {exc}")

def get_admin_email_from_claims(claims):
    email = (claims.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(401, "Invalid session")
    return email

def extract_reprint_key(order_id: str):
    """
    If order_id = TEST#366_RP1 → returns 'RP1'
    Else returns None
    """
    if not order_id:
        return None
    m = re.search(r"_RP(\d+)$", order_id)
    if not m:
        return None
    return f"RP{m.group(1)}"

def find_order_by_any_id(order_id: str):
    """
    Finds order by:
      - order_id
      - reprint_order_id
    """
    order = orders_collection.find_one({"order_id": order_id})
    if order:
        return order

    order = orders_collection.find_one({"reprint_order_id": order_id})
    if order:
        return order

    return None

def _to_safe_value(v):
    """Convert values that are not JSON-serializable to safe string representations."""
    if v is None:
        return ""
    if isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (datetime, date)):
        # choose format you prefer; ISO is safe and sortable
        return v.isoformat()
    if isinstance(v, ObjectId):
        return str(v)
    # fallback: cast to string
    return str(v)



def order_to_sheet_row(order: dict) -> list:
    """
    Build a sheet row that leaves column A empty and safely converts datetimes.
    Column mapping (B -> K) as requested in your screenshot.
    """
    diffrun_order_id = _to_safe_value(order.get("order_id", ""))

    # choose the created/ordered time field from your schema
    # current IST time for Google-Sheets entry (safe and independent)
    IST_1 = ZoneInfo("Asia/Kolkata")
    now_ist = datetime.now(IST_1)
    order_date = now_ist.strftime("%d %b, %H:%M")

    child_name = _to_safe_value(order.get("name") or "")
    book_style = _to_safe_value(order.get("book_style") or "")
    book_id = _to_safe_value(order.get("book_id") or "")

    shipping = order.get("shipping_address") or {}
    city = _to_safe_value(shipping.get("city") or "")

    address_parts = [
        shipping.get("name") or "",
        shipping.get("address1") or "",
        shipping.get("address2") or "",
        shipping.get("city") or "",
        shipping.get("province") or "",
        shipping.get("country") or "",
        shipping.get("zip") or ""
    ]
    # join non-empty parts with comma (or use "\n" for line breaks)
    address = "\n".join([p for p in address_parts if p])
    address = _to_safe_value(address)

    phone = _to_safe_value(shipping.get("phone") or order.get(
        "phone_number") or order.get("customer_phone") or "")

    quantity = int(order.get("quantity", 1) or 1)

    cover_url = order.get("cover_url") or order.get("coverpage_url") or ""
    interior_url = order.get("book_url") or order.get("interior_pdf") or ""

    cover_link_formula = f'=HYPERLINK("{_to_safe_value(cover_url)}","View")' if cover_url else ""
    interior_link_formula = f'=HYPERLINK("{_to_safe_value(interior_url)}","View PDF")' if interior_url else ""

    logged_at = _to_safe_value(datetime.utcnow())

    row = [
        "",                        # A: intentionally blank
        diffrun_order_id,          # B
        order_date,                # C
        child_name,                # D
        book_style,                # E
        book_id,                   # F
        city,                      # G
        address,                   # H
        phone,                     # I
        cover_link_formula,        # J
        interior_link_formula,      # K
        quantity,            # L
    ]

    # ensure every element is a primitive (str/int/float/bool)
    row = [_to_safe_value(x) for x in row]
    return row

def _extract_url_from_formula(formula: str) -> str:
    """
    Extract the URL from a Google Sheets HYPERLINK formula.
    Example:
      '=HYPERLINK("https://abc.com/file.pdf","View")' -> 'https://abc.com/file.pdf'
    If not a formula, returns the original string.
    """
    if not isinstance(formula, str):
        return formula
    match = re.search(r'HYPERLINK\("([^"]+)"', formula)
    if match:
        return match.group(1)
    return formula



def append_shipping_details(row: list, order: dict, printer: str):
    """
    Upsert into MongoDB using:
      - sheet-mirrored fields from `row`
      - extra fields (user_name, email) directly from `order` (NOT written to sheet)
    """
    try:
        cover_link_raw = _extract_url_from_formula(row[9])
        interior_link_raw = _extract_url_from_formula(row[10])

        # Pick keys that exist in YOUR payload. These fallbacks are safe:
        user_name = (
            order.get("user_name")
            or order.get("customer_name")
            or (order.get("shipping_address") or {}).get("name")
            or order.get("name")
            or ""
        )
        email = (
            order.get("email")
            or order.get("customer_email")
            or (order.get("shipping_address") or {}).get("email")
            or ""
        )
        age = (order.get("age") or "")
        total_price = (order.get("total_price") or "")
        gender = (order.get("gender") or "")
        paid = (order.get("paid") or "")
        approved = (order.get("approved") or "")
        created_at_ = (order.get("created_at") or "")
        updated_at = (order.get("updated_at") or "")
        discount_code = (order.get("discount_code") or "")
        payment_at = (order.get("payment_at") or "")
        shipping_address = (order.get("shipping_address") or "")
        transaction_id = (order.get("transaction_id") or "")
        partial_preview = (order.get("partial_preview") or "")
        final_preview = (order.get("final_preview") or "")

        doc = {
            "order_id": row[1],
            "order_date": row[2],
            "child_name": row[3],
            "book_style": row[4],
            "book_id": row[5],
            "city": row[6],
            "address": row[7],
            "phone": row[8],
            "cover_link": cover_link_raw,
            "interior_link": interior_link_raw,
            "quantity": row[11],

            # Mongo-only additions:
            "user_name": user_name,
            "email": email,
            "age": age,
            "total_price": total_price,
            "gender": gender,
            "paid": paid,
            "approved": approved,
            "created_at_": created_at_,
            "updated_at": updated_at,
            "discount_code": discount_code,
            "payment_at": payment_at,
            "shipping_address": shipping_address,
            "transaction_id": transaction_id,
            "partial_preview": partial_preview,
            "final_preview": final_preview,
            "printer": printer,

            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        shipping_collection.update_one(
            {"order_id": doc["order_id"]},
            {"$set": doc, "$setOnInsert": {
                "created_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )

        print(f"[MONGO] upserted shipping_details for order {row[1]}")
    except Exception as exc:
        print(
            f"[MONGO][ERROR] failed to upsert shipping_details for order {row[1]}: {exc}")




def _get_child_age(order: Dict[str, Any], idx: int) -> Optional[Union[int, str]]:

    if idx == 1:
        for key in ("child1_age", "age", "child_age", "kid_age"):
            v = order.get(key)
            if v not in (None, ""):
                return v
    if idx == 2:
        v = order.get("child2_age")
        if v not in (None, ""):
            return v

    # nested dicts commonly used
    child_key = f"child{idx}"
    v = (order.get(child_key) or {}).get("age")
    if v not in (None, ""):
        return v

    # array style: children[0], children[1]
    children = order.get("children") or order.get("kids") or []
    if isinstance(children, list) and len(children) >= idx:
        v = (children[idx - 1] or {}).get("age")
        if v not in (None, ""):
            return v

    return None

def _pick_excel_engine():
    try:
        
        return "xlsxwriter"
    except Exception:
        try:
            
            return "openpyxl"
        except Exception:
            return None
        
def get_ec2_client():
    region = get_aws_region()
    return boto3.client("ec2", region_name=region)

def _fmt_ist(dt):
    try:
        if dt is None:
            return ""
        if isinstance(dt, str):
            try:
                dt = parser.isoparse(dt)
            except Exception:
                return ""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def _get_ec2_status_rows():
    try:
        if not AWS_REGION:
            return [], "AWS region not set. Set AWS_REGION or AWS_DEFAULT_REGION."

        ec2 = get_ec2_client()
        resp = ec2.describe_instances(InstanceIds=INSTANCE_IDS)
        reservations = resp.get("Reservations", [])

        # Gather instance ids for status checks
        instance_ids = [
            inst["InstanceId"]
            for r in reservations
            for inst in r.get("Instances", [])
        ]
        checks_map = {}
        if instance_ids:
            status_resp = ec2.describe_instance_status(
                InstanceIds=instance_ids, IncludeAllInstances=True
            )
            for s in status_resp.get("InstanceStatuses", []):
                checks_map[s["InstanceId"]] = {
                    "InstanceStatus": s.get("InstanceStatus", {}).get("Status", ""),
                    "SystemStatus": s.get("SystemStatus", {}).get("Status", ""),
                }

        now_ist = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(IST)
        rows = []
        for r in reservations:
            for inst in r.get("Instances", []):
                iid = inst.get("InstanceId", "")
                state = (inst.get("State") or {}).get("Name", "")
                name = ""
                for tag in inst.get("Tags", []) or []:
                    if tag.get("Key") == "Name":
                        name = tag.get("Value") or ""
                        break

                rows.append({
                    "Name": name,
                    "InstanceId": iid,
                    "State": state,                           # running/stopped/…
                    "OnOff": "on" if state == "running" else "off",
                    "InstanceStatus": checks_map.get(iid, {}).get("InstanceStatus", ""),
                    "SystemStatus": checks_map.get(iid, {}).get("SystemStatus", ""),
                    "PublicIP": inst.get("PublicIpAddress", ""),
                    "PrivateIP": inst.get("PrivateIpAddress", ""),
                    "LaunchTime_IST": _fmt_ist(inst.get("LaunchTime")),
                    "CheckedAt_IST": now_ist.strftime("%Y-%m-%d %H:%M:%S"),
                })

        return rows, None

    except (BotoCoreError, ClientError) as e:
        return [], f"AWS error: {e}"
    except Exception as e:
        return [], f"Unexpected error: {e}"


def _get_ec2_status_rows() -> Tuple[List[dict], Optional[str]]:
    """
    Return (rows, err).  Skips any missing instance IDs instead of failing.
    rows schema includes keys used later: OnOff, Name, InstanceId (plus extras).
    """
    ec2 = get_ec2_client()

    # Source of instance IDs: keep whatever you already use
    # Example: a global/list env. Do NOT change your current source; just read it.
    # If you already have EC2_INSTANCE_IDS somewhere, keep that.
    instance_ids: List[str] = INSTANCE_IDS  # type: ignore[name-defined]

    rows: List[dict] = []
    if not instance_ids:
        # Nothing to do; do not error
        return rows, None

    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    skipped: List[str] = []

    for chunk in chunks(instance_ids, 100):
        to_query = list(chunk)
        if not to_query:
            continue

        while to_query:
            try:
                resp = ec2.describe_instances(InstanceIds=to_query)
            except ClientError as e:
                code = e.response.get("Error", {}).get("Code")
                if code == "InvalidInstanceID.NotFound":
                    # Extract bad IDs from the message and drop them
                    msg = e.response.get("Error", {}).get("Message", "")
                    bad = re.findall(r"i-[0-9a-f]+", msg)
                    if not bad:
                        # If we can't parse, skip this whole chunk and move on
                        logging.warning(
                            "EC2: could not parse missing IDs from: %s", msg)
                        break
                    skipped.extend(bad)
                    to_query = [i for i in to_query if i not in bad]
                    if not to_query:
                        break
                    # retry with the remaining IDs
                    continue
                else:
                    # Any other AWS error: surface a single error string (optional)
                    logging.exception("EC2 describe_instances failed")
                    return rows, f"AWS error: {e}"

            # Process reservations -> instances
            for r in resp.get("Reservations", []):
                for inst in r.get("Instances", []):
                    iid = inst.get("InstanceId", "")
                    state = (inst.get("State", {}) or {}).get("Name", "")
                    # OnOff field as int (1 running, 0 otherwise), matches your sort later
                    onoff = 1 if state == "running" else 0
                    # Name tag
                    name = ""
                    for t in inst.get("Tags", []) or []:
                        if t.get("Key") == "Name":
                            name = t.get("Value", "")
                            break
                    rows.append({
                        "OnOff": onoff,
                        "Name": name,
                        "InstanceId": iid,
                        "State": state,
                        "Type": inst.get("InstanceType", ""),
                        "AZ": (inst.get("Placement", {}) or {}).get("AvailabilityZone", ""),
                        "PrivateIP": inst.get("PrivateIpAddress", ""),
                        "PublicIP": inst.get("PublicIpAddress", ""),
                        "LaunchTime": inst.get("LaunchTime", ""),
                    })
            break  # exit the inner while after successful call

    if skipped:
        logging.warning("EC2: skipped missing instance IDs: %s",
                        ", ".join(skipped))

    # IMPORTANT: we return no error so the caller writes 'ec2_status' (not *_error)
    return rows, None



@app.post("/api/orders/send-to-google-sheet")
async def send_to_google_sheet(
    payload: BulkPrintRequest,
    background_tasks: BackgroundTasks,
    claims=Depends(require_auth),   # ✅ use request instead of claims
): 
    if not GOOGLE_SHEET_ENABLED:
        raise HTTPException(
            status_code=410,
            detail="Google Sheet export is disabled. Use the printer portal instead.",
        )
    print(claims)
    
    admin_email = get_admin_email_from_claims(claims)
    print("ADMIN EMAIL:", admin_email)

    order_ids = payload.order_ids
    print_sent_by = admin_email   # ✅ DO NOT trust frontend email

    if not SPREADSHEET_ID:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_SHEET_ID is not configured"
        )

    # De-duplicate IDs
    seen = set()
    unique_order_ids = []

    for oid in order_ids:
        if oid not in seen:
            seen.add(oid)
            unique_order_ids.append(oid)

    results = []

    for order_id in unique_order_ids:

        print(f"[SHEETS] Processing order ID: {order_id}")

        order = find_order_by_any_id(order_id)

        if not order:
            results.append({
                "order_id": order_id,
                "status": "error",
                "message": "Order not found",
                "step": "database_lookup"
            })
            continue

        reprint_key = extract_reprint_key(order_id)

        if reprint_key:

            lock_filter = {
                "_id": order["_id"],
                f"reprint_meta.{reprint_key}.sheet_queued": {"$ne": True}
            }

            lock_update = {
                "$set": {
                    f"reprint_meta.{reprint_key}.sheet_queued": True,
                    f"reprint_meta.{reprint_key}.printer": "Genesis",
                    f"reprint_meta.{reprint_key}.print_status": "sent_to_genesis",
                    f"reprint_meta.{reprint_key}.print_sent_at": datetime.now().isoformat(),
                    f"reprint_meta.{reprint_key}.print_sent_by": print_sent_by,
                }
            }

        else:

            lock_filter = {
                "_id": order["_id"],
                "sheet_queued": {"$ne": True}
            }

            lock_update = {
                "$set": {
                    "sheet_queued": True,
                    "printer": "Genesis",
                    "print_status": "sent_to_genesis",
                    "print_sent_at": datetime.now().isoformat(),
                    "print_sent_by": print_sent_by,
                }
            }

        lock_result = orders_collection.update_one(
            lock_filter,
            lock_update
        )

        if lock_result.modified_count == 0:

            results.append({
                "order_id": order_id,
                "status": "skipped",
                "message": "Already queued previously",
                "step": "idempotency_check"
            })

            continue
        
        # ✅ send production email ONCE (idempotent)
        once = orders_collection.update_one(
            {"order_id": order_id, "$or": [
                {"production_email_sent": {"$exists": False}},
                {"production_email_sent": False}
            ]},
            {"$set": {"production_email_sent": True}}
        )

        if once.modified_count == 1:
            to_email = (order.get("customer_email")
                        or order.get("email") or "").strip()
            display_name = order.get("user_name") or "there"
            child_name = order.get("name") or "Your"
            job_id = order.get("job_id")

            if to_email and EMAIL_USER and EMAIL_PASS:
                background_tasks.add_task(
                    _send_production_email,
                    to_email,
                    display_name,
                    child_name,
                    job_id,
                    order_id
                )
                print(f"[EMAIL] queued production email to {to_email} for {order_id}")
            else:
                print(f"[EMAIL] skipped (missing recipient or creds) for {order_id}")
        else:
            print(f"[EMAIL] already sent for {order_id}, skipping")

        order_copy = dict(order)
        order_copy["order_id"] = order_id

        row = order_to_sheet_row(order_copy)

        background_tasks.add_task(
            append_shipping_details,
            row,
            order,
            "Genesis"
        )

        quantity = max(1, int(order.get("quantity", 1) or 1))

        for _ in range(quantity):
            background_tasks.add_task(
                append_row_to_google_sheet,
                row
            )

        results.append({
            "order_id": order_id,
            "status": "queued",
            "message": "Queued for Genesis sheet append",
            "step": "queued"
        })

    return results

def order_to_sheet_row_yara(order: dict) -> list:
    """
    Build a sheet row that leaves column A empty and safely converts datetimes.
    Column mapping (B -> K) as requested in your screenshot.
    """
    diffrun_order_id = _to_safe_value(order.get("order_id", ""))

    # choose the created/ordered time field from your schema
    # current IST time for Google-Sheets entry (safe and independent)
    IST_1 = ZoneInfo("Asia/Kolkata")
    now_ist = datetime.now(IST_1)
    order_date = now_ist.strftime("%d %b, %H:%M")

    child_name = _to_safe_value(order.get("name") or "")
    book_style = _to_safe_value(order.get("book_style") or "")
    book_id = _to_safe_value(order.get("book_id") or "")

    shipping = order.get("shipping_address") or {}
    city = _to_safe_value(shipping.get("city") or "")

    address_parts = [
        shipping.get("name") or "",
        shipping.get("address1") or "",
        shipping.get("address2") or "",
        shipping.get("city") or "",
        shipping.get("province") or "",
        shipping.get("country") or "",
        shipping.get("zip") or ""
    ]
    # join non-empty parts with comma (or use "\n" for line breaks)
    address = "\n".join([p for p in address_parts if p])
    address = _to_safe_value(address)

    phone = _to_safe_value(shipping.get("phone") or order.get(
        "phone_number") or order.get("customer_phone") or "")

    quantity = int(order.get("quantity", 1) or 1)

    cover_url = order.get("cover_url") or order.get("coverpage_url") or ""
    interior_url = order.get("book_url") or order.get("interior_pdf") or ""

    cover_link_formula = f'=HYPERLINK("{_to_safe_value(cover_url)}","View")' if cover_url else ""
    interior_link_formula = f'=HYPERLINK("{_to_safe_value(interior_url)}","View PDF")' if interior_url else ""

    logged_at = _to_safe_value(datetime.utcnow())

    row = [
        "",                        # A: intentionally blank
        diffrun_order_id,          # B
        order_date,                # C
        child_name,                # D
        book_style,                # E
        book_id,                   # F
        city,                      # G
        address,                   # H
        phone,                     # I
        cover_link_formula,        # J
        interior_link_formula,      # K
        quantity,            # L
    ]

    # ensure every element is a primitive (str/int/float/bool)
    row = [_to_safe_value(x) for x in row]
    return row

    """
    Upsert into MongoDB using:
      - sheet-mirrored fields from `row`
      - extra fields (user_name, email) directly from `order` (NOT written to sheet)
    """
    try:
        cover_link_raw = _extract_url_from_formula(row[9])
        interior_link_raw = _extract_url_from_formula(row[10])

        # Pick keys that exist in YOUR payload. These fallbacks are safe:
        user_name = (
            order.get("user_name")
            or order.get("customer_name")
            or (order.get("shipping_address") or {}).get("name")
            or order.get("name")
            or ""
        )
        email = (
            order.get("email")
            or order.get("customer_email")
            or (order.get("shipping_address") or {}).get("email")
            or ""
        )

        doc = {
            "order_id": row[1],
            "order_date": row[2],
            "child_name": row[3],
            "book_style": row[4],
            "book_id": row[5],
            "city": row[6],
            "address": row[7],
            "phone": row[8],
            "cover_link": cover_link_raw,
            "interior_link": interior_link_raw,
            "quantity": row[11],

            # Mongo-only additions:
            "user_name": user_name,
            "email": email,

            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        shipping_collection.update_one(
            {"order_id": doc["order_id"]},
            {"$set": doc, "$setOnInsert": {
                "created_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )

        print(f"[MONGO] upserted shipping_details for order {row[1]}")
    except Exception as exc:
        print(
            f"[MONGO][ERROR] failed to upsert shipping_details for order {row[1]}: {exc}")

def append_row_to_google_sheet_yara(row: list):
    try:
        client = get_gspread_client_yara()
        sh = client.open_by_key(SPREADSHEET_ID_YARA)
        worksheet = sh.worksheet(WORKSHEET_NAME_YARA)

        _ensure_quantity_header(worksheet)

        # use configured option (fallback to USER_ENTERED)
        option = VALUE_INPUT_OPTION_YARA or "USER_ENTERED"
        worksheet.insert_row(row, index=2, value_input_option=option)
        print(
            f"[SHEETS][YARA] appended row for order {row[1]} to worksheet {WORKSHEET_NAME_YARA}")
    except Exception as exc:
        print(
            f"[SHEETS][YARA][ERROR] failed to append row for order {row[1]}: {exc}")

@app.post("/api/orders/send-to-yara")
async def send_to_yara(payload: BulkPrintRequest, background_tasks: BackgroundTasks,claims=Depends(require_auth),):
    print(claims)
    
    admin_email = get_admin_email_from_claims(claims)
    print("ADMIN EMAIL:", admin_email)

    order_ids = payload.order_ids
    print_sent_by = admin_email   # ✅ DO NOT trust frontend email

    if not GOOGLE_SHEET_ENABLED:
        raise HTTPException(
            status_code=410,
            detail="Google Sheet export is disabled. Use the printer portal instead.",
        )

    # Ensure the Yara spreadsheet id is configured
    if not SPREADSHEET_ID_YARA:
        raise HTTPException(
            status_code=500, detail="GOOGLE_SHEET_ID_YARA is not configured")

    # 1) De-duplicate IDs within this request (preserve order)
    seen = set()
    unique_order_ids = []
    for oid in order_ids:
        if oid not in seen:
            seen.add(oid)
            unique_order_ids.append(oid)

    results = []
    for order_id in unique_order_ids:
        print(f"[SHEETS][YARA] Processing order ID: {order_id}")
        order = find_order_by_any_id(order_id)

        if not order:
            print(f"[SHEETS][YARA] Order not found: {order_id}")
            results.append({
                "order_id": order_id,
                "status": "error",
                "message": "Order not found",
                "step": "database_lookup"
            })
            continue

        # ATOMIC LOCK: mark as queued only if not already queued (Yara-specific flags)
        reprint_key = extract_reprint_key(order_id)

        if reprint_key:
            # REPRINT FLOW
            lock_filter = {
                "_id": order["_id"],
                f"reprint_meta.{reprint_key}.sheet_queued": {"$ne": True}
            }

            lock_update = {
                "$set": {
                    f"reprint_meta.{reprint_key}.sheet_queued": True,
                    f"reprint_meta.{reprint_key}.printer": "Yara",
                    f"reprint_meta.{reprint_key}.print_status": "sent_to_yara",
                    f"reprint_meta.{reprint_key}.print_sent_at": datetime.now().isoformat(),
                    f"reprint_meta.{reprint_key}.print_sent_by": print_sent_by,
                }
            }
        else:
            # ORIGINAL FLOW (unchanged)
            lock_filter = {"_id": order["_id"], "sheet_queued": {"$ne": True}}
            lock_update = {
                "$set": {
                    "sheet_queued": True,
                    "printer": "Yara",
                    "print_status": "sent_to_yara",
                    "print_sent_at": datetime.now().isoformat(),
                    "print_sent_by": print_sent_by,
                }
            }

        lock_result = orders_collection.update_one(lock_filter, lock_update)

        if lock_result.modified_count == 0:
            results.append({
                "order_id": order_id,
                "status": "skipped",
                "message": "Already queued previously; not sending again",
                "step": "idempotency_check"
            })
            continue
        
        # ✅ send production email ONCE (idempotent)
        once = orders_collection.update_one(
            {"order_id": order_id, "$or": [
                {"production_email_sent": {"$exists": False}},
                {"production_email_sent": False}
            ]},
            {"$set": {"production_email_sent": True}}
        )

        if once.modified_count == 1:
            to_email = (order.get("customer_email")
                        or order.get("email") or "").strip()
            display_name = order.get("user_name") or "there"
            child_name = order.get("name") or "Your"
            job_id = order.get("job_id")

            if to_email and EMAIL_USER and EMAIL_PASS:
                background_tasks.add_task(
                    _send_production_email,
                    to_email,
                    display_name,
                    child_name,
                    job_id,
                    order_id
                )
                print(f"[EMAIL] queued production email to {to_email} for {order_id}")
            else:
                print(f"[EMAIL] skipped (missing recipient or creds) for {order_id}")
        else:
            print(f"[EMAIL] already sent for {order_id}, skipping")

        # Build the row and schedule background tasks
        order_copy = dict(order)
        order_copy["order_id"] = order_id

        row = order_to_sheet_row_yara(order_copy)

        background_tasks.add_task(append_shipping_details, row, order, "Yara")
        quantity = int(order.get("quantity", 1) or 1)
        quantity = max(1, quantity)
        for _ in range(quantity):
            background_tasks.add_task(append_row_to_google_sheet_yara, row)

        results.append({
            "order_id": order_id,
            "status": "queued",
            "message": "Queued for Yara sheet append",
            "step": "queued"
        })

    return results


@app.get("/api/orders/reprint")
async def serve_order_detail():
    # Manually serve the order-detail.html file from the out directory
    orders_path = "../frontend/out/orders/reprint.html"
    if os.path.exists(orders_path):
        with open(orders_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return {"message": "Frontend order-reprint.html not found."}

@app.get("/api/orders/order-detail")
async def serve_order_detail():
    # Manually serve the order-detail.html file from the out directory
    orders_path = "../frontend/out/orders/order-detail.html"
    if os.path.exists(orders_path):
        with open(orders_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return {"message": "Frontend order-detail.html not found."}
    
@app.get("/api/jobs/job-detail")
async def serve_job_detail():
    # Manually serve the job-detail.html file from the out directory
    jobs_path = "../frontend/out/jobs/job-detail.html"
    if os.path.exists(jobs_path):
        with open(jobs_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return {"message": "Frontend job-detail.html not found."}

@app.get("/api/jobs/{job_id}/mini")
def get_job_mini(job_id: str) -> Dict[str, Any]:
    order = orders_collection.find_one({"job_id": job_id})
    if not order:
        raise HTTPException(status_code=404, detail="Job not found")

    email = _first_non_empty(
        order, ["email", "customer_email", "paypal_email"], default="")
    book_id = order.get("book_id", "") or ""
    is_twin = _is_twin_book(book_id)

    preview_url = (
        order.get("preview_url")
        or ""
    )

    saved_files = _pick_image_list(order)
    input_image_urls = _presigned_urls_for_saved_files(
        saved_files, expires_in=3600) if saved_files else []

    child1_filenames = order.get("child1_image_filenames") or []
    child2_filenames = order.get("child2_image_filenames") or []

    if not isinstance(child1_filenames, list):
        child1_filenames = [child1_filenames]
    if not isinstance(child2_filenames, list):
        child2_filenames = [child2_filenames]
    child1_filenames = [str(x).strip()
                        for x in child1_filenames if str(x).strip()][:3]
    child2_filenames = [str(x).strip()
                        for x in child2_filenames if str(x).strip()][:3]

    child1_input_images = _presigned_urls_for_saved_files(
        child1_filenames, expires_in=3600) if child1_filenames else []
    child2_input_images = _presigned_urls_for_saved_files(
        child2_filenames, expires_in=3600) if child2_filenames else []

    return {
        "job_id": job_id,
        "name": order.get("name", ""),
        "gender": (order.get("gender", "") or "").lower(),
        "age": order.get("age", ""),
        "email": email,
        "created_at": _iso(order.get("created_at")),
        "book_id": book_id,
        "preview_url": preview_url,
        "partial_preview": order.get("partial_preview", ""),
        "final_preview": order.get("final_preview", ""),
        "input_images": input_image_urls,
        "paid": bool(order.get("paid", False)),
        "approved": bool(order.get("approved", False)),
        "child1_age": _get_child_age(order, 1),
        "child2_age": _get_child_age(order, 2) if is_twin else None,
        "child1_image_filenames": child1_filenames,
        "child2_image_filenames": child2_filenames,
        "child1_input_images": child1_input_images,
        "child2_input_images": child2_input_images,
        "is_twin": is_twin,
    }

def get_pdf_page_count(pdf_url: str) -> int:
    try:
        # Download the PDF
        response = requests.get(pdf_url)
        if response.status_code != 200:
            return 35

        # Read the PDF content
        pdf_content = io.BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_content)

        # Get the page count
        return len(pdf_reader.pages)
    except Exception as e:
        print(f"Error counting PDF pages: {str(e)}")
        return 35  # Fallback to default value

def _send_production_email(
    to_email: str,
    display_name: str,
    child_name: str,
    job_id: str | None,
    order_id: str | None,
):
    if not to_email:
        print("[MAIL] skipped: empty recipient for production email")
        return

    display = (display_name or "there").strip().title() or "there"
    child = (child_name or "Your").strip().title() or "Your"
    track_href = f"https://peekori.com/track-your-order?job_id={job_id}"
    safe_order = order_id or "—"
    subject = f"Order {safe_order}: {child}'s storybook is now in production 🎉"

    html_template = """<!doctype html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="x-apple-disable-message-reformatting">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <meta name="supported-color-schemes" content="light">
  <style>
    body { margin:0; padding:20px; background:#f7f7f7; -webkit-text-size-adjust:100%; -ms-text-size-adjust:100%; }
    .container { width:100%; max-width:768px; margin:0 auto; background:#ffffff; border-radius:8px; box-shadow:0 0 10px rgba(0,0,0,0.08); overflow:hidden; }
    .inner { padding:24px; font-family:Arial, Helvetica, sans-serif; color:#111; }
    p { margin:0 0 14px 0; font-size:16px; line-height:1.5; }
    .row { width:100%; }
    .col { vertical-align:top; }
    .col-text { padding:20px; }
    .col-img { padding:0 20px 0 0; }
    img { border:0; outline:none; text-decoration:none; display:block; height:auto; }
    .badge { display:inline-block; padding:0; margin:0; }

    @keyframes shine-sweep {
      0%   { transform: translateX(-100%) rotate(45deg); }
      50%  { transform: translateX(100%)  rotate(45deg); }
      100% { transform: translateX(100%)  rotate(45deg); }
    }

    .cta {
      position: relative;
      overflow: hidden;
      border-radius:9999px; text-align:center; mso-line-height-rule:exactly;
      font-family:Arial, Helvetica, sans-serif; font-weight:bold; text-decoration:none; display:block;
      color:#ffffff !important; background:#5784ba;
    }
    .cta::before {
      content: "";
      position: absolute;
      top: 0;
      left: -50%;
      height: 100%;
      width: 200%;
      background: linear-gradient(120deg, transparent 0%, rgba(255,255,255,0.6) 50%, transparent 100%);
      animation: shine-sweep 4s infinite;
    }

    .cta-wrap { width:auto; }
    .cta-text { font-size:15px; line-height:1.2; padding:12px 24px; display:block; color:#ffffff !important; text-decoration:none; }
    .cta-secondary { background:#5784ba; } /* static secondary */

    .banner { background:#f7f6cf; border-radius:8px; }
    .banner p { font-size:15px; }
    .center { text-align:center; }

    @media only screen and (max-width:480px) {
      .inner { padding:16px !important; }
      p { font-size:15px !important; }
      .stack { display:block !important; width:100% !important; }
      .col-text { padding:0px !important; text-align:center !important; }
      .col-img { padding:16px 0 0 0 !important; text-align:center !important; }
      .cta-wrap { width:100% !important; }
      .cta-text { font-size:13px !important; padding:10px 14px !important; }
      .center-sm { text-align:center !important; }
      .banner { padding:12px !important; }
      .mt-sm { margin-top:12px !important; }
      .banner .row { display:block !important; width:100% !important; }
      .banner .col { display:block !important; width:100% !important; }
      .banner img { margin:0 auto !important; }
    }
  </style>
</head>
<body>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="container">
          <tr>
            <td class="inner">
              <p>Hey {display},</p>
              <p><strong>{child}'s storybook</strong> has been moved to production at our print factory. 🎉</p>
              <p>It will be shipped within the next 3–4 business days. We will notify you with the tracking ID once your order is shipped.</p>

              <table role="presentation" cellpadding="0" cellspacing="0" border="0" class="cta-wrap" style="margin:8px 0 18px 0;">
                <tr>
                  <td>
                    <a href="{track_href}" class="cta">
                      <span class="cta-text">Track your order</span>
                    </a>
                  </td>
                </tr>
              </table>

              <p>Thanks,<br>Team Peekori</p>

              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="banner" style="margin-top:24px;">
                <tr>
                  <td>
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="row">
                      <tr>
                        <td class="col col-text stack" width="60%">
                          <p>Explore more magical books in our growing collection</p>

                          <table role="presentation" cellpadding="0" cellspacing="0" border="0" class="cta-wrap mt-sm" style="margin-top:16px;">
                            <tr>
                              <td>
                                <a href="https://peekori.com" class="cta cta-secondary">
                                  <span class="cta-text">Browse Now</span>
                                </a>
                              </td>
                            </tr>
                          </table>
                        </td>

                        <td class="col col-img stack" width="40%" align="right">
                          <img src="https://peekori.com/peekori-meta.png"
                               alt="Storybook Preview" width="300" style="max-width:100%;">
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    html = (html_template
            .replace("{display}", display)
            .replace("{child}", child)
            .replace("{track_href}", track_href))

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"Peekori <{EMAIL_USER}>"
    msg["To"] = to_email
    msg.set_content(
        f"Hey {display},\n\n"
        f"{child}'s storybook has been moved to production. "
        f"Track here: {track_href}\n\n"
        "Thanks,\nTeam Peekori"
    )
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)

def get_product_details(book_style: str | None, book_id: str | None) -> tuple[str, str]:
    style = (book_style or "").lower()
    bid = (book_id or "").lower()

    if bid == "wigu":
        if style == "paperback":
            return ("Paperback", "photobook_pb_270x200_mm_l_fc")
        if style == "hardcover":
            return ("Hardcover", "photobook_cw_270x200_mm_l_fc")
        # Fallback for WIGU
        return ("Hardcover", "photobook_cw_270x200_mm_l_fc")

    # Default (non-WIGU): square s210 products
    if style == "paperback":
        return ("Paperback", "photobook_pb_s210_s_fc")
    if style == "hardcover":
        return ("Hardcover", "photobook_cw_s210_s_fc")

    # Fallback to Hardcover for unknown styles
    return ("Hardcover", "photobook_cw_s210_s_fc")

def get_shipping_level(country_code: str) -> str:
    if country_code == "IN":
        return "cp_saver"
    elif country_code in {"US", "GB"}:
        return "cp_ground"
    return "cp_ground"  # default fallback


@app.post("/api/orders/approve-printing")
async def approve_printing(payload: BulkPrintRequest, background_tasks: BackgroundTasks):
    order_ids = payload.order_ids
    print_sent_by = payload.print_sent_by
    CLOUDPRINTER_API_KEY = os.getenv(
        "CLOUDPRINTER_API_KEY", "1414e4bd0220dc1e518e268937ff18a3")
    CLOUDPRINTER_API_URL = "https://api.cloudprinter.com/cloudcore/1.0/orders/add"

    results = []
    for order_id in order_ids:
        print(f"Processing order ID: {order_id}")
        # Fetch order details from MongoDB
        order = orders_collection.find_one({"order_id": order_id})
        if not order:
            print(f"Order not found in database: {order_id}")
            results.append({
                "order_id": order_id,
                "status": "error",
                "message": "Order not found",
                "step": "database_lookup"
            })
            continue

        if order.get("locked"):
            results.append({
                "order_id": order_id,
                "status": "skipped",
                "message": "Order is locked; cannot send to printer",
                "step": "locked",
            })
            continue

        print(f"Found order in database: {order_id}")
        print(f"Calculating MD5 sums for PDFs...")

        try:
            # Calculate MD5 sums for the PDFs
            book_url = order.get("book_url", "")
            cover_url = order.get("cover_url", "")
            quantity = order.get("quantity")

            print(f"Downloading and calculating MD5 for cover PDF...")
            cover_md5 = hashlib.md5(requests.get(
                cover_url).content).hexdigest() if cover_url else None
            print(f"Cover PDF MD5: {cover_md5}")

            print(f"Downloading and calculating MD5 for interior PDF...")
            interior_md5 = hashlib.md5(requests.get(
                book_url).content).hexdigest() if book_url else None
            print(f"Interior PDF MD5: {interior_md5}")

            # Get the page count from the interior PDF
            print(f"Calculating page count for interior PDF...")
            total_pages = get_pdf_page_count(book_url) if book_url else 35
            print(f"Total pages: {total_pages}")

            # Split shipping name into first and last name
            shipping_name = order.get("shipping_address", {}).get("name", "")
            firstname, lastname = split_full_name(shipping_name)
            print(f"Split shipping name: {firstname} {lastname}")

            # Get country code
            country = order.get("shipping_address", {}).get("country", "")
            country_code = COUNTRY_CODES.get(country, country)
            print(f"Mapped country {country} to code {country_code}")

            # Get product details based on book style
            book_style = order.get("book_style", "hardcover")
            book_id = order.get("book_id", "")
            reference, product_code = get_product_details(book_style, book_id)
            print(f"Selected product: {reference} ({product_code})")

            shipping_level = get_shipping_level(country_code)
            print(
                f"Selected shipping level: {shipping_level} for {country_code}")

            # Prepare the request payload
            print(f"Preparing CloudPrinter payload for order {order_id}...")
            payload = {
                "apikey": CLOUDPRINTER_API_KEY,
                "reference": order.get("order_id", ""),
                "email": "support@peekori.com",
                "addresses": [{
                    "type": "delivery",
                    "firstname": firstname,
                    "lastname": lastname,
                    "street1": order.get("shipping_address", {}).get("address1", ""),
                    "street2": order.get("shipping_address", {}).get("address2", ""),
                    "zip": order.get("shipping_address", {}).get("zip", ""),
                    "city": order.get("shipping_address", {}).get("city", ""),
                    "state": order.get("shipping_address", {}).get("province", ""),
                    "country": country_code,
                    "email": order.get("email", ""),
                    "phone": order.get("shipping_address", {}).get("phone", "") if country_code == "IN" else order.get("phone_number", "")
                }],
                "items": [{
                    "reference": reference,
                    "product": product_code,
                    "shipping_level": shipping_level,
                    "title": f"{order.get('order_id', '')}_{order.get('name', 'Book')}",
                    "count": quantity,
                    "files": [
                        {
                            "type": "cover",
                            "url": cover_url,
                            "md5sum": cover_md5
                        },
                        {
                            "type": "book",
                            "url": book_url,
                            "md5sum": interior_md5
                        }
                    ],
                    "options": [
                        {
                            "type": "total_pages",
                            "count": str(total_pages)
                        }
                    ]
                }]
            }

            print(f"Sending request to CloudPrinter for order {order_id}...")

            response = requests.post(
                CLOUDPRINTER_API_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response_data = response.json()

            print(
                f"CloudPrinter API Response (Status {response.status_code}): {response_data}")

            if response.status_code in [200, 201]:
                print(f"Updating order status in database for {order_id}...")
                # mark that Cloudprinter was used and save reference + timestamp
                orders_collection.update_one(
                    {"order_id": order_id},
                    {
                        "$set": {
                            "print_status": "sent_to_printer",
                            "printer": "Cloudprinter",                                   # NEW
                            "cloudprinter_reference": response_data.get("reference", ""),
                            "print_sent_at": datetime.now().isoformat(),
                            "print_sent_by": print_sent_by
                        }
                    }
                )

                # send the production email ONCE, idempotent
                once = orders_collection.update_one(
                    {"order_id": order_id, "$or": [
                        {"production_email_sent": {"$exists": False}},
                        {"production_email_sent": False}
                    ]},
                    {"$set": {"production_email_sent": True}}
                )

                if once.modified_count == 1:
                    to_email = (order.get("customer_email")
                                or order.get("email") or "").strip()
                    display_name = order.get("user_name") or "there"
                    child_name = order.get("name") or "Your"
                    job_id = order.get("job_id")

                    if to_email and EMAIL_USER and EMAIL_PASS:
                        background_tasks.add_task(
                            _send_production_email,
                            to_email,
                            display_name,
                            child_name,
                            job_id,
                            order_id
                        )
                        print(
                            f"[EMAIL] queued production email to {to_email} for {order_id}")
                    else:
                        print(
                            f"[EMAIL] skipped (missing recipient or creds) for {order_id}")
                else:
                    print(f"[EMAIL] already sent for {order_id}, skipping")

                results.append({
                    "order_id": order_id,
                    "status": "success",
                    "message": "Successfully sent to printer",
                    "step": "completed",
                    "cloudprinter_reference": response_data.get("reference", "")
                })
                print(f"Successfully processed order {order_id}")
            else:
                error_msg = response_data.get(
                    "message", "Failed to send to printer")
                print(
                    f"Failed to send order {order_id} to printer: {error_msg}")
                results.append({
                    "order_id": order_id,
                    "status": "error",
                    "message": error_msg,
                    "step": "cloudprinter_api"
                })

        except Exception as e:
            error_msg = str(e)
            print(f"Error processing order {order_id}: {error_msg}")
            results.append({
                "order_id": order_id,
                "status": "error",
                "message": error_msg,
                "step": "processing"
            })

    return results



@app.get("/api/orders/{order_id}")
def get_order_detail(order_id: str):
    print(f"[DEBUG] Fetching details for order_id: {order_id}")
    order = _find_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _build_order_response(order)

@app.get("/api/orders_api/{order_id}")
def get_order_detail(order_id: str):
    print(f"[DEBUG] Fetching details for order_id: {order_id}")
    order = _find_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _build_order_response(order)

@app.get("/api/shipping/{order_id}")
def get_shipping_detail(order_id: str):
    # debug
    print("DEBUG received order_id:", repr(order_id))
    shipping = shipping_collection.find_one({"order_id": order_id})
    print("DEBUG db find result:", shipping is not None)
    if not shipping:
        # fallback: check orders collection for embedded shipping info
        order = _find_order_by_id(order_id)
        if order and order.get("shipping_address"):
            return {"shipping_address": order.get("shipping_address")}
        raise HTTPException(
            status_code=404, detail="Shipping details not found")
    shipping["_id"] = str(shipping.get("_id")) if shipping.get("_id") else None
    return shipping


@app.get("/api/shipment-orders")
def get_shipment_orders(
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    sort_dir: Optional[str] = Query("asc", description="asc or desc"),

    filter_status: Optional[str] = Query(None),
    filter_book_style: Optional[str] = Query(None),
    filter_print_approval: Optional[str] = Query(None),

    filter_discount_code: Optional[str] = Query(None),
    exclude_discount_code: Optional[List[str]] = Query(None),

    q: Optional[str] = Query(
        None,
        description="Search job_id, order_id, email, name, discount_code, city, locale, book_id"
    ),

    # New filters
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    shipping_status: Optional[str] = Query(None, description="current_status filter"),
    order_ids: Optional[List[str]] = Query(None),


    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=1000),
):
    """
    Shipment Orders API
    Supports:
    - date filtering
    - shipping status filtering (based on current_status)
    - search, pagination, sorting
    """

    # -------------------------
    # Base Query
    # -------------------------
    query: Dict[str, Any] = {}
    # Filter by specific order IDs
    if order_ids:
        query["order_id"] = {"$in": order_ids}

    ex_values: List[str] = []

    # -------------------------
    # Status Filters (Approved / Uploaded)
    # -------------------------
    if filter_status == "approved":
        query["approved"] = True
    elif filter_status == "uploaded":
        query["approved"] = False

    if filter_book_style:
        query["book_style"] = filter_book_style

    if filter_print_approval == "yes":
        query["print_approval"] = True
    elif filter_print_approval == "no":
        query["print_approval"] = False
    elif filter_print_approval == "not_found":
        query["print_approval"] = {"$exists": False}

    # -------------------------
    # Discount Filters
    # -------------------------
    if filter_discount_code:
        if filter_discount_code.lower() == "none":
            query["discount_amount"] = 0
            query["paid"] = True
        else:
            query["discount_code"] = filter_discount_code.upper()

    if exclude_discount_code:
        if not isinstance(exclude_discount_code, list):
            ex_values = [p.strip() for p in str(exclude_discount_code).split(",")]
        else:
            ex_values = exclude_discount_code

    ex_values = [v for v in (s.strip() for s in ex_values) if v]

    if ex_values:
        regexes = [re.compile(rf"^{re.escape(v)}$", re.IGNORECASE) for v in ex_values]
        existing = query.pop("discount_code", None)
        exclude_cond = {"discount_code": {"$nin": regexes}}

        if existing is None:
            query["discount_code"] = exclude_cond["discount_code"]
        else:
            query.setdefault("$and", []).append({"discount_code": existing})
            query["$and"].append(exclude_cond)

    # -------------------------
    # Search Query
    # -------------------------
    if q:
        term = q.strip()
        if term:
            rx = re.compile(re.escape(term), re.IGNORECASE)
            query.setdefault("$and", []).append({
                "$or": [
                    {"order_id": {"$regex": rx}},
                    {"job_id": {"$regex": rx}},
                    {"email": {"$regex": rx}},
                    {"name": {"$regex": rx}},
                    {"discount_code": {"$regex": rx}},
                    {"book_id": {"$regex": rx}},
                    {"locale": {"$regex": rx}},
                    {"shipping_address.city": {"$regex": rx}},
                ]
            })
    
   

    IST = timezone(timedelta(hours=5, minutes=30))

    # -------------------------
    # DATE FILTER (processed_at with IST)
    # -------------------------
    if start_date or end_date:
        date_filter = {}

        try:
            if start_date:
                # Parse start_date and set IST midnight
                sd = date_parser.parse(start_date)
                sd_ist = sd.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=IST)

                # Convert IST to UTC
                sd_utc = sd_ist.astimezone(timezone.utc)
                date_filter["$gte"] = sd_utc

            if end_date:
                # Parse end_date and set IST end of day
                ed = date_parser.parse(end_date)
                ed_ist = ed.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=IST)

                # Convert IST → UTC
                ed_utc = ed_ist.astimezone(timezone.utc)
                date_filter["$lte"] = ed_utc

            query["processed_at"] = date_filter

        except Exception as e:
            print("DATE PARSE ERROR:", e)




    # -------------------------
    # SHIPPING STATUS FILTER  (current_status)
    # -------------------------
    STATUS_MAP = {
        "out for pickup": "OUT FOR PICKUP",
        "in transit": "IN TRANSIT",
        "picked up": "PICKED UP",
        "pickup done": "PICKUP DONE",
        "out for delivery": "OUT FOR DELIVERY",
        "delivered": "DELIVERED",
        "pickup exception": "PICKUP EXCEPTION",
    }

    if shipping_status and shipping_status.lower() != "all":
        normalized = STATUS_MAP.get(shipping_status.lower())
        if normalized:
            query["current_status"] = normalized

    query = _with_paid_fallback(query)

    # -------------------------
    # Pagination + Sorting
    # -------------------------
    skip = (page - 1) * limit
    total_count = orders_collection.count_documents(query)

    sort_field = sort_by if sort_by else "created_at"
    sort_order = 1 if sort_dir == "asc" else -1

    # -------------------------
    # Projection
    # -------------------------
    projection = {
        "order_id": 1,
        "job_id": 1,
        "cover_url": 1,
        "book_url": 1,
        "preview_url": 1,
        "name": 1,
        "shipping_address": 1,
        "created_at": 1,
        "processed_at": 1,
        "approved_at": 1,
        "approved": 1,
        "book_id": 1,
        "book_style": 1,
        "print_status": 1,
        "price": 1,
        "total_price": 1,
        "amount": 1,
        "total_amount": 1,
        "feedback_email": 1,
        "print_approval": 1,
        "discount_code": 1,
        "currency": 1,
        "locale": 1,
        "quantity": 1,
        "_id": 0,
        "shipped_at": 1,
        "cust_status": 1,
        "printer": 1,
        "locked": 1,
        "locked_by": 1,
        "unlock_by": 1,
        "print_sent_by": 1,
        "current_status": 1,
    }

    cursor = (
        orders_collection
        .find(query, projection)
        .sort(sort_field, sort_order)
        .skip(skip)
        .limit(limit)
    )

    # -------------------------
    # Format Output
    # -------------------------
    result = []
    for doc in list(cursor):
        result.append({
            "order_id": _order_id_fallback(doc),
            "job_id": doc.get("job_id", ""),
            "coverPdf": _first_non_empty(doc, ["cover_url", "cover_pdf", "cover_image"], default=""),
            "interiorPdf": _first_non_empty(doc, ["book_url", "interior_pdf", "interior_url"], default=""),
            "previewUrl": _first_non_empty(doc, ["preview_url", "preview"], default=""),

            "name": doc.get("name", ""),
            "city": doc.get("shipping_address", {}).get("city", ""),

            "price": doc.get(
                "price",
                doc.get("total_price", doc.get("amount", doc.get("total_amount", 0)))
            ),

            "paymentDate": doc.get("processed_at", ""),
            "approvalDate": doc.get("approved_at", ""),
            "status": _derive_status(doc),

            "bookId": doc.get("book_id", ""),
            "bookStyle": _first_non_empty(doc, ["book_style", "binding", "cover_type"], default=""),
            "printStatus": doc.get("print_status", ""),
            "print_approval": doc.get("print_approval", None),

            "discount_code": doc.get("discount_code", ""),
            "currency": _first_non_empty(doc, ["currency", "currency_code"], default=""),
            "locale": doc.get("locale", ""),

            "shippedAt": doc.get("shipped_at"),
            "quantity": doc.get("quantity", 1),
            "cust_status": doc.get("cust_status", ""),
            "printer": doc.get("printer", ""),

            "locked": bool(doc.get("locked", False)),
            "locked_by": doc.get("locked_by", ""),
            "unlock_by": doc.get("unlock_by", ""),
            "print_sent_by": doc.get("print_sent_by", ""),

            # NEW FIELD
            "shippingStatus": doc.get("current_status", ""),
        })

    return {
        "orders": result,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": (total_count + limit - 1) // limit,
        }
    }

def _sr_login_token() -> str:
    if not SHIPROCKET_EMAIL or not SHIPROCKET_PASSWORD:
        raise HTTPException(
            status_code=500, detail="Shiprocket API creds missing")
    r = requests.post(
        f"{SHIPROCKET_BASE}/v1/external/auth/login",
        json={"email": SHIPROCKET_EMAIL, "password": SHIPROCKET_PASSWORD},
        timeout=30,
    )
    if r.status_code != 200:
        raise HTTPException(
            status_code=502, detail=f"Shiprocket auth failed: {r.text}")
    token = (r.json() or {}).get("token")
    if not token:
        raise HTTPException(
            status_code=502, detail="Shiprocket auth returned no token")
    return token

def _sr_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def split_full_name(full_name: str) -> tuple[str, str]:
    """Split a full name into first name and last name."""
    if not full_name:
        return ("", "")

    parts = full_name.strip().split()
    if len(parts) == 1:
        return (parts[0], "")
    return (" ".join(parts[:-1]), parts[-1])

def generate_book_title(book_id, child_name):
    if not child_name:
        child_name = "Your child"
    else:
        child_name = child_name.strip().capitalize()

    book_id = (book_id or "").lower()

    if book_id == "wigu":
        return f"When {child_name} grows up"
    elif book_id == "astro":
        return f"{child_name}'s Space Adventure"
    elif book_id == "abcd":
        return f"{child_name} meets ABC"
    elif book_id == "dream":
        return f"Many Dreams of {child_name}"
    elif book_id == "sports":
        return f"Game On, {child_name}!"
    elif book_id == "hero":
        return f"{child_name}, the Little Hero"
    elif book_id == "bloom":
        return f"{child_name}' is Growing Up Fast"
    else:
        return f"{child_name}'s Storybook"


def _sr_order_payload_from_doc(doc: Dict[str, Any], order_id_override: str = None) -> Dict[str, Any]:
    ship = doc.get("shipping_address") or {}
    # name split (helper exists earlier in this file)
    first, last = split_full_name(ship.get("name", "") or (
        doc.get("user_name") or doc.get("name") or ""))

    # price/qty
    qty = int(doc.get("quantity", 1) or 1)
    subtotal = float(
        doc.get("total_amount")
        or doc.get("total_price")
        or doc.get("amount")
        or doc.get("price")
        or 0.0
    )

    # package: apply dimensions by book_id
    book_id = (doc.get("book_id") or "").lower().strip()

    if book_id == "wigu":
        length, breadth, height = 32.0, 23.0, 3.0
    else:
        length, breadth, height = 23.0, 23.0, 3.0

    base_weight = float(doc.get("weight_kg", 0.5))
    weight = round(base_weight * qty, 3)


    # book identity for item line
    order_id = order_id_override or doc.get("order_id")
    book_id = (doc.get("book_id") or "BOOK").upper()
    book_style = (doc.get("book_style") or "HARDCOVER").upper()
    book_id_norm = book_id.lower()
    book_style_norm = book_style.lower()

    if book_id_norm == "wigu":
        sku_prefix = "24_W"
    elif book_id_norm == "abcd":
        sku_prefix = "28_S"
    else:
        sku_prefix = "24_S"

    if book_style_norm == "hardcover":
        sku_suffix = "HC"
    elif book_style_norm == "paperback":
        sku_suffix = "PB"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid book_style for SKU: {book_style}"
        )

    sku = f"{sku_prefix}_{sku_suffix}"

    order_id_long = (doc.get("order_id_long"))
    name = (doc.get("name"))
    product_name = generate_book_title(book_id, name)

    # order date "YYYY-MM-DD HH:MM" (IST)
    dt = doc.get("processed_at") or doc.get("created_at")
    try:
        if isinstance(dt, str):
            dt = parser.isoparse(dt)
        if isinstance(dt, datetime) and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        order_date = (dt or datetime.now(timezone.utc)).astimezone(
            IST_TZ).strftime("%Y-%m-%d %H:%M")
    except Exception:
        order_date = datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M")

    # ---- PICKUP LOCATION BASED ON PRINTER ----
    printer = (doc.get("printer") or "").strip().lower()

    if printer == "yara":
        # must match the pickup name configured in Shiprocket
        pickup_name = "Peekori"
    elif printer == "genesis":
        # must match the pickup name configured in Shiprocket
        pickup_name = "warehouse-1"

    if not pickup_name:
        raise HTTPException(
            status_code=400, detail="Shiprocket pickup_location not configured")

    # payment
    cod = bool(doc.get("payment_method") == "COD")

    return {
        # your reference
        "order_id": str(order_id),
        "order_date": order_date,
        "pickup_location": pickup_name,
        "comment": doc.get("comment", ""),

        "billing_customer_name": first or ship.get("name", "") or "Customer",
        "billing_last_name": last,
        "billing_address": ship.get("address1", ""),
        "billing_address_2": ship.get("address2", ""),
        "billing_city": ship.get("city", ""),
        "billing_pincode": str(ship.get("zip", ""))[:6],
        "billing_state": ship.get("province", ""),
        "billing_country": ship.get("country", "India"),
        "billing_email": (doc.get("email") or doc.get("customer_email") or ""),
        "billing_phone": ship.get("phone") or doc.get("phone_number") or "",

        "shipping_is_billing": True,
        "shipping_customer_name": "",
        "shipping_last_name": "",
        "shipping_address": "",
        "shipping_address_2": "",
        "shipping_city": "",
        "shipping_pincode": "",
        "shipping_country": "",
        "shipping_state": "",
        "shipping_email": "",
        "shipping_phone": "",

        "order_items": [
            {
                "name": f"{product_name}",
                "sku": sku,
                "units": qty,
                "selling_price": float(round(subtotal / max(qty, 1), 2)),
                "discount": 0,
                "tax": 0,
                "hsn": ""
            }
        ],
        "payment_method": "COD" if cod else "Prepaid",
        "shipping_charges": 0,
        "giftwrap_charges": 0,
        "transaction_charges": 0,
        "total_discount": 0,
        "sub_total": float(subtotal),

        "length": length,
        "breadth": breadth,
        "height": height,
        "weight": weight,
    }

def _parse_dt(value):
    """Return naive datetime from common string or datetime inputs; None if not parseable."""
    if isinstance(value, datetime):
        # Strip tzinfo if present (we’ll treat it as naive UTC below)
        return value.replace(tzinfo=None)
    if isinstance(value, str):
        # Try a few common wire formats
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ):
            try:
                dt = datetime.strptime(value, fmt)
                return dt.replace(tzinfo=None)
            except ValueError:
                pass
    return None

def _render_na_table(title: str, wnd_from: str, wnd_to: str, rows: list[dict]) -> str:
    """Render an HTML table with: Payment ID, Email, Payment Date, Amount, Paid, Preview, Job ID."""
    def safe(v):  # basic escape
        return html.escape(str(v)) if v is not None else "—"

    header = f"""
    <h2 style="margin:0 0 8px 0;font-family:Arial,sans-serif">{safe(title)}</h2>
    <div style="font-family:Arial,sans-serif;font-size:13px;margin:0 0 12px 0">
      <strong>Window (IST):</strong> {safe(wnd_from)} → {safe(wnd_to)}
    </div>
    """

    if not rows:
        return header + '<p style="font-family:Arial,sans-serif">No NA payment details.</p>'

    # Build table rows
    tr_html = []
    for r in rows:
        pid = r.get("id") or r.get("payment_id") or "—"
        email = r.get("email") or "—"
        dt = r.get("created_at") or "—"
        amt = r.get("amount_display") or "—"
        paid = r.get("paid")
        paid_str = "true" if paid is True else (
            "false" if paid is False else "—")
        prev = r.get("preview_url") or ""
        job = r.get("job_id") or "—"

        prev_link = f'<a href="{html.escape(prev)}" target="_blank">preview</a>' if prev else "—"

        tr_html.append(f"""
          <tr>
            <td style="padding:6px 8px;border:1px solid #e5e7eb;font-family:Consolas,Menlo,monospace">{safe(pid)}</td>
            <td style="padding:6px 8px;border:1px solid #e5e7eb">{safe(email)}</td>
            <td style="padding:6px 8px;border:1px solid #e5e7eb">{safe(dt)}</td>
            <td style="padding:6px 8px;border:1px solid #e5e7eb">{safe(amt)}</td>
            <td style="padding:6px 8px;border:1px solid #e5e7eb">{safe(paid_str)}</td>
            <td style="padding:6px 8px;border:1px solid #e5e7eb">{prev_link}</td>
            <td style="padding:6px 8px;border:1px solid #e5e7eb;font-family:Consolas,Menlo,monospace">{safe(job)}</td>
          </tr>
        """)

    table = f"""
    <table cellspacing="0" cellpadding="0" style="border-collapse:collapse;border:1px solid #e5e7eb;font-family:Arial,sans-serif;font-size:13px">
      <thead>
        <tr style="background:#f9fafb">
          <th style="text-align:left;padding:6px 8px;border:1px solid #e5e7eb">Payment ID</th>
          <th style="text-align:left;padding:6px 8px;border:1px solid #e5e7eb">Email</th>
          <th style="text-align:left;padding:6px 8px;border:1px solid #e5e7eb">Payment Date</th>
          <th style="text-align:left;padding:6px 8px;border:1px solid #e5e7eb">Amount</th>
          <th style="text-align:left;padding:6px 8px;border:1px solid #e5e7eb">Paid</th>
          <th style="text-align:left;padding:6px 8px;border:1px solid #e5e7eb">Preview</th>
          <th style="text-align:left;padding:6px 8px;border:1px solid #e5e7eb">Job ID</th>
        </tr>
      </thead>
      <tbody>
        {''.join(tr_html)}
      </tbody>
    </table>
    """

    return header + table

@app.get("/api/stats/order-status")
def stats_order_status(
    range: str = Query("1w", description="1d, 1w, 1m, 6m, this_month, custom"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    printer: Optional[str] = Query("all", description="genesis | yara"),
    loc: Optional[str] = Query("IN", description="country code"),
):
    """
    Order Status
    Same logic as ship-status-v2
    WITHOUT out_for_pickup, pickup_exception, issue columns
    WITH cancelled, rejected, refunded, reprint
    """

    exclude_codes = ["TEST", "COLLAB", "REJECTED", "TINA"]
    exclude_set = {c.upper() for c in exclude_codes}

    # --------------------------------------------------
    # Location match
    # --------------------------------------------------
    try:
        loc_match = _build_loc_match(loc)
    except Exception:
        loc_match = None

    # --------------------------------------------------
    # 1) Determine Period
    # --------------------------------------------------
    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST_TZ)

    effective_range = "1w" if range == "1d" else range

    try:
        if start_date and end_date:
            cs, ce, ps, pe, _ = _periods_custom(start_date, end_date)
            labels = _labels_for("custom", cs, ce)
        else:
            cs, ce, ps, pe, gran = _periods(effective_range, now_utc)
            labels = _labels_for(effective_range, cs, ce)
    except Exception:
        labels = []
        for i in range(6, -1, -1):
            d = (now_ist - timedelta(days=i))
            labels.append(d.strftime("%Y-%m-%d"))
        cs = ce = None

    # --------------------------------------------------
    # 2) Base order query
    # --------------------------------------------------
    base_match = {
        "paid": True,
        "processed_at": {"$exists": True, "$ne": None},
    }

    if loc_match:
        base_match = {"$and": [base_match, loc_match]}

    if cs and ce:
        date_filter = {"processed_at": {"$gte": cs, "$lt": ce}}
        if "$and" in base_match:
            base_match["$and"].append(date_filter)
        else:
            base_match = {"$and": [base_match, date_filter]}

    projection = {
        "order_id": 1,
        "processed_at": 1,
        "printer": 1,
        "discount_code": 1,
        "current_status": 1,
        "_id": 0,
    }

    cursor = orders_collection.find(base_match, projection)

    # --------------------------------------------------
    # 3) Organize orders
    # --------------------------------------------------
    orders_by_date = {k.split(" ")[0]: [] for k in labels}

    for doc in cursor:
        try:
            raw_code = (doc.get("discount_code") or "").strip().upper()
            if raw_code in exclude_set:
                continue

            dt = doc.get("processed_at")
            if isinstance(dt, str):
                dt = date_parser.isoparse(dt)

            if not dt:
                continue

            dt_ist = dt.astimezone(IST_TZ)
            ist_date = dt_ist.strftime("%Y-%m-%d")

            if ist_date not in orders_by_date:
                continue

            printer_val = (doc.get("printer") or "").strip().lower()
            if printer and printer.lower() not in ("all", ""):
                if printer_val != printer.lower():
                    continue

            status = (doc.get("current_status") or "").strip().lower()
            order_status = (doc.get("order_status") or "").strip().lower()
            oid = doc.get("order_id")

            orders_by_date[ist_date].append({
                "order_id": oid,
                "current_status": status,
                "order_status": order_status,
                "printer": printer_val,
            })

        except Exception:
            continue

    # --------------------------------------------------
    # 4) Build rows per day
    # --------------------------------------------------
    rows = []

    for lbl in labels:
        date_key = lbl.split(" ")[0]
        day_orders = orders_by_date.get(date_key, [])

        unapproved_ids = []
        new_ids = []
        sent_to_print_ids = []
        shipped_ids = []
        delivered_ids = []

        cancelled_ids = []
        rejected_ids = []
        refunded_ids = []
        reprint_ids = []

        for od in day_orders:
            oid = od["order_id"]
            printer_val = od["printer"]
            status = od["current_status"]
            order_status = od["order_status"]

            # ------------------------------
            # BUSINESS TERMINAL STATES FIRST
            # ------------------------------
            if order_status == "cancelled":
                cancelled_ids.append(oid)
                continue

            if order_status == "rejected":
                rejected_ids.append(oid)
                continue

            if order_status == "refunded":
                refunded_ids.append(oid)
                continue

            if order_status == "reprint":
                reprint_ids.append(oid)
                continue

            # ------------------------------
            # NORMAL FLOW
            # ------------------------------
            if not printer_val:
                unapproved_ids.append(oid)

            if printer_val in ("genesis", "yara"):
                sent_to_print_ids.append(oid)

            if not status:
                new_ids.append(oid)
                continue

            if "delivered" in status:
                delivered_ids.append(oid)
                continue

            if (
                "picked up" in status
                or "pickup done" in status
                or "in transit" in status
                or "transit" in status
            ):
                shipped_ids.append(oid)
                continue

            shipped_ids.append(oid)

        rows.append({
            "date": date_key,
            "total": len(day_orders),

            "unapproved": len(unapproved_ids),
            "unapproved_ids": unapproved_ids,

            "sent_to_print": len(sent_to_print_ids),
            "sent_to_print_ids": sent_to_print_ids,

            "new": len(new_ids),
            "new_ids": new_ids,

            "shipped": len(shipped_ids),
            "shipped_ids": shipped_ids,

            "delivered": len(delivered_ids),
            "delivered_ids": delivered_ids,

            # ✅ NEW FIELDS
            "cancelled": len(cancelled_ids),
            "cancelled_ids": cancelled_ids,

            "rejected": len(rejected_ids),
            "rejected_ids": rejected_ids,

            "refunded": len(refunded_ids),
            "refunded_ids": refunded_ids,

            "reprint": len(reprint_ids),
            "reprint_ids": reprint_ids,
        })

    return {
        "labels": labels,
        "rows": rows,
        "printer": printer or "all",
    }


@app.post("/api/shiprocket/create-from-orders", tags=["shiprocket"])
def shiprocket_create_from_orders(
    order_ids: List[str] = Body(..., embed=True,
                                description="Peekori order_ids like ['#123', '#124']"),
    assign_awb: bool = Body(
        False, embed=True, description="If true, assign AWB after creating order"),
    request_pickup: bool = Body(
        False, embed=True, description="If true, generate pickup after AWB assignment"),
):
    """
    Creates Shiprocket orders for the provided order_ids (reads delivery details from Mongo),
    optionally assigns AWB and requests pickup. By default this WILL ONLY create orders.
    """
    if not order_ids:
        raise HTTPException(status_code=400, detail="order_ids required")

    # dedupe, preserve order
    seen, unique_ids = set(), []
    for oid in order_ids:
        if oid not in seen:
            seen.add(oid)
            unique_ids.append(oid)

    token = _sr_login_token()
    headers = _sr_headers(token)

    created_refs: List[Dict[str, Any]] = []
    shipment_ids: List[int] = []
    errors: List[str] = []

    # 1) Create orders only
    for oid in unique_ids:
        doc = find_order_by_any_id(oid)
        if not doc:
            errors.append(f"{oid}: not found")
            continue

        reprint_key = extract_reprint_key(oid)

        # ================= ORIGINAL ORDER =================
        if not reprint_key:
            # already created? skip
            if doc.get("sr_order_id") and doc.get("sr_shipment_id"):
                errors.append(f"{oid}: shiprocket already exists for original order")
                continue

            payload = _sr_order_payload_from_doc(doc, order_id_override=doc["order_id"])

        # ================= REPRINT ORDER =================
        else:
            rp_meta = (doc.get("reprint_meta") or {}).get(reprint_key) or {}

            # already created? skip
            if rp_meta.get("sr_order_id") and rp_meta.get("sr_shipment_id"):
                errors.append(f"{oid}: shiprocket already exists for reprint {reprint_key}")
                continue

            payload = _sr_order_payload_from_doc(doc, order_id_override=oid)

        try:
            r = requests.post(
                f"{SHIPROCKET_BASE}/v1/external/orders/create/adhoc",
                headers=headers, json=payload, timeout=40
            )
            if r.status_code != 200:
                errors.append(f"{oid}: create failed {r.status_code} {r.text}")
                continue

            j = r.json() or {}
            sr_order_id = j.get("order_id")
            shipment_id = j.get("shipment_id")

            # ================= SAVE =================
            if not reprint_key:
                # original order
                orders_collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {
                        "sr_order_id": sr_order_id,
                        "sr_shipment_id": shipment_id,
                        "shiprocket_created_at": datetime.utcnow().isoformat(),
                        "shiprocket_pickup_location": payload.get("pickup_location")
                    }}
                )
            else:
                # reprint order
                orders_collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {
                        f"reprint_meta.{reprint_key}.sr_order_id": sr_order_id,
                        f"reprint_meta.{reprint_key}.sr_shipment_id": shipment_id,
                        f"reprint_meta.{reprint_key}.shiprocket_created_at": datetime.utcnow().isoformat(),
                        f"reprint_meta.{reprint_key}.shiprocket_pickup_location": payload.get("pickup_location")
                    }}
                )

            created_refs.append({
                "order_id": oid,
                "sr_order_id": sr_order_id,
                "shipment_id": shipment_id
            })

            if shipment_id:
                shipment_ids.append(int(shipment_id))

        except Exception as e:
            errors.append(f"{oid}: exception {e}")

    # If caller didn't request AWB, stop here (this keeps orders unassigned)
    if not assign_awb:
        return {"created": created_refs, "awbs": [], "pickup": None, "errors": errors}

    # 2) Assign AWB (only if assign_awb == True)
    awb_results: List[Dict[str, Any]] = []
    for sid in shipment_ids:
        try:
            rr = requests.post(
                f"{SHIPROCKET_BASE}/v1/external/courier/assign/awb",
                headers=headers, json={"shipment_id": sid}, timeout=30
            )
            if rr.status_code != 200:
                errors.append(f"awb({sid}) failed {rr.status_code}: {rr.text}")
                continue
            j = rr.json() or {}
            awb_code = j.get("awb_code")
            courier_id = j.get("courier_company_id")
            awb_results.append(
                {"shipment_id": sid, "awb_code": awb_code, "courier_company_id": courier_id})

            orders_collection.update_one({"sr_shipment_id": sid}, {
                                         "$set": {"awb_code": awb_code, "courier_company_id": courier_id}})
        except Exception as e:
            errors.append(f"awb({sid}): exception {e}")

    # 3) Generate pickup (only if request_pickup == True)
    pickup_res = None
    if request_pickup and awb_results:
        try:
            rr = requests.post(
                f"{SHIPROCKET_BASE}/v1/external/courier/generate/pickup",
                headers=headers,
                json={"shipment_id": [x["shipment_id"] for x in awb_results]},
                timeout=30
            )
            if rr.status_code == 200:
                pickup_res = rr.json()
                orders_collection.update_many(
                    {"sr_shipment_id": {
                        "$in": [x["shipment_id"] for x in awb_results]}},
                    {"$set": {"pickup_requested": True,
                              "pickup_requested_at": datetime.utcnow().isoformat()}}
                )
            else:
                errors.append(f"pickup failed {rr.status_code}: {rr.text}")
        except Exception as e:
            errors.append(f"pickup: exception {e}")

    return {"created": created_refs, "awbs": awb_results, "pickup": pickup_res, "errors": errors}

def _to_number(value):
    try:
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            return value
        value = value.strip()
        if value == "":
            return 0
        return float(value)
    except Exception:
        return 0


@app.get("/api/shiprocket/order/show")
def shiprocket_order_show(internal_order_id: str):

    if not internal_order_id:
        raise HTTPException(
            status_code=400, detail="internal_order_id required")

    # 1️⃣ Lookup internal order in orders collection (UNCHANGED)
    doc = orders_collection.find_one({"order_id": internal_order_id})
    if not doc:
        raise HTTPException(
            status_code=404, detail=f"{internal_order_id} not found in database")

    sr_order_id = (
        doc.get("sr_order_id")
        or doc.get("shiprocket_data", {}).get("sr_order_id")
    )
    if not sr_order_id:
        raise HTTPException(
            status_code=400,
            detail=f"{internal_order_id} has no Shiprocket order linked (sr_order_id missing)"
        )

    # 2️⃣ Call Shiprocket API (UNCHANGED)
    token = _sr_login_token()
    headers = _sr_headers(token)
    url = f"{SHIPROCKET_BASE}/v1/external/orders/show/{sr_order_id}"

    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"Shiprocket API error: {str(e)}")

    data = r.json().get("data", {}) or {}

    # 3️⃣ Extract shipping_charges (UNCHANGED)
    raw_shipping = (
        data.get("others", {}).get("shipping_charges")
        or data.get("others", {}).get("shipping_charge")
        or data.get("shipping_charges")
        or data.get("shipping_charge")
        or data.get("awb_data", {}).get("charges", {}).get("freight_charges")
        or "0"
    )

    shipping_charges = _to_number(raw_shipping)

    # 4️⃣ Extract courier_name (UNCHANGED)
    shipments = data.get("shipments") or {}
    if isinstance(shipments, dict):
        courier_name = shipments.get(
            "courier") or shipments.get("courier_name") or ""
    elif isinstance(shipments, list) and shipments:
        courier_name = shipments[0].get(
            "courier") or shipments[0].get("courier_name") or ""
    else:
        courier_name = ""

    # 5️⃣ Store the result ONLY in shipping_collection
    try:
        shipping_collection.update_one(
            {"order_id": internal_order_id},
            {
                "$set": {
                    "order_id": internal_order_id,
                    "sr_order_id": sr_order_id,
                    "shipping_charges": shipping_charges,
                    "courier_name": courier_name,
                    "shiprocket_raw": data,
                }
            },
            upsert=True
        )
    except Exception as e:
        logging.exception(
            f"[SR] Failed to update shipping_collection for {internal_order_id}: {e}")
    
    # 6️⃣ Also update ONLY shipping_charges in orders_collection
    try:
        orders_collection.update_one(
            {"order_id": internal_order_id},
            {
                "$set": {
                    "shipping_charges": shipping_charges
                }
            }
        )
    except Exception as e:
        logging.exception(
            f"[SR] Failed to update orders_collection for {internal_order_id}: {e}"
        )

    return {
        "order_id": internal_order_id,
        "courier_name": courier_name,
        "shipping_charges": shipping_charges
    }


def format_date(date_input: any) -> str:

    if not date_input:
        return ""
    try:
        # If it's a MongoDB date object (Python datetime)
        if isinstance(date_input, datetime):
            dt = date_input
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            formatted = dt.astimezone(IST).strftime("%d %b, %I:%M %p")

            return formatted
        # If it's a MongoDB extended JSON
        if isinstance(date_input, dict):
            if '$date' in date_input and '$numberLong' in date_input['$date']:
                timestamp = int(date_input['$date']['$numberLong']) / 1000
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                formatted = dt.astimezone(IST).strftime("%d %b, %I:%M %p")

                return formatted
            elif 'date' in date_input:
                timestamp = int(date_input['date']['$numberLong']) / \
                    1000 if '$numberLong' in date_input['date'] else int(
                        date_input['date']) / 1000
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                formatted = dt.astimezone(IST).strftime("%d %b, %I:%M %p")

                return formatted
        # If it's an ISO string
        elif isinstance(date_input, str):
            if date_input.strip() == "":
                return ""
            dt = datetime.fromisoformat(date_input.replace('Z', '+00:00'))
            formatted = dt.astimezone(IST).strftime("%d %b, %I:%M %p")

            return formatted
        else:
            print(f"[DEBUG] Unknown date format")
            return ""
    except Exception as e:
        print(f"[DEBUG] Error formatting date: {e}")
        return ""

def _to_naive_utc(x):
    if isinstance(x, datetime):
        # convert tz-aware -> naive UTC; leave others unchanged
        return x.astimezone(timezone.utc).replace(tzinfo=None) if x.tzinfo else x
    return x

@app.get("/api/jobs_api")
def get_jobs(
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    sort_dir: Optional[str] = Query("asc", description="asc or desc"),
    filter_status: Optional[str] = Query(None),
    filter_book_style: Optional[str] = Query(None),
    q: Optional[str] = Query(
        None, description="Search by job_id, order_id, name"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=1000),
):

    query = {}

    if filter_status == "approved":
        query["approved"] = True
    elif filter_status == "uploaded":
        query["approved"] = False

    if filter_book_style:
        query["book_id"] = filter_book_style

    # NEW: Search functionality
    if q and q.strip():
        term = q.strip()
        rx = re.compile(re.escape(term), re.IGNORECASE)
        query.setdefault("$and", []).append({
            "$or": [
                {"job_id": {"$regex": rx}},
                {"order_id": {"$regex": rx}},
                {"name": {"$regex": rx}},
                {"book_id": {"$regex": rx}},
            ]
        })

    sort_field = sort_by if sort_by else "created_at"
    sort_order = 1 if sort_dir == "asc" else -1

    projection = {
        "order_id": 1,
        "job_id": 1,
        "cover_url": 1,
        "book_url": 1,
        "preview_url": 1,
        "name": 1,
        "shipping_address": 1,
        "created_at": 1,
        "processed_at": 1,
        "approved_at": 1,
        "approved": 1,
        "book_id": 1,
        "book_style": 1,
        "print_status": 1,
        "price": 1,
        "total_price": 1,
        "amount": 1,
        "total_amount": 1,
        "feedback_email": 1,
        "locale": 1,
        "partial_preview": 1,
        "final_preview": 1,
        "pp_instance":1,
        "fp_instance":1,
        "printer": 1,
        "_id": 0,
        "error_reason": 1,
    }

    skip = (page - 1) * limit
    total_count = orders_collection.count_documents(query)

    records = list(orders_collection.find(
        query, projection).sort(sort_field, sort_order).skip(skip).limit(limit))

    result = []

    for doc in records:
        shipping_address = doc.get("shipping_address", {})
        if isinstance(shipping_address, dict):
            city = shipping_address.get("city", "")
        else:
            city = ""
        result.append({
            "order_id": doc.get("order_id", ""),
            "job_id": doc.get("job_id", ""),
            "coverPdf": doc.get("cover_url", ""),
            "interiorPdf": doc.get("book_url", ""),
            "previewUrl": doc.get("preview_url", ""),
            "name": doc.get("name", ""),
            "city": city,
            "price": doc.get("price", doc.get("total_price", doc.get("amount", doc.get("total_amount", 0)))),
            "createdAt": format_date(jsonable_encoder(doc.get("created_at", ""))),
            "paymentDate": doc.get("processed_at", ""),
            "approvalDate": doc.get("approved_at", ""),
            "status": "Approved" if doc.get("approved") else "Uploaded",
            "bookId": doc.get("book_id", ""),
            "bookStyle": doc.get("book_style", ""),
            "printStatus": doc.get("print_status", ""),
            "locale": doc.get("locale", ""),
            "partial_preview": doc.get("partial_preview", "") or "",
            "final_preview": doc.get("final_preview", "") or "",
            "pp_instance":doc.get("pp_instance", "") or "",
            "fp_instance":doc.get("fp_instance", "") or "",
            "printer": doc.get("printer", "") or "",
            "error_reason": doc.get("error_reason", ""), 
        })

    return {
        "jobs": result,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": (total_count + limit - 1) // limit
        }
    }

@app.get("/api/export-orders-csv")
def export_orders_csv():
    fields = [
        "email", "phone_number", "age", "book_id", "book_style", "total_price", "gender", "paid",
        "approved", "created_date", "created_time", "creation_hour",
        "payment_date", "payment_time", "payment_hour",
        "locale", "name", "user_name", "shipping_address.city", "shipping_address.province",
        "order_id", "discount_code", "paypal_capture_id", "transaction_id", "tracking_code","pp_instance", "partial_preview", "fp_instance","final_preview", "cust_status", "printer",
    ]

    projection = {
        "email": 1, "phone_number": 1, "age": 1, "book_id": 1, "book_style": 1, "total_price": 1,
        "gender": 1, "paid": 1, "approved": 1, "created_at": 1, "processed_at": 1,
        "locale": 1, "name": 1, "user_name": 1, "shipping_address": 1, "order_id": 1,
        "discount_code": 1, "paypal_capture_id": 1, "transaction_id": 1, "tracking_code": 1, "pp_instance": 1, "partial_preview": 1, "fp_instance": 1, "final_preview": 1, "cust_status": 1, "printer": 1,
    }

    cursor = orders_collection.find({}, projection).sort("created_at", -1)

    def format_datetime_parts(dt):
        try:
            if isinstance(dt, str):
                dt = parser.isoparse(dt)
            if isinstance(dt, datetime):
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                dt_ist = dt.astimezone(IST)
                return (
                    dt_ist.strftime("%d-%m-%Y"),     # date
                    dt_ist.strftime("%I:%M %p"),     # time
                    dt_ist.strftime("%H")            # 24-hour
                )
        except Exception as e:
            print("⚠️ Date parse failed:", e)
        return "", "", ""

    with tempfile.NamedTemporaryFile(mode="w+", newline='', delete=False, suffix=".csv", encoding="utf-8") as temp_file:
        writer = csv.writer(temp_file)
        writer.writerow(fields)

        for doc in cursor:
            created_date, created_time, creation_hour = format_datetime_parts(
                doc.get("created_at"))
            payment_date, payment_time, payment_hour = format_datetime_parts(
                doc.get("processed_at"))

            row = []
            for field in fields:
                if field == "created_date":
                    row.append(created_date)
                elif field == "created_time":
                    row.append(created_time)
                elif field == "creation_hour":
                    row.append(creation_hour)
                elif field == "payment_date":
                    row.append(payment_date)
                elif field == "payment_time":
                    row.append(payment_time)
                elif field == "payment_hour":
                    row.append(payment_hour)
                else:
                    # Nested field handling
                    if '.' in field:
                        value = doc
                        for part in field.split('.'):
                            if isinstance(value, dict):
                                value = value.get(part, "")
                            else:
                                value = ""
                    else:
                        value = doc.get(field, "")

                    # Price formatting for relevant fields
                    if field in ["total_price", "price", "amount", "total_amount"]:
                        try:
                            value = float(value)
                            value = "{:.2f}".format(value)
                        except:
                            value = ""
                    if field == "phone_number":
                        value = str(value).replace(",", "").strip()

                    row.append(value)

            writer.writerow(row)

        temp_file.flush()
        return FileResponse(temp_file.name, media_type="text/csv", filename="orders_export.csv")

@app.get("/api/export-orders-filtered-csv")
def export_orders_filtered_csv(
    paid: Optional[bool] = Query(
        None, description="Filter by paid (true/false)"),
    approved: Optional[bool] = Query(
        None, description="Filter by approved (true/false)"),
    locale: Optional[str] = Query(None, description="Filter by locale"),
    start: Optional[str] = Query(
        None, description="Start created_at ISO datetime (inclusive)"),
    end: Optional[str] = Query(
        None, description="End created_at ISO datetime (inclusive)"),
    fields: Optional[str] = Query(
        None,
        description="Comma-separated fields to include (nested fields with dot notation). "
                    "If omitted, a sensible default set will be used."
    ),
):
    """
    Returns CSV of orders filtered by query params.
    - only includes documents whose order_id exactly matches '#<digits>' (excludes 'Test', 'reject', etc).
    - fields param controls which columns are present in the CSV (comma-separated).
    """

    # Default fields
    default_fields = [
        "email", "order_id", "phone_number", "age", "book_id", "book_style", "total_price",
        "gender", "paid", "approved",
        "created_date", "created_time", "creation_hour",
        "payment_date", "payment_time", "payment_hour",
        "locale", "name", "user_name",
        "shipping_address.city", "shipping_address.province", "shipping_address.zip",
        "discount_code", "paypal_capture_id", "transaction_id", "tracking_code",
        "pp_instance","partial_preview", "fp_instance", "final_preview", "cust_status", "printer",
        "shipping_status", "time_taken", "shipping_charges",
    ]

    # Resolve requested fields
    if fields:
        requested_fields = [f.strip() for f in fields.split(",") if f.strip()]
    else:
        requested_fields = default_fields

    # Build MongoDB projection
    projection = {}
    for f in requested_fields:
        if f in ("created_date", "created_time", "creation_hour"):
            projection["created_at"] = 1
        elif f in ("payment_date", "payment_time", "payment_hour"):
            projection["processed_at"] = 1
        else:
            if "." in f:
                top = f.split(".")[0]
                projection[top] = 1
            else:
                projection[f] = 1

    projection["order_id"] = 1
    projection["created_at"] = projection.get("created_at", 0) or 1
    projection["processed_at"] = projection.get("processed_at", 0) or 1
    projection["current_status"] = 1
    projection["current_timestamp_iso"] = 1   # REQUIRED for time_taken
    projection["shipping_charges"] = 1


    # Filters
    query = {"order_id": {"$regex": r"^#\d+$"}}

    if paid is not None:
        query["paid"] = paid
    if approved is not None:
        query["approved"] = approved
    if locale:
        query["locale"] = locale

    # Date-range handling
    try:
        if start:
            start_dt = dateutil_parser.isoparse(start)
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            query.setdefault("created_at", {})
            query["created_at"]["$gte"] = start_dt

        if end:
            end_dt = dateutil_parser.isoparse(end)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)
            query.setdefault("created_at", {})
            query["created_at"]["$lte"] = end_dt

    except Exception as e:
        print("⚠️ Date range parse failed:", e)

    cursor = orders_collection.find(query, projection).sort("created_at", -1)

    # Format helper
    def format_datetime_parts(dt):
        try:
            if isinstance(dt, str):
                dt = dateutil_parser.isoparse(dt)
            if isinstance(dt, datetime):
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                dt_ist = dt.astimezone(IST)
                return (
                    dt_ist.strftime("%d-%m-%Y"),
                    dt_ist.strftime("%I:%M %p"),
                    dt_ist.strftime("%H")
                )
        except Exception:
            pass
        return "", "", ""

    # Write CSV
    with tempfile.NamedTemporaryFile(mode="w+", newline='', delete=False, suffix=".csv", encoding="utf-8") as temp_file:

        writer = csv.writer(temp_file)

        # Header
        header_row = [
            "Shipping Status" if f == "shipping_status"
            else "Time taken" if f == "time_taken"
            else "Shipping Charges" if f == "shipping_charges"
            else f
            for f in requested_fields
        ]
        writer.writerow(header_row)

        # Rows
        for doc in cursor:
            created_date, created_time, creation_hour = format_datetime_parts(
                doc.get("created_at"))
            payment_date, payment_time, payment_hour = format_datetime_parts(
                doc.get("processed_at"))

            row = []

            for field in requested_fields:

                # Date/time fields
                if field == "created_date":
                    row.append(created_date)
                    continue
                if field == "created_time":
                    row.append(created_time)
                    continue
                if field == "creation_hour":
                    row.append(creation_hour)
                    continue
                if field == "payment_date":
                    row.append(payment_date)
                    continue
                if field == "payment_time":
                    row.append(payment_time)
                    continue
                if field == "payment_hour":
                    row.append(payment_hour)
                    continue

                # Shipping status
                if field == "shipping_status":
                    row.append(doc.get("current_status", ""))
                    continue

                # ⬇️ FINAL CORRECT TIME_TAKEN LOGIC
                if field == "time_taken":
                    status = (doc.get("current_status", "") or "").lower()

                    if status == "delivered":

                        proc = doc.get("processed_at")
                        end_ts = doc.get("current_timestamp_iso")

                        try:
                            # Parse processed_at
                            if isinstance(proc, str):
                                proc_dt = dateutil_parser.isoparse(proc)
                            else:
                                proc_dt = proc

                            # Parse current_timestamp_iso
                            if isinstance(end_ts, str):
                                end_dt = dateutil_parser.isoparse(end_ts)
                            else:
                                end_dt = end_ts

                            if proc_dt and end_dt:

                                if proc_dt.tzinfo is None:
                                    proc_dt = proc_dt.replace(
                                        tzinfo=timezone.utc)
                                if end_dt.tzinfo is None:
                                    end_dt = end_dt.replace(
                                        tzinfo=timezone.utc)

                                delta = end_dt - proc_dt
                                days = delta.days

                                row.append(str(days) if days >= 0 else "")
                            else:
                                row.append("")

                        except Exception as e:
                            print("⚠️ Time taken calc failed:", e)
                            row.append("")
                    else:
                        row.append("")
                    continue
                # Shipping Charges field
                if field == "shipping_charges":
                    row.append(doc.get("shipping_charges", ""))  # Add shipping_charges value
                    continue


                # Nested field handling
                if "." in field:
                    value = doc
                    for part in field.split('.'):
                        value = value.get(part, "") if isinstance(
                            value, dict) else ""
                else:
                    value = doc.get(field, "")

                # Price formatting
                if field in ["total_price", "price", "amount", "total_amount"]:
                    try:
                        value = "{:.2f}".format(float(value))
                    except:
                        value = ""

                # Phone cleanup
                if field == "phone_number":
                    value = str(value).replace(",", "").strip()

                # Boolean formatting
                if isinstance(value, bool):
                    value = "TRUE" if value else "FALSE"

                row.append(value)

            writer.writerow(row)

        temp_file.flush()
        return FileResponse(temp_file.name, media_type="text/csv", filename="orders_filtered_export.csv")


def _send_html_email(
    to_email: Union[str, List[str], None],
    subject: str,
    html_body: str
) -> None:
    email_user = (os.getenv("EMAIL_ADDRESS") or "").strip()
    email_pass = (os.getenv("EMAIL_PASSWORD") or "").strip()
    if not email_user or not email_pass:
        raise RuntimeError("EMAIL_ADDRESS/EMAIL_PASSWORD not configured")

    # Normalize recipients
    if to_email is None:
        recipients = EMAIL_TO[:]  # from env
    elif isinstance(to_email, list):
        recipients = [e.strip() for e in to_email if e and e.strip()]
    else:  # string
        recipients = [e.strip() for e in to_email.split(",") if e.strip()]

    if not recipients:
        raise RuntimeError(
            "No recipients found. Configure EMAIL_TO in .env or pass a recipient.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"Peekori <{email_user}>"
    msg["To"] = ", ".join(recipients)
    msg.set_content("This message contains HTML.")
    msg.add_alternative(html_body, subtype="html")

    # Send to all recipients
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(email_user, email_pass)
        # send_message uses the headers for recipients; passing explicitly is extra safe:
        smtp.sendmail(email_user, recipients, msg.as_string())


def _hourly_reconcile_and_email():
    IST = ZoneInfo(os.getenv("RECONCILE_TZ", "Asia/Kolkata"))
    now_ist = datetime.now(IST)

    # Same window the UI uses: [yesterday 00:00 → today 23:59:59] IST
    y_date = now_ist.date() - timedelta(days=1)
    t_date = now_ist.date()
    from_date = y_date.strftime("%Y-%m-%d")
    to_date = t_date.strftime("%Y-%m-%d")

    logger.info(
        "[RECONCILE-HOURLY] Calling vlookup for IST window %s → %s", from_date, to_date)

    # 1) Pull summary + NA payment IDs via the same UI endpoint
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.get(
                f"{API_BASE}{VLOOKUP_PATH}",
                params={
                    "from_date": from_date,
                    "to_date": to_date,
                    "na_status": "captured",
                    "max_fetch": 200000,
                },
            )
            logger.info("[RECONCILE-HOURLY] vlookup GET %s -> %s",
                        resp.request.url, resp.status_code)
            resp.raise_for_status()
            lookup_json = resp.json()
    except Exception as e:
        logger.exception("[RECONCILE-HOURLY] vlookup API failed: %s", e)
        return

    summary = lookup_json.get("summary", {}) or {}
    na_ids = lookup_json.get("na_payment_ids", []) or []
    na_count = int(summary.get("na_count", len(na_ids)))
    window = summary.get("date_window", {}) or {}
    wnd_from = window.get("from_date", from_date)
    wnd_to = window.get("to_date", to_date)

    # ✅ Only email if there are NA IDs
    if not na_ids:
        logger.info(
            "[RECONCILE-HOURLY] No NA payment IDs in window (%s → %s) — skipping email.", wnd_from, wnd_to)
        return

    logger.info("[RECONCILE-HOURLY] NA count: %d — preparing email.", na_count)

    # 2) Enrich those NA IDs just like the UI (email, created_at, amount, paid, preview_url, job_id, etc.)
    details_items = []
    try:
        with httpx.Client(timeout=60.0) as client:
            dresp = client.post(
                f"{API_BASE}{DETAILS_PATH}",
                json={"ids": na_ids},
                headers={"Content-Type": "application/json"},
            )
            logger.info("[RECONCILE-HOURLY] details POST %s -> %s",
                        dresp.request.url, dresp.status_code)
            dresp.raise_for_status()
            djson = dresp.json() or {}
            details_items = djson.get("items", []) or []
    except Exception as e:
        logger.exception("[RECONCILE-HOURLY] details API failed: %s", e)
        # We still send the email, but with just the IDs table if enrichment failed.

    # 3) Render a compact HTML table with the requested columns
    subject = f"[Reconcile] NA payments: {na_count} (IST {wnd_from} → {wnd_to})"
    html_body = _render_na_table(
        title="Razorpay NA Reconciliation",
        wnd_from=wnd_from,
        wnd_to=wnd_to,
        rows=details_items,
    )

    logger.info("[RECONCILE-HOURLY] Sending email: %s", subject)
    try:
        _send_html_email(EMAIL_TO, subject, html_body)
        logger.info("[RECONCILE-HOURLY] Email sent successfully")
    except Exception as e:
        logger.exception("[RECONCILE-HOURLY] Email send failed: %s", e)

def _parse_iso_utc(dt):
    """
    Safely parse ISO datetime string or datetime to UTC-aware datetime.
    Returns None if invalid.
    """
    if not dt:
        return None

    if isinstance(dt, datetime):
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    if isinstance(dt, str):
        try:
            parsed = datetime.fromisoformat(dt)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except Exception:
            return None

    return None

def _last_iso_week(year: int) -> int:
    return datetime(year, 12, 28).isocalendar()[1]

def _iso_week_bounds(year: int, week: int):
    start_ist = datetime.fromisocalendar(year, week, 1).replace(tzinfo=IST_TZ)
    end_ist = start_ist + timedelta(days=7)
    return start_ist.astimezone(timezone.utc), end_ist.astimezone(timezone.utc)

def _sla_base_query(start_utc, end_utc):
    return {
        "$and": [
            {"paid": True},
            {"processed_at": {"$gte": start_utc, "$lt": end_utc}},
            {"printer": {"$in": ["Genesis", "Yara"]}},
            {"order_id": {"$regex": r"^#\d+(_\d+)?$"}},
            {
                "$or": [
                    {"current_status": {"$exists": False}},
                    {"current_status": {"$not": {"$regex": "cancelled", "$options": "i"}}},
                ]
            },
            {
                "$or": [
                    {"order_status": {"$exists": False}},
                    {"order_status": {"$not": {"$regex": "cancelled", "$options": "i"}}},
                ]
            },
        ]
    }




@app.get("/api/download-xlsx-yippee")
def download_xlsx_yippee(from_date: str = Query(...), to_date: str = Query(...)):
    try:
        # Validate range (dates are interpreted as UTC-naive, like your original)
        from_dt = datetime.strptime(from_date, "%Y-%m-%d")
        to_dt = datetime.strptime(
            to_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        if from_dt > to_dt:
            return Response("from_date cannot be after to_date", media_type="text/plain", status_code=400)

        # Query Yippee collection (exclude _id)
        data = list(
            collection_yippee.find(
                {TIMESTAMP_FIELD: {"$gte": from_dt, "$lte": to_dt}},
                {"_id": 0},
            )
        )
        if not data:
            return Response("No data available", media_type="text/plain", status_code=404)

        # Build rows + IST helper columns (same logic as your DF endpoint)
        rows_out = []
        for row in data:
            r = dict(row)
            base_ts = _parse_dt(r.get(TIMESTAMP_FIELD))

            r["date"] = ""
            r["hour"] = ""
            r["date-hour"] = ""
            r["ist-date"] = ""
            r["ist-hour"] = ""

            if base_ts is not None:
                ist_ts = base_ts + IST_OFFSET  # keep same assumption as DF endpoint
                r["date"] = base_ts.strftime("%d/%m/%Y")
                r["hour"] = base_ts.strftime("%H")
                r["date-hour"] = ist_ts.strftime("%Y-%m-%d %H:%M:%S")
                r["ist-date"] = ist_ts.strftime("%d/%m/%Y")
                r["ist-hour"] = ist_ts.strftime("%H")

            rows_out.append(r)

        df = pd.DataFrame(rows_out)

        # Ensure required columns exist
        for col in ["ist-date", "ist-hour", "room_id"]:
            if col not in df.columns:
                df[col] = ""

        # Pivot: count of room_id by (ist-date × ist-hour)
        hours = [f"{h:02d}" for h in range(24)]
        df["ist-hour"] = df["ist-hour"].astype(str)
        pivot = pd.pivot_table(
            df,
            index="ist-date",
            columns="ist-hour",
            values="room_id",
            aggfunc="count",
            fill_value=0,
        )
        pivot = pivot.reindex(columns=hours, fill_value=0)

        # Sort ist-date as real dates when possible
        def _date_key(x):
            try:
                return datetime.strptime(x, "%d/%m/%Y")
            except Exception:
                return x

        pivot = pivot.sort_index(key=lambda idx: [_date_key(x) for x in idx])

        # Totals
        pivot["Total"] = pivot.sum(axis=1)
        pivot.loc["Total"] = pivot.sum(numeric_only=True)

        # Pick writer engine
        engine = _pick_excel_engine()
        if engine is None:
            return Response(
                "Missing Excel writer engine. Install one of: pip install xlsxwriter OR pip install openpyxl",
                media_type="text/plain",
                status_code=500,
            )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine=engine) as writer:
            # pivot sheet
            pivot.to_excel(writer, sheet_name="pivot")

            # EC2 status sheet (same as DF)
            ec2_rows, ec2_err = _get_ec2_status_rows()
            if ec2_err:
                pd.DataFrame([{"error": ec2_err}]).to_excel(
                    writer, index=False, sheet_name="ec2_status_error"
                )
            else:
                ec2_df = pd.DataFrame(ec2_rows)
                if not ec2_df.empty:
                    for col in ec2_df.columns:
                        if pd.api.types.is_datetime64tz_dtype(ec2_df[col]):
                            ec2_df[col] = ec2_df[col].dt.tz_convert(
                                'UTC').dt.tz_localize(None)
                        elif ec2_df[col].dtype == "object":
                            if ec2_df[col].apply(lambda v: isinstance(v, datetime) and getattr(v, "tzinfo", None) is not None).any():
                                ec2_df[col] = ec2_df[col].apply(_to_naive_utc)
                ec2_df.to_excel(writer, index=False, sheet_name="ec2_status")

            # Freeze panes
            if engine == "xlsxwriter":
                ws1 = writer.sheets["pivot"]
                ws2 = writer.sheets.get("ec2_status")
                if ws1:
                    ws1.freeze_panes(1, 1)  # row 2, col B
                if ws2:
                    ws2.freeze_panes(1, 0)
            else:  # openpyxl
                ws1 = writer.sheets.get("pivot")
                ws2 = writer.sheets.get("ec2_status")
                if ws1 is not None:
                    ws1.freeze_panes = "B2"
                if ws2 is not None:
                    ws2.freeze_panes = "A2"

        output.seek(0)
        filename = f"yippee_{from_date}_to_{to_date}.xlsx"
        headers = {"Content-Disposition": f"attachment; filename={filename}"}
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers,
        )
    except Exception as e:
        return Response(f"❌ Error building XLSX: {e}", media_type="text/plain", status_code=500)

@app.post("/api/reconcile/mark")
def mark_reconciled(payload: dict):
    job_id = payload.get("job_id")
    razorpay_payment_id = payload.get(
        "razorpay_payment_id")  # optional, nice to store

    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    now = datetime.now(timezone.utc)
    update = {
        "reconcile": True,
        "reconciled_at": now,
    }
    if razorpay_payment_id:
        # doesn’t overwrite your verify logic—just stores it if you want
        update["transaction_id"] = razorpay_payment_id

    result = orders_collection.update_one(
        {"job_id": job_id},
        {"$set": update}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="job_id not found")

    return {"ok": True, "matched": result.matched_count, "modified": result.modified_count}


@app.post("/debug/run-reconcile-now")
def debug_run_reconcile_now():
    _hourly_reconcile_and_email()
    return {"ok": True}

EXCLUDE_CODES = ["TEST", "REJECTED", "TINA"]
EXCLUDE_SET = {c.upper() for c in EXCLUDE_CODES}

@app.get("/api/stats/sla-cohorts") #Delivery vs Undelivered in 8 days
def stats_sla_cohorts(
    start_date: str = Query(..., description="YYYY-MM-DD (processed_at cohort)"),
    end_date: str = Query(..., description="YYYY-MM-DD (processed_at cohort)"),
    cohort_date: Optional[str] = Query(
        None, description="YYYY-MM-DD for table drill-down"
    ),
):
    start_ist = _ist_midnight(_parse_ymd_ist(start_date))
    end_ist = _ist_midnight(_parse_ymd_ist(end_date)) + timedelta(days=1)

    start_utc = start_ist.astimezone(timezone.utc)
    end_utc = end_ist.astimezone(timezone.utc)

    # -------------------------------------------------
    # Mongo query
    # -------------------------------------------------
    base_query = {
        "$and": [
            {"paid": True},
            {"processed_at": {"$gte": start_utc, "$lt": end_utc}},
            {"printer": {"$in": ["Genesis", "Yara"]}},
            {"order_id": {"$regex": r"^#\d+(_\d+)?$"}},
            {
                "$or": [
                    {"discount_code": {"$exists": False}},
                    {"discount_code": None},
                    {
                        "$expr": {
                            "$not": {
                                "$in": [
                                    {"$toUpper": "$discount_code"},
                                    EXCLUDE_CODES
                                ]
                            }
                        }
                    }
                ]
            },
            {
                "$or": [
                    {"current_status": {"$exists": False}},
                    {"current_status": {"$not": {"$regex": "cancelled", "$options": "i"}}},
                ]
            },
            {
                "$or": [
                    {"order_status": {"$exists": False}},
                    {"order_status": {"$not": {"$regex": "cancelled", "$options": "i"}}},
                ]
            },
        ]
    }


    projection = {
        "_id": 0,
        "order_id": 1,
        "processed_at": 1,
        "current_status": 1,
        "current_timestamp_iso": 1,  # used ONLY if DELIVERED
    }

    docs = list(orders_collection.find(base_query, projection))

    cohorts: Dict[str, Dict[str, Any]] = {}

    # -------------------------------------------------
    # Core processing
    # -------------------------------------------------
    for d in docs:
        processed_at = d.get("processed_at")
        if not processed_at:
            continue

        # Cohort key = processed_at date (IST)
        proc_date_ist = processed_at.astimezone(IST_TZ).date()
        cohort_key = proc_date_ist.isoformat()

        status = (d.get("current_status") or "").upper()
        is_delivered = status == "DELIVERED"

        # -----------------------------
        # SLA check (strict & safe)
        # -----------------------------
        delivered_in_8_days = "NO"

        if is_delivered:
            delivered_at = _parse_iso_utc(d.get("current_timestamp_iso"))

            if delivered_at:
                delta_days = (delivered_at - processed_at).days
                if delta_days <= 8:
                    delivered_in_8_days = "YES"

        cohorts.setdefault(
            cohort_key,
            {
                "total": 0,
                "delivered": 0,
                "undelivered": 0,
                "orders": [],
            },
        )

        c = cohorts[cohort_key]
        c["total"] += 1

        if is_delivered:
            c["delivered"] += 1
        else:
            c["undelivered"] += 1

        c["orders"].append(
            {
                "order_id": d["order_id"],
                "processed_at": processed_at,
                "current_status": d.get("current_status"),
                "delivered_in_8_days": delivered_in_8_days,
                "delivered_at": d.get("current_timestamp_iso") if is_delivered else None,
            }
        )

    # -------------------------------------------------
    # Drill-down table (date click)
    # -------------------------------------------------
    if cohort_date:
        bucket = cohorts.get(cohort_date)
        if not bucket:
            return []
        return bucket["orders"]

    # -------------------------------------------------
    # Summary for bar chart
    # -------------------------------------------------
    response = []

    for day in sorted(cohorts.keys()):
        c = cohorts[day]
        total = c["total"]

        response.append(
            {
                "processed_date": day,
                "delivered_pct": round(c["delivered"] * 100 / total, 1),
                "undelivered_pct": round(c["undelivered"] * 100 / total, 1),
                "total_orders": total,
            }
        )

    return response

@app.get("/api/stats/delivery-latency-cohorts") #Delivery Time Cohort table
def delivery_latency_cohorts(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
):
    # -----------------------------
    # Date range (IST → UTC)
    # -----------------------------
    start_ist = _ist_midnight(_parse_ymd_ist(start_date))
    end_ist = _ist_midnight(_parse_ymd_ist(end_date)) + timedelta(days=1)

    start_utc = start_ist.astimezone(timezone.utc)
    end_utc = end_ist.astimezone(timezone.utc)

    # -----------------------------
    # Mongo query — ALL orders
    # -----------------------------
    query = {
        "$and": [
            {"paid": True},
            {"processed_at": {"$gte": start_utc, "$lt": end_utc}},
            {"printer": {"$in": ["Genesis", "Yara"]}},
            {"order_id": {"$regex": r"^#\d+(_\d+)?$"}},
            {
                "$or": [
                    {"discount_code": {"$exists": False}},
                    {"discount_code": None},
                    {
                        "$expr": {
                            "$not": {
                                "$in": [
                                    {"$toUpper": "$discount_code"},
                                    EXCLUDE_CODES
                                ]
                            }
                        }
                    }
                ]
            },
            {
                "$or": [
                    {"current_status": {"$exists": False}},
                    {"current_status": {"$not": {"$regex": "cancelled", "$options": "i"}}},
                ]
            },
            {
                "$or": [
                    {"order_status": {"$exists": False}},
                    {"order_status": {"$not": {"$regex": "cancelled", "$options": "i"}}},
                ]
            },
        ]
    }

    projection = {
        "_id": 0,
        "processed_at": 1,
        "current_status": 1,
        "current_timestamp_iso": 1,
    }

    docs = list(orders_collection.find(query, projection))

    # -----------------------------
    # Buckets by processed date
    # -----------------------------
    buckets_by_day: Dict[str, Dict[str, Any]] = {}

    for d in docs:
        processed_at = d.get("processed_at")
        if not processed_at:
            continue

        cohort_day = processed_at.astimezone(IST_TZ).date().isoformat()

        buckets_by_day.setdefault(
            cohort_day,
            {
                "total_orders": 0,
                "delivered_orders": 0,
                "day_le_3": 0,   # 👈 NEW
                "day_4": 0,
                "day_5": 0,
                "day_6": 0,
                "day_7": 0,
                "day_8": 0,
                "day_9": 0,
                "day_10_plus": 0,
            },
        )

        c = buckets_by_day[cohort_day]

        # ✅ Count ALL orders
        c["total_orders"] += 1

        # Only delivered orders go into buckets
        status = (d.get("current_status") or "").strip().upper()
        if status != "DELIVERED":
            continue

        delivered_at = _parse_iso_utc(d.get("current_timestamp_iso"))
        if not delivered_at:
            continue

        c["delivered_orders"] += 1

        days_taken = (delivered_at - processed_at).days

        # -----------------------------
        # NEW BUCKET LOGIC
        # -----------------------------
        if days_taken <= 3:
            c["day_le_3"] += 1
        elif days_taken == 4:
            c["day_4"] += 1
        elif days_taken == 5:
            c["day_5"] += 1
        elif days_taken == 6:
            c["day_6"] += 1
        elif days_taken == 7:
            c["day_7"] += 1
        elif days_taken == 8:
            c["day_8"] += 1
        elif days_taken == 9:
            c["day_9"] += 1
        elif days_taken >= 10:
            c["day_10_plus"] += 1

    # -----------------------------
    # Build response + TOTAL row
    # -----------------------------
    response = []

    total_acc = {
        "total_orders": 0,
        "delivered_orders": 0,
        "day_le_3": 0,
        "day_4": 0,
        "day_5": 0,
        "day_6": 0,
        "day_7": 0,
        "day_8": 0,
        "day_9": 0,
        "day_10_plus": 0,
    }

    for day in sorted(buckets_by_day.keys()):
        c = buckets_by_day[day]
        total = c["total_orders"] or 1

        # accumulate raw counts
        for k in total_acc:
            total_acc[k] += c.get(k, 0)

        response.append(
            {
                "processed_date": day,
                "total_orders": c["total_orders"],
                "delivered_orders": c["delivered_orders"],
                "day_le_3": round(c["day_le_3"] * 100 / total, 1),
                "day_4": round(c["day_4"] * 100 / total, 1),
                "day_5": round(c["day_5"] * 100 / total, 1),
                "day_6": round(c["day_6"] * 100 / total, 1),
                "day_7": round(c["day_7"] * 100 / total, 1),
                "day_8": round(c["day_8"] * 100 / total, 1),
                "day_9": round(c["day_9"] * 100 / total, 1),
                "day_10_plus": round(c["day_10_plus"] * 100 / total, 1),
            }
        )

    grand_total = total_acc["total_orders"] or 1

    response.append(
        {
            "processed_date": "TOTAL",
            "total_orders": total_acc["total_orders"],
            "delivered_orders": total_acc["delivered_orders"],
            "day_le_3": round(total_acc["day_le_3"] * 100 / grand_total, 1),
            "day_4": round(total_acc["day_4"] * 100 / grand_total, 1),
            "day_5": round(total_acc["day_5"] * 100 / grand_total, 1),
            "day_6": round(total_acc["day_6"] * 100 / grand_total, 1),
            "day_7": round(total_acc["day_7"] * 100 / grand_total, 1),
            "day_8": round(total_acc["day_8"] * 100 / grand_total, 1),
            "day_9": round(total_acc["day_9"] * 100 / grand_total, 1),
            "day_10_plus": round(total_acc["day_10_plus"] * 100 / grand_total, 1),
        }
    )

    return response

@app.get("/api/stats/shipment-weekly-sla")
def shipment_weekly_sla(
    weeks: int = Query(6, ge=1, le=12),
    exclude_weeks: int = Query(2, ge=0, le=4),

    # ISO week params (optional)
    start_year: Optional[int] = Query(None),
    start_week: Optional[int] = Query(None, ge=1, le=53),
    end_year: Optional[int] = Query(None),
    end_week: Optional[int] = Query(None, ge=1, le=53),

    # 🔹 Date params (USED BY FRONTEND)
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """
    Weekly Shipment SLA (ISO Week based)

    MODES:
    - Rolling (default)
    - Custom (via start_date & end_date OR ISO weeks)
    """

    now_ist = datetime.now(IST_TZ)
    iso_year, iso_week, _ = now_ist.isocalendar()

    # --------------------------------------------------
    # 🔹 DATE → ISO WEEK ADAPTER (KEY FIX)
    # --------------------------------------------------
    if start_date and end_date and not start_year:
        try:
            sd = datetime.fromisoformat(start_date).replace(tzinfo=IST_TZ)
            ed = datetime.fromisoformat(end_date).replace(tzinfo=IST_TZ)

            start_year, start_week, _ = sd.isocalendar()
            end_year, end_week, _ = ed.isocalendar()
        except Exception:
            pass

    # --------------------------------------------------
    # 1) Determine target weeks
    # --------------------------------------------------
    target_weeks = []

    # ---------- CUSTOM MODE ----------
    if start_year and start_week and end_year and end_week:
        year, week = start_year, start_week

        while True:
            target_weeks.append((year, week))

            if year == end_year and week == end_week:
                break

            week += 1
            if week > _last_iso_week(year):
                week = 1
                year += 1

    # ---------- ROLLING MODE ----------
    else:
        year = iso_year
        week = iso_week - exclude_weeks

        while len(target_weeks) < weeks:
            if week <= 0:
                year -= 1
                week = _last_iso_week(year)

            target_weeks.insert(0, (year, week))
            week -= 1

    timeline = []
    rows = []

    # --------------------------------------------------
    # 2) Process each week (UNCHANGED SLA LOGIC)
    # --------------------------------------------------
    for year, week in target_weeks:
        timeline.append(week)

        start_utc, end_utc = _iso_week_bounds(year, week)
        start_ist = start_utc.astimezone(IST_TZ)
        end_ist = (end_utc - timedelta(seconds=1)).astimezone(IST_TZ)

        query = _sla_base_query(start_utc, end_utc)

        projection = {
            "_id": 0,
            "processed_at": 1,
            "current_status": 1,
            "current_timestamp_iso": 1,
        }

        docs = list(orders_collection.find(query, projection))

        total_orders = len(docs)
        delivered_orders = 0
        le_3 = d4_8 = ge_9 = 0
        delivery_days = []

        for d in docs:
            if (d.get("current_status") or "").upper() != "DELIVERED":
                continue

            delivered_at = _parse_iso_utc(d.get("current_timestamp_iso"))
            if not delivered_at:
                continue

            processed_at = d["processed_at"]
            days = max((delivered_at - processed_at).days, 0)

            delivered_orders += 1
            delivery_days.append(days)

            if days <= 3:
                le_3 += 1
            elif 4 <= days <= 8:
                d4_8 += 1
            else:
                ge_9 += 1

        avg_days = round(sum(delivery_days) / len(delivery_days), 2) if delivery_days else 0
        delivered_pct = round(delivered_orders * 100 / total_orders, 2) if total_orders else 0

        rows.append({
            "week": week,
            "year": year,
            "from_date": start_ist.date().isoformat(),
            "to_date": end_ist.date().isoformat(),
            "total_orders": total_orders,
            "total_delivered": delivered_orders,
            "delivered_pct": delivered_pct,
            "avg_days": avg_days,
            "sla_counts": {
                "le_3": le_3,
                "d4_8": d4_8,
                "ge_9": ge_9,
            },
            "sla_pct": {
                "le_3": round(le_3 * 100 / delivered_orders, 2) if delivered_orders else 0,
                "d4_8": round(d4_8 * 100 / delivered_orders, 2) if delivered_orders else 0,
                "ge_9": round(ge_9 * 100 / delivered_orders, 2) if delivered_orders else 0,
            },
        })

    # --------------------------------------------------
    # 3) Final response
    # --------------------------------------------------
    return {
        "timeline": timeline,
        "weeks": rows,
        "meta": {
            "mode": "custom" if start_year else "rolling",
            "weeks_shown": len(rows),
            "excluded_recent_weeks": exclude_weeks if not start_year else None,
            "generated_at": now_ist.isoformat(),
        },
    }

@app.get("/api/stats/sla-summary") #“Orders delivered within 8 days”, “Not delivered within 8 days”)
def stats_sla_summary(
    start_date: str = Query(...),
    end_date: str = Query(...)
):
    start_ist = _ist_midnight(_parse_ymd_ist(start_date))
    end_ist = _ist_midnight(_parse_ymd_ist(end_date)) + timedelta(days=1)

    start_utc = start_ist.astimezone(timezone.utc)
    end_utc = end_ist.astimezone(timezone.utc)

    query = {
        "$and": [
            {"paid": True},
            {"processed_at": {"$gte": start_utc, "$lt": end_utc}},
            {"printer": {"$in": ["Genesis", "Yara"]}},
            {"order_id": {"$regex": r"^#\d+(_\d+)?$"}},
            {
                "$or": [
                    {"discount_code": {"$exists": False}},
                    {"discount_code": None},
                    {
                        "$expr": {
                            "$not": {
                                "$in": [
                                    {"$toUpper": "$discount_code"},
                                    EXCLUDE_CODES
                                ]
                            }
                        }
                    }
                ]
            },
            {
                "$or": [
                    {"current_status": {"$exists": False}},
                    {"current_status": {"$not": {"$regex": "cancelled", "$options": "i"}}},
                ]
            },
            {
                "$or": [
                    {"order_status": {"$exists": False}},
                    {"order_status": {"$not": {"$regex": "cancelled", "$options": "i"}}},
                ]
            },
        ]
    }


    projection = {
        "_id": 0,
        "processed_at": 1,
        "current_status": 1,
        "current_timestamp_iso": 1,
    }

    docs = list(orders_collection.find(query, projection))

    delivered = 0
    undelivered = 0

    for d in docs:
        status = (d.get("current_status") or "").upper()

        if status == "DELIVERED":
            delivered_at = _parse_iso_utc(d.get("current_timestamp_iso"))
            if delivered_at:
                delta = (delivered_at - d["processed_at"]).days
                if delta <= 8:
                    delivered += 1
                else:
                    undelivered += 1
            else:
                undelivered += 1
        else:
            undelivered += 1

    return {
        "delivered_within_8_days": delivered,
        "not_delivered_within_8_days": undelivered,
        "total_orders": delivered + undelivered,
    }

@app.get("/api/stats/production-kpis")
def production_kpis():
    query = {
        "$and": [
            {"paid": True},
            {"printer": {"$in": ["Genesis", "Yara"]}},
            {"order_id": {"$regex": r"^#\d+(_\d+)?$"}},
            {
                "$or": [
                    {"discount_code": {"$exists": False}},
                    {"discount_code": None},
                    {
                        "$expr": {
                            "$not": {
                                "$in": [
                                    {"$toUpper": "$discount_code"},
                                    EXCLUDE_CODES
                                ]
                            }
                        }
                    }
                ]
            },
            {
                "$or": [
                    {"current_status": {"$exists": False}},
                    {"current_status": {"$not": {"$regex": "cancelled", "$options": "i"}}},
                ]
            },
            {
                "$or": [
                    {"order_status": {"$exists": False}},
                    {"order_status": {"$not": {"$regex": "cancelled", "$options": "i"}}},
                ]
            },
        ]
    }


    projection = {
        "_id": 0,
        "printer": 1,
        "current_status": 1,
    }

    docs = list(orders_collection.find(query, projection))

    genesis_total = yara_total = 0
    genesis_in_prod = yara_in_prod = 0
    genesis_shipped = yara_shipped = 0

    for d in docs:
        printer = (d.get("printer") or "").strip().lower()
        status = (d.get("current_status") or "").strip().upper()
        is_shipped = status in SHIPPED_STATUSES

        if printer == "genesis":
            genesis_total += 1
            if is_shipped:
                genesis_shipped += 1
            else:
                genesis_in_prod += 1

        elif printer == "yara":
            yara_total += 1
            if is_shipped:
                yara_shipped += 1
            else:
                yara_in_prod += 1

    return {
        "in_production": {
            "genesis": genesis_in_prod,
            "yara": yara_in_prod,
        },
        "shipped": {
            "genesis": genesis_shipped,
            "yara": yara_shipped,
        },
        "total_sent": {
            "genesis": genesis_total,
            "yara": yara_total,
        },
    }

@app.get("/api/stats/production-kpis-graph")
def production_kpis_graph(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
):
    """
    Date-filtered KPIs.
    Used ONLY for Production vs Shipped graph.
    """

    # -----------------------------
    # Date range (IST → UTC)
    # -----------------------------
    try:
        start_ist = _ist_midnight(_parse_ymd_ist(start_date))
        end_ist = _ist_midnight(_parse_ymd_ist(end_date)) + timedelta(days=1)

        start_utc = start_ist.astimezone(timezone.utc)
        end_utc = end_ist.astimezone(timezone.utc)
    except Exception:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}

    # -----------------------------
    # Mongo query
    # -----------------------------
    query = {
        "$and": [
            {"paid": True},
            {"processed_at": {"$gte": start_utc, "$lt": end_utc}},
            {"printer": {"$in": ["Genesis", "Yara"]}},
            {"order_id": {"$regex": r"^#\d+(_\d+)?$"}},

            {
                "$or": [
                    {"current_status": {"$exists": False}},
                    {"current_status": {"$not": {"$regex": "cancelled", "$options": "i"}}},
                ]
            },
            {
                "$or": [
                    {"order_status": {"$exists": False}},
                    {"order_status": {"$not": {"$regex": "cancelled", "$options": "i"}}},
                ]
            },
        ]
    }

    projection = {
        "_id": 0,
        "printer": 1,
        "current_status": 1,
    }

    docs = list(orders_collection.find(query, projection))

    # -----------------------------
    # Buckets
    # -----------------------------
    genesis_in_prod = []
    yara_in_prod = []

    genesis_shipped = []
    yara_shipped = []

    # -----------------------------
    # Core logic (same as before)
    # -----------------------------
    for d in docs:
        printer = (d.get("printer") or "").strip().lower()
        status = (d.get("current_status") or "").strip().upper()

        is_shipped = status in SHIPPED_STATUSES

        if printer == "genesis":
            if is_shipped:
                genesis_shipped.append(1)
            else:
                genesis_in_prod.append(1)

        elif printer == "yara":
            if is_shipped:
                yara_shipped.append(1)
            else:
                yara_in_prod.append(1)

    # -----------------------------
    # Response (EXACT format you want)
    # -----------------------------
    return {
        "in_production": {
            "genesis": len(genesis_in_prod),
            "yara": len(yara_in_prod),
        },
        "shipped": {
            "genesis": len(genesis_shipped),
            "yara": len(yara_shipped),
        },
        "range": {
            "start_date": start_date,
            "end_date": end_date,
        },
    }

@app.get("/api/stats/ship-status-v2")
def stats_ship_status_v2(
    range: str = Query("1w", description="1d, 1w, 1m, 6m, this_month, custom"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    printer: Optional[str] = Query("all", description="genesis | yara"),
    loc: Optional[str] = Query("IN", description="country code"),
):
    """
    Shipment Status V2
    Uses ONLY orders_collection.current_status
    Adds pending_age_chart with order_ids for NO-status orders
    """

    exclude_codes = ["TEST", "COLLAB", "REJECTED", "TINA"]
    exclude_set = {c.upper() for c in exclude_codes}

    # --------------------------------------------------
    # Location match
    # --------------------------------------------------
    try:
        loc_match = _build_loc_match(loc)
    except Exception:
        loc_match = None

    # --------------------------------------------------
    # 1) Determine Period
    # --------------------------------------------------
    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST_TZ)

    effective_range = "1w" if range == "1d" else range

    try:
        if start_date and end_date:
            cs, ce, ps, pe, _ = _periods_custom(start_date, end_date)
            labels = _labels_for("custom", cs, ce)
        else:
            cs, ce, ps, pe, gran = _periods(effective_range, now_utc)
            labels = _labels_for(effective_range, cs, ce)
    except Exception:
        labels = []
        for i in range(6, -1, -1):
            d = (now_ist - timedelta(days=i))
            labels.append(d.strftime("%Y-%m-%d"))
        cs = ce = None

    # --------------------------------------------------
    # 2) Base order query
    # --------------------------------------------------
    base_match = {
        "$and": [
            {"paid": True},
            {"processed_at": {"$exists": True, "$ne": None}},
            {
                "$or": [
                    {"current_status": {"$exists": False}},
                    {"current_status": {"$not": {"$regex": "cancelled|refunded", "$options": "i"}}},
                ]
            },
            {
                "$or": [
                    {"order_status": {"$exists": False}},
                    {"order_status": {"$not": {"$regex": "cancelled|refunded", "$options": "i"}}},
                ]
            },
        ]
    }


    if loc_match:
        base_match["$and"].append(loc_match)


    if cs and ce:
        base_match["$and"].append(
            {"processed_at": {"$gte": cs, "$lt": ce}}
        )


    projection = {
        "order_id": 1,
        "processed_at": 1,
        "printer": 1,
        "discount_code": 1,
        "current_status": 1,
        "order_status": 1,
        "_id": 0,
    }

    cursor = orders_collection.find(base_match, projection)

    # --------------------------------------------------
    # 3) Organize orders
    # --------------------------------------------------
    orders_by_date = {k.split(" ")[0]: [] for k in labels}

    # ✅ CHANGED: store order_ids per age bucket
    pending_age_buckets = defaultdict(list)

    for doc in cursor:
        try:
            raw_code = (doc.get("discount_code") or "").strip().upper()
            if raw_code in exclude_set:
                continue

            dt = doc.get("processed_at")
            if isinstance(dt, str):
                dt = date_parser.isoparse(dt)

            if not dt:
                continue

            dt_ist = dt.astimezone(IST_TZ)
            ist_date = dt_ist.strftime("%Y-%m-%d")

            if ist_date not in orders_by_date:
                continue

            printer_val = (doc.get("printer") or "").strip().lower()
            if printer and printer.lower() not in ("all", ""):
                if printer_val != printer.lower():
                    continue

            status = (doc.get("current_status") or "").strip().lower()
            oid = doc.get("order_id")

            
            if status != "delivered" and printer_val!="cloudprinter":
                age_days = (now_ist.date() - dt_ist.date()).days
                if age_days >= 0:
                    pending_age_buckets[age_days].append(oid)


            orders_by_date[ist_date].append({
                "order_id": oid,
                "current_status": status,
                "printer": printer_val,
            })

        except Exception:
            continue

    # --------------------------------------------------
    # 4) Build rows per day
    # --------------------------------------------------
    rows = []

    for lbl in labels:
        date_key = lbl.split(" ")[0]
        day_orders = orders_by_date.get(date_key, [])

        unapproved_ids = []
        new_ids = []
        sent_to_print_ids = []
        out_for_pickup_ids = []
        pickup_exception_ids = []
        shipped_ids = []
        delivered_ids = []
        issue_ids = []

        for od in day_orders:
            oid = od["order_id"]
            printer_val = od["printer"]
            status = od["current_status"]

            if not printer_val:
                unapproved_ids.append(oid)

            if printer_val in ("genesis", "yara"):
                sent_to_print_ids.append(oid)

            if not status:
                new_ids.append(oid)
                continue

            if "pickup exception" in status:
                pickup_exception_ids.append(oid)
                continue

            if "out for pickup" in status:
                out_for_pickup_ids.append(oid)
                continue

            if "delivered" in status:
                delivered_ids.append(oid)
                continue

            if "issue" in status or "rto" in status or "undelivered" in status:
                issue_ids.append(oid)
                continue

            if (
                "picked up" in status
                or "pickup done" in status
                or "in transit" in status
                or "transit" in status
            ):
                shipped_ids.append(oid)
                continue

            shipped_ids.append(oid)

        rows.append({
            "date": date_key,
            "total": len(day_orders),

            "unapproved": len(unapproved_ids),
            "unapproved_ids": unapproved_ids,

            "sent_to_print": len(sent_to_print_ids),
            "sent_to_print_ids": sent_to_print_ids,

            "new": len(new_ids),
            "new_ids": new_ids,

            "out_for_pickup": len(out_for_pickup_ids),
            "out_for_pickup_ids": out_for_pickup_ids,

            "pickup_exception": len(pickup_exception_ids),
            "pickup_exception_ids": pickup_exception_ids,

            "shipped": len(shipped_ids),
            "shipped_ids": shipped_ids,

            "delivered": len(delivered_ids),
            "delivered_ids": delivered_ids,

            "issue": len(issue_ids),
            "issue_ids": issue_ids,
        })

    # --------------------------------------------------
    # 5) Build pending age chart (FINAL)
    # --------------------------------------------------
    if pending_age_buckets:
        min_day = min(pending_age_buckets.keys())
        max_day = max(pending_age_buckets.keys())
    else:
        min_day = max_day = 0

    pending_age_chart = []

    for day in builtins.range(min_day, max_day + 1):
        order_ids = pending_age_buckets.get(day, [])

        pending_age_chart.append({
            "label": f"{day} days",
            "value": len(order_ids),
            "order_ids": order_ids,
        })


    return {
        "labels": labels,
        "rows": rows,
        "pending_age_chart": pending_age_chart,
        "printer": printer or "all",
    }

@app.post("/api/orders/{order_id}/status")
def update_order_status(order_id: str, payload: OrderStatusUpdatePayload):
    allowed = {"refunded", "cancelled", "rejected", "reprint"}

    status = payload.order_status.strip().lower()
    remarks = payload.order_status_remarks.strip()

    if status not in allowed:
        raise HTTPException(status_code=400, detail="Invalid order_status value")

    if not remarks:
        raise HTTPException(status_code=400, detail="order_status_remarks is required")

    now = datetime.utcnow()

    update_data = {
        "order_status": status,
        "order_status_remarks": remarks,
        "order_status_updated_at": now,
    }

    # ===============================
    # REPRINT LOGIC (ONLY if reprint)
    # ===============================
    if status == "reprint":
        order = orders_collection.find_one({"order_id": order_id})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        existing_reprint_id = order.get("reprint_order_id")

        if not existing_reprint_id:
            # First reprint
            new_reprint_id = f"{order_id}_RP1"
        else:
            # Extract number and increment
            match = re.search(r"_RP(\d+)$", existing_reprint_id)
            if match:
                current_num = int(match.group(1))
                new_reprint_id = f"{order_id}_RP{current_num + 1}"
            else:
                # fallback safety
                new_reprint_id = f"{order_id}_RP1"

        update_data["reprint_order_id"] = new_reprint_id
        update_data["reprint_created_at"] = now

    # ===============================
    # UPDATE IN DB
    # ===============================
    updated = orders_collection.find_one_and_update(
        {"order_id": order_id},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Order not found")

    # IMPORTANT: clean response
    response = {
        "success": True,
        "order_id": order_id,
        "order_status": updated.get("order_status"),
        "order_status_remarks": updated.get("order_status_remarks"),
        "order_status_updated_at": updated.get("order_status_updated_at"),
    }

    if status == "reprint":
        response["reprint_order_id"] = updated.get("reprint_order_id")

    return response

@app.post("/api/orders/{order_id}/issue-origin")
def update_issue_origin(order_id: str, payload: IssueOriginUpdatePayload):
    allowed = {"peekori", "genesis", "yara", "customer"}

    origin = payload.issue_origin.strip().lower()

    if origin not in allowed:
        raise HTTPException(status_code=400, detail="Invalid issue_origin value")

    now = datetime.utcnow()

    update_data = {
        "issue_origin": origin,
        "issue_origin_updated_at": now,
    }

    updated = orders_collection.find_one_and_update(
        {"order_id": order_id},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "success": True,
        "order_id": order_id,
        "issue_origin": updated.get("issue_origin"),
        "issue_origin_updated_at": updated.get("issue_origin_updated_at"),
    }

IMMUTABLE_PATHS = {
    "saved_files",
    "child.saved_files",
    "child.saved_file_urls",
    "child.child1_input_images",
    "child.child2_input_images",
    "child.child1_image_filenames",
    "child.child2_image_filenames",
    "cover_image",
    "order.cover_image",
}

def _is_forbidden(path: str) -> bool:
    return any(path == p or path.startswith(p + ".") for p in IMMUTABLE_PATHS)


@app.patch("/api/orders/{order_id}")
def patch_order(order_id: str, update: OrderUpdate):
    payload = update.model_dump(exclude_unset=True, by_alias=True)

    set_ops: dict[str, object] = {}

    if "shipping_address" in payload and payload["shipping_address"]:
        for sk, sv in payload["shipping_address"].items():
            if sv is not None:
                path = f"shipping_address.{sk}"
                if _is_forbidden(path):
                    raise HTTPException(
                        status_code=400, detail=f"Field '{path}' is not editable")
                set_ops[path] = sv

    if "timeline" in payload and payload["timeline"]:
        for tk, tv in payload["timeline"].items():
            if tv is not None:
                path = tk
                if _is_forbidden(path):
                    raise HTTPException(
                        status_code=400, detail=f"Field '{path}' is not editable")
                set_ops[path] = tv

    field_map = {
        "name": "name",
        "age": "age",
        "gender": "gender",
        "book_id": "book_id",
        "book_style": "book_style",
        "discount_code": "discount_code",
        "quantity": "quantity",
        "preview_url": "preview_url",
        "total_price": "total_price",
        "transaction_id": "transaction_id",
        "paypal_capture_id": "paypal_capture_id",
        "paypal_order_id": "paypal_order_id",
        "cover_url": "cover_url",
        "book_url": "book_url",
        "user_name": "user_name",
        "email": "email",
        "phone": "phone_number",
        "current_status": "current_status",
        "order_id": "order_id",
        "remarks": "remarks",   # ✅ ADD
        "tracking_code": "tracking_code"
    }

    for incoming, doc_path in field_map.items():
        if incoming in payload and payload[incoming] is not None:
            if _is_forbidden(doc_path):
                raise HTTPException(
                    status_code=400, detail=f"Field '{doc_path}' is not editable")
            set_ops[doc_path] = payload[incoming]

    if not set_ops:
        existing = orders_collection.find_one({"order_id": order_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Order not found")
        return {"updated": False, "order": _build_order_response(existing)}

    res = orders_collection.update_one(
        {"order_id": order_id}, {"$set": set_ops})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")

    updated = orders_collection.find_one({"order_id": order_id})
    return {"updated": bool(res.modified_count), "order": _build_order_response(updated)}

class LockRequest(BaseModel):
    # Who is locking/unlocking – you can use admin email here
    order_id: str

@app.post("/api/orders/unapprove")
async def unapprove_orders(req: UnapproveRequest):
    print(f"Unapprove request: {req}")
    for job_id in req.job_ids:
        print(f"Unapproving order with job_id: {job_id}")
        result = orders_collection.update_one(
            {"job_id": job_id},
            {"$set": {"approved": False}}
        )
        print(f"Update result: {result}")
        if result.modified_count == 0:
            raise HTTPException(
                status_code=404, detail=f"No order found with job_id {job_id}")

    prefix = f"output/{job_id}/"
    folders_to_move = ["final_coverpage/", "approved_output/"]
    for folder in folders_to_move:
        print(f"Moving folder: {folder}")
        old_prefix = prefix + folder
        new_prefix = prefix + "previous/" + folder

        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=old_prefix)
        print(f"List objects response: {response}")

        if "Contents" not in response:
            continue

        for obj in response["Contents"]:
            src_key = obj["Key"]
            dst_key = src_key.replace(old_prefix, new_prefix, 1)
            print(f"Moving from: {src_key} to: {dst_key}")

            s3.copy_object(Bucket=BUCKET_NAME, CopySource={
                           "Bucket": BUCKET_NAME, "Key": src_key}, Key=dst_key)
            s3.delete_object(Bucket=BUCKET_NAME, Key=src_key)

    print(f"Unapproved {len(req.job_ids)} orders successfully")
    return {"message": f"Unapproved {len(req.job_ids)} orders successfully"}

@app.post("/api/orders/lock")
async def lock_order(
    payload: LockRequest,
    claims=Depends(require_auth)
):
    order_id = payload.order_id

    admin_email = get_admin_email_from_claims(claims)

    order = orders_collection.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(404, "Order not found")

    if order.get("locked"):
        locked_by = order.get("locked_by") or "unknown"
        raise HTTPException(
            400,
            f"Order is already locked by {locked_by}"
        )

    result = orders_collection.update_one(
        {"order_id": order_id},
        {
            "$set": {
                "locked": True,
                "locked_by": admin_email,
                "locked_at": datetime.now(timezone.utc).isoformat(),
                "unlock_by": "",
                "unlock_at": "",
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(409, "Failed to lock order – retry")

    return {
        "order_id": order_id,
        "locked": True,
        "locked_by": admin_email,
    }

@app.post("/api/orders/unlock")
async def unlock_order(
    payload: LockRequest,
    claims=Depends(require_auth)
):
    order_id = payload.order_id

    admin_email = get_admin_email_from_claims(claims)

    order = orders_collection.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(404, "Order not found")

    if not order.get("locked"):
        raise HTTPException(400, "Order is not locked")

    result = orders_collection.update_one(
        {"order_id": order_id},
        {
            "$set": {
                "locked": False,
                "unlock_by": admin_email,
                "unlock_at": datetime.now(timezone.utc).isoformat(),
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(409, "Failed to unlock order – retry")

    return {
        "order_id": order_id,
        "locked": False,
    }

@app.get("/api")
def read_root():
    return {"message": "Hello from the backend!"}

@app.get("/hp")
async def serve_hp():
    # Manually serve the hp.html file from the out directory
    hp_path = "../frontend/out/hp.html"
    if os.path.exists(hp_path):
        with open(hp_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return {"message": "Frontend hp.html not found."}
    
@app.get("/ls")
async def serve_ls():
    # Manually serve the ls.html file from the out directory
    ls_path = "../frontend/out/ls.html"
    if os.path.exists(ls_path):
        with open(ls_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return {"message": "Frontend ls.html not found."}

@app.get("/dashboard")
async def serve_dashboard():
    # Manually serve the dashboard.html file from the out directory
    dashboard_path = "../frontend/out/dashboard.html"
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return {"message": "Frontend dashboard.html not found."}
    

           
@app.get("/api/orders")
async def serve_orders():
    # Manually serve the orders.html file from the out directory
    orders_path = "../frontend/out/orders.html"
    if os.path.exists(orders_path):
        with open(orders_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return {"message": "Frontend orders.html not found."}
    
@app.get("/api/jobs")
async def serve_jobs():
    # Manually serve the jobs.html file from the out directory
    jobs_path = "../frontend/out/jobs.html"
    if os.path.exists(jobs_path):
        with open(jobs_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return {"message": "Frontend jobs.html not found."}
    

@app.get("/api/test")
async def serve_test_orders():
    # Manually serve the orders.html file from the out directory
    orders_path = "../frontend/out/test.html"
    if os.path.exists(orders_path):
        with open(orders_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return {"message": "Frontend test.html not found."}
           
@app.get("/api/rejected-orders")
async def serve_rejected_orders():
    # Manually serve the rejected-orders.html file from the out directory
    orders_path = "../frontend/out/rejected-orders.html"
    if os.path.exists(orders_path):
        with open(orders_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return {"message": "Frontend rejected-orders.html not found."}
           
@app.get("/api/export")
async def serve_export():
    # Manually serve the export.html file from the out directory
    orders_path = "../frontend/out/export.html"
    if os.path.exists(orders_path):
        with open(orders_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return {"message": "Frontend export.html not found."}
   

@app.get("/api/razorpay_analysis")
async def serve_razorpay_analysis():
    # Manually serve the razorpay_analysis.html file from the out directory
    orders_path = "../frontend/out/razorpay_analysis.html"
    if os.path.exists(orders_path):
        with open(orders_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return {"message": "Frontend razorpay_analysis.html not found."}
  
@app.get("/api/Shipment_status")
async def serve_shipment_status():
    # Manually serve the shipment_status.html file from the out directory
    orders_path = "../frontend/out/Shipment_status.html"
    if os.path.exists(orders_path):
        with open(orders_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return {"message": "Frontend shipment_status.html not found."}
  
@app.get("/api/Order_status")
async def serve_order_status():
    # Manually serve the order_status.html file from the out directory
    orders_path = "../frontend/out/Order_status.html"
    if os.path.exists(orders_path):
        with open(orders_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return {"message": "Frontend Order_status.html not found."}
    
@app.get("/api/Shipment_KPI")
async def serve_shipment_kpi():
    # Manually serve the Shipment_KPI.html file from the out directory
    orders_path = "../frontend/out/Shipment_KPI.html"
    if os.path.exists(orders_path):
        with open(orders_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return {"message": "Frontend Shipment_KPI.html not found."}

@app.get("/api/Shipment_orders")
async def serve_shipment_orders():
    # Manually serve the Shipment_orders.html file from the out directory
    orders_path = "../frontend/out/Shipment_orders.html"
    if os.path.exists(orders_path):
        with open(orders_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return {"message": "Frontend Shipment_orders.html not found."}

@app.get("/Bulk_orders")
async def serve_bulk_orders():
    # Manually serve the Bulk_orders.html file from the out directory
    orders_path = "../frontend/out/Bulk_orders.html"
    if os.path.exists(orders_path):
        with open(orders_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return {"message": "Frontend Bulk_orders.html not found."}
    

@app.get("/unauthorized")
async def serve_unauthorized():
    # Manually serve the unauthorized.html file from the out directory
    unauthorized_path = "../frontend/out/unauthorized.html"
    if os.path.exists(unauthorized_path):
        with open(unauthorized_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return {"message": "Frontend unauthorized.html not found."}


# Serve all files from the Next.js export folder (out/) when present
_frontend_out_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "frontend", "out"))
if os.path.isdir(_frontend_out_dir):
    app.mount("/", StaticFiles(directory=_frontend_out_dir, html=True), name="static")
else:
    logger.warning("Frontend export directory not found: %s", _frontend_out_dir)
