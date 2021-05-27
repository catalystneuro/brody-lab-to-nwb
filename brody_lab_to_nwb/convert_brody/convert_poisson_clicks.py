"""Authors: Cody Baker."""
from pathlib import Path
from isodate import duration_isoformat
from datetime import timedelta, datetime

from brody_lab_to_nwb import PoissonClicksNWBConverter

# Point to the base folder path for both recording data and Virmen
base_path = Path("E:/Brody/Chronic Rat Neuropixels (Poisson Clicks Task)")

# Name the NWBFile and point to the desired save path
nwbfile_path = base_path / "FullTesting.nwb"

# Point to the various files for the conversion
session_name = "A242_2019_05_30"  # or "A256_2020_10_07", or "T219_2019_11_22"
processed_file_path = base_path / session_name / "Processed" / f"{session_name}_Cells.mat"

# Enter Session and Subject information here - uncomment any fields you want to include
session_description = "Enter session description here."

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
session_start = datetime(*[int(x) for x in session_name.split("_")[1:]])
session_str = str(session_start)[:10]
raw_data_file = base_path / session_name / "Raw" / f"{session_str}_g0" / f"{session_str}_g0_imec0" \
    / f"{session_str}_g0_t0.imec0.ap.bin"
lfp_data_file = raw_data_file.parent / raw_data_file.name.replace("ap", "lf")
source_data = dict(
    SpikeGLXRecording=dict(file_path=str(raw_data_file)),
    SpikeGLXLFP=dict(file_path=str(lfp_data_file)),
    Processed=dict(file_path=str(processed_file_path))
)
conversion_options = dict(SpikeGLXRecording=dict(stub_test=stub_test), SpikeGLXLFP=dict(stub_test=stub_test))
converter = PoissonClicksNWBConverter(source_data=source_data)
metadata = converter.get_metadata()
metadata['NWBFile'].update(session_description=session_description, session_start=session_start)
metadata['Subject'].update(subject_info)
converter.run_conversion(
    nwbfile_path=str(nwbfile_path),
    metadata=metadata,
    conversion_options=conversion_options,
    overwrite=True
)
