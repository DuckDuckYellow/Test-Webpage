"""
Parser Factory for Football Manager HTML Exports.
"""

from bs4 import BeautifulSoup
from typing import Union
from services.fm_parser import FMHTMLParser
from services.fm_parser_v2 import FMHTMLParserV2

class ParserFactory:
    """Detects the appropriate parser based on the HTML structure."""
    
    @staticmethod
    def get_parser(html_content: str) -> Union[FMHTMLParser, FMHTMLParserV2]:
        """
        Detects column count and returns the appropriate parser instance.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('table')
        
        if not table:
            raise ValueError("No table found in HTML content")
            
        headers = [th.get_text().strip() for th in table.find_all('th')]
        column_count = len(headers)
        
        if column_count == 32:
            return FMHTMLParserV2()
        else:
            # Fallback to legacy parser for other column counts
            return FMHTMLParser()
