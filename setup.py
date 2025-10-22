from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pg-monitor-cli",
    version="1.0.0",
    author="Your Name",
    description="A lightweight PostgreSQL monitoring CLI tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pg-monitor-cli",
    py_modules=["pg_monitor"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "psycopg2-binary>=2.9.9",
        "python-dotenv>=1.0.0",
        "tabulate>=0.9.0",
        "click>=8.1.7",
    ],
    entry_points={
        "console_scripts": [
            "pg-monitor=pg_monitor:main",
        ],
    },
)
