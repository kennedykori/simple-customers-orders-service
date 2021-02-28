from enum import Enum
from typing import List, Tuple


class Choices(Enum):
    """
    This class defines `django.db.models.fields.Field` choices as an
    enumeration.
    """

    @classmethod
    def get_choice_name(cls, value: str) -> str:
        """
        Given the value of a choice, return the choice's human readable name.
        A `StopIteration` is raised if the given value doesn't belong to any
        choice in this enum.

        :param value: The value of a choice.

        :return: the human readable name of a choice with the given value.

        :raise StopIteration: If the given value doesn't belong to any choice
        in this enum.
        """
        return next(x.value[1] for x in cls if x.value[0] == value)

    @classmethod
    def get_value(cls, choice: str) -> str:
        """
        Given a choice in this enum, return the choice's value. Will raise a
        `KeyError` if the given choice is not a valid member of this enum.

        :param choice: A choice in this enum.

        :return: the value of the given choice.

        :raise KeyError: If the given choice is not a valid member of this enum.
        """
        return cls[choice].value[0]

    @classmethod
    def to_list(cls) -> List[Tuple[str, str]]:
        """
        Returns a `list` of all the choices in this enum.

        :return: a list of all the choices in this enum.
        """
        return [member.value for member in cls]
