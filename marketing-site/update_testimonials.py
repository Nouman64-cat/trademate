import re

filepath = "app/case-studies/page.tsx"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

new_case_studies = """const caseStudies = [
  {
    id: "saeed-trading",
    company: "Saeed Trading and Co.",
    industry: "Textiles & General Merchandise",
    role: "Importer",
    location: "Lahore, Pakistan",
    logo: "S",
    stats: [
      { label: "Time Saved", value: "85%", description: "Reduced classification time" },
      { label: "Duty Savings", value: "$120K", description: "Annual duty optimization" },
      { label: "HS Accuracy", value: "99.9%", description: "Classification accuracy" },
    ],
    challenge:
      "Saeed Trading and Co. was spending hours manually classifying products across hundreds of SKUs. HS code errors were causing customs delays and unexpected duty costs. They needed a faster, more accurate way to classify shipments.",
    solution:
      `${process.env.NEXT_PUBLIC_APP_NAME}'s AI automatically classifies each product and identifies applicable SRO exemptions. The team now generates accurate HS codes in seconds with full duty breakdowns.`,
    result:
      "85% reduction in classification time, $120K annual duty savings from correct SRO identification, and zero customs delays in the past year.",
  },
  {
    id: "rizviz",
    company: "Rizviz International Impex",
    industry: "Logistics",
    role: "Freight Forwarder",
    location: "Karachi, Pakistan",
    logo: "R",
    stats: [
      { label: "Quote Time", value: "85%", description: "Faster quote generation" },
      { label: "Client Growth", value: "+40%", description: "New clients YoY" },
      { label: "Revenue", value: "+35%", description: "Increased revenue" },
    ],
    challenge:
      "Rizviz International Impex was struggling to calculate accurate landed costs for complex shipments due to constantly changing tariffs and shipping rates, causing them to lose deals to competitors who provided faster quotes.",
    solution:
      `${process.env.NEXT_PUBLIC_APP_NAME}'s conversational interface and live shipping rate data provide complete DDP breakdowns and route optimizations in seconds, directly within the chat.`,
    result:
      "85% faster quote generation, won 40% more deals, and 35% revenue increase. Clients love the instant, accurate cost breakdowns.",
  },
  {
    id: "fed-point",
    company: "Fed Point",
    industry: "Electronics & Tech",
    role: "Importer",
    location: "Islamabad, Pakistan",
    logo: "F",
    stats: [
      { label: "Research Time", value: "-90%", description: "Less time reading docs" },
      { label: "Tariff Coverage", value: "100%", description: "PK + US coverage" },
      { label: "Compliance", value: "100%", description: "Perfect documentation" },
    ],
    challenge:
      "Fed Point's team was bogged down trying to navigate complex compliance documentation, multi-layered SROs, and regulatory requirements for multiple product categories.",
    solution:
      `${process.env.NEXT_PUBLIC_APP_NAME}'s semantic document retrieval system allows them to instantly query official customs schedules and regulatory documents in plain English.`,
    result:
      "Compliance research time cut from hours to seconds. The team now confidently navigates complex regulations, ensuring perfectly documented and compliant shipments.",
  },
];"""

new_testimonials = """const testimonials = [
  {
    id: "t-1",
    quote:
      `${process.env.NEXT_PUBLIC_APP_NAME} cut our HS code classification time from hours to seconds. What used to require sifting through multiple databases and a compliance expert is now a single AI-powered query.`,
    author: "Adnan Saeed Rizvi",
    title: "CEO",
    company: "Saeed Trading and Co.",
  },
  {
    id: "t-2",
    quote:
      "The real-time tariff and shipping analysis is game-changing. Being able to ask 'what's the total landed cost from Karachi to Los Angeles?' and get a breakdown instantly gives us a massive edge over our competitors.",
    author: "Syed Faraz Mehdi",
    title: "Operations Director",
    company: "Rizviz International Impex",
  },
  {
    id: "t-3",
    quote:
      `${process.env.NEXT_PUBLIC_APP_NAME}'s ability to instantly retrieve and summarize complex customs documents and SROs has transformed our workflow. It's literally like having a trade expert available 24/7.`,
    author: "Furqan Saeed",
    title: "Managing Partner",
    company: "Fed Point",
  },
];"""

content = re.sub(r"const caseStudies = \[.*?\];", new_case_studies, content, flags=re.DOTALL)
content = re.sub(r"const testimonials = \[.*?\];", new_testimonials, content, flags=re.DOTALL)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated testimonials")
