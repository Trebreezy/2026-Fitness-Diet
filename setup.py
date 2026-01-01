"""
Setup script for Fitness & Diet Logger
"""
from setuptools import setup, find_packages

setup(
    name="fitness-diet-logger",
    version="1.0.0",
    description="A fitness and diet logging system with Notion integration and Claude Code MCP support",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "notion-client>=2.0.0",
        "python-dotenv>=1.0.0",
        "Pillow>=10.0.0",
        "SpeechRecognition>=3.10.0",
        "pydub>=0.25.1",
        "mcp>=1.0.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "pandas>=2.0.0",
        "httpx>=0.25.0",
        "python-dateutil>=2.8.0",
    ],
    entry_points={
        "console_scripts": [
            "fitness-log=src.cli:main",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
