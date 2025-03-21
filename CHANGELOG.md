# [Changelog](https://github.com/mhcomm/django-pwdtk/releases)

## [v2.0.0](https://github.com/mhcomm/django-pwdtk/compare/v1.1.0...v2.0.0)
* Version bump to 2.0.0
* Removed watchers
* Add password history validation
  - Prevents users from reusing their previous passwords
  - Configurable history length via PWDTK_PASSWD_HISTORY_LEN setting
  - Automatically tracks and stores password hashes with timestamps
* Add regex-based password validation
  - Enforces password complexity rules via regex patterns
  - Configurable via PWDTK_PASSWORD_ALLOWED_PATTERN setting
  - Customizable error messages with PWDTK_PASSWORD_DEFAULT_PATTERN_INFO
  - Supports common patterns like requiring letters, numbers, and special characters
## [v1.0.0](https://github.com/mhcomm/django-pwdtk/compare/v0.4.0...v1.0.0)
* break django 1.11 compatibility
* break python < 3.7 compatibility
* security fix: block logins with non existing user names after count
* add support for django 3.1
* new redirect policy (no more default redirect)
* major restructuring. breaks compatibility with 0.4.0
## [v0.4.0](https://github.com/mhcomm/django-pwdtk/compare/v0.3.1...v0.4.0)
* break django 1.8 compatibility
* add support for django 2.2
## [v0.3.1](https://github.com/mhcomm/django-pwdtk/compare/v0.3.0...v0.3.1)
* fix for migrations
## [v0.3.0](https://github.com/mhcomm/django-pwdtk/compare/v0.2.9...v0.3.0)
* allow to fetch settings not only from django settings if needed (PWDTK_CUSTOM_SETTINGS_CLS)
* add PWDTK_LOCKOUT_VIEW for lockout redirection
* large refactoring
## [v0.2.9](https://github.com/mhcomm/django-pwdtk/compare/v0.2.8...v0.2.9)
* fix bug w py36/dj1.11 + MIDDLEWARE_CLASSES
* add CI for py36 with django 1.11 and old style MIDDLEWARE_CLASSES
## [v0.2.8](https://github.com/mhcomm/django-pwdtk/compare/v0.2.7...v0.2.8)
* fix CI runners (limit max version for some packages)
* allow to completely disable pwdtk
## [v0.2.7](https://github.com/mhcomm/django-pwdtk/compare/v0.2.6...v0.2.7)
* same as 0.2.7, but rebuilt somehow a bad migration file slipped into the release
## [v0.2.6](https://github.com/mhcomm/django-pwdtk/compare/v0.2.5...v0.2.6)
* add migrations to force uniqueness on PwdData (PwdData.username should be unique)
## [v0.2.5](https://github.com/mhcomm/django-pwdtk/compare/v0.2.4...v0.2.5)
* fix requirements in order to remain py2 compatible (limit minibelt to < 0.2.0)
## [v0.2.4](https://github.com/mhcomm/django-pwdtk/compare/v0.2.3...v0.2.4)
* fix bug #13 (potential issues with django introspection due to monkey patches
## [v0.2.3](https://github.com/mhcomm/django-pwdtk/compare/v0.2.2...v0.2.3)
* improve project description
* improve README slightly
* update changelog
## [v0.2.2](https://github.com/mhcomm/django-pwdtk/compare/v0.2.1...v0.2.2)
* fix bug #8 (recursion issue if password set with non default hash and user logs in)
* add some CI test for py2 py3 django 1.8 / django 1.11
* TODO: improve documentation / README / changelog
## [v0.2.1](https://github.com/mhcomm/django-pwdtk/compare/0.2.0...v0.2.1)
* auto discover modules for release generation (forgot migrations in prev release)
* test projects use django_extensions if installed
* add license file + release notes
* add a few more logs and comments

## [0.2.0](https://github.com/mhcomm/django-pwdtk/compare/0.1.0...0.2.0)
* minor fixes on py2 py3 compatibility
* more data for lockout template (minutes and seconds are calculated and passed)
* passwd change templatge should now be working

## [0.1.0](https://github.com/mhcomm/django-pwdtk/compare/9a16261b1abb56df9fd28a251358196fca438219...0.2.0)
