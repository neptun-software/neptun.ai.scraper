import json
import sys

if len(sys.argv) != 3:
    print("Usage: python script.py input.jsonl output.jsonl")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
    for line in infile:
        try:
            data = json.loads(line)
            if 'text' in data:
                new_data = {'text': data['text']}
                outfile.write(json.dumps(new_data) + '\n')
        except json.JSONDecodeError:
            print(f"Skipping invalid JSON line: {line}")

"""
python to-training-data-only.py input.jsonl output.jsonl
"""
