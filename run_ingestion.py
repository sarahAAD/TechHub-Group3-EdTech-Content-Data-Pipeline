"""
سكربت التشغيل الحقيقي جوا Azure Container Apps Job.

بشكل افتراضي يسحب كل الخمسة مصادر (زي main.py الأصلي بس بدون
مراحل التنظيف/التحقق/التحويل - هذي صارت شغل Databricks).

يشتغل الآن بتصميم batch_id: كل تشغيلة تاخذ batch_id (من ADF عن
طريق متغير البيئة BATCH_ID، أو يتولّد تلقائياً لو تشغيلة يدوية)،
وترفع بياناتها الخام جوا ADLS تحت raw/batch_id=<batch_id>/...
عشان Databricks يقدر يقرأ بس بيانات هالـ batch الحالي ويسوي MERGE
على url فوق Silver/Gold.

الـ incremental (تفادي إعادة استخراج نفس المقالة) صار على مستوى
كل مقالة لحالها (بالـ URL)، مو على مستوى المصدر كامل: كل extractor
يتأكد بنفسه (قبل ما يجيب المحتوى) هل هالرابط سبق استخرجناه بـ
batch سابق، ويجيب بس الجديد أو المتغيّر. القائمة هذي محفوظة بشكل
دائم بـ ADLS (خارج أي batch) عشان تفضل صحيحة حتى لو كل تشغيلة
تصير بحاوية جديدة كلياً.

كل مصدر محمي بمهلة زمنية قصوى خاصة فيه ومعزول عن باقي المصادر
(لو مصدر تعطل أو تعلق، الباقي يكمل عادي).

بعد ما يخلص، يطبع ملخص واضح (notification) يبين حالة كل مصدر
وأي batch_id استخدمناه.

للاختبار المحلي، تقدرين تحددين مصدر أو أكثر بس عن طريق متغير بيئة:
    EXTRACTION_SOURCES="dev.to"
    EXTRACTION_SOURCES="dev.to,freeCodeCamp"

وإجبار إعادة السحب حتى لو مقالة معيّنة سبق شفناها (يتجاهل قائمة
الروابط المعروفة كلياً لهالتشغيلة):
    EXTRACTION_REFRESH=true

ولو تبين تحددين batch_id يدوياً (بدل ما يتولّد تلقائياً):
    BATCH_ID=20260921_120000
"""

import os

from src.extract import SUPPORTED_SOURCES, run_extraction
from src.upload import upload_raw_to_adls


def print_summary(sources_to_run, outputs, batch_id):
    print("\n" + "=" * 60)
    print("INGESTION SUMMARY")
    print(f"BATCH_ID: {batch_id}")
    print("=" * 60)

    any_failure = False

    for source in sources_to_run:
        result = outputs.get(source)

        if result is None:
            status = "FAILED / TIMED OUT (see the message above for why)"
            any_failure = True
        else:
            status = (
                "OK - batch processed (see the per-source new/changed "
                "vs skipped counts above)"
            )

        print(f"  {source}: {status}")

    print("=" * 60)

    if any_failure:
        print(
            "RESULT: completed WITH FAILURES on one or more sources. "
            "The other sources' data was still extracted and uploaded "
            "normally."
        )
    else:
        print("RESULT: all sources completed successfully.")

    print("=" * 60)


def main():
    refresh = (
        os.environ.get("EXTRACTION_REFRESH", "false").lower() == "true"
    )

    only_sources = os.environ.get("EXTRACTION_SOURCES")

    sources_to_run = (
        [s.strip() for s in only_sources.split(",") if s.strip()]
        if only_sources
        else SUPPORTED_SOURCES
    )

    print("=== Step 1: Extraction (فلترة الجديد/المتغيّر بالـ URL تصير جوا كل extractor) ===")
    outputs = run_extraction(refresh=refresh, sources=sources_to_run)

    print("\n=== Step 2: Upload raw files to ADLS (مقسّمة بـ batch_id) ===")
    batch_id = upload_raw_to_adls()

    print_summary(sources_to_run, outputs, batch_id)


if __name__ == "__main__":
    main()
