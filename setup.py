from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent

# Đọc requirements.txt, loại bỏ comment và dòng trống
def parse_requirements(path):
    lines = (here / path).read_text().splitlines()
    reqs = [
        line.strip() 
        for line in lines 
        if line.strip() and not line.strip().startswith("#")
    ]
    return reqs

setup(
    name="multi_agent",
    version="0.1.0",
    package_dir={"": "src"},     # backend code nằm trong src/, nên chỉ định package_dir như này
    packages=find_packages(where="src"),
    install_requires=parse_requirements("requirements.txt"),
    include_package_data=True,
)