import json


def load_json(input_file) -> dict:
    with open(input_file, 'r') as f:
        return json.load(f)


def dump_json(output_file, data):
    with open(output_file, 'w') as f:
        json.dump(data, f)
