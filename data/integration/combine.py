"""
Integration script: combines all teammates' finished, per-source
data/processed/final*.csv files into one dataset, WITHOUT modifying any
of the original source files.
"""
import pandas as pd
import os

BASE = os.path.expanduser("~/mnt")
BATOOL_FINAL = os.path.join(BASE, "TechHub-Group3-EdTech-Content-Data-Pipeline-main", "TechHub-Group3-EdTech-Content-Data-Pipeline", "data", "processed", "final.csv")
SARAH_PLURALSIGHT_FINAL = os.path.join(BASE, "TechHub-Group3-EdTech-Content-Data-Pipeline-Sarah", "data", "processed", "final.csv")
SARAH_NEW_SOURCES_FINAL = os.path.join(BASE, "TechHub-Group3-EdTech-Content-Data-Pipeline-Sarah", "data", "processed", "final_new_sources.csv")
DANA_FINAL = os.path.join(BASE, "TechHub-Group3-EdTech-Content-Data-Pipeline-Dana", "data", "processed", "final.csv")

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "final_combined.csv")

# ---- Load (read-only, originals never touched) ----
batool = pd.read_csv(BATOOL_FINAL)
sarah_pluralsight = pd.read_csv(SARAH_PLURALSIGHT_FINAL)
sarah_new = pd.read_csv(SARAH_NEW_SOURCES_FINAL)
dana = pd.read_csv(DANA_FINAL)

print("Batool raw shape:", batool.shape)
print("Sarah (Pluralsight) raw shape:", sarah_pluralsight.shape)
print("Sarah (GeeksforGeeks + Medium) raw shape:", sarah_new.shape)
print("Dana raw shape:", dana.shape)

# ---- Align column names to a common schema (rename only, on in-memory copies) ----
batool = batool.rename(columns={
    "topic": "category",         # Batool's topic -> common 'category'
    "content_clean": "content",  # Batool's cleaned body -> common 'content'
})
sarah_pluralsight = sarah_pluralsight.rename(columns={
    "publication_date": "published_date",
})
sarah_new = sarah_new.rename(columns={
    "publication_date": "published_date",
})
dana = dana.rename(columns={
    "publication_date": "published_date",
    "topic": "category",     # Dana's AI/Cloud/Data Science grouping -> common 'category'
    "category": "tags",      # Dana's site-level tag -> common 'tags'
})

# Combine Sarah's two batches into one before tagging/concatenating with the group
sarah = pd.concat([sarah_pluralsight, sarah_new], ignore_index=True, sort=False)

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
print()
print("Rows per contributor:")
print(combined["contributor"].value_counts())
print()
print("Rows per source (within Sarah's contribution):")
print(combined[combined["contributor"]=="Sarah"]["source"].value_counts())

combined.to_csv(OUTPUT_CSV, index=False)
print()
print(f"Saved combined dataset to: {OUTPUT_CSV}")
