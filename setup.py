from setuptools import setup

setup(
    name='mistra',
    version='0.0.11',
    packages=['mistra.core',
              'mistra.core.growing_arrays',
              'mistra.core.indicators',
              'mistra.core.indicators.mixins',
              'mistra.core.indicators.stats',
              'mistra.core.utils',
              'mistra.core.utils.mappers'],
    url='',
    license='MIT',
    author='luismasuelli',
    author_email='luisfmasuelli@gmail.com',
    description='MISTRA (Market InSights / TRading Algorithms) provides core support to market timelapses and indicators management',
    python_requires='>=3.3',
    install_requires=['numpy==1.17.4', 'requests==2.22.0', 'scipy==1.3.2']
)
