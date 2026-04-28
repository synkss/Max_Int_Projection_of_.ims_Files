# Imports
from tkinter import Tk
from tkinter import filedialog
from zarr import open as zarr_open
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

def get_pixel_size(file):
    """
    Function that accepts an .ims file as an input and extracts the pixel size,
    outputting x_size and y_size in micrometers
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
        ]

        ext_max = [
            parse(attrs['ExtMax0']),
            parse(attrs['ExtMax1']),
        ]

        # Read the number of pixels along each axis
        size_x = parse_int(attrs['X'])
        size_y = parse_int(attrs['Y'])

    # Compute the voxel size from the physical size of the volume and the number of pixels
    x_size = (ext_max[0] - ext_min[0]) / size_x
    y_size = (ext_max[1] - ext_min[1]) / size_y

    return x_size, y_size

def main():

    print("Maximum Intensity Projection of .ims Files")
    print("----------------------------------------------")
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
            root.destroy()
            print("No folder selected. Exiting the program.")
            return

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
            print("Please choose another folder.")
            print()
    
    # Get the number of .ims files in the folder
    n_files = len(ims_files)
    if n_files == 1:
        print(f"Found 1 .ims file.")
    else:
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

        store = None
        zarr_array = None
        max_int_proj = None
        max_int_proj_final = None

        print(f"\nProcessing file {i}/{n_files}:")
        print(f"{file.name}")

        try:
            # Opening in this method for "Opening file" messages of the ims library to not appear
            with builtins.open(os.devnull, "w") as f, redirect_stdout(f), redirect_stderr(f):

                # Open the file as a zarr in read mode
                # This constructs a 5D zarr_array that assumes the axes as (T,C,Z,Y,X)
                store = ims(file, aszarr=True, squeeze_output=False)
                zarr_array = zarr_open(store, mode="r")

            # Check to see if the data is 5D. If not, raise an error, since the code cannot properly function
            if len(zarr_array.shape) != 5:
                raise RuntimeError(f"Expected 5D TCZYX, got {zarr_array.shape}")
                
            # Opening in this method for "Opening file" messages of the ims library to not appear
            with builtins.open(os.devnull, "w") as f, redirect_stdout(f), redirect_stderr(f):
                # Get the dimensions of the image
                T, C, Z, Y, X = zarr_array.shape

                # Perform the maximum intensity projection
                # This method opens each slice one at a time as an array with dimensions TCYX and stores the maximum value for each individual pixel
                # The final slice array in memory thus corresponds to the maximum intensity projection
                max_int_proj = None
                slice_z = None
                for z in range(Z):

                    slice_z = zarr_array[:,:,z,:,:]

                    if max_int_proj is None:
                        max_int_proj = slice_z.copy()

                    else:
                        max_int_proj = maximum(max_int_proj, slice_z, out=max_int_proj)

                # After the loop delete slice_z to keep minimal memory use
                if slice_z is not None:
                    del slice_z

        except Exception:
            print("Could not perform Maximum Intensity Projection.")
            print_exc()

            # Save the failed file, the stage and the error
            full_error = format_exc()
            failed_files.append((file.name, "processing max. int. proj.", full_error))
            
            # Do not stop execution, continue to the next file.
            continue

        finally:
            # Clean up memory after the maximum intensity projected is computed
            if zarr_array is not None:
                del zarr_array
            if store is not None:
                try:
                    store.close()
                except Exception:
                    print(f"Warning: failed to close store for {file.name}")
            collect()

        # --------------------------------------------------------------
        # Save the Max. Int. Proj.

        # Choose the correct axes for OME-TIFF saving
        try:
            with builtins.open(os.devnull, "w") as f, redirect_stdout(f), redirect_stderr(f):

                if T == 1:
                    if C == 1:
                        axes = 'YX'
                        max_int_proj_final = max_int_proj[0,0,:,:]
                    else:
                        axes = 'CYX'
                        max_int_proj_final = max_int_proj[0,:,:,:]

                else:
                    if C == 1:
                        axes = 'TYX'
                        max_int_proj_final = max_int_proj[:,0,:,:]
                    else:
                        axes = 'TCYX'
                        max_int_proj_final = max_int_proj
                        # No change in shape

                del max_int_proj

                # Get the voxel size in micrometers from the ims metadata
                try:
                    x_size, y_size = get_pixel_size(file)
                    pixelsize_metadata_available = True
                except Exception:
                    print(f"Warning: could not read pixel size for {file.name}")
                    print_exc()
                    x_size, y_size = None, None
                    pixelsize_metadata_available = False

                # Create a metadata dictionary
                metadata_dict = {'axes': axes}

                # Add sizes if they are available
                if pixelsize_metadata_available:
                    metadata_dict.update({
                        'PhysicalSizeX': x_size,
                        'PhysicalSizeY': y_size,
                        'PhysicalSizeXUnit': 'µm',
                        'PhysicalSizeYUnit': 'µm',
                    })

                # Compute the OME-TIFF file name
                output_file = new_folder / f"{file.stem}_max_int_proj.ome.tiff"

                # Save the file
                imwrite(
                        output_file,
                        max_int_proj_final ,
                        ome=True,
                        bigtiff=True,
                        photometric="minisblack",
                        metadata=metadata_dict,
                        compression="zlib",
                        compressionargs={"level": 6},
                        tile=(256, 256)
                        )

                # Delete the data in memory before closing
                del max_int_proj_final
                collect()

                successful_files.append(file.name)

            print(f"Finished processing file {i}/{n_files}.")

        except Exception:
            print("Could not save the Maximum Intensity Projection.")
            print_exc()

            # Save the failed file, the stage and the error
            full_error = format_exc()
            failed_files.append((file.name, "saving max. int. proj.", full_error))
            
            # Continue to the next file
            continue


    # --------------------------------------------------------------
    # Save the final report

    report_file = new_folder / "report.txt"

    # Delete the report if it already is there
    if report_file.exists():
        report_file.unlink()

    with builtins.open(report_file, "w") as f:

        f.write("=== MAXIMUM INTENSITY PROJECTION REPORT ===\n\n")

        f.write(f"Total files: {n_files}\n")
        f.write(f"Successful:  {len(successful_files)}\n")
        f.write(f"Failed:      {len(failed_files)}\n\n")

        if failed_files:
            f.write("=== FAILED FILES ===\n\n")

            for name, stage, error in failed_files:
                f.write(f"{name}\n")

            f.write("\n--------------------------------------\n\n")

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

    print()
    print("Report saved.")
        
    # --------------------------------------------------------------
    # Exhibit a final message on the console
    if failed_files:

        # If there was only one file
        if n_files == 1:
            print("The file could not be processed.")

        # If there was more than one file
        else:
            if len(failed_files) == 1:
                print(f"All {n_files} files were processed, with 1 failed file.")
            else:
                print(f"All {n_files} files were processed, with {len(failed_files)} failed files.")
    
    # There were no failed files
    else:
        if n_files == 1:
            print("The file was processed successfully.")
        else:
            print(f"All {n_files} files were processed successfully.")

    print()
    print("--------------------------------------------------------------")
    print("Author: Simão Peniche Seixas")
    print("simao.seixas@i3s.up.pt")
    print("simao.peniche.seixas@gmail.com")
    print("i3S - Institute for Research and Innovation in Health")
    print()
    input("Press Enter to exit.")

# --------------------------------------------------------------
# Run the program
if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("Program crashed:")
        print_exc()
        input("Press Enter to exit.")