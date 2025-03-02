import gzip
import xml.etree.ElementTree as ET
from io import BytesIO
import trackTime  # Import the trackTime module

# Input and output file paths
input_file = "/Users/alirahimlou/myapps/alsGenerator/70.als"
output_file = "/Users/alirahimlou/myapps/alsGenerator/70_modified.als"
flac_file = "drums-PHILDEL - The Wolf.flac"  # Path to your FLAC file

# Project BPM (needed to convert seconds to beats)
bpm = 70  # Adjust this to match your Ableton project’s tempo

# Step 1: Get the track duration from trackTime.py
try:
    duration_seconds = trackTime.get_track_duration(flac_file)
    print(f"FLAC Duration: {duration_seconds:.2f} seconds")
except Exception as e:
    print(f"Error getting duration: {e}")
    exit(1)

# Step 2: Convert duration from seconds to beats
# Beats = (seconds * BPM) / 60
duration_beats = (duration_seconds * bpm) / 60
new_loop_end = f"{duration_beats:.6f}"  # Format as string with 6 decimal places
print(f"Converted to {bpm} BPM: {new_loop_end} beats")

# Step 3: Read and decompress the .als file
with gzip.open(input_file, 'rb') as f_in:
    xml_content = f_in.read()

# Step 4: Parse the XML content
tree = ET.parse(BytesIO(xml_content))
root = tree.getroot()

# Step 5: Find and modify LoopEnd values
target_loop_end = "244.00005281177155"
modified_count = 0

# Iterate through all elements in the XML tree
for elem in root.iter():
    # Check if the element is <LoopEnd> with the target value
    if elem.tag == "LoopEnd" and elem.get("Value") == target_loop_end:
        # Modify the LoopEnd value to the FLAC duration in beats
        elem.set("Value", new_loop_end)
        modified_count += 1
        
        # Optional: Verify the surrounding block
        parent = elem.find("..")
        if (parent is not None and
            parent.find("./LoopStart[@Value='0']") is not None and
            parent.find("./StartRelative[@Value='0']") is not None and
            parent.find("./LoopOn[@Value='false']") is not None and
            parent.find("./OutMarker[@Value='244.00005281177155']") is not None and
            parent.find("./HiddenLoopStart[@Value='0']") is not None and
            parent.find("./HiddenLoopEnd[@Value='4']") is not None):
            print(f"Found and modified a matching block at {ET.tostring(parent, encoding='unicode')[:100]}...")

# Step 6: Write the modified XML back to a gzipped file
with gzip.open(output_file, 'wb') as f_out:
    tree.write(f_out, encoding="utf-8", xml_declaration=True)

# Step 7: Report the result
print(f"Modified {modified_count} <LoopEnd> elements from {target_loop_end} to {new_loop_end}")
print(f"Output saved to {output_file}")