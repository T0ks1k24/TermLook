import unittest
from unittest.mock import Mock
from termlook.services.terminal import TerminalSession, shell_environment, user_shell


class ShellEnvironmentTests(unittest.TestCase):
    def test_outside_snap_keeps_environment(self):
        env = shell_environment(['HOME=/home/user', 'PATH=/usr/bin', 'EMPTY=', 'TERM=dumb'])
        self.assertEqual(sorted(env), ['EMPTY=', 'HOME=/home/user', 'PATH=/usr/bin', 'TERM=xterm-256color'])

    def test_classic_snap_restores_launcher_changes(self):
        env = shell_environment([
            'HOME=/home/user', 'PATH=/usr/bin', 'SNAP=/snap/termlook/x2', 'SNAP_NAME=termlook',
            'XDG_DATA_DIRS=/snap/termlook/x2/usr/share:/usr/share',
            'TERMLOOK_SNAP_ORIG_XDG_DATA_DIRS=/usr/share',
            'LD_LIBRARY_PATH=/snap/termlook/x2/usr/lib/x86_64-linux-gnu',
            'GDK_PIXBUF_MODULE_FILE=/cache',
            'TERMLOOK_SNAP_RESTORE=XDG_DATA_DIRS LD_LIBRARY_PATH GDK_PIXBUF_MODULE_FILE',
        ])
        self.assertEqual(sorted(env), ['HOME=/home/user', 'PATH=/usr/bin', 'TERM=xterm-256color',
                                       'XDG_DATA_DIRS=/usr/share'])

    def test_snap_variables_survive_without_launcher(self):
        env = shell_environment(['SNAP=/snap/other/1', 'SNAP_NAME=other'])
        self.assertIn('SNAP=/snap/other/1', env)

    def test_invalid_configured_shell_falls_back(self):
        self.assertNotEqual(user_shell('/missing/shell'), '/missing/shell')
        self.assertEqual(user_shell('/bin/sh'), '/bin/sh')


class DirectoryNotificationTests(unittest.TestCase):
    def test_repeated_directory_notification_does_not_save(self):
        session = TerminalSession.__new__(TerminalSession)
        session.closed = False
        session.tab = Mock(cwd='/tmp')
        session.on_directory = Mock()
        terminal = Mock()
        terminal.get_current_directory_uri.return_value = 'file:///tmp'
        session._directory(terminal, None)
        session.on_directory.assert_not_called()
        terminal.get_current_directory_uri.return_value = 'file:///'
        session._directory(terminal, None)
        self.assertEqual(session.tab.cwd, '/')
        session.on_directory.assert_called_once()


if __name__ == '__main__':
    unittest.main()
