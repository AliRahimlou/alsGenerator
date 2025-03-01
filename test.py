import os
import shutil
import gzip
import re

# 🛠 CONFIG: Paths
BLANK_ALS_PATH = "Untitled.als"
FLAC_FOLDER = "/Users/alirahimlou/Desktop/test-music"

def find_flac_files(directory):
    """Find .flac files and categorize them into drums, Inst, and vocals."""
    flac_files = sorted([f for f in os.listdir(directory) if f.endswith(".flac")])
    
    track_names = {
        "drums": next((f for f in flac_files if "drums" in f.lower()), None),
        "Inst": next((f for f in flac_files if "inst" in f.lower()), None),
        "vocals": next((f for f in flac_files if "vocals" in f.lower()), None),
    }
    
    print("🔍 New FLAC files found in folder:", track_names)
    return track_names

def clean_filename(filename):
    """Remove 'drums-', 'Inst-', 'vocals-' from filename and keep the main part."""
    if filename:
        return re.sub(r'^(drums-|Inst-|vocals-)', '', filename, flags=re.IGNORECASE).replace('.flac', '')
    return "Modified"

def get_original_flac_references(als_data, display_names):
    """Extract and categorize FLAC file references from the ALS file."""
    als_str = als_data.decode("latin1", errors="ignore")
    # Broad regex to catch all .flac references, quoted or unquoted
    flac_matches = set(re.findall(r'[^\s<>"]*?\.flac', als_str))
    
    if not flac_matches:
        print("⚠️ No FLAC matches found. First 1000 chars of ALS:", als_str[:1000])
    
    # Categorize based on keywords or display names
    categorized = {
        "drums": [],
        "Inst": [],
        "vocals": []
    }
    
    for match in flac_matches:
        if '.flac' in match:
            clean_match = match.split('#')[-1].replace('%20', ' ').lower()
            if "drums" in clean_match:
                categorized["drums"].append(match)
            elif "inst" in clean_match:
                categorized["Inst"].append(match)
            elif "vocals" in clean_match:
                categorized["vocals"].append(match)
            else:
                # Use display names to infer category for partial matches
                for attr in display_names:
                    for name in display_names[attr]:
                        name_lower = name.lower()
                        if clean_match in name_lower:
                            if "drums" in name_lower:
                                categorized["drums"].append(match)
                            elif "inst" in name_lower:
                                categorized["Inst"].append(match)
                            elif "vocals" in name_lower:
                                categorized["vocals"].append(match)
                            break
    
    # Pick one representative for base mapping
    base_refs = {
        "drums": categorized["drums"][0] if categorized["drums"] else None,
        "Inst": categorized["Inst"][0] if categorized["Inst"] else None,
        "vocals": categorized["vocals"][0] if categorized["vocals"] else None
    }
    
    print("🔍 All FLAC matches in ALS:", flac_matches)
    print("🔍 Categorized FLAC references in ALS:", categorized)
    print("🔍 Base references for mapping:", base_refs)
    return categorized, base_refs, als_str, flac_matches

def get_display_names(als_str):
    """Extract display names from the ALS file."""
    display_names = {}
    for attr in ["MemorizedFirstClipName", "UserName", "Name", "EffectiveName"]:
        matches = re.findall(rf'<{attr} Value="([^"]+)"', als_str)
        if matches:
            display_names[attr] = matches
    print("🔍 Display names found in ALS:", display_names)
    return display_names

def modify_als_file(input_path, flac_folder, track_names):
    """Loads a working .als file, modifies track names & FLAC references, and saves with a new name."""
    try:
        # Generate output ALS name from the new track name
        primary_track_name = clean_filename(track_names.get("drums") or track_names.get("Inst") or track_names.get("vocals"))
        output_als = os.path.join(flac_folder, f"{primary_track_name}.als")

        # Make a copy of the blank ALS to modify
        shutil.copy(input_path, output_als)

        # Read ALS file as binary (gzip compressed)
        with gzip.open(output_als, "rb") as f:
            als_data = f.read()

        # Get display names first for categorization
        als_str = als_data.decode("latin1", errors="ignore")
        display_names = get_display_names(als_str)

        # Get original FLAC references and ALS string
        categorized_flacs, base_refs, als_str, all_flac_matches = get_original_flac_references(als_data, display_names)

        if not all_flac_matches:
            print("❌ No FLAC references found in ALS file. Aborting.")
            return

        # Create a list of new FLAC files in order (drums, Inst, vocals)
        new_flacs = [track_names["drums"], track_names["Inst"], track_names["vocals"]]
        new_flacs = [f for f in new_flacs if f]  # Remove None

        # Build base replacement mapping
        replacements = {}
        for key in ["drums", "Inst", "vocals"]:
            if base_refs[key] and track_names[key]:
                replacements[base_refs[key]] = track_names[key]

        # Fallback: Map all matches if base refs are empty or incomplete
        if not replacements or len(replacements) < 3:
            print("⚠️ Incomplete base replacements. Mapping all FLAC matches.")
            for match in all_flac_matches:
                clean_match = match.split('#')[-1].replace('%20', ' ')
                matched = False
                for key, new in track_names.items():
                    if key in clean_match.lower():
                        replacements[match] = new
                        matched = True
                        break
                if not matched:
                    # Use display names for partial matches
                    for attr in display_names:
                        for name in display_names[attr]:
                            name_lower = name.lower()
                            if clean_match in name_lower:
                                if "drums" in name_lower:
                                    replacements[match] = track_names["drums"]
                                elif "inst" in name_lower:
                                    replacements[match] = track_names["Inst"]
                                elif "vocals" in name_lower:
                                    replacements[match] = track_names["vocals"]
                                matched = True
                                break
                        if matched:
                            break
        
        if not replacements:
            print("❌ No valid FLAC replacements found. Forcing replacements with display name mapping.")
            # Force mapping based on display names
            for attr in display_names:
                for name in display_names[attr]:
                    name_lower = name.lower()
                    if "drums" in name_lower:
                        replacements[name + '.flac'] = track_names["drums"]
                    elif "inst" in name_lower:
                        replacements[name + '.flac'] = track_names["Inst"]
                    elif "vocals" in name_lower:
                        replacements[name + '.flac'] = track_names["vocals"]

        print("🔄 Base replacement mapping:", replacements)

        # Extend replacements to cover all variations
        all_replacements = {}
        for old, new in replacements.items():
            new_simple = new  # Use just the filename
            all_replacements[old] = new_simple
            # Replace all categorized matches
            for category in categorized_flacs:
                if category in old.lower():
                    for variant in categorized_flacs[category]:
                        all_replacements[variant] = new_simple

        # Replace all .flac references explicitly in key tags
        for old, new in replacements.items():
            als_str = re.sub(
                rf'(<(?:RelativePath|Path|BrowserContentPath)\s+[^>]*Value=")[^"]*?{re.escape(old.split('#')[-1].replace('%20', ' '))}[^"]*?("[^>]*>)',
                rf'\1{new}\2',
                als_str
            )
            all_replacements[old] = new

        # Replace all remaining .flac matches
        for match in all_flac_matches:
            if match not in all_replacements:
                clean_match = match.split('#')[-1].replace('%20', ' ')
                for key, new in track_names.items():
                    if key in clean_match.lower():
                        all_replacements[match] = new
                        als_str = re.sub(
                            rf'(<(?:RelativePath|Path|BrowserContentPath)\s+[^>]*Value=")[^"]*?{re.escape(clean_match)}[^"]*?("[^>]*>)',
                            rf'\1{new}\2',
                            als_str
                        )
                        break

        print("🔄 Full replacement mapping:", all_replacements)

        # Fix display names
        for old_flac, new_flac in replacements.items():
            old_name = old_flac.split('#')[-1].replace('%20', ' ').replace('.flac', '')  # Extract base name
            new_name = new_flac.replace('.flac', '')
            
            for attr, names in display_names.items():
                for name in names:
                    if old_name in name:
                        new_display_name = name.replace(old_name, new_name)
                        pattern = rf'(<{attr} Value="){re.escape(name)}("[^>]*>)'
                        replacement = rf'\1{new_display_name}\2'
                        if re.search(pattern, als_str):
                            als_str = re.sub(pattern, replacement, als_str)
                            print(f"🔧 Replaced {attr}: '{name}' -> '{new_display_name}'")

        # Debug: Log remaining .flac references and snippet
        remaining_flacs = set(re.findall(r'[^\s"]*?\.flac', als_str))
        print("🔍 Remaining FLAC references after replacement:", remaining_flacs)
        flac_locations = [m.start() for m in re.finditer(r'\.flac', als_str)]
        flac_snippet = "\n".join([als_str[max(0, i-50):i+50] for i in flac_locations]) if flac_locations else "No FLACs found"
        print("🔍 Snippet of modified ALS with FLAC references:", flac_snippet)

        # Convert back to binary and save
        modified_data = als_str.encode("latin1", errors="ignore")
        with gzip.open(output_als, "wb") as f:
            f.write(modified_data)

        print(f"✅ Final modified ALS saved at: {output_als}")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    track_names = find_flac_files(FLAC_FOLDER)
    if not any(track_names.values()):
        print("❌ No relevant FLAC files found in the folder!")
    else:
        modify_als_file(BLANK_ALS_PATH, FLAC_FOLDER, track_names)
        print("🎵 Modified ALS file created successfully!")