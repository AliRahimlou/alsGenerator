import os
import shutil
import gzip
import re

# 🛠 CONFIG: Paths
BLANK_ALS_PATH = "/Users/alirahimlou/myapps/alsGenerator/Untitled.als"
FLAC_FOLDER = "/Users/alirahimlou/Desktop/test-music"

def find_flac_files(directory):
    """Find .flac files and categorize them into drums, Inst, and vocals."""
    flac_files = sorted([f for f in os.listdir(directory) if f.endswith(".flac")])

    # Extract specific file types based on naming convention
    track_names = {
        "drums": next((f for f in flac_files if "drums" in f.lower()), None),
        "Inst": next((f for f in flac_files if "inst" in f.lower()), None),
        "vocals": next((f for f in flac_files if "vocals" in f.lower()), None),
    }

    return track_names

def clean_filename(filename):
    """Remove 'drums-', 'Inst-', 'vocals-' from filename and keep the main part."""
    return re.sub(r'^(drums-|Inst-|vocals-)', '', filename).replace('.flac', '')

def modify_als_file(input_path, flac_folder, track_names):
    """Loads a working .als file, modifies track names & FLAC references, and saves with a new name."""
    try:
        # Generate output ALS name from the new track name
        primary_track_name = clean_filename(track_names.get("drums") or track_names.get("Inst") or track_names.get("vocals") or "Modified")
        output_als = os.path.join(flac_folder, f"{primary_track_name}.als")

        # Make a copy of the blank ALS to modify
        shutil.copy(input_path, output_als)

        # Read ALS file as binary (gzip compressed)
        with gzip.open(output_als, "rb") as f:
            als_data = f.read()  # Read raw binary data

        # Convert binary to a mutable format (latin1 for safe handling)
        als_str = als_data.decode("latin1")  # Ensures all bytes are preserved

        # 🔍 Debugging: Print found .flac references
        matches = re.findall(r'["\']([^"\']+\.flac)["\']', als_str)
        print("🔍 Found FLAC references in ALS:", matches)

        # Dynamically set replacements (using actual filenames, no placeholders)
        replacements = {
            "drums-Tape B - i won't be ur drug.flac": track_names["drums"] if track_names["drums"] else "",
            "Inst-Tape B - i won't be ur drug.flac": track_names["Inst"] if track_names["Inst"] else "",
            "vocals-Tape B - i won't be ur drug.flac": track_names["vocals"] if track_names["vocals"] else "",
        }

        # Ensure replacements happen for absolute, relative, and URL-encoded paths
        for old, new in replacements.items():
            if new:  # Only perform replacement if the actual file exists
                als_str = als_str.replace(old, new)  # Standard replacements
                als_str = als_str.replace(f"../{old}", f"../{new}")  # Fix relative paths
                als_str = als_str.replace(f"{flac_folder}/{old}", f"{flac_folder}/{new}")  # Fix dynamic absolute paths
                als_str = als_str.replace(old.replace(" ", "%20"), new.replace(" ", "%20"))  # Fix URL encoding in BrowserContentPath

        # 🔄 **Fix Display Names (MemorizedFirstClipName, EffectiveName, UserName, Name)**
        for old, new in replacements.items():
            old_track_name = old.replace(".flac", "")  # Remove .flac for display name replacements
            new_track_name = new.replace(".flac", "")

            if new:  # Only replace if the actual track exists
                # Replace in `MemorizedFirstClipName`
                als_str = re.sub(rf'(<MemorizedFirstClipName Value="){re.escape(old_track_name)}(")', rf'\1{new_track_name}\2', als_str)

                # Replace in `UserName`
                als_str = re.sub(rf'(<UserName Value="){re.escape(old_track_name)}(")', rf'\1{new_track_name}\2', als_str)

                # Replace in `Name`
                als_str = re.sub(rf'(<Name Value="){re.escape(old_track_name)}(")', rf'\1{new_track_name}\2', als_str)

                # Replace in `EffectiveName`
                als_str = re.sub(rf'(<EffectiveName Value="){re.escape(old_track_name)}(")', rf'\1{new_track_name}\2', als_str)

        # Convert back to binary
        modified_data = als_str.encode("latin1")  # Preserve original byte structure

        # Save the modified ALS file (gzip compressed)
        with gzip.open(output_als, "wb") as f:
            f.write(modified_data)

        print(f"✅ Final modified ALS saved at: {output_als}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    track_names = find_flac_files(FLAC_FOLDER)
    if not any(track_names.values()):
        print("❌ No relevant FLAC files found in the folder!")
    else:
        modify_als_file(BLANK_ALS_PATH, FLAC_FOLDER, track_names)
        print("🎵 Modified ALS file created successfully!")
