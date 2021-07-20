"""Authors: Cody Baker."""
from nwb_conversion_tools import NWBConverter, SpikeGLXRecordingInterface, SpikeGLXLFPInterface

from .poissonclicksprocesseddatainterface import PoissonClicksProcessedInterface
from .neuralynxprocesseddatainterface import NeuralynxProcessedInterface
from .wirelesstetrodeprocesseddatainterface import WirelessTetrodeProcessedInterface

from .temporary_interfaces.neuralynxdatainterface import NeuralynxRecordingInterface
from .temporary_interfaces.spikegadgetsdatainterface import SpikeGadgetsRecordingInterface


class PoissonClicksNWBConverter(NWBConverter):
    """Primary conversion class for the SpikeGLX formatted Brody lab data."""

    data_interface_classes = dict(
        SpikeGLXRecording=SpikeGLXRecordingInterface,
        SpikeGLXLFP=SpikeGLXLFPInterface,
        Processed=PoissonClicksProcessedInterface
    )


class BrodyNeuralynxNWBConverter(NWBConverter):
    """Primary conversion class for the Neuralynx formatted Brody lab data."""

    data_interface_classes = dict(
        NeuralynxRecording=NeuralynxRecordingInterface,
        Processed=NeuralynxProcessedInterface
    )


class WirelessTetrodeNWBConverter(NWBConverter):
    """Primary conversion class for the SpikeGadgets formatted Brody lab data."""

    data_interface_classes = dict(
        SpikeGadgetsRecording=SpikeGadgetsRecordingInterface,
        Processed=WirelessTetrodeProcessedInterface
    )
