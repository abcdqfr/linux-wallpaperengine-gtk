"""Machine-optimized name conversion utility."""

import re
from typing import Dict, Set, List, Optional, Tuple

class N:  # NameOptimizer
    """KEY: Machine-optimized name conversion
    p: patterns dict
    r: reserved words set
    """
    def __init__(s):
        # Core patterns with Unicode where applicable
        s.p = {
            r'\b(self|this)\b': 'ꜱ',  # Latin small letter s
            r'\b(parent|root)\b': 'ᴘ',  # Latin letter p
            r'\b(window|widget)\b': 'ᴡ',  # Latin letter w
            r'\b(logger|log)\b': 'ʟ',  # Latin letter l
            r'\b(display|directory)\b': 'ᴅ',  # Latin letter d
            r'\b(current|command)\b': 'ᴄ',  # Latin letter c
            r'\b(engine|event)\b': 'ᴇ',  # Latin letter e
            r'\b(manager|model)\b': 'ᴍ',  # Latin letter m
            r'\b(button|box)\b': 'ʙ',  # Latin letter b
            r'\b(value|view)\b': 'ᴠ',  # Latin letter v
            r'\b(text|type)\b': 'ᴛ',  # Latin letter t
            r'\b(frame|file)\b': 'ꜰ',  # Latin letter f
            r'\b(image|item)\b': 'ɪ',  # Latin letter i
            r'\b(object|option)\b': 'ᴏ',  # Latin letter o
            r'\b(name|node)\b': 'ɴ',  # Latin letter n
            r'\b(queue|query)\b': 'ǫ',  # Latin letter q with ogonek
            r'\b(result|response)\b': 'ʀ',  # Latin letter r
            r'\b(status|state)\b': 'ꜱᴛ',  # st combination
            r'\b(update|utility)\b': 'ᴜ',  # Latin letter u
            r'\b(error|exception)\b': 'ᴇx',  # ex combination
            r'\b(yield|year)\b': 'ʏ',  # Latin letter y
            r'\b(zero|zoom)\b': 'ᴢ',  # Latin letter z
            # Method patterns
            r'\bupdate_window\b': 'ᴜᴡ',
            r'\binfo\b': 'ɪɴꜰ',
            r'\bcurrent_widget\b': 'ᴄᴡ',
            # Class patterns
            r'\bWindowManager\b': 'Wᴍ',
            r'\bLogger\b': 'Lɢ'
        }
        
        # Reserved words (never convert)
        s.r = set([
            # Python keywords
            'if', 'else', 'elif', 'while', 'for', 'in', 'is', 'not',
            'and', 'or', 'True', 'False', 'None', 'try', 'except',
            'finally', 'with', 'as', 'def', 'class', 'return', 'yield',
            'break', 'continue', 'pass', 'raise', 'from', 'import',
            'global', 'nonlocal', 'assert', 'del', 'lambda',
            # Common operators
            'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple',
            'min', 'max', 'sum', 'any', 'all', 'zip', 'map', 'filter',
            # Common variables
            'i', 'j', 'k', 'x', 'y', 'z', 'n', 'm',
            # Special methods
            '__init__', '__str__', '__repr__', '__len__', '__call__',
            '__enter__', '__exit__', '__iter__', '__next__', '__getitem__',
            '__setitem__', '__delitem__', '__contains__'
        ])
    
    def c(s, text: str) -> str:
        """Convert text to machine-optimized form"""
        parts = s._split_code(text)
        result = []
        
        for type_, content in parts:
            if type_ == 'code':
                # Apply patterns
                for pattern, repl in s.p.items():
                    content = re.sub(pattern, repl, content)
            elif type_ == 'string':
                # Preserve string content exactly
                result.append(content)
                continue
            elif type_ == 'comment':
                # Preserve comment content exactly
                result.append(content)
                continue
            result.append(content)
        
        return ''.join(result)
    
    def _split_code(s, text: str) -> List[Tuple[str, str]]:
        """Split text into code, string, and comment parts."""
        parts = []
        i = 0
        length = len(text)
        current = []
        
        while i < length:
            char = text[i]
            
            # Handle strings
            if char in ('"', "'"):
                if current:
                    parts.append(('code', ''.join(current)))
                    current = []
                
                quote = char
                string_content = [quote]
                i += 1
                
                while i < length:
                    char = text[i]
                    string_content.append(char)
                    i += 1
                    if char == quote:
                        break
                
                parts.append(('string', ''.join(string_content)))
                continue
            
            # Handle comments
            if char == '#':
                if current:
                    parts.append(('code', ''.join(current)))
                    current = []
                
                comment_content = ['#']
                i += 1
                
                while i < length and text[i] != '\n':
                    comment_content.append(text[i])
                    i += 1
                
                if i < length:  # Include newline if present
                    comment_content.append(text[i])
                    i += 1
                
                parts.append(('comment', ''.join(comment_content)))
                continue
            
            current.append(char)
            i += 1
        
        if current:
            parts.append(('code', ''.join(current)))
        
        return parts
    
    def ᴀ(s, pattern: str, repl: str) -> None:
        """Add new pattern
        pattern: regex pattern
        repl: replacement
        """
        if pattern not in s.p and repl not in s.r:
            s.p[pattern] = repl
    
    def ᴅ(s, pattern: str) -> None:
        """Delete pattern
        pattern: regex pattern to remove
        """
        # Find and remove the pattern
        for p in list(s.p.keys()):
            if p == pattern:
                del s.p[p]
                break
    
    # Alias for backward compatibility using Unicode
    a = ᴀ  # add
    r = ᴅ  # delete