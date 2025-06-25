from __future__ import absolute_import


# third party modules
from setuptools import find_packages
from setuptools import setup

install_requires = [
    "django-jsonfield-backport",
    "future",
    "minibelt",
    "python-dateutil",
    "pytz",
    ]


long_description = """package to tune django password authentification

It spans a rather wide range of python and django versions and supports:
- temporary lockout after too many bad logins.
- max life time for passwords
""",

setup(
    name="django-pwdtk",
    version="2.0.3",
    description="package to tune django password authentification",
    # long_description=long_description,
    # long_description_content_type="text/x-rst",
    classifiers=[
        "Development Status :: 3 - Alpha",
        ],
    keywords="django authentification password",
    url="https://github.com/mhcomm/django-pwdtk",
    author="MHComm",
    author_email="info@mhcomm.fr",
    license="MIT",
    packages=find_packages(),
    scripts=[],
    entry_points={
        "console_scripts": [
          ]
    },
    project_urls={
      "Documentation": "https://github.com/mhcomm/django-pwdtk",
      "Source": "https://github.com/mhcomm/django-pwdtk",
      "SayThanks": "https://github.com/mhcomm",
      "Funding": "https://donate.pypi.org",
      "Tracker": "https://github.com/mhcomm/django-pwdtk/issues",
    },
    # TODO in the near future
    # python_requires=">=3.6, <4",
    python_requires=">=3.7, <4",
    include_package_data=True,
    )
