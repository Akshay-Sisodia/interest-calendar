"""
Fix for Streamlit importlib.metadata issues in PyInstaller bundles.
This script is used as a hook for PyInstaller to ensure Streamlit can find its metadata.
"""

import os
import sys
import importlib.metadata
import importlib.abc
import importlib.machinery

# Create a custom finder for metadata
class MetadataFinder(importlib.abc.MetaPathFinder):
    def __init__(self):
        self.packages = {
            'streamlit': '1.31.0',  # Set this to the version you're using
            'streamlit-extras': '0.3.6',
            'altair': '5.2.0',
            'pandas': '2.2.0',
            'numpy': '1.26.3',
            'plotly': '5.18.0',
            'openpyxl': '3.1.2',
            'xlsxwriter': '3.1.9'
        }
    
    def find_spec(self, fullname, path, target=None):
        # We only care about importlib.metadata
        if fullname != 'importlib.metadata':
            return None
        
        # Return the existing spec
        return None
    
    def get_version(self, package_name):
        """Return version for known packages."""
        return self.packages.get(package_name)

# Create a patched version of importlib.metadata.version
original_version = importlib.metadata.version
original_distribution = importlib.metadata.distribution

def patched_version(name):
    """Patched version that handles known packages."""
    try:
        return original_version(name)
    except importlib.metadata.PackageNotFoundError:
        # Check our custom finder
        for finder in sys.meta_path:
            if isinstance(finder, MetadataFinder):
                version = finder.get_version(name)
                if version:
                    return version
        # If we got here, we couldn't find the package
        raise

def patched_distribution(name):
    """Patched distribution that handles known packages."""
    try:
        return original_distribution(name)
    except importlib.metadata.PackageNotFoundError:
        # For streamlit particularly, we need to handle this
        if name == 'streamlit':
            # Create a minimal Distribution-like object
            class MinimalDistribution:
                def __init__(self, name, version):
                    self.name = name
                    self._version = version
                
                @property
                def version(self):
                    return self._version
                
                def read_text(self, filename):
                    # Return minimal package metadata
                    if filename == 'METADATA':
                        return f"Metadata-Version: 2.1\nName: {self.name}\nVersion: {self._version}\n"
                    return None
            
            # Check our custom finder
            for finder in sys.meta_path:
                if isinstance(finder, MetadataFinder):
                    version = finder.get_version(name)
                    if version:
                        return MinimalDistribution(name, version)
        
        # If we got here, we couldn't find the package
        raise

def patch_metadata():
    """Apply all patches to importlib.metadata."""
    # Add our custom finder
    sys.meta_path.insert(0, MetadataFinder())
    
    # Patch the functions
    importlib.metadata.version = patched_version
    importlib.metadata.distribution = patched_distribution
    
    print("Streamlit metadata patching applied successfully")

if __name__ == '__main__':
    patch_metadata() 