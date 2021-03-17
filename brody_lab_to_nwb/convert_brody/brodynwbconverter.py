"""Authors: Cody Baker."""
from nwb_conversion_tools import NWBConverter, SpikeGadgetsRecordingInterface, NeuralynxRecordingInterface, \
    SpikeGLXRecordingInterface, SpikeGLXLFPInterface

from .brodybehaviordatainterface import BrodyBehaviorDataInterface


class BrodysNWBConverter(NWBConverter):
    """Primary conversion class for the Brody lab processing pipeline."""

    data_interface_classes = dict(
        SpikeGadgetsRecording=SpikeGadgetsRecordingInterface,
        NeuralynxRecording=NeuralynxRecordingInterface,
        SpikeGLXRecording=SpikeGLXRecordingInterface,
        SpikeGLXLFP=SpikeGLXLFPInterface,
        Behavior=BrodyBehaviorDataInterface
    )

    def get_metadata(self):
        # TODO
        raise NotImplementedError("Not built yet!")
