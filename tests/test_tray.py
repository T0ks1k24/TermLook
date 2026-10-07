import unittest
from unittest.mock import Mock, patch

from termlook.services import tray as tray_module
from termlook.services.tray import Tray


class TrayTests(unittest.TestCase):
    def test_indicator_waits_for_host_and_recovers_when_host_returns(self):
        backend = Mock()
        unavailable = Mock()
        with patch.object(tray_module.gi, 'require_version'), \
             patch.object(tray_module.importlib, 'import_module', return_value=backend), \
             patch.object(tray_module.Gio, 'bus_watch_name', return_value=42), \
             patch.object(tray_module.Gio, 'bus_unwatch_name') as unwatch, \
             patch.object(tray_module, 'Gtk'):
            tray = Tray('/icon.svg', Mock(), Mock(), Mock(), Mock(), unavailable)
            tray._vanished()
            backend.Indicator.new.assert_not_called()
            unavailable.assert_not_called()
            self.assertFalse(tray.available)

            tray._appeared()
            self.assertTrue(tray.available)
            backend.Indicator.new.assert_called_once()
            tray._vanished()
            self.assertFalse(tray.available)
            unavailable.assert_called_once()
            tray.indicator.set_status.assert_called_with(backend.IndicatorStatus.PASSIVE)

            tray._appeared()
            backend.Indicator.new.assert_called_once()
            tray.indicator.set_status.assert_called_with(backend.IndicatorStatus.ACTIVE)
            tray.close()
            unwatch.assert_called_once_with(42)
            self.assertFalse(tray.available)
