
# Note: This file contains defaults. Modify per-user via ~/.crunner.json

editor = {
	"font": "monospace 11",
	"style": "solarized-dark",
	"language": "python",
	"styles": [
		"classic",
		"cobalt",
		"kate",
		"oblivion",
		"solarized-dark",
		"solarized-light",
		"tango"
	]
}

languages = {
	"c":{
		"mime": "text/x-c",
		"syntax": "c",
		"action": "gcc",
		"actions": {
			"gcc":[["gcc", "-xc", "-o", ".runner", "-"],["./.runner"]]
		},
		"clean": ".runner"
	},
	"python":{
		"mime": "text/x-python",
		"syntax": "python",
		"action": "python2",
		"actions": {
			"python":[["python"]],
			"python2":[["python2"]],
			"python3":[["python3"]]
		}
	},
	"javascript":{
		"mime": "text/plain",
		"syntax": "js",
		"action": "node",
		"actions": {"node":[["node"]]}
	}
}

# Load per-user configuration

import os, sys, json
userconfig = os.path.expanduser("~/.crunner.json")

sys.path.append(os.path.dirname(userconfig))
try:
	if not os.path.exists(userconfig):
		print("Creating default config...")
		with open(userconfig, "w") as fd:
			json.dump({"editor": editor, "languages":languages},fd, indent=2)
except:
	print("Error creating config...")

try:
	with open(userconfig, "r") as fd:
		to_load = json.load(fd)
		if 'languages' in to_load:
			for k,v in to_load['languages'].items():
				languages[k] = v
		if 'editor' in to_load:
			for k,v in to_load['editor'].items():
				editor[k] = v
except:
	print("Error loading config...")

