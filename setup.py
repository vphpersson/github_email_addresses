from setuptools import setup, find_packages

setup(
    name='github_email_addresses',
    version='0.11',
    packages=find_packages(),
    install_requires=[
        'httpx',
        'typed_argument_parser @ git+https://github.com/vphpersson/typed_argument_parser.git#egg=typed_argument_parser',
        'strings_utils_py @ git+https://github.com/vphpersson/string_utils_py.git#egg=string_utils_py'
    ]
)
