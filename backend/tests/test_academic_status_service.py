"""
Automated unit tests for VCIS 3.0 Academic Status Service (academic_status_service.py).

Validates the frozen academic status rules:
- NORMAL: predicted_final_semester_score >= 60.0
- MONITOR: 50.0 <= predicted_final_semester_score < 60.0
- INTERVENTION: predicted_final_semester_score < 50.0

Validation and safety:
- Rejection of NaN, +inf, -inf
- Rejection of booleans (True, False)
- Rejection of non-numeric types (str, None, list, dict)
- Exact boundary precision (no premature rounding or clamping)
- Zero database dependency
"""

import math
import sys
import unittest

# Ensure app imports resolve cleanly
sys.path.insert(0, "backend")

from app.services.academic_status_service import (
    AcademicStatus,
    InvalidScoreError,
    get_academic_status,
)


class TestAcademicStatusService(unittest.TestCase):
    """Unit test suite for the academic status classification service."""

    # ==================================================================
    # 1. Classification Tests Across Categories
    # ==================================================================

    def test_01_score_60_classifies_as_normal(self):
        """Verify boundary score 60.0 returns NORMAL."""
        status = get_academic_status(60)
        self.assertEqual(status, AcademicStatus.NORMAL)
        status_float = get_academic_status(60.0)
        self.assertEqual(status_float, AcademicStatus.NORMAL)

    def test_02_score_75_classifies_as_normal(self):
        """Verify standard passing score 75 returns NORMAL."""
        status = get_academic_status(75)
        self.assertEqual(status, AcademicStatus.NORMAL)
        status_float = get_academic_status(75.5)
        self.assertEqual(status_float, AcademicStatus.NORMAL)

    def test_03_score_59_99_classifies_as_monitor(self):
        """Verify boundary score 59.99 returns MONITOR."""
        status = get_academic_status(59.99)
        self.assertEqual(status, AcademicStatus.MONITOR)

    def test_04_score_50_classifies_as_monitor(self):
        """Verify lower boundary score 50.0 returns MONITOR."""
        status = get_academic_status(50)
        self.assertEqual(status, AcademicStatus.MONITOR)
        status_float = get_academic_status(50.0)
        self.assertEqual(status_float, AcademicStatus.MONITOR)

    def test_05_score_55_classifies_as_monitor(self):
        """Verify mid-range score 55 returns MONITOR."""
        status = get_academic_status(55)
        self.assertEqual(status, AcademicStatus.MONITOR)
        status_float = get_academic_status(55.25)
        self.assertEqual(status_float, AcademicStatus.MONITOR)

    def test_06_score_49_99_classifies_as_intervention(self):
        """Verify upper boundary score 49.99 returns INTERVENTION."""
        status = get_academic_status(49.99)
        self.assertEqual(status, AcademicStatus.INTERVENTION)

    def test_07_score_0_classifies_as_intervention(self):
        """Verify lowest possible percentage 0 returns INTERVENTION."""
        status = get_academic_status(0)
        self.assertEqual(status, AcademicStatus.INTERVENTION)
        status_float = get_academic_status(0.0)
        self.assertEqual(status_float, AcademicStatus.INTERVENTION)

    def test_08_score_100_classifies_as_normal(self):
        """Verify maximum percentage 100 returns NORMAL."""
        status = get_academic_status(100)
        self.assertEqual(status, AcademicStatus.NORMAL)
        status_float = get_academic_status(100.0)
        self.assertEqual(status_float, AcademicStatus.NORMAL)

    # ==================================================================
    # 2. Rejection of Invalid Numeric Values (NaN, Infinity)
    # ==================================================================

    def test_09_nan_rejected(self):
        """Verify NaN input raises InvalidScoreError."""
        with self.assertRaises(InvalidScoreError):
            get_academic_status(float("nan"))
        with self.assertRaises(InvalidScoreError):
            get_academic_status(math.nan)

    def test_10_positive_infinity_rejected(self):
        """Verify +inf input raises InvalidScoreError."""
        with self.assertRaises(InvalidScoreError):
            get_academic_status(float("inf"))
        with self.assertRaises(InvalidScoreError):
            get_academic_status(math.inf)

    def test_11_negative_infinity_rejected(self):
        """Verify -inf input raises InvalidScoreError."""
        with self.assertRaises(InvalidScoreError):
            get_academic_status(float("-inf"))
        with self.assertRaises(InvalidScoreError):
            get_academic_status(-math.inf)

    # ==================================================================
    # 3. Rejection of Non-Numeric & Boolean Types
    # ==================================================================

    def test_12_boolean_input_rejected(self):
        """
        Verify booleans are rejected even though bool is a subclass of int in Python.
        """
        with self.assertRaises(InvalidScoreError):
            get_academic_status(True)
        with self.assertRaises(InvalidScoreError):
            get_academic_status(False)

    def test_13_invalid_string_rejected(self):
        """Verify string inputs are rejected cleanly without silent conversion."""
        invalid_strings = ["abc", "60", "60.0", "", "   ", "True"]
        for s in invalid_strings:
            with self.assertRaises(InvalidScoreError):
                get_academic_status(s)

    def test_14_non_numeric_objects_rejected(self):
        """Verify None, list, dict, and tuple inputs raise InvalidScoreError."""
        invalid_objects = [None, [60.0], {"score": 60.0}, (60.0,)]
        for obj in invalid_objects:
            with self.assertRaises(InvalidScoreError):
                get_academic_status(obj)

    # ==================================================================
    # 4. Status Values & Enum Invariants
    # ==================================================================

    def test_15_status_values_are_exact_enum_members(self):
        """
        Verify AcademicStatus contains exactly the three frozen members:
        NORMAL, MONITOR, INTERVENTION.
        """
        members = set(AcademicStatus.__members__.keys())
        expected_members = {"NORMAL", "MONITOR", "INTERVENTION"}
        self.assertEqual(members, expected_members)

        values = {status.value for status in AcademicStatus}
        self.assertEqual(values, {"NORMAL", "MONITOR", "INTERVENTION"})

    # ==================================================================
    # 5. Boundary Precision & No Premature Rounding
    # ==================================================================

    def test_16_no_rounding_before_classification(self):
        """
        Prove that scores approaching boundaries are NOT rounded before classification:
        - 59.999 must remain MONITOR (must NOT round up to 60.0 / NORMAL)
        - 49.999 must remain INTERVENTION (must NOT round up to 50.0 / MONITOR)
        - 50.0001 must remain MONITOR
        - 60.0001 must remain NORMAL
        """
        # Close to 60 boundary
        self.assertEqual(get_academic_status(59.999), AcademicStatus.MONITOR)
        self.assertEqual(get_academic_status(59.999999), AcademicStatus.MONITOR)
        self.assertEqual(get_academic_status(60.0), AcademicStatus.NORMAL)
        self.assertEqual(get_academic_status(60.000001), AcademicStatus.NORMAL)

        # Close to 50 boundary
        self.assertEqual(get_academic_status(49.999), AcademicStatus.INTERVENTION)
        self.assertEqual(get_academic_status(49.999999), AcademicStatus.INTERVENTION)
        self.assertEqual(get_academic_status(50.0), AcademicStatus.MONITOR)
        self.assertEqual(get_academic_status(50.000001), AcademicStatus.MONITOR)


if __name__ == "__main__":
    unittest.main()
