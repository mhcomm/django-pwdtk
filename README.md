# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/mhcomm/django-pwdtk/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                              |    Stmts |     Miss |   Cover |   Missing |
|---------------------------------- | -------: | -------: | ------: | --------: |
| pwdtk/\_\_init\_\_.py             |        3 |        1 |     67% |         4 |
| pwdtk/admin.py                    |        6 |        0 |    100% |           |
| pwdtk/apps.py                     |       11 |        0 |    100% |           |
| pwdtk/auth\_backends.py           |       37 |        1 |     97% |        24 |
| pwdtk/auth\_backends\_settings.py |        4 |        4 |      0% |       1-7 |
| pwdtk/checks.py                   |       12 |        0 |    100% |           |
| pwdtk/exceptions.py               |        6 |        0 |    100% |           |
| pwdtk/helpers.py                  |       27 |       15 |     44% |11-19, 24-30, 40-42 |
| pwdtk/middlewares.py              |       24 |        5 |     79% |8-10, 26, 49 |
| pwdtk/models.py                   |      111 |        5 |     95% |21-22, 30, 35-36 |
| pwdtk/settings.py                 |       29 |        0 |    100% |           |
| pwdtk/signals.py                  |        2 |        0 |    100% |           |
| pwdtk/validators.py               |       84 |       10 |     88% |40, 53, 80, 83, 110, 148, 176, 204, 239, 259 |
| **TOTAL**                         |  **356** |   **41** | **88%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/mhcomm/django-pwdtk/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/mhcomm/django-pwdtk/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/mhcomm/django-pwdtk/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/mhcomm/django-pwdtk/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fmhcomm%2Fdjango-pwdtk%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/mhcomm/django-pwdtk/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.