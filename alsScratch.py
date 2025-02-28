import os
import shutil
import gzip

# 🛠 CONFIG: Paths
BLANK_ALS_PATH = "/Users/alirahimlou/myapps/alsGenerator/scratch/Untitled.als"  # Truly empty ALS
FLAC_FOLDER = "/Users/alirahimlou/Desktop/test-music"  # Folder with new FLACs

# 🛠 Basic ALS Template (Includes empty tracks)
ALS_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<LiveSet>
    <Tracks>
        {track_data}
    </Tracks>
</LiveSet>
"""

TRACK_TEMPLATE = """
<AudioTrack Id="{track_id}">
    <Name Value="{track_name}" />
    <SampleRef>
        <RelativePath Value="../{file_name}" />
        <Path Value="{file_path}" />
        <BrowserContentPath Value="userfolder:{file_path}" />
    </SampleRef>
</AudioTrack>
"""

def find_flac_files(directory):
    """Finds and categorizes FLAC files into drums, Inst, and vocals."""
    flac_files = sorted([f for f in os.listdir(directory) if f.endswith(".flac")])

    return {
        "drums": next((f for f in flac_files if "drums" in f.lower()), None),
        "Inst": next((f for f in flac_files if "inst" in f.lower()), None),
        "vocals": next((f for f in flac_files if "vocals" in f.lower()), None),
    }

def clean_filename(filename):
    """Removes prefixes like 'drums-', 'Inst-', 'vocals-' to get the base track name."""
    return filename.replace(".flac", "") if filename else "Untitled"

def build_als_file(track_names, flac_folder):
    """Builds a brand new ALS file from scratch with proper tracks."""
    try:
        primary_track_name = clean_filename(track_names.get("drums") or track_names.get("Inst") or track_names.get("vocals"))
        output_als = os.path.join(flac_folder, f"{primary_track_name}.als")

        track_order = ["drums", "Inst", "vocals"]
        track_data = ""

        for i, track_type in enumerate(track_order):
            file_name = track_names.get(track_type)
            if file_name:
                file_path = os.path.join(flac_folder, file_name)
                track_name = file_name.replace(".flac", "")
                track_id = str(i + 1)

                track_data += TRACK_TEMPLATE.format(track_id=track_id, track_name=track_name, file_name=file_name, file_path=file_path)

        if not track_data:
            print("❌ No valid FLAC files found. ALS will remain empty.")
            return

        # Generate final ALS content
        final_als_content = ALS_TEMPLATE.format(track_data=track_data)

        # Save as gzip compressed ALS file
        with gzip.open(output_als, "wb") as f:
            f.write(final_als_content.encode("utf-8"))

        print(f"✅ Successfully created a new ALS: {output_als}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    track_names = find_flac_files(FLAC_FOLDER)
    if not any(track_names.values()):
        print("❌ No relevant FLAC files found in the folder!")
    else:
        build_als_file(track_names, FLAC_FOLDER)
        print("🎵 New ALS file created successfully!")
