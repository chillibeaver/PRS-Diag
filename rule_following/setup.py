from setuptools import setup, find_packages

setup(
    name="vlm-rule-following-test",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "chess",
        "Pillow",
        "numpy",
        "matplotlib",
        "python-dotenv",
        "requests",
        "openai",
    ],
    description="VLM Diagnostic Framework",
    python_requires=">=3.8",
)
