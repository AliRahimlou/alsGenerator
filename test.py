import os
import shutil
import re

# 🛠 CONFIG: Paths
EMPTY_ALS_TEMPLATE = "/Users/alirahimlou/myapps/alsGenerator/scratch/Untitled.als"  # Path to empty ALS template
FLAC_FOLDER = "/Users/alirahimlou/Desktop/test-music"  # Folder where FLAC files are stored

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

def create_empty_als(flac_folder, track_names):
    """Create a brand new empty ALS file and inject track info."""
    try:
        # Create new ALS file from template
        new_als_path = os.path.join(flac_folder, "NewTrack.als")
        
        # Copy the empty ALS template to the new location
        shutil.copy(EMPTY_ALS_TEMPLATE, new_als_path)
        
        with open(new_als_path, "r", encoding="latin1") as f:
            als_data = f.read()

        # Inject FLAC paths and track names into the ALS
        for track, file in track_names.items():
            if file:
                # Replace placeholders with actual file path and track name
                als_data = als_data.replace(f"<{track}FilePath/>", os.path.join(flac_folder, file))  # Assuming this tag exists in template
                als_data = als_data.replace(f"<{track}Name/>", clean_filename(file))  # Replace name with cleaned file name

        # Save the new ALS with injected data
        with open(new_als_path, "w", encoding="latin1") as f:
            f.write(als_data)

        print(f"✅ New ALS file created at: {new_als_path}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    track_names = find_flac_files(FLAC_FOLDER)
    if not any(track_names.values()):
        print("❌ No relevant FLAC files found in the folder!")
    else:
        create_empty_als(FLAC_FOLDER, track_names)
        print("🎵 New ALS file created successfully!")
