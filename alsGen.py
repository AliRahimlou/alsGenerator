import os
import shutil
import gzip
import re

# 🛠 CONFIG: Paths (Can be changed dynamically)
ALS_FILES_FOLDER = "alsFiles"  # Folder where BPM ALS templates are stored
DEFAULT_FLAC_FOLDER = "/Users/alirahimlou/Desktop/STEMS/separated/htdemucs"
FLAC_FOLDER = os.getenv("FLAC_FOLDER", DEFAULT_FLAC_FOLDER)  # Allow environment override
SKIP_EXISTING = True  # 🔄 Set to False to overwrite CH1.als if it already exists

def find_flac_folders(directory):
    """
    Recursively search for folders in `directory` that contain .flac files.
    Returns a list of tuples: (folder_path, track_names, bpm_value).
    """
    results = []
    for root, dirs, files in os.walk(directory):
        flac_files = sorted([f for f in files if f.lower().endswith(".flac")])
        if flac_files:
            track_names = {"drums": None, "Inst": None, "vocals": None}
            for f in flac_files:
                rel_path = os.path.relpath(os.path.join(root, f), directory)  # Compute **relative** path
                if "drums" in f.lower() and track_names["drums"] is None:
                    track_names["drums"] = rel_path
                elif "inst" in f.lower() and track_names["Inst"] is None:
                    track_names["Inst"] = rel_path
                elif "vocals" in f.lower() and track_names["vocals"] is None:
                    track_names["vocals"] = rel_path
            
            # Extract BPM value from folder structure
            bpm_value = extract_bpm_from_path(root)

            if any(track_names.values()):  # Only add folders that contain at least one relevant FLAC file
                results.append((root, track_names, bpm_value))
    return results

def extract_bpm_from_path(folder_path):
    """
    Extracts the BPM from the folder structure.
    The BPM is assumed to be any numeric value (70-200) found in the path.
    """
    bpm_match = re.search(r"/(\d{2,3})/", folder_path)  # Find first 2-3 digit number in path
    if bpm_match:
        bpm = int(bpm_match.group(1))  # Convert to integer
        if 70 <= bpm <= 200:  # Ensure it's a valid BPM
            print(f"📌 Extracted BPM: {bpm} from {folder_path}")  # Debugging info
            return str(bpm)  # Convert to string for ALS matching
    
    print(f"⚠️ No valid BPM found in {folder_path}")  # Debugging info
    return None  # No BPM found

def select_blank_als(bpm_value):
    """
    Dynamically selects the correct blank ALS file based on BPM value.
    If no exact match is found, print a warning and return a default ALS.
    """
    if bpm_value:
        bpm_als_path = os.path.join(ALS_FILES_FOLDER, f"{bpm_value}.als")
        if os.path.exists(bpm_als_path):
            print(f"✅ Found ALS template for BPM {bpm_value}: {bpm_als_path}")  # Debugging info
            return bpm_als_path  # Exact match found
    
    # Use a fallback ALS template
    default_als = os.path.join(ALS_FILES_FOLDER, "default.als")
    if os.path.exists(default_als):
        print(f"⚠️ Warning: No ALS file found for BPM {bpm_value}. Using default ALS.")
        return default_als
    
    print(f"❌ No ALS file available for BPM {bpm_value}. Skipping...")
    return None  # Return None if no ALS template exists

def modify_als_file(input_path, target_folder, track_names):
    """
    Loads the selected ALS file, replaces FLAC references with actual filenames,
    and saves the ALS as "CH1.als" inside the same folder where the FLAC files are located.
    """
    try:
        if input_path is None:
            print(f"❌ Skipping folder '{target_folder}' due to missing ALS template.")
            return

        output_als = os.path.join(target_folder, "CH1.als")

        # **Check if CH1.als already exists and skip if enabled**
        if SKIP_EXISTING and os.path.exists(output_als):
            print(f"⏭️ Skipping '{target_folder}' – CH1.als already exists.")
            return

        # Copy the blank ALS to the target folder
        shutil.copy(input_path, output_als)

        # Read the copied ALS file (which is gzip compressed)
        with gzip.open(output_als, "rb") as f:
            als_data = f.read()

        # Convert binary data to string (latin1 encoding to preserve bytes)
        als_str = als_data.decode("latin1")

        # 🔍 Debug: Show FLAC references found in the blank ALS file
        matches = re.findall(r'["\']([^"\']+\.flac)["\']', als_str)
        print(f"🔍 In folder '{target_folder}': Found FLAC references in ALS:", matches)

        # Dynamically set replacements (must match exactly what is in your blank ALS file)
        replacements = {
            "drums-Tape B - i won't be ur drug.flac": track_names["drums"] if track_names["drums"] else "",
            "Inst-Tape B - i won't be ur drug.flac": track_names["Inst"] if track_names["Inst"] else "",
            "vocals-Tape B - i won't be ur drug.flac": track_names["vocals"] if track_names["vocals"] else "",
        }

        # Perform replacements in ALS for file paths
        for old, new in replacements.items():
            if new:
                als_str = als_str.replace(old, new)  # Standard replacement
                als_str = als_str.replace(f"../{old}", f"../{new}")  # Fix relative paths
                als_str = als_str.replace(f"{target_folder}/{old}", f"{target_folder}/{new}")  # Fix absolute paths
                als_str = als_str.replace(old.replace(" ", "%20"), new.replace(" ", "%20"))  # Fix URL encoding

        # Fix display names in the ALS
        for old, new in replacements.items():
            if new:
                old_track_name = old.replace(".flac", "")
                new_track_name = os.path.basename(new).replace(".flac", "")
                als_str = re.sub(rf'(<MemorizedFirstClipName Value="){re.escape(old_track_name)}(")', rf'\1{new_track_name}\2', als_str)
                als_str = re.sub(rf'(<UserName Value="){re.escape(old_track_name)}(")', rf'\1{new_track_name}\2', als_str)
                als_str = re.sub(rf'(<Name Value="){re.escape(old_track_name)}(")', rf'\1{new_track_name}\2', als_str)
                als_str = re.sub(rf'(<EffectiveName Value="){re.escape(old_track_name)}(")', rf'\1{new_track_name}\2', als_str)

        # Re-encode the modified ALS back to binary and gzip-compress it
        modified_data = als_str.encode("latin1")
        with gzip.open(output_als, "wb") as f:
            f.write(modified_data)

        print(f"✅ Final modified ALS saved at: {output_als}\n")

    except Exception as e:
        print(f"❌ Error modifying ALS in folder '{target_folder}': {e}")

if __name__ == "__main__":
    folders = find_flac_folders(FLAC_FOLDER)
    if not folders:
        print("❌ No relevant FLAC files found in any folder!")
    else:
        for folder, track_names, bpm_value in folders:
            blank_als_path = select_blank_als(bpm_value)
            modify_als_file(blank_als_path, folder, track_names)
        print("🎵 All ALS files generated successfully!")
