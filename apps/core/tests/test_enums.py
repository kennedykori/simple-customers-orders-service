from unittest import TestCase

from ..enums import Choices


# Helpers

class Status(Choices):
    """
    Dummy sample class.
    """
    PENDING = ('P', 'PENDING')
    APPROVED = ('A', 'APPROVED')
    REJECTED = ('R', 'REJECTED')


# TestCases

class ChoicesTests(TestCase):
    """
    Tests for the `Choices` enum.
    """

    def test_choice_display(self):
        self.assertEqual(Status.APPROVED.choice_display, 'APPROVED')
        self.assertEqual(Status.PENDING.choice_display, 'PENDING')
        self.assertEqual(Status.REJECTED.choice_display, 'REJECTED')

    def test_choice_value(self):
        self.assertEqual(Status.APPROVED.choice_value, 'A')
        self.assertEqual(Status.PENDING.choice_value, 'P')
        self.assertEqual(Status.REJECTED.choice_value, 'R')

    def test_get_choice_name(self):
        # Assert that we get the correct value
        self.assertEqual(Status.get_choice_display('P'), 'PENDING')
        self.assertEqual(Status.get_choice_display('A'), 'APPROVED')

        # Assert that StopIteration is raised when a value not belonging to
        # any of the choices in the enum is passed
        self.assertRaises(StopIteration, Status.get_choice_display, 'S')
        self.assertRaises(StopIteration, Status.get_choice_display, None)
        self.assertRaises(StopIteration, Status.get_choice_display, 6)

    def test_get_value(self):
        # Assert that we get the correct value
        self.assertEqual(Status.get_choice_value('PENDING'), 'P')
        self.assertEqual(Status.get_choice_value('REJECTED'), 'R')

        # Assert that a KeyError is raised when a value that isn't a member of
        # the enum is given
        self.assertRaises(KeyError, Status.get_choice_value, 'CREATED')
        self.assertRaises(KeyError, Status.get_choice_value, '')
        self.assertRaises(KeyError, Status.get_choice_value, None)
        self.assertRaises(KeyError, Status.get_choice_value, 7)

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
