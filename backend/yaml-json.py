import yaml
import json

data = {
    "name": "baka",
    "age": 22,
    "language": ["python", "java"],
    "class":
        [{
            "name": "baka",
            "age": 22,
            "language": ["python", "java"],
        },
        {
            "name": "baka",
            "age": 22,
            "language": ["python", "java"],
        }
        ]
}

json_string = json.dumps(data, indent=2)
print(json_string)

data2 = json.loads(json_string)

with open("data.json", "w") as f:
    json.dump(data2, f, indent=2)

with open("data.json", "r") as f:
    data = json.load(f)

yaml_text = yaml.dump(data, sort_keys=False, default_flow_style=False)

print(yaml_text)

data3 = yaml.safe_load(yaml_text)

with open("config.yaml", "w") as f:
    yaml.dump(data, f, sort_keys=False, default_flow_style=False)

with open("config.yaml", "r") as f:
    data = yaml.safe_load(f)