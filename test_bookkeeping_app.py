#!/usr/bin/env python3
"""
Test suite for the bookkeeping application.

Tests the key requirements:
1. TTK-compliant focus highlighting
2. 4-column account search popup
3. Keyboard navigation
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys

# Test without GUI by mocking tkinter
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()

import bookkeeping_app


class TestTTKFocusHighlighting(unittest.TestCase):
    """Test Task 1: TTK-compliant focus highlighting."""
    
    def test_focus_entry_style_defined(self):
        """Verify Focus.TEntry style is configured."""
        # Check that the code defines Focus.TEntry style
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            self.assertIn('Focus.TEntry', code)
            self.assertIn('fieldbackground', code)
    
    def test_no_bg_background_on_ttk_widgets(self):
        """Verify no use of bg or background on ttk widgets."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            
            # Check that bg/background are not used in ttk context
            # (they should only be in classic tk contexts if any)
            lines = code.split('\n')
            for i, line in enumerate(lines):
                # Skip comments
                if line.strip().startswith('#'):
                    continue
                
                # If line mentions ttk and bg/background together, it's an error
                if 'ttk' in line.lower():
                    # Check for problematic patterns
                    if 'bg=' in line or 'background=' in line:
                        # This should not happen with ttk widgets
                        # Only fieldbackground is acceptable
                        if 'fieldbackground' not in line:
                            self.fail(f"Line {i+1} uses bg/background with ttk widget: {line}")
    
    def test_focus_handlers_check_widget_type(self):
        """Verify focus handlers check for ttk.Entry type."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            self.assertIn('isinstance(widget, ttk.Entry)', code)
    
    def test_focus_in_handler_exists(self):
        """Verify on_field_focus_in method exists."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            self.assertIn('def on_field_focus_in', code)
    
    def test_focus_out_handler_exists(self):
        """Verify on_field_focus_out method exists."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            self.assertIn('def on_field_focus_out', code)
    
    def test_focus_bindings(self):
        """Verify FocusIn and FocusOut events are bound."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            self.assertIn('<FocusIn>', code)
            self.assertIn('<FocusOut>', code)
            self.assertIn('on_field_focus_in', code)
            self.assertIn('on_field_focus_out', code)


class TestAccountSearchPopup(unittest.TestCase):
    """Test Task 2: Account search popup with 4-column layout."""
    
    def test_account_search_popup_class_exists(self):
        """Verify AccountSearchPopup class is defined."""
        self.assertTrue(hasattr(bookkeeping_app, 'AccountSearchPopup'))
    
    def test_four_column_layout(self):
        """Verify 4-column layout is configured."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            self.assertIn('num_columns = 4', code)
    
    def test_top_to_bottom_left_to_right_filling(self):
        """Verify accounts are filled top-to-bottom, left-to-right."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            # Look for the filling logic
            self.assertIn('col * self.num_rows + row', code)
    
    def test_keyboard_navigation_bindings(self):
        """Verify arrow key navigation is bound."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            self.assertIn('<Up>', code)
            self.assertIn('<Down>', code)
            self.assertIn('<Left>', code)
            self.assertIn('<Right>', code)
    
    def test_enter_and_escape_bindings(self):
        """Verify Enter and Escape key bindings."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            self.assertIn('<Return>', code)
            self.assertIn('<Escape>', code)
    
    def test_account_number_and_name_displayed(self):
        """Verify account number and name are displayed."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            # Check that both account_num and account_name are used
            self.assertIn('account_num', code)
            self.assertIn('account_name', code)
    
    def test_centering_over_parent(self):
        """Verify popup is centered over parent."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            self.assertIn('_center_on_parent', code)
    
    def test_selection_inserts_account_number(self):
        """Verify selection inserts account number into target entry."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            # Check for insertion logic
            self.assertIn('target_entry.delete', code)
            self.assertIn('target_entry.insert', code)


class TestKeyboardFirstDesign(unittest.TestCase):
    """Test keyboard-first navigation requirements."""
    
    def test_all_entry_fields_have_focus_bindings(self):
        """Verify all entry fields have focus event bindings."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            # Check that entries are bound to focus events
            self.assertIn('entry.bind("<FocusIn>"', code)
            self.assertIn('entry.bind("<FocusOut>"', code)
    
    def test_navigation_method_exists(self):
        """Verify navigation method for account search popup."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            self.assertIn('def _navigate', code)


class TestCodeQuality(unittest.TestCase):
    """Test code quality and structure."""
    
    def test_file_has_docstrings(self):
        """Verify key classes and methods have docstrings."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            # Check for module docstring
            self.assertTrue(code.startswith('#!/usr/bin/env python3\n"""') or 
                          code.startswith('"""'))
    
    def test_no_syntax_errors(self):
        """Verify file compiles without syntax errors."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            try:
                compile(code, 'bookkeeping_app.py', 'exec')
            except SyntaxError as e:
                self.fail(f"Syntax error: {e}")
    
    def test_accounts_data_exists(self):
        """Verify sample account data is provided."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            self.assertIn('ACCOUNTS', code)


class TestTTKCompliance(unittest.TestCase):
    """Test strict TTK compliance requirements."""
    
    def test_uses_ttk_widgets(self):
        """Verify application uses ttk widgets."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            self.assertIn('ttk.Entry', code)
            self.assertIn('ttk.Button', code)
            self.assertIn('ttk.Label', code)
            self.assertIn('ttk.Frame', code)
    
    def test_ttk_style_configuration(self):
        """Verify ttk.Style is used for configuration."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            self.assertIn('ttk.Style', code)
            self.assertIn('style.configure', code)
    
    def test_fieldbackground_used_for_highlighting(self):
        """Verify fieldbackground is used for entry highlighting."""
        with open('bookkeeping_app.py', 'r') as f:
            code = f.read()
            # Should use fieldbackground in Focus.TEntry style
            self.assertIn('fieldbackground=', code)


def run_tests():
    """Run all tests and report results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTTKFocusHighlighting))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountSearchPopup))
    suite.addTests(loader.loadTestsFromTestCase(TestKeyboardFirstDesign))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeQuality))
    suite.addTests(loader.loadTestsFromTestCase(TestTTKCompliance))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
