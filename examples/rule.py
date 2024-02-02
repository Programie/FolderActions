# This rule file will look for two files: `some-file.txt` and `another-file.json`.
#
# In case it finds `some-file.txt`, it will move it to `~/target-dir/some-file.txt` without changing anything of it.
#
# In case it finds `another-file.json`, it will read the file as JSON and write the JSON pretty-printed (i.e. indented with two spaces) to the target file. After that, it will remove the source file.

import json
import os


class Rule:
    def get_rules(self):
        return [
            dict(regex=r"^some-file.txt$", target="~/target-dir/some-file.txt"),
            dict(regex=r"^another-file.json$", target="~/some-dir/another-file.json", action=self.prettyprint_json_action)
        ]

    def prettyprint_json_action(self, filename, target):
        self.source_target_info("Writing JSON", filename, target)

        with open(filename, "r") as input_file:
            with open(target, "w") as output_file:
                json.dump(json.load(input_file), output_file, indent=2, sort_keys=True)

        os.remove(filename)
