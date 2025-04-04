from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        packages=find_packages(),
        entry_points={
            'pytest11': [
                'scenario = scenario.pytest_plugin',
            ]
        }
    )