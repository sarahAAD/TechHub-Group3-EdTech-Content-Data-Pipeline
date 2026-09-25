import datetime
import json
import os
from pathlib import Path

from azure.storage.blob import BlobServiceClient

from .config import RAW_DIR, RAW_PATTERNS

# يحول اسم المصدر لاسم مجلد آمن جوا ADLS (بدون نقاط أو مسافات)
SOURCE_FOLDER_MAP = {
    "dev.to": "devto",
    "Pluralsight": "pluralsight",
    "freeCodeCamp": "freecodecamp",
    "Medium": "medium",
    "GeeksforGeeks": "geeksforgeeks",
}

CONTAINER_NAME = os.environ.get("ADLS_CONTAINER_NAME", "edtech")
CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")

# مسار ثابت (خارج أي batch) نخزن فيه "قائمة الروابط المعروفة" لكل
# مصدر. هذا الملف هو اللي يخلي البايبلاين يعرف عبر batches مختلفة
# (وحاويات مختلفة كل مرة) وش المقالات اللي سبق استخرجناها، عشان كل
# batch جديد يجيب بس الجديد أو المتغيّر (حسب تصميم الفريق).
KNOWN_URLS_PREFIX = "raw/_known_urls"


def get_batch_id():
    """
    يرجع batch_id لهالتشغيلة.

    لو ADF مرره عن طريق متغير البيئة BATCH_ID، نستخدمه زي ما هو
    (نفس القيمة اللي Member 3 ولّدها بصيغة yyyyMMdd_HHmmss، عشان
    تتطابق مع اللي بيستخدمه Databricks لنفس التشغيلة بالضبط).

    لو ما كان موجود (تشغيلة يدوية/تجربة محلية بدون ADF)، نولّد
    وحد بنفس الصيغة عشان نقدر نختبر السكربت لحاله.
    """

    return (
        os.environ.get("BATCH_ID")
        or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    )


def load_known_urls_from_adls(source):
    """
    يرجع dict {url: signature} لكل الروابط اللي سبق استخرجناها
    لنفس المصدر من أي batch قبل كذا. يرجع {} لو أول مرة، أو لو ما
    فيه اتصال بـ ADLS، أو أي خطأ غير متوقع (ما نفشل التشغيلة بسبب
    هذا - أسوأ حالة إننا نعيد استخراج شي سبق استخرجناه).

    "signature" تختلف حسب المصدر (extract.py هو اللي يقرر شكلها):
    - مصادر جلب المحتوى فيها مكلف (dev.to, Pluralsight,
      freeCodeCamp): بس علامة "seen" (يكفي لتفادي إعادة الجلب).
    - مصادر محتواها يجي مجاني مع تحميل الداتاسيت كامل (Medium,
      GeeksforGeeks): هاش فعلي للمحتوى، عشان نكتشف "تغيّر" حقيقي.
    """

    folder_name = SOURCE_FOLDER_MAP.get(source, source.lower())

    if not CONNECTION_STRING:
        return {}

    try:
        blob_service = BlobServiceClient.from_connection_string(
            CONNECTION_STRING
        )
        container_client = blob_service.get_container_client(
            CONTAINER_NAME
        )

        if not container_client.exists():
            return {}

        blob_path = f"{KNOWN_URLS_PREFIX}/{folder_name}.json"
        blob_client = container_client.get_blob_client(blob_path)

        if not blob_client.exists():
            return {}

        downloader = blob_client.download_blob()
        return json.loads(downloader.readall())

    except Exception as error:
        print(
            f"[{source}] تعذر تحميل قائمة الروابط المعروفة من "
            f"ADLS: {error}. هنتعامل معاها كأنها فاضية (يعني ممكن "
            "نعيد استخراج شي سبق استخرجناه لو صار هذا الخطأ، بس ما "
            "بيوقف التشغيلة)."
        )
        return {}


def save_known_urls_to_adls(source, url_signature_map):
    """
    يدمج url_signature_map (روابط هالـ batch الحالي) مع قائمة
    الروابط المخزّنة بالفعل بـ ADLS، ويرفع النسخة المحدثة.

    تنادى بعد ما الاستخراج ينجح فعلياً (مو قبل)، عشان لو فشل
    الاستخراج ما نسجل روابط ما تأكدنا إنها فعلاً انحفظت.
    """

    if not CONNECTION_STRING or not url_signature_map:
        return

    folder_name = SOURCE_FOLDER_MAP.get(source, source.lower())

    try:
        existing = load_known_urls_from_adls(source)
        existing.update(url_signature_map)

        blob_service = BlobServiceClient.from_connection_string(
            CONNECTION_STRING
        )
        container_client = blob_service.get_container_client(
            CONTAINER_NAME
        )

        if not container_client.exists():
            container_client.create_container()

        blob_path = f"{KNOWN_URLS_PREFIX}/{folder_name}.json"

        payload = json.dumps(
            existing,
            ensure_ascii=False,
        ).encode("utf-8")

        container_client.upload_blob(
            name=blob_path,
            data=payload,
            overwrite=True,
        )

    except Exception as error:
        print(
            f"[{source}] تعذر تحديث قائمة الروابط المعروفة بـ "
            f"ADLS: {error}. هذا ما يوقف التشغيلة، بس معناه إن "
            "الـ batch الجاي ممكن يعيد جلب نفس المقالات."
        )


def upload_raw_to_adls(batch_id=None, outputs=None):
    """
    يرفع ملفات data/raw لكل مصدر إلى ADLS تحت:
    <container>/raw/batch_id=<batch_id>/<اسم_المصدر>/<اسم_الملف>

    كل تشغيلة (batch) تكتب تحت مجلدها الخاص بدل ما تكتب فوق نفس
    المسار القديم، عشان Databricks (Member 2) يقدر يقرأ بس بيانات
    هالـ batch الحالي، ويسوي MERGE على url فوق Silver/Gold.

    يرجع الـ batch_id المستخدم (سواء جاك من ADF أو تولّد هنا)
    عشان نطبعه بملخص التشغيلة.
    """

    if not CONNECTION_STRING:
        raise RuntimeError(
            "متغير البيئة AZURE_STORAGE_CONNECTION_STRING غير موجود. "
            "لازم تحطينه قبل تشغيل هذا السكربت."
        )

    batch_id = batch_id or get_batch_id()

    blob_service = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    container_client = blob_service.get_container_client(CONTAINER_NAME)

    if not container_client.exists():
        print(f"Container '{CONTAINER_NAME}' غير موجود، جاري إنشاؤه...")
        container_client.create_container()

    total_uploaded = 0

    def has_records(local_file):
        # Return False for an empty JSON list or a header-only CSV.
        local_file = Path(local_file)

        try:
            if local_file.suffix.lower() == ".json":
                with local_file.open("r", encoding="utf-8") as file:
                    data = json.load(file)
                return bool(data)

            if local_file.suffix.lower() == ".csv":
                with local_file.open("r", encoding="utf-8-sig") as file:
                    return sum(1 for _ in file) > 1

            return local_file.stat().st_size > 0

        except Exception as error:
            print(
                f"[upload] Could not inspect {local_file.name}: {error}. "
                "Uploading it as a fallback."
            )
            return True

    # Upload only files produced by THIS extraction run.
    # This prevents stale raw files baked into the Docker image from
    # being copied into every new Bronze batch.
    if outputs is not None:
        files_by_source = {}

        for source, result in outputs.items():
            if result is None:
                continue

            candidates = (
                result
                if isinstance(result, (list, tuple))
                else [result]
            )

            files_by_source[source] = [
                Path(path)
                for path in candidates
                if path and Path(path).exists()
            ]

    else:
        # Backward-compatible fallback for manual/legacy calls.
        files_by_source = {}

        for source, patterns in RAW_PATTERNS.items():
            matched_files = []

            for pattern in patterns:
                matched_files.extend(
                    Path(RAW_DIR).glob(pattern)
                )

            files_by_source[source] = matched_files

    for source, matched_files in files_by_source.items():
        folder_name = SOURCE_FOLDER_MAP.get(
            source,
            source.lower(),
        )

        nonempty_files = [
            local_file
            for local_file in matched_files
            if has_records(local_file)
        ]

        if not nonempty_files:
            print(
                f"[{source}] No new/changed records to upload "
                f"for batch_id={batch_id}."
            )
            continue

        for local_file in nonempty_files:
            blob_path = (
                f"raw/batch_id={batch_id}/{folder_name}/{local_file.name}"
            )

            print(
                f"Uploading {local_file.name} -> "
                f"{CONTAINER_NAME}/{blob_path}"
            )

            with open(local_file, "rb") as data:
                container_client.upload_blob(
                    name=blob_path,
                    data=data,
                    overwrite=True,
                )

            total_uploaded += 1

    print(
        f"انتهى رفع {total_uploaded} ملف/ملفات إلى ADLS تحت "
        f"batch_id={batch_id} بنجاح."
    )

    return batch_id
