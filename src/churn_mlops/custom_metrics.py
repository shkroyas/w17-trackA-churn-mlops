"""A real Evidently extension, rather than a number placed beside a report."""

from evidently.core.metric_types import SingleValueCalculation, SingleValueMetric
from evidently.tests import lt


class MeanChargeShift(SingleValueMetric):
    def _default_tests_with_reference(self, context):
        return [lt(15.0).bind_single(self.get_fingerprint())]


class MeanChargeShiftCalculation(SingleValueCalculation[MeanChargeShift]):
    def calculate(self, context, current_data, reference_data):
        if reference_data is None:
            raise ValueError("Reference data required")
        a = current_data.column("MonthlyCharges").data.mean()
        b = reference_data.column("MonthlyCharges").data.mean()
        return self.result(float(abs(a - b)))

    def display_name(self):
        return "Absolute mean MonthlyCharges shift (USD)"
