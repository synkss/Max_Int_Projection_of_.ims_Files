--------------------------------------------------
GENERAL DESCRIPTION:

When the program starts, a window opens allowing the user to select the folder containing the .ims files to process.

The program will then:
	1. Create a new folder inside the selected directory, called "maximum intensity projections".
	2. Scan the selected directory for all .ims files.
	3. Compute the Maximum Intensity Projection of each file, sequentially.
	4. Save the resulting projections in the newly created folder.
	5. Save a report.txt file detailing the process.

This approach ensures that large .ims files can be easily processed by any computer, without loading all the data into memory simultaneously.

If, for any reason, the program cannot process any specific file, its name and error will be saved in a generated report, and the program will continue its operation.

--------------------------------------------------
USAGE:

1. Run the executable: "Max. Int. Projection of ims data.exe"
2. Select the folder containing the .ims files.
3. Wait while the program automatically processes all files and saves the projections.

--------------------------------------------------
OUTPUT:

The generated projections and report.txt file will be saved in:

<selected folder>/maximum intensity projections/


--------------------------------------------------
Author:

Simão Peniche Seixas
simao.peniche.seixas@gmail.com
i3S - Institute for Research and Innovation in Health