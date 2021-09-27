"""Authors: Cody Baker."""
import numpy as np
import scipy.io as spio

from nwb_conversion_tools.datainterfaces.ecephys.basesortingextractorinterface import BaseSortingExtractorInterface
from nwb_conversion_tools.utils.json_schema import FilePathType

from .ksphysortingextractor import ksphySortingExtractor
from .protocol_info_utils import make_spks_dict


class ksphySortingInterface(BaseSortingExtractorInterface):
    """Conversion class for the pre-sorted data corresponding to the SpikeGadgets format for the Brody lab."""

    SX = ksphySortingExtractor

    @classmethod
    def get_source_schema(cls):
        source_schema = dict(
            required=["file_path"],
            properties=dict(
                file_path=dict(
                    type="string",
                    format="file",
                    description="Path to .mat file containing processed data."
                )
            ),
            type="object",
            additionalProperties=False
        )
        return source_schema

    def __init__(self, file_path: FilePathType):
        super().__init__()
        spks_info = spio.loadmat(file_path)
        spks_info = spks_info["PWMspkS"][0]
        spks_dict = make_spks_dict(spks_info)
        self.sorting_extractor.set_sampling_frequency(sampling_frequency=spks_dict["fs"])
        for j, spk_times in enumerate(spks_dict["spk_times"]):
            self.sorting_extractor.add_unit(unit_id=j, times=np.array([x[0] for x in spk_times]))
        for property_name in ["spk_qual", "trode_nums"]:
            for j, value in enumerate(spks_dict[property_name]):
                self.sorting_extractor.set_unit_property(unit_id=j, property_name=property_name, value=value)
        for mat_name, property_name in zip(["mean_wav", "std_wav"], ["waveform_mean", "waveform_sd"]):
            for j, value in enumerate(spks_dict[mat_name]):
                self.sorting_extractor.set_unit_property(unit_id=j, property_name=property_name, value=value.T)

    def get_metadata(self):
        return dict(
            Ecephys=dict(
                UnitProperties=[
                    dict(
                        name="spk_qual", description="Whether the unit is a single- or multi- unit activity."
                    ),
                    dict(name="trode_nums", description=""),
                    dict(
                        name="waveform_mean",
                        description=(
                            "Mean waveform for this unit. Only includes waveforms for channels in the channel group."
                        )
                    ),
                    dict(
                        name="waveform_sd",
                        description=(
                            "Standard deviation of waveform for this unit. "
                            "Only includes waveforms for channels in the channel group."
                        ),
                    )
                ]
            )
        )
