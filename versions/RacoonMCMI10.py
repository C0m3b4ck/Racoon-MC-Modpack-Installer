import os
import json
import zipfile
import shutil
import urllib.request
import requests
from bs4 import BeautifulSoup
from pathlib import Path

def download_and_install_ftb_pack_from_link(pack_url, minecraft_dir=".", pack_name="FTB_Pack"):
    """
    Downloads, extracts, and installs an FTB modpack from a direct download link into the vanilla Minecraft launcher directory.

    Args:
        pack_url (str): URL of the FTB pack zip file. Must be a direct download link ending with .zip.
        minecraft_dir (str, optional):  Path to the Minecraft directory. Defaults to ".".
        pack_name (str, optional): Name of the modpack.  Will be used for the profile name. Defaults to "FTB_Pack".
    """

    # Ensure pack_url is a direct download link
    if not pack_url.endswith(".zip") or not pack_url.startswith("http"):
        print("Invalid direct download link. Please provide a URL ending with .zip.")
        return

    minecraft_path = Path(minecraft_dir).expanduser().resolve()
    instances_dir = minecraft_path / "instances"
    profiles_path = minecraft_path / "launcher_profiles.json"
    pack_instance_dir = instances_dir / pack_name

    # Create directories if they don't exist
    instances_dir.mkdir(parents=True, exist_ok=True)
    pack_instance_dir.mkdir(parents=True, exist_ok=True)

    # 1. Download the FTB pack
    print(f"Downloading FTB pack from {pack_url}...")
    zip_file_path = pack_instance_dir / "pack.zip"
    try:
        urllib.request.urlretrieve(pack_url, zip_file_path)
    except Exception as e:
        print(f"Error downloading pack: {e}")
        return

    # 2. Extract the FTB pack
    print("Extracting FTB pack...")
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(pack_instance_dir)
    except Exception as e:
        print(f"Error extracting pack: {e}")
        return

    # 3. Move mods, configs, etc. to the correct locations (if needed)
    mods_source_dir = pack_instance_dir / "mods"
    config_source_dir = pack_instance_dir / "config"
    mods_target_dir = pack_instance_dir / "minecraft" / "mods"
    config_target_dir = pack_instance_dir / "minecraft" / "config"

    # Create directories if they don't exist
    (pack_instance_dir / "minecraft").mkdir(parents=True, exist_ok=True)
    mods_target_dir.mkdir(parents=True, exist_ok=True)
    config_target_dir.mkdir(parents=True, exist_ok=True)

    if mods_source_dir.exists():
        print("Moving mods...")
        for item in mods_source_dir.iterdir():
            shutil.move(str(item), str(mods_target_dir))

    if config_source_dir.exists():
        print("Moving configs...")
        for item in config_source_dir.iterdir():
            shutil.move(str(item), str(config_target_dir))

    # Create a libraries folder if necessary
    libraries_source_dir = pack_instance_dir / "libraries"
    libraries_target_dir = pack_instance_dir / "minecraft" / "libraries"
    libraries_target_dir.mkdir(parents=True, exist_ok=True)
    if libraries_source_dir.exists():
        print("Moving libraries...")
        for item in libraries_source_dir.iterdir():
            shutil.move(str(item), str(libraries_target_dir))

    # 4. Create or update the launcher_profiles.json file
    print("Updating launcher profile...")
    try:
        with open(profiles_path, 'r') as f:
            profiles_data = json.load(f)
    except FileNotFoundError:
        profiles_data = {"profiles": {}, "settings": {}, "version": 2}
    except json.JSONDecodeError:
        print("Error decoding launcher_profiles.json. Backing up the file and creating a new one.")
        shutil.copyfile(profiles_path, str(profiles_path) + ".bak")
        profiles_data = {"profiles": {}, "settings": {}, "version": 2}

    # Unique ID for the new profile
    profile_id = f"{pack_name}"
    profile_version = str(input("Input Minecraft version for modpack: "))

    profiles_data["profiles"][profile_id] = {
        "name": pack_name,
        "type": "custom",
        "created": "2024-01-01T00:00:00.000Z",
        "lastUsed": "2024-01-01T00:00:00.000Z",
        "icon": "Furnace",
        "lastVersionId": profile_version,  # Set the correct Minecraft version here!
        "javaDir": "",  # Let the launcher choose the Java runtime
        "javaArgs": "-Xmx4G",  # Adjust memory allocation as needed
        "gameDir": str(pack_instance_dir / "minecraft")
    }

    try:
        with open(profiles_path, 'w') as f:
            json.dump(profiles_data, f, indent=4)
    except Exception as e:
        print(f"Error writing to launcher_profiles.json: {e}")
        return

    print(f"FTB pack '{pack_name}' installed successfully! Launch Minecraft and select the '{pack_name}' profile.")

def download_and_install_ftb_pack_from_html(html_file_path, minecraft_dir=".", pack_name="FTB_Pack"):
    """
    Installs mods from a local HTML file into the vanilla Minecraft launcher directory.

    Args:
        html_file_path (str): Path to the local HTML file containing mod links.
        minecraft_dir (str, optional):  Path to the Minecraft directory. Defaults to ".".
        pack_name (str, optional): Name of the modpack.  Will be used for the profile name. Defaults to "FTB_Pack".
    """

    # Parse the local HTML file
    try:
        with open(html_file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
    except Exception as e:
        print(f"Error parsing HTML file: {e}")
        return

    # Find all links on the page
    mod_links = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and (href.endswith('.jar') or href.endswith('.zip')):
            mod_links.append(href)

    # Download mods
    minecraft_path = Path(minecraft_dir).expanduser().resolve()
    mods_dir = minecraft_path / "mods"
    mods_dir.mkdir(parents=True, exist_ok=True)

    for link in mod_links:
        # Check if the link is a local file path or a URL
        if os.path.isfile(link):
            # If it's a local file path, copy the file to the mods directory
            try:
                shutil.copy2(link, mods_dir)
                print(f"Mod copied from {link} to {mods_dir}")
            except Exception as e:
                print(f"Error copying mod from {link}: {e}")
        elif link.startswith('http'):
            # If it's a URL, download the file
            try:
                print(f"Downloading mod from {link}...")
                response = requests.get(link, stream=True)
                if response.status_code == 200:
                    file_name = Path(link).name
                    file_path = mods_dir / file_name
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)
                    print(f"Mod {file_name} downloaded successfully!")
                else:
                    print(f"Failed to download mod from {link}. Status code: {response.status_code}")
            except Exception as e:
                print(f"Error downloading mod from {link}: {e}")
        else:
            print(f"Unsupported link type: {link}")

    # Create or update the launcher_profiles.json file
    print("Updating launcher profile...")
    profiles_path = minecraft_path / "launcher_profiles.json"
    try:
        with open(profiles_path, 'r') as f:
            profiles_data = json.load(f)
    except FileNotFoundError:
        profiles_data = {"profiles": {}, "settings": {}, "version": 2}
    except json.JSONDecodeError:
        print("Error decoding launcher_profiles.json. Backing up the file and creating a new one.")
        shutil.copyfile(profiles_path, str(profiles_path) + ".bak")
        profiles_data = {"profiles": {}, "settings": {}, "version": 2}

    # Unique ID for the new profile
    profile_id = f"{pack_name}"
    profile_version = str(input("Input Minecraft version for modpack: "))

    profiles_data["profiles"][profile_id] = {
        "name": pack_name,
        "type": "custom",
        "created": "2024-01-01T00:00:00.000Z",
        "lastUsed": "2024-01-01T00:00:00.000Z",
        "icon": "Furnace",
        "lastVersionId": profile_version,  # Set the correct Minecraft version here!
        "javaDir": "",  # Let the launcher choose the Java runtime
        "javaArgs": "-Xmx4G",  # Adjust memory allocation as needed
        "gameDir": str(minecraft_path)  # Use the main Minecraft directory
    }

    try:
        with open(profiles_path, 'w') as f:
            json.dump(profiles_data, f, indent=4)
    except Exception as e:
        print(f"Error writing to launcher_profiles.json: {e}")
        return

    print(f"Mods installed successfully! Launch Minecraft and select the '{pack_name}' profile.")

def main():
    print("Choose an installation method:")
    print("1. Install from a direct download link")
    print("2. Install from an HTML document")
    
    choice = input("Enter your choice (1/2): ")

    pack_name = str(input("Input pack name: "))
    minecraft_dir = "~/.minecraft"

    if choice == "1":
        print("To download a modpack, you need a direct download link ending with .zip.")
        print("You can obtain this link by using tools like the Minecraft Serverpack Installer script or by manually downloading the modpack from CurseForge and then providing the direct link to the downloaded zip file.")
        pack_url = input("Input direct download URL (ending with .zip): ")
        download_and_install_ftb_pack_from_link(pack_url, minecraft_dir, pack_name)
    elif choice == "2":
        html_file_path = input("Input the path to the local HTML file: ")
        download_and_install_ftb_pack_from_html(html_file_path, minecraft_dir, pack_name)
    else:
        print("Invalid choice. Please choose again.")

if __name__ == "__main__":
    main()
