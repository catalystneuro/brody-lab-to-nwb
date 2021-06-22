"""Authors: Cody Baker."""
from pathlib import Path
from isodate import duration_isoformat
from datetime import timedelta, datetime

from brody_lab_to_nwb import BrodyNeuralynxNWBConverter

# Point to the base folder path for both recording data and Virmen
base_path = Path("D:/Brody/Neuralynx Tetrode Data")

# Name the NWBFile and point to the desired save path
nwbfile_path = base_path / "FullTesting.nwb"

# Point to the various files for the conversion
session_name = "A182_2018_10_05"
raw_data_folder = base_path / session_name / "Raw"
processed_file_path = base_path / session_name / "Processed" / "Msorted_A182_2018-10-05.mat"

# Enter Session and Subject information here - uncomment any fields you want to include
session_description = "Enter session description here."
session_start = datetime(1970, 1, 1)  # (Year, Month, Day)

subject_info = dict(
    description="Enter optional subject description here",
    # weight="Enter subject weight here",
    # age=duration_isoformat(timedelta(days=0)),  # Enter the age of the subject in days
    # species="Mus musculus",
    # genotype="Enter subject genotype here",
    # sex="Enter subject sex here"
)

# Set some global conversion options here
stub_test = True


# Run the conversion
source_data = dict(
    NeuralynxRecording=dict(folder_path=str(raw_data_folder)),
    Processed=dict(file_path=str(processed_file_path))
)
conversion_options = dict(NeuralynxRecording=dict(stub_test=stub_test))
converter = BrodyNeuralynxNWBConverter(source_data=source_data)
metadata = converter.get_metadata()
metadata['NWBFile'].update(session_description=session_description)
metadata['Subject'].update(subject_info)
converter.run_conversion(
    nwbfile_path=str(nwbfile_path),
    metadata=metadata,
    conversion_options=conversion_options,
    overwrite=True
)
