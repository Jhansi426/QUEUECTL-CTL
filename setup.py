from setuptools import setup, find_packages

setup(
    name="queuectl",
    version="1.0.0",
    # author="Your Name",
    # author_email="youremail@example.com",
    description="QueueCTL - A CLI-based background job queue system with workers, DLQ, and dashboard",
    long_description=open("README.md").read() if open("README.md", "r") else "",
    long_description_content_type="text/markdown",
    # url="https://github.com/yourusername/queuectl",
    license="MIT",
    packages=find_packages(include=["core*", "cli*", "web*"]),
    py_modules=["main"],
    include_package_data=True,
    install_requires=[
        "typer>=0.9.0",
        "flask>=3.0.0",
        "python-dateutil>=2.8.2",
    ],
    entry_points={
        "console_scripts": [
            "queuectl=main:app",
        ],
    },
    python_requires=">=3.9",
)