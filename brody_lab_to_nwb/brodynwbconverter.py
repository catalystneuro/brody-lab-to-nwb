"""Authors: Cody Baker."""
from nwb_conversion_tools import (
    NWBConverter,
    NeuralynxRecordingInterface,
    SpikeGLXRecordingInterface,
    SpikeGLXLFPInterface,
)

from .msortedprocesseddatainterface import MSortedProcessedInterface


class PoissonClicksNWBConverter(NWBConverter):
    """Primary conversion class for the SpikeGLX formatted Brody lab data."""

    data_interface_classes = dict(
        SpikeGLXRecording=SpikeGLXRecordingInterface,
        SpikeGLXLFP=SpikeGLXLFPInterface,
        Processed=MSortedProcessedInterface
    )


class BrodyNeuralynxNWBConverter(NWBConverter):
    """Primary conversion class for the Neuralynx formatted Brody lab data."""

    data_interface_classes = dict(
        NeuralynxRecording=NeuralynxRecordingInterface,
        Processed=MSortedProcessedInterface
    )
