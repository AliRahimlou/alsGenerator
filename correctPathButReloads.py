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
                abs_path = os.path.join(root, f)  # Store absolute path for verification
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

    flac_section = als_str[als_str.find(".flac")-50:als_str.find(".flac")+50] if ".flac" in als_str else "No .flac found"
    print(f"🔍 Raw ALS snippet (before): {flac_section}")

    template_flac_names = get_template_flac_names(input_path)
    print(f"🔍 Template FLACs: {template_flac_names}")
    print(f"🔍 Detected track files: { {k: v[0] for k, v in track_names.items() if v} }")

    # Map template FLACs to new paths (using absolute paths for now)
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
            # Use absolute path temporarily to ensure Ableton finds the files
            new_path = abs_path  # e.g., /Users/alirahimlou/Desktop/STEMS/138/8A/Vin Jay - Drop/drums-Vin Jay - Drop.flac
            if os.path.exists(new_path):
                replacements[old_flac] = new_path
            else:
                print(f"⚠️ FLAC file not found: {new_path}")
    print(f"🔍 Replacements: {replacements}")

    # Perform replacements
    for old, new in replacements.items():
        if new:
            print(f"🔍 Replacing '{old}' with '{new}'")
            als_str = als_str.replace(old, new)
            als_str = als_str.replace(f"../{old}", f"../{new}")
            als_str = als_str.replace(old.replace(" ", "%20"), new.replace(" ", "%20"))

            old_track_name = os.path.basename(old).replace(".flac", "")
            new_track_name = os.path.basename(new).replace(".flac", "")
            print(f"🔍 Updating display name: '{old_track_name}' -> '{new_track_name}'")
            als_str = re.sub(rf'(<MemorizedFirstClipName Value="){re.escape(old_track_name)}(")', rf'\1{new_track_name}\2', als_str)
            als_str = re.sub(rf'(<UserName Value="){re.escape(old_track_name)}(")', rf'\1{new_track_name}\2', als_str)
            als_str = re.sub(rf'(<Name Value="){re.escape(old_track_name)}(")', rf'\1{new_track_name}\2', als_str)
            als_str = re.sub(rf'(<EffectiveName Value="){re.escape(old_track_name)}(")', rf'\1{new_track_name}\2', als_str)

    new_flac_section = als_str[als_str.find(".flac")-50:als_str.find(".flac")+50] if ".flac" in als_str else "No .flac found"
    print(f"🔍 Raw ALS snippet (after): {new_flac_section}")

    modified_data = als_str.encode("latin1")
    with gzip.open(output_als, "wb") as f:
        f.write(modified_data)
    print(f"✅ Saved new ALS: {output_als}\n")

if __name__ == "__main__":
    folders = find_flac_folders(FLAC_FOLDER)
    if not folders:
        print("❌ No relevant FLAC files found!")
    else:
        for folder, track_names, bpm_value, key_value, track_name in folders:
            blank_als_path = select_blank_als(bpm_value)
            modify_als_file(blank_als_path, folder, track_names, track_name)
        print("🎵 All ALS files processed!")