"""Authors: Cody Baker."""
import numpy as np

from h5py import File
from nwb_conversion_tools.datainterfaces.ecephys.basesortingextractorinterface import BaseSortingExtractorInterface

from ..customsortingextractor import CustomSortingExtractor


class MSortedSortingInterface(BaseSortingExtractorInterface):
    """Conversion class for the pre-sorted data corresponding to the Neuralynx format for the Brody lab."""

    SX = CustomSortingExtractor

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

    def __init__(self, **source_data):
        processed_file_path = source_data["file_path"]
        mat_file = File(processed_file_path, mode="r")
        sf = mat_file["Msorted"]["sampling_frequency"][()][0][0]
        self.sorting_extractor = self.SX()
        self.sorting_extractor.set_sampling_frequency(sampling_frequency=sf)
        for j, unit in enumerate(mat_file["Msorted"]["raw_spike_time_s"][0]):
            self.sorting_extractor.add_unit(unit_id=j, times=np.array([x[0] for x in mat_file[unit][()]]))
        # TODO, in future PR add properties by 'metrics' fields
