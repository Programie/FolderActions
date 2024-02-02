# Folder Actions

Folder Actions is a script which executes actions for files in a specific folder (like your downloads folder) and is able to move and sort them based on defined rules.

Each rule is a Python script defining a `Rule` class which then does whatever you want it to do.

At the heart, it uses [watchdog](https://pypi.org/project/watchdog/) to observe the specified directory and wait for events. Once a new file has been saved into the watched directory, the configured rules will be checked. If a rule matches, the rule will be executed for that file.

## Defining rules

The script looks into `~/.config/folder-actions/rules` and loads any Python script. Each script should contain a `Rule` class containing at least a `get_rules()` method returning a list of paths to match.

### Example rule script

```python
import json
import os


class Rule:
    def get_rules(self):
        return [
            dict(regex=r"^some-file.txt$", target="~/target-dir/some-file.txt"),
            dict(regex=r"^another-file.json$", target="~/some-dir/another-file.json", action=self.prettyprint_json_action)
        ]

    def prettyprint_json_action(self, filename, target):
        with open(filename, "r") as input_file:
            with open(target, "w") as output_file:
                json.dump(json.load(input_file), output_file, indent=2, sort_keys=True)

        os.remove(filename)
```

With that rule, Folder Actions will look for two files: `some-file.txt` and `another-file.json`.

In case it finds `some-file.txt`, it will move it to `~/target-dir/some-file.txt` without changing anything of it.

In case it finds `another-file.json`, it will read the file as JSON and write the JSON pretty-printed (i.e. indented with two spaces) to the target file. After that, it will remove the source file.