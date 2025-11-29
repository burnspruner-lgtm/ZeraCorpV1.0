import os

def create_init_files():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # List of directories that need to be Python packages
    packages = [
        "src",
        "src/core",
        "src/ai",
        "src/services",
        "src/ml",
        "src/config",
        "src/utils"
    ]
    
    print(f"🔧 Scanning project at: {root_dir}")
    
    for package in packages:
        path = os.path.join(root_dir, package)
        if os.path.exists(path):
            init_file = os.path.join(path, "__init__.py")
            if not os.path.exists(init_file):
                print(f"   [+] Creating missing __init__.py in {package}")
                with open(init_file, 'w') as f:
                    f.write("# Package initialization")
            else:
                print(f"   [OK] {package} is already a package.")
        else:
            print(f"   [!] Warning: Directory {package} does not exist.")

if __name__ == "__main__":
    create_init_files()
    print("\n✅ Package initialization complete. Try running your main script again.")