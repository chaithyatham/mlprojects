# Company registry: ATS type, domain for logo, VC backer
# Greenhouse API: https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
# Lever API:      https://api.lever.co/v0/postings/{slug}?mode=json

GREENHOUSE = {
    # AI / LLM
    "openai":       {"name": "OpenAI",         "domain": "openai.com",       "vc": "Microsoft, a16z"},
    "anthropic":    {"name": "Anthropic",       "domain": "anthropic.com",    "vc": "Google, Spark Capital"},
    "cohere-1":     {"name": "Cohere",          "domain": "cohere.com",       "vc": "Index, Tiger Global"},
    "mistral":      {"name": "Mistral AI",      "domain": "mistral.ai",       "vc": "a16z, Lightspeed"},

    # Fintech
    "stripe":       {"name": "Stripe",          "domain": "stripe.com",       "vc": "Sequoia, a16z, YC"},
    "brex":         {"name": "Brex",            "domain": "brex.com",         "vc": "YC, DST Global"},
    "ramp":         {"name": "Ramp",            "domain": "ramp.com",         "vc": "Founders Fund, D1"},
    "robinhood":    {"name": "Robinhood",        "domain": "robinhood.com",    "vc": "a16z, Sequoia"},
    "plaid":        {"name": "Plaid",           "domain": "plaid.com",        "vc": "a16z, Kleiner"},
    "coinbase":     {"name": "Coinbase",         "domain": "coinbase.com",     "vc": "a16z, YC"},
    "rippling":     {"name": "Rippling",         "domain": "rippling.com",     "vc": "Founders Fund, YC"},
    "gusto":        {"name": "Gusto",           "domain": "gusto.com",        "vc": "General Catalyst, YC"},
    "klaviyo":      {"name": "Klaviyo",          "domain": "klaviyo.com",      "vc": "Summit Partners"},

    # Developer Tools / Infra
    "cloudflare":   {"name": "Cloudflare",       "domain": "cloudflare.com",   "vc": "NEA, Pelion"},
    "datadog":      {"name": "Datadog",          "domain": "datadoghq.com",    "vc": "OpenView, ICONIQ"},
    "hashicorp":    {"name": "HashiCorp",         "domain": "hashicorp.com",    "vc": "GGV, Mayfield"},
    "netlify":      {"name": "Netlify",          "domain": "netlify.com",      "vc": "a16z, USVP"},
    "vercel":       {"name": "Vercel",           "domain": "vercel.com",       "vc": "Accel, CRV"},
    "supabase":     {"name": "Supabase",         "domain": "supabase.com",     "vc": "YC, a16z"},
    "retool":       {"name": "Retool",           "domain": "retool.com",       "vc": "Sequoia, a16z"},
    "sentry":       {"name": "Sentry",           "domain": "sentry.io",        "vc": "Accel"},
    "postman":      {"name": "Postman",          "domain": "postman.com",      "vc": "Nexus Venture"},
    "gitlab":       {"name": "GitLab",           "domain": "gitlab.com",       "vc": "GV, ICONIQ"},
    "mongodb":      {"name": "MongoDB",          "domain": "mongodb.com",      "vc": "Public"},
    "zendesk":      {"name": "Zendesk",          "domain": "zendesk.com",      "vc": "Benchmark"},
    "twilio":       {"name": "Twilio",           "domain": "twilio.com",       "vc": "Bessemer, Salesforce"},
    "pagerduty":    {"name": "PagerDuty",         "domain": "pagerduty.com",    "vc": "Sequoia, Accel"},
    "segment":      {"name": "Segment",          "domain": "segment.com",      "vc": "Accel (Twilio)"},
    "zapier":       {"name": "Zapier",           "domain": "zapier.com",       "vc": "Sequoia"},
    "mixpanel":     {"name": "Mixpanel",         "domain": "mixpanel.com",     "vc": "Sequoia, a16z"},
    "intercom":     {"name": "Intercom",         "domain": "intercom.com",     "vc": "KPCB, Index"},
    "webflow":      {"name": "Webflow",          "domain": "webflow.com",      "vc": "Accel, YC"},
    "grammarly":    {"name": "Grammarly",         "domain": "grammarly.com",    "vc": "General Catalyst"},

    # Consumer / Marketplace
    "airbnb":       {"name": "Airbnb",           "domain": "airbnb.com",       "vc": "Sequoia, a16z, YC"},
    "doordash":     {"name": "DoorDash",          "domain": "doordash.com",     "vc": "Sequoia, YC"},
    "lyft":         {"name": "Lyft",             "domain": "lyft.com",         "vc": "Andreessen, Fidelity"},
    "instacart":    {"name": "Instacart",         "domain": "instacart.com",    "vc": "Sequoia, a16z"},
    "pinterest":    {"name": "Pinterest",         "domain": "pinterest.com",    "vc": "Bessemer, FirstMark"},
    "etsy":         {"name": "Etsy",             "domain": "etsy.com",         "vc": "Public"},
    "squarespace":  {"name": "Squarespace",       "domain": "squarespace.com",  "vc": "Accel"},
    "faire":        {"name": "Faire",            "domain": "faire.com",        "vc": "Sequoia, Y Combinator"},
    "flexport":     {"name": "Flexport",          "domain": "flexport.com",     "vc": "Founders Fund, DST"},
    "reddit":       {"name": "Reddit",           "domain": "reddit.com",       "vc": "a16z, YC"},
    "discord":      {"name": "Discord",          "domain": "discord.com",      "vc": "Greenoaks, Index"},
    "dropbox":      {"name": "Dropbox",          "domain": "dropbox.com",      "vc": "Sequoia, a16z, YC"},

    # Productivity / Collaboration
    "notion":       {"name": "Notion",           "domain": "notion.com",       "vc": "Index, Coatue"},
    "airtable":     {"name": "Airtable",          "domain": "airtable.com",     "vc": "Benchmark, Coatue"},
    "asana":        {"name": "Asana",            "domain": "asana.com",        "vc": "Benchmark, Peter Thiel"},
    "miro":         {"name": "Miro",             "domain": "miro.com",         "vc": "Accel, ICONIQ"},
    "figma":        {"name": "Figma",            "domain": "figma.com",        "vc": "a16z, Sequoia"},
    "canva":        {"name": "Canva",            "domain": "canva.com",        "vc": "Sequoia, Bond"},

    # Data / ML / Analytics
    "scale-ai":     {"name": "Scale AI",          "domain": "scale.com",        "vc": "Accel, Tiger Global"},
    "huggingface":  {"name": "Hugging Face",      "domain": "huggingface.co",   "vc": "Lux Capital, a16z"},
    "databricks":   {"name": "Databricks",        "domain": "databricks.com",   "vc": "a16z, NEA"},
    "dbt-labs":     {"name": "dbt Labs",          "domain": "getdbt.com",       "vc": "Andreessen, Sequoia"},

    # Media / Entertainment
    "netflix":      {"name": "Netflix",          "domain": "netflix.com",      "vc": "Public"},

    # Security
    "crowdstrike":  {"name": "CrowdStrike",       "domain": "crowdstrike.com",  "vc": "Public"},
    "zscaler":      {"name": "Zscaler",          "domain": "zscaler.com",      "vc": "Public"},
    "1password":    {"name": "1Password",         "domain": "1password.com",    "vc": "Accel"},

    # HR / People
    "lattice":      {"name": "Lattice",          "domain": "lattice.com",      "vc": "Thrive Capital, YC"},
    "greenhouse":   {"name": "Greenhouse",        "domain": "greenhouse.io",    "vc": "Benchmark"},
    "lever":        {"name": "Lever",            "domain": "lever.co",         "vc": "Matrix, Scale"},

    # Other Notable
    "palantir":     {"name": "Palantir",          "domain": "palantir.com",     "vc": "Public"},
    "duolingo":     {"name": "Duolingo",          "domain": "duolingo.com",     "vc": "Public"},
    "benchling":    {"name": "Benchling",         "domain": "benchling.com",    "vc": "Benchmark, Sequoia"},
    "carta":        {"name": "Carta",            "domain": "carta.com",        "vc": "a16z, Spark"},
    "amplitude":    {"name": "Amplitude",         "domain": "amplitude.com",    "vc": "Benchmark, IVP"},
    "hubspot":      {"name": "HubSpot",           "domain": "hubspot.com",      "vc": "Public"},
    "qualtrics":    {"name": "Qualtrics",         "domain": "qualtrics.com",    "vc": "Public"},

    # Consumer / Social (good for PM roles)
    "tinder":       {"name": "Tinder",            "domain": "tinder.com",       "vc": "Public (IAC)"},
    "bumble":       {"name": "Bumble",            "domain": "bumble.com",       "vc": "Public"},
    "snap":         {"name": "Snap",              "domain": "snap.com",         "vc": "Public"},
    "twitter":      {"name": "X (Twitter)",       "domain": "twitter.com",      "vc": "Public"},
    "uber":         {"name": "Uber",              "domain": "uber.com",         "vc": "Public"},
    "lyft":         {"name": "Lyft",              "domain": "lyft.com",         "vc": "a16z"},
    "spotify":      {"name": "Spotify",           "domain": "spotify.com",      "vc": "Public"},

    # Growth / Product-led (PM heavy)
    "figma":        {"name": "Figma",             "domain": "figma.com",        "vc": "a16z, Sequoia"},
    "linear":       {"name": "Linear",            "domain": "linear.app",       "vc": "Sequoia"},
    "productboard": {"name": "Productboard",      "domain": "productboard.com", "vc": "Dragoneer, Tiger"},
    "pendo":        {"name": "Pendo",             "domain": "pendo.io",         "vc": "Battery Ventures"},
    "mixpanel":     {"name": "Mixpanel",          "domain": "mixpanel.com",     "vc": "Sequoia, a16z"},
}

LEVER = {
    "toast":        {"name": "Toast",            "domain": "toasttab.com",     "vc": "TPG, Tiger"},
    "brainly":      {"name": "Brainly",          "domain": "brainly.com",      "vc": "Prosus"},
    "airbyte":      {"name": "Airbyte",          "domain": "airbyte.com",      "vc": "Benchmark, Accel"},
    "fivetran":     {"name": "Fivetran",          "domain": "fivetran.com",     "vc": "Andreessen, General Catalyst"},
    "alchemy":      {"name": "Alchemy",          "domain": "alchemy.com",      "vc": "Lightspeed, a16z"},
    "replit":       {"name": "Replit",           "domain": "replit.com",       "vc": "a16z, YC"},
    "cursor":       {"name": "Cursor",           "domain": "cursor.com",       "vc": "a16z, Sequoia"},
    "anyscale":     {"name": "Anyscale",          "domain": "anyscale.com",     "vc": "NEA, a16z"},
    "weights-biases": {"name": "Weights & Biases", "domain": "wandb.ai",       "vc": "Insight Partners"},
    "together-ai":  {"name": "Together AI",       "domain": "together.ai",      "vc": "Kleiner Perkins"},
    "modal-labs":   {"name": "Modal Labs",        "domain": "modal.com",        "vc": "Redpoint, YC"},
    "weaviate":     {"name": "Weaviate",          "domain": "weaviate.io",      "vc": "NEA, Cortical"},
    "pinecone":     {"name": "Pinecone",          "domain": "pinecone.io",      "vc": "Menlo Ventures, a16z"},
    "neon":         {"name": "Neon",             "domain": "neon.tech",        "vc": "GV, Khosla"},
    "fly-io":       {"name": "Fly.io",           "domain": "fly.io",           "vc": "YC"},
    "render":       {"name": "Render",           "domain": "render.com",       "vc": "South Park Commons, YC"},
}

BIG_TECH = {
    "google":    {"name": "Google",    "domain": "google.com"},
    "microsoft": {"name": "Microsoft", "domain": "microsoft.com"},
    "amazon":    {"name": "Amazon",    "domain": "amazon.com"},
    "meta":      {"name": "Meta",      "domain": "meta.com"},
    "apple":     {"name": "Apple",     "domain": "apple.com"},
    "salesforce": {"name": "Salesforce", "domain": "salesforce.com"},
    "oracle":    {"name": "Oracle",    "domain": "oracle.com"},
    "servicenow": {"name": "ServiceNow", "domain": "servicenow.com"},
    "workday":   {"name": "Workday",   "domain": "workday.com"},
}

# Curated late-stage startup targets for this app. The ATS slugs below point to
# public Greenhouse/Lever boards; stage labels are hints and should be verified
# before outreach because funding rounds change over time.
TARGET_GREENHOUSE = {
    "cohere-1":     {**GREENHOUSE["cohere-1"],     "stage": "Series D", "stage_focus": "Series C/D"},
    "huggingface":  {**GREENHOUSE["huggingface"],  "stage": "Series D", "stage_focus": "Series C/D"},
    "ramp":         {**GREENHOUSE["ramp"],         "stage": "Series D", "stage_focus": "Series C/D"},
    "vercel":       {**GREENHOUSE["vercel"],       "stage": "Series D+", "stage_focus": "Series C/D"},
    "supabase":     {**GREENHOUSE["supabase"],     "stage": "Series C", "stage_focus": "Series C/D"},
    "retool":       {**GREENHOUSE["retool"],       "stage": "Series C", "stage_focus": "Series C/D"},
    "postman":      {**GREENHOUSE["postman"],      "stage": "Series D", "stage_focus": "Series C/D"},
    "intercom":     {**GREENHOUSE["intercom"],     "stage": "Series D", "stage_focus": "Series C/D"},
    "notion":       {**GREENHOUSE["notion"],       "stage": "Series C", "stage_focus": "Series C/D"},
    "webflow":      {**GREENHOUSE["webflow"],      "stage": "Series C", "stage_focus": "Series C/D"},
    "faire":        {**GREENHOUSE["faire"],        "stage": "Series D+", "stage_focus": "Series C/D"},
    "linear":       {**GREENHOUSE["linear"],       "stage": "Series C", "stage_focus": "Series C/D"},
    "productboard": {**GREENHOUSE["productboard"], "stage": "Series D", "stage_focus": "Series C/D"},
    "pendo":        {**GREENHOUSE["pendo"],        "stage": "Series D+", "stage_focus": "Series C/D"},
    "dbt-labs":     {**GREENHOUSE["dbt-labs"],     "stage": "Series D", "stage_focus": "Series C/D"},
    "airtable":     {**GREENHOUSE["airtable"],     "stage": "Series F", "stage_focus": "Late-stage startup"},
    "lattice":      {**GREENHOUSE["lattice"],      "stage": "Series F", "stage_focus": "Late-stage startup"},
    "benchling":    {**GREENHOUSE["benchling"],    "stage": "Series F", "stage_focus": "Late-stage startup"},
    "scale-ai":     {**GREENHOUSE["scale-ai"],     "stage": "Series F", "stage_focus": "Late-stage startup"},
    "grammarly":    {**GREENHOUSE["grammarly"],    "stage": "Late-stage", "stage_focus": "Late-stage startup"},
    "databricks":   {**GREENHOUSE["databricks"],   "stage": "Late-stage", "stage_focus": "Late-stage startup"},
    "mistral":      {**GREENHOUSE["mistral"],      "stage": "Series B/C", "stage_focus": "Series C/D"},
}

TARGET_LEVER = {
    "fivetran":        {**LEVER["fivetran"],        "stage": "Series D", "stage_focus": "Series C/D"},
    "alchemy":         {**LEVER["alchemy"],         "stage": "Series C", "stage_focus": "Series C/D"},
    "replit":          {**LEVER["replit"],          "stage": "Series C", "stage_focus": "Series C/D"},
    "cursor":          {**LEVER["cursor"],          "stage": "Series C/D", "stage_focus": "Series C/D"},
    "anyscale":        {**LEVER["anyscale"],        "stage": "Series C", "stage_focus": "Series C/D"},
    "weights-biases":  {**LEVER["weights-biases"],  "stage": "Series C", "stage_focus": "Series C/D"},
    "pinecone":        {**LEVER["pinecone"],        "stage": "Series B/C", "stage_focus": "Series C/D"},
    "airbyte":         {**LEVER["airbyte"],         "stage": "Series B/C", "stage_focus": "Series C/D"},
    "together-ai":     {**LEVER["together-ai"],     "stage": "Series B/C", "stage_focus": "Series C/D"},
    "modal-labs":      {**LEVER["modal-labs"],      "stage": "Series B/C", "stage_focus": "Series C/D"},
    "weaviate":        {**LEVER["weaviate"],        "stage": "Series B/C", "stage_focus": "Series C/D"},
    "neon":            {**LEVER["neon"],            "stage": "Series B/C", "stage_focus": "Series C/D"},
    "render":          {**LEVER["render"],          "stage": "Series B/C", "stage_focus": "Series C/D"},
}

# Verified against Ashby's public posting API. These boards are used alongside
# Greenhouse and Lever because many current startup roles have moved to Ashby.
TARGET_ASHBY = {
    "Ramp":       {**GREENHOUSE["ramp"],        "stage": "Series D", "stage_focus": "Series C/D"},
    "Linear":     {**GREENHOUSE["linear"],      "stage": "Series C", "stage_focus": "Series C/D"},
    "Cursor":     {**LEVER["cursor"],           "stage": "Series C/D", "stage_focus": "Series C/D"},
    "PostHog":    {"name": "PostHog", "domain": "posthog.com", "vc": "Y Combinator, Y Combinator Continuity", "stage": "Series D", "stage_focus": "Series C/D"},
    "Pinecone":   {**LEVER["pinecone"],         "stage": "Series B/C", "stage_focus": "Series C/D"},
    "Anyscale":   {**LEVER["anyscale"],         "stage": "Series C", "stage_focus": "Series C/D"},
    "Vanta":      {"name": "Vanta", "domain": "vanta.com", "vc": "Sequoia, Craft Ventures", "stage": "Series D", "stage_focus": "Series C/D"},
    "ClickUp":    {"name": "ClickUp", "domain": "clickup.com", "vc": "a16z, Tiger Global", "stage": "Series C", "stage_focus": "Series C/D"},
    "Plaid":      {**GREENHOUSE["plaid"],        "stage": "Series D", "stage_focus": "Series C/D"},
    "Replit":     {**LEVER["replit"],            "stage": "Series C", "stage_focus": "Series C/D"},
    "Notion":     {**GREENHOUSE["notion"],       "stage": "Series C", "stage_focus": "Series C/D"},
    "Supabase":   {**GREENHOUSE["supabase"],     "stage": "Series C", "stage_focus": "Series C/D"},
    "Cohere":     {**GREENHOUSE["cohere-1"],     "stage": "Series D", "stage_focus": "Series C/D"},
    "Harvey":     {"name": "Harvey", "domain": "harvey.ai", "vc": "Sequoia, Kleiner Perkins", "stage": "Series D", "stage_focus": "Series C/D"},
    "Sentry":     {**GREENHOUSE["sentry"],       "stage": "Late-stage", "stage_focus": "Late-stage startup"},
    "Benchling":  {**GREENHOUSE["benchling"],    "stage": "Series F", "stage_focus": "Late-stage startup"},
}
