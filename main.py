# Imports
from tkinter import Tk
from tkinter import filedialog
from zarr import open
from imaris_ims_file_reader.ims import ims
from numpy import maximum
from pathlib import Path
from tifffile import imwrite
from contextlib import redirect_stdout, redirect_stderr
import os
import builtins
from traceback import print_exc
from sys import exit
from gc import collect
from h5py import File
from traceback import format_exc

def get_voxel_size(file):
    """
    Function that accepts a .ims file as an input and constructs the voxel size,
    outputting x_size, y_size and z_step in micrometers
    """

    def parse(val):
        """
        Convert a byte array into a float
        """
        return float(b''.join(val).decode())

    def parse_int(val):
        """
        Convert a byte array into an integer
        """
        return int(b''.join(val).decode())
    
    # Open the .ims file using h5py to access the raw metadata
    with File(file, 'r') as f:

        # Access the Image metadata group
        attrs = f['DataSetInfo']['Image'].attrs

        # ExtMin and ExtMax define the spatial bounds of the volume
        ext_min = [
            parse(attrs['ExtMin0']),
            parse(attrs['ExtMin1']),
            parse(attrs['ExtMin2'])
        ]

        ext_max = [
            parse(attrs['ExtMax0']),
            parse(attrs['ExtMax1']),
            parse(attrs['ExtMax2'])
        ]

        # Read the number of pixels along each axis
        size_x = parse_int(attrs['X'])
        size_y = parse_int(attrs['Y'])
        size_z = parse_int(attrs['Z'])

    # Compute the voxel size from the physical size of the volume and the number of pixels
    x_size = (ext_max[0] - ext_min[0]) / size_x
    y_size = (ext_max[1] - ext_min[1]) / size_y

    if size_z > 1:
        z_step = (ext_max[2] - ext_min[2]) / (size_z)
    else:
        z_step = 0

    return x_size, y_size, z_step

def main():

    # Print my name:
    print("Maximum Intensity Projection of .ims files")
    print("Author: Simão Peniche Seixas")
    print("simao.peniche.seixas@gmail.com")
    print("i3S - Institute for Research and Innovation in Health")
    print()

    # --------------------------------------------------------------
    # Open the window to choose the folder and screen it for .ims files

    are_there_ims_files = False

    # Repeat the process if the user chooses a folder with no .ims files
    while are_there_ims_files == False:

        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)  # makes dialog appear in front

        # Open folder selection dialog
        folder_path = filedialog.askdirectory()

        # if the user cancels the dialog, exit the program
        if not folder_path:
            print("No folder selected. Exiting the program.")
            exit()

        # Destroy root
        root.destroy()

        # Get the actual folder variable
        folder = Path(folder_path)

        print("Selected folder:", folder)

        # Screen the folder for .ims files
        ims_files = sorted(folder.glob("*.ims"))

        if len(ims_files) != 0:
            # If there are .ims files in the folder, accept the chosen folder and exit the loop
            are_there_ims_files = True
        else:
            # If there are no .ims files in the folder, decline the chosen folder and reset the loop
            print("No .ims files found in this folder.", flush=True)
            print("Choose another folder.")
            print()
    
    # Get the number of .ims files in the folder
    n_files = len(ims_files)
    print(f"Found {n_files} .ims files.")

    # --------------------------------------------------------------
    # Create new folder for the Maximum intensity projections
    new_folder = folder / "maximum intensity projections"
    new_folder.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------
    # Iterate within all the .ims files of the folder

    # Create a list for the failed files
    successful_files = []
    failed_files = []

    for i, file in enumerate(ims_files, start=1):

        print(f"\nProcessing file {i}/{n_files}:")
        print(f"{file.name}")

        try:
            # Opening in this method for "Opening file" messages of the ims library to not appear
            with builtins.open(os.devnull, "w") as f, redirect_stdout(f), redirect_stderr(f):

                # Open the file as a zarr in read mode
                store = ims(file, aszarr=True)
                zarr_array = open(store, mode="r")

                # Get dtype and metadata
                dtype = zarr_array.dtype

                # Get the voxel size in micrometers
                try:
                    x_size, y_size, z_step = get_voxel_size(file)
                    voxel_metadata_available = True
                except Exception:
                    x_size, y_size, z_step = None, None, None
                    voxel_metadata_available = False

                # Get the shape of the image
                T, C, Z, Y, X = zarr_array.shape

                # Perform the maximum intensity projection
                # This method opens each slice one at a time and stores the maximum value for each individual pixel
                # The final slice in memory thus corresponds to the maximum intensity projection
                max_int_proj = None
                for z in range(Z):

                    slice_z = zarr_array[:,:,z,:,:]

                    if max_int_proj is None:
                        max_int_proj = slice_z.copy()

                    else:
                        max_int_proj = maximum(max_int_proj, slice_z, out=max_int_proj)

                # Compute the OME-TIFF file name
                output_file = new_folder / f"{file.stem}_max_int_proj.ome.tiff"

                # Clean up memory after the maximum intensity projected is computed
                del zarr_array
                del store
                collect()

        except Exception as e:
            print("Could not perform Max. Int. Projection.")
            print_exc()

            # Save the failed file, the stage and the error
            full_error = format_exc()
            failed_files.append((file.name, "processing max. int. proj.", full_error))
            # Do not stop execution, continue to the next file.
            continue

        # --------------------------------------------------------------
        # Save the Max. Int. Proj.

        # Choose the correct axes for OME-TIFF saving

        # Opening in this method for "Closing file" messages of the ims library to not appear
        
        try:
            with builtins.open(os.devnull, "w") as f, redirect_stdout(f), redirect_stderr(f):
                if T == 1:
                    if C == 1:
                        axes = 'YX'
                        max_int_proj = max_int_proj[0,0,:,:].copy()
                    else:
                        axes = 'CYX'
                        max_int_proj = max_int_proj[0,:,:,:].copy()

                else:
                    if C == 1:
                        axes = 'TYX'
                        max_int_proj = max_int_proj[:,0,:,:].copy()
                    else:
                        axes = 'TCYX'
                        # No change in shape

                collect()

                # Make sure to assign the proper data type
                max_int_proj = max_int_proj.astype(dtype, copy=False)

                # Create a metadata dictionary
                metadata_dict = {'axes': axes}

                # Add sizes if they are available
                if voxel_metadata_available:
                    metadata_dict.update({
                        'PhysicalSizeX': x_size,
                        'PhysicalSizeY': y_size,
                        'PhysicalSizeXUnit': 'µm',
                        'PhysicalSizeYUnit': 'µm',
                    })

                # Save the file
                imwrite(
                        output_file,
                        max_int_proj,
                        ome=True,
                        bigtiff=True,
                        photometric="minisblack",
                        metadata=metadata_dict,
                        compression="zlib",
                        compressionargs={"level": 6},
                        tile=(256, 256)
                        )

                # Delete the data in memory before closing
                del max_int_proj
                collect()

                successful_files.append(file.name)

            print(f"file {i}/{n_files} finished.")

        except Exception as e:
            print("Could not save the Max. Int. Projection.")
            print_exc()

            # Save the failed file, the stage and the error
            full_error = format_exc()
            failed_files.append((file.name, "saving max. int. proj.", full_error))

            # Delete the data in memory before closing
            del max_int_proj
            collect()
            
            # Continue to the next file
            continue

    # --------------------------------------------------------------
    # Save the final report

    print()
    print("Saving report of the procedure.")
    report_file = new_folder / "report.txt"

    # Delete the report if it already is there
    if report_file.exists():
        report_file.unlink()

    with builtins.open(report_file, "w") as f:

        f.write("=== MAX. INT. PROJ. REPORT ===\n\n")

        f.write(f"Total files: {n_files}\n")
        f.write(f"Successful:  {len(successful_files)}\n")
        f.write(f"Failed:      {len(failed_files)}\n\n")

        if failed_files:
            f.write("=== FAILED FILES ===\n\n")

            for name, stage, error in failed_files:
                f.write(f"File:  {name}\n")
                f.write(f"Stage: {stage}\n\n")
                f.write(f"Error:\n")
                f.write(f"{error}\n")
                f.write("--------------------------------------\n\n")

        if successful_files:
            f.write("=== SUCCESSFUL FILES ===\n\n")

            for name in successful_files:
                f.write(f"{name}\n")
        
    # --------------------------------------------------------------
    # Exhibit a final message on the console
    if failed_files:
        print("All files were processed.")
    else:
        print("All files processed successfully.")
    input("Press any key to exit.")

# --------------------------------------------------------------
# Run the program
if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("Program crashed:")
        print_exc()
        input("Press any key to exit.")