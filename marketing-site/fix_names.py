import os
import re

targets = [r'intellitrade', r'intellotrade', r'trademate']
pattern = re.compile(f'(?i)({"|".join(targets)})')

def replace_in_tsx(content):
    # This is a basic replacement strategy. It's difficult to perfectly parse TSX with regex,
    # but we can handle common cases:
    # 1. Inside existing template literals: `${process.env.NEXT_PUBLIC_APP_NAME}`
    # 2. Inside normal JSX text: `{process.env.NEXT_PUBLIC_APP_NAME}`
    # 3. Inside standard strings (double/single quotes): we will convert to template literals or concatenate.
    
    # Actually, the user's instruction is very specific:
    # Example: <h1>Welcome to {process.env.NEXT_PUBLIC_APP_NAME}</h1>
    # Example: <input placeholder={`Search ${process.env.NEXT_PUBLIC_APP_NAME}...`} />
    
    # We will just replace it with `{process.env.NEXT_PUBLIC_APP_NAME}` in JSX text,
    # and `${process.env.NEXT_PUBLIC_APP_NAME}` in template literals.
    # For strings like "Welcome to TradeMate", we change to `Welcome to ${process.env.NEXT_PUBLIC_APP_NAME}`
    
    # Since writing a perfect parser is hard, let's use a simpler approach.
    pass

