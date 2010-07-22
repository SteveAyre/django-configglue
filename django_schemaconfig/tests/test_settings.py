import os.path

import django
from django.conf import settings

from helpers import SchemaConfigDjangoCommandTestCase


class SettingsCommandTestCase(SchemaConfigDjangoCommandTestCase):
    COMMAND = 'settings'

    def test_no_args(self):
        self.call_command()
        self.assertTrue(self.capture['stdout'].startswith('Usage: '))

    def test_get(self):
        self.call_command('installed_apps')
        expected_output = "INSTALLED_APPS = ['django_schemaconfig']"
        self.assertEqual(self.capture['stdout'].strip(), expected_output)

    def test_get_not_found(self):
        self.call_command('bogus')
        expected_output = "setting BOGUS not found"
        self.assertEqual(self.capture['stdout'].strip(), expected_output)

    def test_show(self):
        expected_values = [
            "ROOT_URLCONF = 'urls'",
            "SITE_ID = 1",
            "SETTINGS_MODULE = 'django_schemaconfig.tests.settings'"
        ]
        if django.VERSION[:2] >= (1, 1):
            expected_values.append("DATABASE_SUPPORTS_TRANSACTIONS = True")
        self.call_command(show_current=True)
        output_lines = self.capture['stdout'].strip().split('\n')
        self.assertEqual(set(expected_values), set(output_lines))

    def test_show_global(self):
        self.call_command(show_current=True, include_global=True)
        expected_output = dict([(key, getattr(settings, key)) for key in
            dir(settings) if self.is_setting(key)])
        # process output into dictionary
        items = map(lambda x: x.split(' = '),
                    self.capture['stdout'].strip().split('\n'))
        items = map(lambda x: (x[0].strip(), eval(x[1].strip())),
            (t for t in items if self.is_setting(t[0])))
        output = dict(items)
        # test equality
        self.assertEqual(output, expected_output)

    def test_locate_setting(self):
        self.call_command('time_zone', locate=True)
        location = os.path.join(os.path.abspath(os.path.curdir), 'test.cfg')
        expected_output = "setting TIME_ZONE last defined in '%s'" % location
        self.assertEqual(self.capture['stdout'].strip(), expected_output)

    def test_locate_setting_not_found(self):
        self.call_command('bogus', locate=True)
        expected_output = 'setting BOGUS not found'
        self.assertEqual(self.capture['stdout'].strip(), expected_output)


class ValidateCommandTestCase(SchemaConfigDjangoCommandTestCase):
    COMMAND = 'settings'

    def test_valid_config(self):
        self.call_command(validate=True)
        expected_output = 'Settings appear to be fine.'
        self.assertEqual(self.capture['stdout'].strip(), expected_output)

    def test_invalid_config(self):
        config = """
[bogus]
invalid_setting = foo
"""
        self.set_config(config)
        self.load_settings()
        self.assertRaises(SystemExit, self.call_command, validate=True)

        try:
            self.call_command(validate=True)
        except SystemExit, e:
            self.assertEqual(e.code, 1)
            error_msg = 'Error: Settings did not validate against schema.'
            self.assertTrue(self.capture['stderr'].strip().startswith(
                error_msg))

