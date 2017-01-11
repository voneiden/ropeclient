import re
import random
import json
MAX_DICES = 100
MAX_SIDES = 1000


class Dice(object):
    # Match complete dice commands
    __roll_pattern = re.compile("!(?:[+-]?(?:\d*d)?\d+)+", re.IGNORECASE)

    # Match all individual operations in a command
    __dice_pattern = re.compile("([+-])?(?:(\d+)?(d))?(\d+)", re.IGNORECASE)

    @classmethod
    def find_and_roll(cls, text, exploding=False):
        """
        Searches the text for dice patterns and rolls em like a boss
        :param text:
        :param exploding:
        :return: text with the roll command replaced by results
        """
        # exploding TODO
        return re.sub(cls.__roll_pattern, cls.__roll_sub, text)

    @classmethod
    def __roll_sub(cls, match, exploding=False):
        operations = re.findall(cls.__dice_pattern, match.group())
        operation_results = [cls.__dice(operation) for operation in operations]
        results = {
            "roll": match.group(),
            "results": operation_results
        }
        return "${{dice:{results}}}".format(results=json.dumps(results))

    @classmethod
    def __dice(cls, operation, exploding=False):
        """
        :param operation:
         [0]: None, + or -
         [1]: None or string representing number of dices
         [2]: None if not a roll or "d" if a roll
         [3]: String representing either sides of dices or just a constant number
        :return: list of result values
        """
        multiplier = -1 if operation[0] == "-" else 1

        # Dice rolls
        if operation[2]:
            dices = int(operation[1])
            sides = int(operation[3])
            if dices < 1 or sides < 2 or MAX_DICES > 100 or MAX_SIDES > 1000:
                return False
            else:
                return [multiplier * random.randint(1, sides) for dice in range(dices)]

        # Regular numbers
        else:
            return multiplier * int(operation[3])




