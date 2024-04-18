
import os
import shutil

# Source directory for Same_in_All
source_Geo = r"C:\Users\mmeshkin\Documents\Speed2Zero\Code_Input_Output\Python_Automated_inputs\inputs\building-geometry"
source_Terrain= r"C:\Users\mmeshkin\Documents\Speed2Zero\Code_Input_Output\Python_Automated_inputs\inputs\topography\terrain.tif"
# Destination directory where files will be copied
destination_Geo = r"C:\Users\mmeshkin\Documents\Speed2Zero\CEA_Automated_Senarios\MTest\SA_1\inputs\building-geometry"
destination_Terrain = r"C:\Users\mmeshkin\Documents\Speed2Zero\CEA_Automated_Senarios\MTest\SA_1\inputs\topography"


# Source directory for Same_in_Year
source_Weather=r"C:\Users\mmeshkin\Documents\Speed2Zero\Code_Input_Output\Python_Automated_inputs\inputs\weather"
Year="2040"
destination_Weather = r"C:\Users\mmeshkin\Documents\Speed2Zero\CEA_Automated_Senarios\MTest\SA_1\inputs\weather"


# Source directory for Same_in_EmissionType
Rates=['17', '32', '58', '37', '70', '99']
EmissionType=['S7', 'S8', 'S9', 'S10', 'S12']
source_Typology = r"C:\Users\mmeshkin\Documents\Speed2Zero\Code_Input_Output\Python_Automated_inputs\AllTypologies"



# for All Senarios
try:
    # Create the destination directory if it doesn't exist
    if not os.path.exists(destination_Geo):
        os.makedirs(destination_Geo)

    # Iterate over all files in the source directory
    for filename in os.listdir(source_Geo):
        # Construct the full path of the source file
        source_file = os.path.join(source_Geo, filename)

        # Check if the file is a regular file
        if os.path.isfile(source_file):
            # Construct the full path of the destination file
            destination_file = os.path.join(destination_Geo, filename)

            # Copy the file from source to destination
            shutil.copy2(source_file, destination_file)

            print(f"File '{filename}' copied successfully.")

    print("All files copied successfully.")

except Exception as e:
    print(f"An error occurred: {e}")

# for Year

try:
    # Create the destination directory if it doesn't exist
    if not os.path.exists(destination_Weather):
        os.makedirs(destination_Weather)

    # Get a list of all files in the source directory
    files = os.listdir(source_Weather)

    # Filter the files based on the condition
    filtered_files = [file for file in files if Year in file]

    # Copy the filtered files to the destination directory
    for file in filtered_files:
        source_file = os.path.join(source_Weather, file)
        destination_file = os.path.join(destination_Weather, "weather.epw")
        shutil.copy2(source_file, destination_file)
        print(f"File '{file}' copied successfully to '{destination_Weather}'.")

    print("All files copied successfully.")

except FileNotFoundError:
    print(f"The directory '{source_Weather}' or '{destination_Weather}' could not be found.")
except Exception as e:
    print(f"An error occurred: {e}")


# for emission type
try:
    # Iterate over each combination of Rates and EmissionType
    for rate in Rates:
        for emission_type in EmissionType:
            # Construct the filename based on the format 'typology_Rates_EmissionType'
            filename = f"typology_{rate}_{emission_type}.dbf"

            # Check if the file exists in the source directory
            if os.path.exists(os.path.join(source_Typology, filename)):
                # Create a folder for the current combination of Rates and EmissionType
                folder_name = f"Rate_{rate}_EmissionType_{emission_type}"
                destination_dir = os.path.join(r"C:\Users\mmeshkin\Documents\Speed2Zero\Code_Input_Output\Python_Automated_inputs\a", folder_name)
                if not os.path.exists(destination_dir):
                    os.makedirs(destination_dir)

                    # Copy the file to the corresponding folder with the filename changed to 'typology'
                    new_filename = f"typology.dbf"
                    shutil.copy2(os.path.join(source_Typology, filename), os.path.join(destination_dir, new_filename))
                print(f"File '{filename}' copied successfully to '{destination_dir}'.")
            else:
                print(f"File '{filename}' not found.")

    print("All files copied successfully.")

except FileNotFoundError:
    print(f"The directory '{source_Typology}' or the destination directory could not be found.")
except Exception as e:
    print(f"An error occurred: {e}")