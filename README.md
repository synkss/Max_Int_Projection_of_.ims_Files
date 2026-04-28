## General Description

When the program starts, a window opens allowing the user to select the folder containing the `.ims` files to process.

The program will then:

1. Create a new folder inside the selected directory, called `maximum intensity projections`.
2. Scan the selected directory for all `.ims` files.
3. Compute the Maximum Intensity Projection of each file, sequentially.
4. Save the resulting projections in the created folder.
5. Save a `report.txt` file detailing the process.

This approach ensures that large `.ims` files can be processed on computers with limited memory, because the full dataset is not loaded into memory simultaneously.

If, for any reason, the program cannot process a specific file, its name and error will be saved in the generated report, and the program will continue processing the remaining files.

---

## Building the executable/Running the code

You will need a Python installation.

**In Windows:**

To build the executable:
- Build the virtual environment by double-clicking `setup_venv.bat`
- Build the executable by double-clicking `build_exe.bat`
- Wait for the executable to be built automatically.
- Double-click the executable.

To directly run the code:
- Build the virtual environment double-clicking `setup_venv.bat`
- Run the code using the virtual environment.


**In macOS:**

To build the executable:
- Build the virtual environment by double-clicking `setup_venv.sh`
- Build the application by double-clicking `build_app.sh`
- Wait for the app to be built automatically.
- Double-click the app.

To directly run the code:
- Build the virtual environment double-clicking `setup_venv.bat`
- Run the code using the virtual environment.

---

## Program usage

1. Run the executable/code:

        Max. Int. Projection of ims data.exe

2. Wait for the program to open

3. Select the folder containing the `.ims` files.

4. Wait while the program automatically:

   - Processes all `.ims` files.
   - Saves the maximum intensity projections.
   - Generates the `report.txt` file.

---

## Output

The generated projections and the `report.txt` file will be saved in:

        <selected folder>/maximum intensity projections/

Example:

        C:/Users/YourName/Desktop/IMS files/maximum intensity projections/

---

## Notes

- The program processes the `.ims` files sequentially.
- Large files are handled without loading the complete dataset into memory.
- If an error occurs in one file, the program continues with the next file.
- All processing information and errors are saved in `report.txt`.

---

## Author

**Simão Peniche Seixas**

**Email:** simao.seixas@i3s.up.pt  
**Email:** simao.peniche.seixas@gmail.com  

**Institution:** i3S - Institute for Research and Innovation in Health
