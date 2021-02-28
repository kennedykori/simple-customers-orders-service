from unittest import TestCase

from ..enums import Choices


# Helpers

class Status(Choices):
    """
    Dummy sample class.
    """
    pending = ('P', 'PENDING')
    approved = ('A', 'APPROVED')
    rejected = ('R', 'REJECTED')


# TestCases

class ChoicesTests(TestCase):
    """
    Tests for the `Choices` enum.
    """

    def test_get_choice_name(self):
        # Assert that we get the correct value
        self.assertEqual(Status.get_choice_name('P'), 'PENDING')
        self.assertEqual(Status.get_choice_name('A'), 'APPROVED')

        # Assert that StopIteration is raised when a value not belonging to
        # any of the choices in the enum is passed
        self.assertRaises(StopIteration, Status.get_choice_name, 'S')
        self.assertRaises(StopIteration, Status.get_choice_name, None)
        self.assertRaises(StopIteration, Status.get_choice_name, 6)

    def test_get_value(self):
        # Assert that we get the correct value
        self.assertEqual(Status.get_value('pending'), 'P')
        self.assertEqual(Status.get_value('rejected'), 'R')

        # Assert that a KeyError is raised when a value that isn't a member of
        # the enum is given
        self.assertRaises(KeyError, Status.get_value, 'created')
        self.assertRaises(KeyError, Status.get_value, '')
        self.assertRaises(KeyError, Status.get_value, None)
        self.assertRaises(KeyError, Status.get_value, 7)

    def test_to_list(self):
        # Assert that we get the correct value
        self.assertListEqual(
            Status.to_list(),
            [
                ('P', 'PENDING'),
                ('A', 'APPROVED'),
                ('R', 'REJECTED')
            ]
        )
