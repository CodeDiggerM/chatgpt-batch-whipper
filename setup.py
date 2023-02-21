from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    install_requirement = f.readlines()

setup(
    name="chatGPT Bach Whipper",
    version="0.1.0",
    author="Codedigger",
    author_email="zhichao.liu@hotmail.com",
    description="The ChatGPT Batch Whipper is a tool designed to simplify batch jobs using ChatGPT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CodeDiggerM/chatgpt-batch-whipper",
    packages=find_packages(),
    install_requires=install_requirement,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "run_chatgpt = chatgpt_batch_whipper.main:main"
        ]
    },
    scripts=["postinstall.sh"],
)