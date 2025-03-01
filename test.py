import os
import shutil
import gzip
import re

# 🛠 CONFIG: Paths
ALS_FILES_FOLDER = "alsFiles"
FLAC_FOLDER = "/Users/alirahimlou/Desktop/STEMS"

# ✅ CONFIG: Skip or overwrite existing ALS files
SKIP_EXISTING = True

def find_flac_folders(directory):
    results = []
    for root, dirs, files in os.walk(directory):
        flac_files = sorted([f for f in files if f.lower().endswith(".flac")])
        if flac_files:
            track_names = {"drums": None, "Inst": None, "vocals": None}
            for f in flac_files:
                rel_path = os.path.relpath(os.path.join(root, f), directory)
                abs_path = os.path.join(root, f)
                if "drums" in f.lower() and track_names["drums"] is None:
                    track_names["drums"] = (rel_path, abs_path)
                elif "inst" in f.lower() and track_names["Inst"] is None:
                    track_names["Inst"] = (rel_path, abs_path)
                elif "vocals" in f.lower() and track_names["vocals"] is None:
                    track_names["vocals"] = (rel_path, abs_path)
            
            bpm_value, key_value, track_name = extract_metadata_from_path(root)
            if any(track_names.values()):
                results.append((root, track_names, bpm_value, key_value, track_name))
    return results

def extract_metadata_from_path(folder_path):
    parts = folder_path.split(os.sep)
    try:
        bpm_value = parts[-3]
        key_value = parts[-2]
        track_name = parts[-1]
        int(bpm_value)
        return bpm_value, key_value, track_name
    except (IndexError, ValueError):
        return None, None, None

def select_blank_als(bpm_value):
    if bpm_value:
        bpm_als_path = os.path.join(ALS_FILES_FOLDER, f"{bpm_value}.als")
        if os.path.exists(bpm_als_path):
            return bpm_als_path
    return None

def get_template_flac_names(als_path):
    if not als_path:
        return []
    with gzip.open(als_path, "rb") as f:
        als_data = f.read()
    als_str = als_data.decode("latin1")
    flac_paths = re.findall(r'["\'](.*?\.flac)["\']', als_str)
    return flac_paths

def modify_als_file(input_path, target_folder, track_names, track_name):
    if input_path is None:
        return

    output_als = os.path.join(target_folder, "CH1.als")
    if os.path.exists(output_als) and SKIP_EXISTING:
        return

    print(f"🔍 Processing new ALS for: {target_folder} (Track: {track_name})")
    shutil.copy(input_path, output_als)
    with gzip.open(output_als, "rb") as f:
        als_data = f.read()
    als_str = als_data.decode("latin1")

    flac_idx = als_str.find(".flac")
    flac_context_before = als_str[flac_idx-100:flac_idx+100] if flac_idx != -1 else "No .flac found"
    print(f"🔍 ALS context (before): {flac_context_before}")

    template_flac_names = get_template_flac_names(input_path)
    print(f"🔍 Template FLACs: {template_flac_names}")
    print(f"🔍 Detected track files: { {k: v[0] for k, v in track_names.items() if v} }")

    # Map template FLACs to new paths
    replacements = {}
    for old_flac in template_flac_names:
        stem_type = None
        old_flac_lower = old_flac.lower()
        if "drums" in old_flac_lower:
            stem_type = "drums"
        elif "inst" in old_flac_lower:
            stem_type = "Inst"
        elif "vocals" in old_flac_lower:
            stem_type = "vocals"
        if stem_type and track_names[stem_type]:
            rel_path, abs_path = track_names[stem_type]
            new_path = os.path.basename(abs_path)  # e.g., drums-Vin Jay - Drop.flac
            if os.path.exists(abs_path):
                replacements[old_flac] = new_path
            else:
                print(f"⚠️ FLAC file not found: {abs_path}")
    print(f"🔍 Replacements: {replacements}")

    # Perform replacements
    for old, new in replacements.items():
        if new:
            print(f"🔍 Replacing FLAC path '{old}' with '{new}'")
            als_str = als_str.replace(old, new)
            als_str = als_str.replace(f"../{old}", f"../{new}")
            als_str = als_str.replace(old.replace(" ", "%20"), new.replace(" ", "%20"))

            # 1-to-1 replacement for display names
            old_name = old_flac.split('/')[-1].replace('.flac', '')  # e.g., drums-Tape B - i won't be ur drug
            new_name = new.replace('.flac', '')  # e.g., drums-Vin Jay - Drop
            print(f"🔍 Updating display name: '{old_name}' -> '{new_name}'")
            als_str = re.sub(rf'(<MemorizedFirstClipName Value="){re.escape(old_name)}(")', rf'\1{new_name}\2', als_str)
            als_str = re.sub(rf'(<UserName Value="){re.escape(old_name)}(")', rf'\1{new_name}\2', als_str)
            als_str = re.sub(rf'(<Name Value="){re.escape(old_name)}(")', rf'\1{new_name}\2', als_str)
            als_str = re.sub(rf'(<EffectiveName Value="){re.escape(old_name)}(")', rf'\1{new_name}\2', als_str)

    remaining_flacs = re.findall(r'["\'](.*?\.flac)["\']', als_str)
    print(f"🔍 Remaining FLACs after replacement: {remaining_flacs}")

    flac_idx = als_str.find(".flac")
    flac_context_after = als_str[flac_idx-100:flac_idx+100] if flac_idx != -1 else "No .flac found"
    print(f"🔍 ALS context (after): {flac_context_after}")

    modified_data = als_str.encode("latin1")
    with gzip.open(output_als, "wb") as f:
        f.write(modified_data)
    print(f"✅ Saved new ALS: {output_als}")

    # Check and clean up .asd files
    asd_files = [f for f in os.listdir(target_folder) if f.endswith('.asd')]
    if asd_files:
        print(f"🔍 Found existing .asd files: {asd_files}")
        print(f"ℹ️ Clearing old .asd files to ensure fresh analysis...")
        for asd in asd_files:
            os.remove(os.path.join(target_folder, asd))
        print(f"ℹ️ To stop re-analyzing:\n"
              f"  1. Open {output_als} in Ableton.\n"
              f"  2. Save the project (File > Save Live Set).\n"
              f"  3. Reopen to confirm analysis persists.")
    else:
        print(f"ℹ️ No .asd files found. Open and save in Ableton to generate them.")

if __name__ == "__main__":
    folders = find_flac_folders(FLAC_FOLDER)
    if not folders:
        print("❌ No relevant FLAC files found!")
    else:
        for folder, track_names, bpm_value, key_value, track_name in folders:
            blank_als_path = select_blank_als(bpm_value)
            modify_als_file(blank_als_path, folder, track_names, track_name)
        print("🎵 All ALS files processed!")