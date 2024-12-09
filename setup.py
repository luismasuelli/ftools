from setuptools import setup

setup(
    name='mistra',
    version='0.1.8',
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
    description='MISTRA (Market InSights / TRading Algorithms) provides core support to market '
                'timelapses and indicators management',
    python_requires='>=3.12',
    install_requires=['numpy>=2.1.3', 'requests>=2.22.0', 'scipy>=1.14.1']
)
