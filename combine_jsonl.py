import json
from pathlib import Path
import shutil
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('combine_jsonl.log'),
        logging.StreamHandler()
    ]
)

def split_json_objects(line):
    """
    Splits a string containing multiple JSON objects into individual objects.
    
    Args:
        line (str): String potentially containing multiple JSON objects
    Returns:
        list: List of valid JSON strings
    """
    line = line.strip()
    if not line:
        return []
    
    # Try parsing as single JSON object first
    try:
        json.loads(line)
        return [line]
    except json.JSONDecodeError:
        pass
    
    # Handle multiple JSON objects
    json_objects = []
    current_object = ""
    bracket_count = 0
    
    for char in line:
        current_object += char
        if char == '{':
            bracket_count += 1
        elif char == '}':
            bracket_count -= 1
            if bracket_count == 0:
                try:
                    json.loads(current_object)
                    json_objects.append(current_object)
                    current_object = ""
                except json.JSONDecodeError:
                    logging.warning(f"Invalid JSON object found: {current_object}")
    
    return json_objects

def combine_jsonl_files(input_dir, output_file):
    """
    Combines all JSONL files from the input directory into a single output file,
    extracting only the 'text' field from each JSON object. Excludes files in
    specified subdirectories.
    
    Args:
        input_dir (str): Path to directory containing JSONL files
        output_file (str): Path to output file
    """
    input_path = Path(input_dir)
    output_path = Path(output_file)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if output_path.exists():
        backup_path = output_path.with_suffix('.jsonl.bak')
        shutil.copy2(output_path, backup_path)
        logging.info(f"Created backup: {backup_path}")
    
    excluded_dirs = ["log", "testing"]
    logging.info(f"Excluding subdirectories: {', '.join(excluded_dirs)}")
    
    processed_files = 0
    total_lines = 0
    problem_lines = 0
    skipped_objects = 0
    skipped_files = 0
    
    with open(output_path, 'w', encoding='utf-8') as outfile:
        for jsonl_file in input_path.glob('**/*.jsonl'):
            rel_parts = jsonl_file.relative_to(input_path).parts[:-1]
            if any(part in excluded_dirs for part in rel_parts):
                logging.info(f"Skipping file in excluded subdirectory: {jsonl_file}")
                skipped_files += 1
                continue
            
            try:
                with open(jsonl_file, 'r', encoding='utf-8') as infile:
                    for line_num, line in enumerate(infile, 1):
                        json_objects = split_json_objects(line)
                        
                        if not json_objects:
                            problem_lines += 1
                            logging.warning(f"No valid JSON objects in line {line_num} of {jsonl_file}")
                            continue
                        
                        for json_str in json_objects:
                            try:
                                data = json.loads(json_str)
                                if 'text' in data:
                                    new_data = {'text': data['text']}
                                    outfile.write(json.dumps(new_data) + '\n')
                                    total_lines += 1
                                else:
                                    skipped_objects += 1
                                    logging.warning(f"No 'text' key in object from {jsonl_file}, line {line_num}: {json_str}")
                            except json.JSONDecodeError:
                                logging.error(f"Unexpected error: Invalid JSON in {jsonl_file}, line {line_num}: {json_str}")
                
                processed_files += 1
                logging.info(f"Processed: {jsonl_file}")
            except Exception as e:
                logging.error(f"Error processing {jsonl_file}: {e}")
    
    logging.info("\nSummary:")
    logging.info(f"Processed files: {processed_files}")
    logging.info(f"Total extracted texts: {total_lines}")
    logging.info(f"Lines with no valid JSON: {problem_lines}")
    logging.info(f"JSON objects without 'text': {skipped_objects}")
    logging.info(f"Files skipped due to excluded subdirectories: {skipped_files}")
    logging.info(f"Combined file saved to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        input_dir = "data"
        output_file = "training-data.jsonl"
        logging.info(f"Using default input_dir='{input_dir}' and output_file='{output_file}'")
    elif len(sys.argv) == 3:
        input_dir = sys.argv[1]
        output_file = sys.argv[2]
    else:
        print(f"Usage: python {sys.argv[0]} [input_dir output.jsonl]")
        sys.exit(1)

    combine_jsonl_files(input_dir, output_file)
