"""
Download module for GoPro video collection
"""

from .adapter import DownloadAdapter, create_download_adapter, get_download_path

__all__ = ['DownloadAdapter', 'create_download_adapter', 'get_download_path']
