import json

with open("config/config.json", "r") as f:
    config_data = json.load(f)


try:
    perms = config_data["default-permissions"]["usr"]
except KeyError:
    perms = config_data["default-permissions"]["fallback"]

print(perms)