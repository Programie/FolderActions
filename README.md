# Folder Actions

Folder Actions is a script which executes actions for files in a specific folder (like your downloads folder) and is able to move and sort them based on defined rules.

Each rule is a Python script defining a `Rule` class which then does whatever you want it to do.

At the heart, it uses [watchdog](https://pypi.org/project/watchdog/) to observe the specified directory and wait for events. Once a new file has been saved into the watched directory, the configured rules will be checked. If a rule matches, the rule will be executed for that file.

## Installation

* Clone this repository into any directory
* Install the requirements using pip: `pip install -r requirements.txt`
* Define your rules (see bellow)
* Execute `folder-actions.py watch /path/to/watch`

## Configuration

The main configuration is done using a file in YAML format. The configuration should be stored at `~/.config/folder-actions/config.yml`.

Take a look at the [example config.yml](examples/config.yml).

## Defining rules

The script looks into `~/.config/folder-actions/rules` and loads any Python script. Each script should contain a `Rule` class containing at least a `get_rules()` method returning a list of paths to match.

Take a look into the [examples](examples) folder for some example rule files as well as the [Rule class structure](examples/rule_structure.py).