import sys
import codecs

try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
except (AttributeError, TypeError):
    # Handle cases where stdout doesn't have encoding attribute or buffer
    pass
