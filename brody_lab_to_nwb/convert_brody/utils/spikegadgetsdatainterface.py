"""Authors: Cody Baker."""
from nwb_conversion_tools.datainterfaces.ecephys.baserecordingextractorinterface import BaseRecordingExtractorInterface

from .spikegadgestrecordingextractor import SpikeGadgetsRecordingExtractor


class SpikeGadgetsRecordingInterface(BaseRecordingExtractorInterface):
    """Primary data interface class for converting the SpikeGadgets format."""

    RX = SpikeGadgetsRecordingExtractor

    @classmethod
    def get_source_schema(cls):
        return dict(
            required=["filename"],
            properties=dict(
                dirname=dict(
                    type="string",
                    format="file",
                    description="Path to SpikeGadgets file."
                ),
            ),
            type="object",
            additionalProperties=True
        )
