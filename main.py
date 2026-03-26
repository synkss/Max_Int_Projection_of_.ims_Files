# Imports
from tkinter import Tk
from tkinter import filedialog
from zarr import open
from imaris_ims_file_reader.ims import ims
from numpy import maximum, squeeze
from pathlib import Path
from tifffile import imwrite
from contextlib import redirect_stdout
import os
import builtins
from traceback import print_exc
from sys import exit
import gc

def main():

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

    for i, file in enumerate(ims_files, start=1):

        print(f"\nProcessing file {i}/{n_files}:")
        print(f"{file.name}")

        try:

            with builtins.open(os.devnull, "w") as f, redirect_stdout(f):

                # Open the file as a zarr in read mode
                store = ims(file, aszarr=True)
                zarr_array = open(store, mode="r")

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

        except Exception:
            print("Could not perform Max. Int. Projection.")
            print_exc()
            input("Press any key to exit.")


        # --------------------------------------------------------------
        # Save the Max. Int. Proj.

        # Choose the correct axes for OME-TIFF saving
        try:
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

            gc.collect()
            
            # Save the file
            imwrite(
                    output_file,
                    max_int_proj,
                    ome=True,
                    bigtiff=True,
                    photometric="minisblack",
                    metadata={'axes': axes},
                    compression="zlib",
                    compressionargs={"level": 6},
                    tile=(256, 256)
                    )

            # Delete the data in memory before closing
            del max_int_proj
            gc.collect()
                
            print(f"file {i}/{n_files} finished.")

        except Exception:
            print("Could not save the Max. Int. Projection.")
            print_exc()
            input("Press any key to exit.")

    # Exhibit a final message
    print()
    print("All files processed successfully.")
    input("Press any key to exit.")

# Run the program
if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("Program crashed:")
        print_exc()
        input("Press any key to exit.")