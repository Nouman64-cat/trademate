import os

files_to_fix = [
    "app/importers/page.tsx",
    "app/exporters/page.tsx",
    "app/freight-forwarders/page.tsx",
    "components/contact/ContactForm.tsx"
]

replacements = [
    ('See TradeMate{" "}', 'See {process.env.NEXT_PUBLIC_APP_NAME}{" "}'),
    ('Why Importers Choose TradeMate', 'Why Importers Choose {process.env.NEXT_PUBLIC_APP_NAME}'),
    ('Why Exporters Choose TradeMate', 'Why Exporters Choose {process.env.NEXT_PUBLIC_APP_NAME}'),
    ('Why Forwarders Choose TradeMate', 'Why Forwarders Choose {process.env.NEXT_PUBLIC_APP_NAME}'),
    ('"TradeMate helps importers', '`${process.env.NEXT_PUBLIC_APP_NAME} helps importers'),
    ('"TradeMate helps freight', '`${process.env.NEXT_PUBLIC_APP_NAME} helps freight'),
    ('"TradeMate helps exporters', '`${process.env.NEXT_PUBLIC_APP_NAME} helps exporters'),
    ('analysis."', 'analysis.`'),
    ('intelligence."', 'intelligence.`'),
    ('markets."', 'markets.`'),
    ('TradeMate handles all major', '{process.env.NEXT_PUBLIC_APP_NAME} handles all major'),
    ('How forwarders use TradeMate', 'How forwarders use {process.env.NEXT_PUBLIC_APP_NAME}')
]

# Wait, I just remembered: `analysis."`, `intelligence."`, `markets."` will be replaced to `analysis.\`` 
# because I used ``${process.env.NEXT_PUBLIC_APP_NAME} helps importers` for the opening quote!
# Ah! I need to replace the closing quote with a backtick as well for those descriptions to be valid template literals!
# BUT the previous error was because I replaced `analysis."` with `analysis.\`` but maybe it didn't find the opening quote because `TradeMate helps importers` wasn't exactly that? 

# Let's write this much smarter.
import re

for filepath in files_to_fix:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. JSX inner text replacements
    content = content.replace('See TradeMate{" "}', 'See {process.env.NEXT_PUBLIC_APP_NAME}{" "}')
    content = content.replace('Why Importers Choose TradeMate', 'Why Importers Choose {process.env.NEXT_PUBLIC_APP_NAME}')
    content = content.replace('Why Exporters Choose TradeMate', 'Why Exporters Choose {process.env.NEXT_PUBLIC_APP_NAME}')
    content = content.replace('Why Forwarders Choose TradeMate', 'Why Forwarders Choose {process.env.NEXT_PUBLIC_APP_NAME}')
    content = content.replace('TradeMate handles all major', '{process.env.NEXT_PUBLIC_APP_NAME} handles all major')
    content = content.replace('How forwarders use TradeMate', 'How forwarders use {process.env.NEXT_PUBLIC_APP_NAME}')
    
    # 2. String literal to template literal replacements
    content = re.sub(r'"([^\n"\\]*?)(TradeMate|IntelliTrade|intellotrade)([^\n"\\]*?)"', r'`\1${process.env.NEXT_PUBLIC_APP_NAME}\3`', content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Safe replace complete")
