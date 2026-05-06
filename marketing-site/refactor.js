const fs = require("fs");
const path = require("path");

const DIR = ".";
const ignoreDirs = ["node_modules", ".next", ".git"];

function walk(dir, callback) {
  fs.readdirSync(dir).forEach((f) => {
    let dirPath = path.join(dir, f);
    let isDirectory = fs.statSync(dirPath).isDirectory();
    if (isDirectory) {
      if (!ignoreDirs.includes(f)) {
        walk(dirPath, callback);
      }
    } else {
      if (dirPath.endsWith(".tsx") || dirPath.endsWith(".ts")) {
        callback(dirPath);
      }
    }
  });
}

function processFile(filePath) {
  let originalContent = fs.readFileSync(filePath, "utf-8");
  let content = originalContent;

  const targets = /(intellitrade|intellotrade|trademate)/ig;

  if (!targets.test(content)) return;

  // 1. Double Quoted Strings (e.g. description: "TradeMate is...") -> description: `${process.env.NEXT_PUBLIC_APP_NAME} is...`
  content = content.replace(/"([^"\\]*?)(IntelliTrade|intellotrade|intellitrade|TradeMate|trademate)([^"\\]*?)"/g, (match, p1, p2, p3) => {
    // skip urls/emails for now
    if (match.includes("http") || match.includes("@") || match.includes(".com")) return match;
    // skip imports
    if (match.includes("/") && match.includes(".")) return match;
    
    // Replace all instances inside this string
    let inner = match.slice(1, -1);
    let replaced = inner.replace(targets, '${process.env.NEXT_PUBLIC_APP_NAME}');
    return '`' + replaced + '`';
  });

  // 2. Single Quoted Strings
  content = content.replace(/'([^'\\]*?)(IntelliTrade|intellotrade|intellitrade|TradeMate|trademate)([^'\\]*?)'/g, (match, p1, p2, p3) => {
    if (match.includes("http") || match.includes("@") || match.includes(".com")) return match;
    if (match.includes("/") && match.includes(".")) return match;
    
    let inner = match.slice(1, -1);
    let replaced = inner.replace(targets, '${process.env.NEXT_PUBLIC_APP_NAME}');
    return '`' + replaced + '`';
  });

  // 3. Existing Template Literals
  content = content.replace(/`([^`\\]*?)(IntelliTrade|intellotrade|intellitrade|TradeMate|trademate)([^`\\]*?)`/g, (match, p1, p2, p3) => {
    if (match.includes("http") || match.includes("@") || match.includes(".com")) return match;
    
    let inner = match.slice(1, -1);
    let replaced = inner.replace(targets, '${process.env.NEXT_PUBLIC_APP_NAME}');
    return '`' + replaced + '`';
  });

  // 4. JSX Text Nodes (e.g. <h1>Welcome to TradeMate</h1>)
  // This is tricky without AST, but we can look for plain text instances.
  // A safe way is to replace word boundaries.
  // e.g. `>TradeMate<` -> `>{process.env.NEXT_PUBLIC_APP_NAME}<`
  content = content.replace(/>([^<]*?)(IntelliTrade|TradeMate)([^<]*?)</g, (match, p1, p2, p3) => {
    let inner = match.slice(1, -1);
    let replaced = inner.replace(targets, '{process.env.NEXT_PUBLIC_APP_NAME}');
    return '>' + replaced + '<';
  });

  // Emails and URLs handling (optional depending on instruction, but we leave them or replace safely)
  // The user said: "Limit your search... Replace all hardcoded instances"

  if (content !== originalContent) {
    console.log(`Updated ${filePath}`);
    fs.writeFileSync(filePath, content, "utf-8");
  }
}

walk(DIR, processFile);
console.log("Done refactoring.");
