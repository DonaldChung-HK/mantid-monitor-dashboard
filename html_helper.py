import html

class html_helper():
    @staticmethod
    def make_html_safe(string):
        """Return a string that is HTML safe

        Args:
            string (str): string

        Returns:
            str: HTML safe string
        """
        return html.escape(string)
    @staticmethod
    def make_html_safe_replace_newline(string, newline_char='\n'):
        """Return a string that is HTML safe with newline character replaced with <br>

        Args:
            string (str): string
            newline_char(str): character to replace for newline

        Returns:
            str: HTML safe string with newline character
        """
        return html.escape(string).replace(newline_char, "<br>")

