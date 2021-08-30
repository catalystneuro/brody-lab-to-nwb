"""Authors: Cody Baker."""
from nwb_conversion_tools import (
    NWBConverter,
    NeuralynxRecordingInterface,
    SpikeGLXRecordingInterface,
    SpikeGLXLFPInterface,
    SpikeGadgetsRecordingInterface,
)

from .msortedprocesseddatainterface import MSortedProcessedInterface
from .msortedsortinginterface import MSortedSortingInterface


class PoissonClicksNWBConverter(NWBConverter):
    """Primary conversion class for the SpikeGLX formatted Brody lab data."""

    data_interface_classes = dict(
        SpikeGLXRecording=SpikeGLXRecordingInterface,
        SpikeGLXLFP=SpikeGLXLFPInterface,
        ProcessedBehavior=MSortedProcessedInterface
    )


class BrodyNeuralynxNWBConverter(NWBConverter):
    """Primary conversion class for the Neuralynx formatted Brody lab data."""

    data_interface_classes = dict(
        NeuralynxRecording=NeuralynxRecordingInterface,
        ProcessedBehavior=MSortedProcessedInterface,
        Sorted=MSortedSortingInterface
    )


class BrodySpikeGadgetsNWBConverter(NWBConverter):
    """Primary conversion class for the SpikeGadgets formatted Brody lab data."""

    data_interface_classes = dict(
        SpikeGadgetsRecording=SpikeGadgetsRecordingInterface,
    )
