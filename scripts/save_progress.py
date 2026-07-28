import os
import shutil
import datetime

def generate_tree(dir_path, prefix=""):
    """Returns a string representation of the directory tree."""
    tree_str = ""
    try:
        items = [item for item in os.listdir(dir_path) if item not in ['.git', '__pycache__']]
        items.sort()
        for index, item in enumerate(items):
            path = os.path.join(dir_path, item)
            is_last = index == len(items) - 1
            tree_str += f"{prefix}{'└── ' if is_last else '├── '}{item}\n"
            if os.path.isdir(path):
                extension = "    " if is_last else "│   "
                tree_str += generate_tree(path, prefix=prefix + extension)
    except PermissionError:
        pass
    return tree_str

def main():
    # Define source and destination
    source_dir = "c:/Projects/mycodingmaster"
    
    # Get user's documents folder for Windows
    docs_folder = os.path.join(os.environ['USERPROFILE'], 'Documents')
    backup_base_dir = os.path.join(docs_folder, 'MyCodingMaster_Backup')
    
    # Ensure backup directory exists
    os.makedirs(backup_base_dir, exist_ok=True)
    
    # Generate timestamp for the backup file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"MyCodingMaster_Progress_{timestamp}"
    zip_path = os.path.join(backup_base_dir, zip_filename)
    
    print(f"Archiving project data to {zip_path}.zip ...")
    
    # Create the zip archive
    try:
        shutil.make_archive(zip_path, 'zip', source_dir)
        
        # Save the current folder tree
        tree_content = f"MyCodingMaster Folder Structure\nGenerated at: {timestamp}\n\n"
        tree_content += generate_tree(source_dir)
        with open(os.path.join(backup_base_dir, "FOLDER_STRUCTURE.txt"), "w", encoding="utf-8") as f:
            f.write(tree_content)
        
        # Also copy the blueprint, tracker, scaffold script, and versions history AS PLAIN FILES outside the zip
        # So they are instantly accessible even if the project is deleted.
        shutil.copy2(os.path.join(source_dir, "PROGRESS_TRACKER.md"), os.path.join(backup_base_dir, "PROGRESS_TRACKER.md"))
        shutil.copy2(os.path.join(source_dir, "PROJECT_BLUEPRINT.md"), os.path.join(backup_base_dir, "PROJECT_BLUEPRINT.md"))
        shutil.copy2(os.path.join(source_dir, "scripts/scaffold.py"), os.path.join(backup_base_dir, "scaffold.py"))
        
        # Copy versions history folder (using copytree with dirs_exist_ok=True for safety)
        versions_history_src = os.path.join(source_dir, "versions history")
        versions_history_dst = os.path.join(backup_base_dir, "versions history")
        if os.path.exists(versions_history_src):
            shutil.copytree(versions_history_src, versions_history_dst, dirs_exist_ok=True)
        
        print("Success! Current progress, folder structure, and tracker files have been safely backed up outside the project.")
    except Exception as e:
        print(f"Error during backup: {e}")

if __name__ == "__main__":
    main()
