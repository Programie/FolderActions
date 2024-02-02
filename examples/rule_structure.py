# This file describes the structure of the Rule class.
# Do NOT use this file as an actual rule as it overwrites some internal methods which should not be overwritten by your Rule class!
#
# Take a look at the other examples in this folder.

from pathlib import Path


class Rule:
    def get_rules(self) -> list[dict]:
        """
        Returns a list of rules to be used.

        Each rule element should be a dict containing the following properties:
        * regex: A regex which will be used to match against the checked filename
        * target: The target path to which the file should be moved to (if no other action has been defined), might contain placeholders
        * action: A callable function which will accept two parameters (input file path and the target property with resolved placeholders)

        The target property accepts some placeholders in the format of "{placeholdername}". The following placeholders can be used:
        * filename: The file name without path of the checked file
        * re_*: A captured group from the rule regex (re_0 will contain the full regex match, re_1 will contain the first group, etc.)

        You might also define any placeholders in the ~/.config/folder-actions/config.yml.
        """
        pass

    # The following methods are available to be called by your rule, but you should not overwrite them.

    @staticmethod
    def show_info(action: str, filename: Path, string: str) -> None:
        """
        Show an info message to the user (by logging it and executing the notify script).

        :param action: The action title understandable to the user (i.e. "Moving file", "Extracting archive" or "Uploading file")
        :param filename: The input file being processed
        :param string: The message to be shown to the user
        """
        pass

    def source_target_info(self, action: str, source: Path, target: Path) -> None:
        """
        Show an info message to the user about progressing the file from source to target.

        This is similar to the `show_info()` method but uses the source and target parameters to build the message.

        :param action: The action title understandable to the user (i.e. "Moving file", "Extracting archive" or "Uploading file")
        :param source: The input file being processed
        :param target: The output file of the action
        """
        pass
