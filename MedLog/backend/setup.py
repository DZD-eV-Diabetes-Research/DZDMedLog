from setuptools import setup
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="DZDMedLog Server",
    description="A Rest API Server on a Postgres DB to store the medical history of study participants.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DZD-eV-Diabetes-Research/DZDMedLog",
    author="TB",
    author_email="tim.bleimehl@helmholtz-munich.de",
    license="MIT",
    packages=["MedLogServer"],
    install_requires=["fastapi", "sqlmodel", "fastapi-users[sqlalchemy,oauth]"],
    extras_require={
        "tests": ["pytest", "deepdiff"],
        "docs": [
            "mkdocs",
            "mkdocstrings[python]",
            "mkdocs-autorefs",
            "mkdocs-material",
        ],
    },
    python_requires=">=3.10",
    zip_safe=False,
    include_package_data=True,
    use_scm_version={
        "root": ".",
        "relative_to": __file__,
        # "local_scheme": "node-and-timestamp"
        "local_scheme": "no-local-version",
        "write_to": "version.py",
    },
    setup_requires=["setuptools_scm"],
)
