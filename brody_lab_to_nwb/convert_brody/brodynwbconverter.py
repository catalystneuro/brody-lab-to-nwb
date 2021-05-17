"""Authors: Cody Baker."""
from nwb_conversion_tools import NWBConverter, NeuralynxRecordingInterface, SpikeGLXRecordingInterface, \
    SpikeGLXLFPInterface

from .poissonclicksdatainterface import PoissonClicksDataInterface
from .neuralynxbehaviordatainterface import NeuralynxBehaviorDataInterface


class PoissonClicksNWBConverter(NWBConverter):
    """Primary conversion class for the Brody lab processing pipeline."""

    data_interface_classes = dict(
        SpikeGLXRecording=SpikeGLXRecordingInterface,
        SpikeGLXLFP=SpikeGLXLFPInterface,
        Processed=PoissonClicksDataInterface
    )

    def get_metadata(self):
        # TODO
        raise NotImplementedError("Not built yet!")


class ChronicRatNWBConverter(NWBConverter):
    """Primary conversion class for the Brody lab processing pipeline."""

    data_interface_classes = dict(
        NeuralynxRecording=NeuralynxRecordingInterface,
        Processed=NeuralynxBehaviorDataInterface
    )

    def get_metadata(self):
        # TODO
        raise NotImplementedError("Not built yet!")
