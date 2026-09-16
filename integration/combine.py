"""
Integration script: combines all three teammates' finished, per-source
data/processed/final.csv files into one dataset, WITHOUT modifying any
of the original source files.
"""
import pandas as pd
import os

BASE = os.path.expanduser("~/mnt")
BATOOL_FINAL = os.path.join(BASE, "TechHub-Group3-EdTech-Content-Data-Pipeline-main", "TechHub-Group3-EdTech-Content-Data-Pipeline", "data", "processed", "final.csv")
SARAH_FINAL = os.path.join(BASE, "TechHub-Group3-EdTech-Content-Data-Pipeline-Sarah", "data", "processed", "final.csv")
DANA_FINAL = os.path.join(BASE, "TechHub-Group3-EdTech-Content-Data-Pipeline-Dana", "data", "processed", "final.csv")

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "final_combined.csv")

# ---- Load (read-only, originals never touched) ----
batool = pd.read_csv(BATOOL_FINAL)
sarah = pd.read_csv(SARAH_FINAL)
dana = pd.read_csv(DANA_FINAL)

print("Batool raw shape:", batool.shape)
print("Sarah raw shape:", sarah.shape)
print("Dana raw shape:", dana.shape)

# ---- Align column names to a common schema (rename only, on in-memory copies) ----
batool = batool.rename(columns={
    "topic": "category",         # Batool's topic -> common 'category'
    "content_clean": "content",  # Batool's cleaned body -> common 'content'
})
sarah = sarah.rename(columns={
    "publication_date": "published_date",  # Sarah's publication_date -> common 'published_date'
})
dana = dana.rename(columns={
    "publication_date": "published_date",  # Dana's publication_date -> common 'published_date'
    "topic": "category",     # Dana's AI/Cloud/Data Science grouping -> common 'category' (matches Sarah's category level)
    "category": "tags",      # Dana's site-level tag (e.g. "#shadcn ui") -> common 'tags' (matches Batool/Sarah's tags concept)
})

# Tag each row with which pipeline/person produced it
batool["contributor"] = "Batool"
sarah["contributor"] = "Sarah"
dana["contributor"] = "Dana"

# ---- Combine: stack (concat), not a relational join -- there is no shared key
# across unrelated content platforms. sort=False keeps column order stable;
# any column unique to one source is filled with NaN for the others. ----
combined = pd.concat([batool, sarah, dana], ignore_index=True, sort=False)

before_dedup = len(combined)
combined = combined.drop_duplicates(subset="url", keep="first")
after_dedup = len(combined)

print(f"Combined rows before dedup: {before_dedup}")
print(f"Combined rows after dedup (by url): {after_dedup}")
print("Combined shape:", combined.shape)
print("Combined columns:", list(combined.columns))
print()
print("Rows per contributor:")
print(combined["contributor"].value_counts())

combined.to_csv(OUTPUT_CSV, index=False)
print()
print(f"Saved combined dataset to: {OUTPUT_CSV}")
