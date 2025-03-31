import setuptools

setuptools.setup(
    name="gopy_machine",
    packages=setuptools.find_packages(include=["gopy_machine"]),
    py_modules=["gopy_machine.service"],
    package_data={"gopy_machine": ["*.so"]},
    include_package_data=True,
)
