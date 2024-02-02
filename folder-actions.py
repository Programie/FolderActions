#! /usr/bin/env python3

import argparse
import importlib.util
import shutil
from pathlib import Path
from threading import Timer
from typing import Dict

import datetime
import re
import subprocess
import sys
import traceback

import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent, FileSystemMovedEvent, FileClosedEvent


class Config:
    def __init__(self, path: Path):
        self.data = {}

        if path.exists():
            with path.open("r") as config_file:
                self.data = yaml.safe_load(config_file)

    def get(self, name: str, default=None):
        name_parts = name.split(".")
        value = self.data

        for part in name_parts:
            if not isinstance(value, dict):
                return default

            value = value.get(part, default)

        return value


class Rule:
    def __init__(self, regex, target=None, validator=None, action=None):
        self.regex = regex
        self.target = target
        self.validator = validator
        self.action = action

    @classmethod
    def from_dict(cls, rule_dict: dict):
        return cls(rule_dict.get("regex"), rule_dict.get("target"), rule_dict.get("validator"), rule_dict.get("action"))


class FileHandler:
    def __init__(self, rules_path: Path, config: Config):
        self.rule_instance = []
        self.config = config

        for path_entry in rules_path.glob("*.py"):
            module_name = path_entry.name.removesuffix(".py")
            module_name = f"folder_actions.rule.{module_name}"

            spec = importlib.util.spec_from_file_location(module_name, path_entry)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            rule_instance = module.Rule()

            rule_instance.show_info = self.show_info
            rule_instance.source_target_info = self.source_target_info

            self.rule_instance.append(rule_instance)

    def show_info(self, action: str, filename: Path, string: str):
        now = datetime.datetime.now()
        print("[{}] {}: {}: {}".format(now, filename.name, action, string), file=sys.stderr)

        notify_script = self.config.get("notify_script")
        if notify_script is not None:
            subprocess.run(notify_script.format_map({
                "action": action,
                "filename": filename.name,
                "string": string
            }), shell=True)

    def source_target_info(self, action: str, source: Path, target: Path):
        self.show_info(action, source, "{} -> {}".format(source.name, target))

    def move_action(self, source: Path, target: Path):
        self.source_target_info("Moving file", source, target)

        shutil.move(source, target)

    def handle_file(self, file_path: Path):
        try:
            for rule_instance in self.rule_instance:
                for rule in rule_instance.get_rules():
                    rule = Rule.from_dict(rule)
                    match = re.match(rule.regex, file_path.name)
                    if match:
                        if self.handle_file_with_rule(rule, match, file_path):
                            return
        except BaseException:
            self.show_info("Exception occurred", file_path, traceback.format_exc())

    def handle_file_with_rule(self, rule: Rule, match: re.Match, file_path: Path):
        if rule.action is not None:
            action = rule.action
        else:
            action = self.move_action

        if rule.target is not None:
            if callable(rule.target):
                target = rule.target(file_path, match)
            else:
                target = rule.target

            if target is not None:
                file_placeholders = dict(self.config.get("placeholders", {}))
                file_placeholders["filename"] = file_path.name

                file_placeholders["re_0"] = match.group(0)
                for match_index, match_entry in enumerate(match.groups()):
                    file_placeholders["re_{}".format(match_index + 1)] = match_entry

                target = Path(target.format(**file_placeholders)).expanduser()
        else:
            target = None

        if target is None:
            return False

        if callable(action):
            action(file_path, target)

        if callable(rule.validator):
            rule.validator(file_path, target)

        self.manage_recent_files(file_path, target)

        return True

    def manage_recent_files(self, file_path: Path, target: Path):
        path = self.config.get("recent_files.path")
        if path is None:
            return

        path = Path(path).expanduser()

        if target.exists():
            symlink_file = path.joinpath(file_path.name)
            symlink_file.unlink(missing_ok=True)
            symlink_file.symlink_to(target)

        max_recent_files = self.config.get("recent_files.max_files")
        if max_recent_files:
            files = [file for file in path.iterdir() if file.exists()]
            files = [file for file in sorted(files, key=lambda file: file.stat().st_mtime, reverse=True)]

            for file in files[int(max_recent_files):]:
                if file.is_symlink():
                    file.unlink()


class WatchdogFilesystemHandler(FileSystemEventHandler):
    def __init__(self, file_handler: FileHandler, config: Config):
        super().__init__()

        self.file_handler = file_handler
        self.config = config
        self.queue: Dict[str, Timer] = {}

    def on_created(self, event: FileSystemEvent):
        if event.is_directory:
            return

        self.handle_file_with_delay(Path(event.src_path))

    def on_closed(self, event: FileClosedEvent):
        if event.is_directory:
            return

        self.handle_file_with_delay(Path(event.src_path))

    def on_moved(self, event: FileSystemMovedEvent):
        if event.is_directory:
            return

        self.handle_file_with_delay(Path(event.dest_path))

    def handle_file_with_delay(self, path: Path):
        if not path.exists() or not path.stat().st_size:
            return

        path_string = str(path)

        if path_string in self.queue:
            self.queue[path_string].cancel()

        self.queue[path_string] = Timer(self.config.get("filesystem_events.delay", 0.5), lambda: self.handle_file(path))
        self.queue[path_string].start()

    def handle_file(self, path: Path):
        if not path.exists():
            return

        self.file_handler.handle_file(path)

        path_string = str(path)

        if path_string in self.queue:
            del self.queue[path_string]


def main():
    arg_parser = argparse.ArgumentParser()

    mode_parser = arg_parser.add_subparsers(dest="mode", required=True)

    process_parser = mode_parser.add_parser("process")
    process_parser.add_argument("filename", nargs="+", type=Path, help="files to process")

    watch_parser = mode_parser.add_parser("watch")
    watch_parser.add_argument("path", type=Path, help="path to watch for changes")

    arguments = arg_parser.parse_args()

    config_path = Path("~/.config/folder-actions").expanduser()

    config = Config(config_path.joinpath("config.yml"))

    file_handler = FileHandler(config_path.joinpath("rules"), config)

    if arguments.mode == "process":
        for filename in arguments.filename:
            file_handler.handle_file(filename)
    elif arguments.mode == "watch":
        observer = Observer()
        observer.schedule(WatchdogFilesystemHandler(file_handler, config), arguments.path)
        observer.start()
        observer.join()


if __name__ == "__main__":
    main()
