import random
import urllib.parse

CRICKETERS = [
    "Virat Kohli", "MS Dhoni", "Rohit Sharma", "Sachin Tendulkar", "Hardik Pandya", "Jasprit Bumrah", 
    "Ravindra Jadeja", "KL Rahul", "Shubman Gill", "Rishabh Pant", "Suryakumar Yadav", "Shreyas Iyer",
    "Mohammed Shami", "Mohammed Siraj", "Ravichandran Ashwin", "Axar Patel", "Ishna Kishan",
    "Pat Cummins", "Steve Smith", "David Warner", "Mitchell Starc", "Glenn Maxwell", "Travis Head",
    "Kane Williamson", "Trent Boult", "Rachin Ravindra", "Daryll Mitchell",
    "Babar Azam", "Shaheen Afridi", "Mohammad Rizwan", "Naseem Shah",
    "Ben Stokes", "Joe Root", "Jos Buttler", "Jofra Archer", "Harry Brook",
    "Rashid Khan", "Shakib Al Hasan", "Wanindu Hasaranga", "Matheesha Pathirana",
    "Sanju Samson", "Yashasvi Jaiswal", "Rinku Singh", "Arshdeep Singh", "Kuldeep Yadav",
    "Yuvraj Singh", "Sourav Ganguly", "Rahul Dravid", "Virender Sehwag", "Gautam Gambhir",
    "AB de Villiers", "Chris Gayle", "Dale Steyn", "Kagiso Rabada", "Quinton de Kock",
    "Ricky Ponting", "Brett Lee", "Adam Gilchrist", "Shane Warne", "Brian Lara"
]

POLITICIANS = [
    "Narendra Modi", "Amit Shah", "Yogi Adityanath", "Rahul Gandhi", "Arvind Kejriwal", "Mamata Banerjee",
    "Droupadi Murmu", "S. Jaishankar", "Nitin Gadkari", "Piyush Goyal", "Nirmala Sitharaman",
    "Joe Biden", "Donald Trump", "Barack Obama", "Kamala Harris", "Rishi Sunak", "Boris Johnson",
    "Vladimir Putin", "Volodymyr Zelenskyy", "Xi Jinping", "Emmanuel Macron", "Justin Trudeau",
    "Giorgia Meloni", "Olaf Scholz", "Fumio Kishida", "Lula da Silva", "Cyril Ramaphosa",
    "Sheikh Hasina", "Shehbaz Sharif", "Kim Jong Un", "Benjamin Netanyahu", "Mohammed bin Salman"
]

FOOTBALLERS = [
    "Lionel Messi", "Cristiano Ronaldo", "Kylian Mbappe", "Erling Haaland", "Neymar Jr",
    "Kevin De Bruyne", "Mohamed Salah", "Harry Kane", "Robert Lewandowski", "Luka Modric",
    "Vinicius Jr", "Jude Bellingham", "Pedri", "Gavi", "Virgil van Dijk", "Son Heung-min",
    "Karim Benzema", "Sadio Mane", "Riyad Mahrez", "Bruno Fernandes", "Marcus Rashford",
    "Sunil Chhetri", "Pele", "Diego Maradona", "Zinedine Zidane", "Ronaldinho", "David Beckham"
]

CITIES_LANDMARKS = [
    "Mumbai India", "Delhi India Gate", "Bangalore Tech Park", "Hyderabad Charminar", "Kolkata Howrah Bridge",
    "Chennai Marina Beach", "Varanasi Ghats", "Jaipur Hawa Mahal", "Kerala Backwaters", "Goa Beach",
    "New York Times Square", "London Big Ben", "Paris Eiffel Tower", "Tokyo Shibuya Crossing",
    "Dubai Burj Khalifa", "Singapore Marina Bay", "Sydney Opera House", "Rome Colosseum",
    "Cairo Pyramids", "Rio de Janeiro Christ Redeemer", "Moscow Kremlin", "Istanbul Hagia Sophia",
    "Toronto CN Tower", "Berlin Brandenburg Gate", "Amsterdam Canals", "Barcelona Sagrada Familia",
    "San Francisco Golden Gate Bridge", "Los Angeles Hollywood Sign", "Chicago Skyline",
    "Shanghai Bund", "Hong Kong Skyline", "Seoul Gangnam", "Bangkok Grand Palace"
]

TECH_TOPICS = [
    "Artificial Intelligence Brain", "Bitcoin Cryptocurrency", "Stock Market Bull", "Cyber Security Hacker",
    "SpaceX Rocket Launch", "Electric Vehicle Charging", "5G Tower Future", "Virtual Reality Headset",
    "Coding Python Screen", "Data Center Server", "Robot Handshake", "Drone Delivery",
    "Smart City Future", "Blockchain Network", "Quantum Computer", "Microchip Processor"
]

# ======================================================
# 1. THE "UNIVERSE" DATABASE (Micro to Macro)
# ======================================================

# --- LEVEL 1: THE MICROCOSM (Underground / Microscopic) ---
MICROCOSM = [
    "Microscopic cell structure", "DNA double helix 4k", "Bacteria under electron microscope",
    "Virus strains high detail", "Red blood cells flowing", "Neuron firing brain",
    "Tardigrade water bear", "Amoeba proteus", "Fungal spores macro",
    "Crystal lattice structure", "Graphene sheet atomic view", "Nanobot technology",
    "Soil particles magnified", "Root systems underground", "Mycelium network"
]

# --- LEVEL 2: NATURE & WILDLIFE (Earth Surface) ---
NATURE = [
    "Amazon Rainforest aerial", "Mount Everest summit", "Sahara Desert dunes",
    "Great Barrier Reef coral", "Antarctica ice shelf", "Volcano erupting lava",
    "Bengal Tiger prowling", "African Elephant herd", "Blue Whale underwater",
    "Eagle flying high resolution", "Panda eating bamboo", "King Cobra hood open",
    "Deep sea bioluminescent creature", "Butterfly macro wing pattern",
    "Thunderstorm supercell", "Tornado touching down", "Northern Lights Aurora"
]

# --- LEVEL 3: HUMANITY (Politicians, Celebs, Leaders - GLOBAL) ---
HUMANITY = [
    # India
    "Narendra Modi speech", "Amit Shah portrait", "Yogi Adityanath", "Rahul Gandhi",
    "Virat Kohli cricket", "Rohit Sharma batting", "MS Dhoni captain", "Shah Rukh Khan",
    # World Leaders
    "Joe Biden white house", "Donald Trump rally", "Vladimir Putin kremlin",
    "Xi Jinping beijing", "Emmanuel Macron paris", "Rishi Sunak london",
    "Elon Musk spaceX", "Mark Zuckerberg meta", "Jeff Bezos amazon",
    "Bill Gates microsoft", "Sundar Pichai google", "Satya Nadella",
    # Pop Culture
    "Taylor Swift concert", "Cristiano Ronaldo goal", "Lionel Messi world cup",
    "Dwayne Johnson", "Tom Cruise action", "Leonardo DiCaprio"
]

# --- LEVEL 4: INFRASTRUCTURE & CITIES ---
CIVILIZATION = [
    "New York Times Square night", "Mumbai skyline sea link", "Burj Khalifa dubai",
    "Tokyo Shibuya crossing neon", "London Tower Bridge", "Paris Eiffel Tower sunset",
    "Ancient Pyramids Giza", "Taj Mahal India", "Great Wall of China",
    "Silicon Valley tech campus", "Stock Exchange bull market", "Bitcoin cryptocurrency gold",
    "Cyberpunk futuristic city", "Busy Indian market street", "High speed bullet train"
]

# --- LEVEL 5: THE COSMOS (Space) ---
COSMOS = [
    "Earth from space ISS", "Moon surface craters", "Mars rover landscape",
    "Sun solar flare eruption", "Saturn rings high res", "Jupiter great red spot",
    "James Webb Telescope nebula", "Black hole event horizon", "Andromeda galaxy spiral",
    "Supernova explosion", "Asteroid belt rendering", "International Space Station",
    "Astronaut floating in space", "SpaceX Starship launch", "Milky Way galaxy core"
]

# Combine all for random backup
ALL_MATTER = MICROCOSM + NATURE + HUMANITY + CIVILIZATION + COSMOS

# ======================================================
# 2. THE "WHOLE INTERNET" SEARCH ENGINE
# ======================================================

def get_image_url(search_keyword=None):
    """
    Intelligent Search Engine.
    1. If a keyword is provided by AI -> Generates that EXACT image.
    2. If no keyword -> Picks from the Universe Database based on random logic.
    """
    
    # A. AI PROVIDED A SPECIFIC KEYWORD (Best Quality)
    if search_keyword and len(search_keyword) > 3:
        # We enhance the prompt for "Best Quality"
        enhanced_prompt = f"hyper realistic news photography of {search_keyword}, 4k, high detail, dramatic lighting"
        safe_query = urllib.parse.quote(enhanced_prompt)
        
        # Using Pollinations AI to generate the specific image on the fly
        return f"https://image.pollinations.ai/prompt/{safe_query}?width=1080&height=620&nologo=true&seed={random.randint(1,999999)}"

    # B. FALLBACK: USE THE UNIVERSE DATABASE
    else:
        # Pick a random topic from our database
        topic = random.choice(ALL_MATTER)
        enhanced_prompt = f"hyper realistic 8k photo of {topic}, cinematic, news style"
        safe_query = urllib.parse.quote(enhanced_prompt)
        
        return f"https://image.pollinations.ai/prompt/{safe_query}?width=1080&height=620&nologo=true&seed={random.randint(1,999999)}"

# Export for compatibility
# ... [Keep your STATIC_POOL list at the top] ...

# ======================================================
# AI ENGINE: MULTI-PROVIDER WATERFALL (Storyteller Mode)
# ======================================================

def ai_rvcj_converter(text):
    """
    Tries AI providers in this specific order (Roles):
    1. SPEED LAYER: Groq, Cerebras (Fastest)
    2. SMART LAYER: NVIDIA, Together, Grok (xAI) (High Intelligence)
    3. GOOGLE LAYER: Gemini (Reliable)
    4. BACKUP LAYER: Mistral, Cohere
    5. FINAL RESORT: OpenRouter (Aggregator)
    """
    import requests
    import json
    import re
    import os
    
    # 1. Input Safety Check
    text = (text or "").strip()
    if not text: return _fallback_data("Breaking News Update")

    # 2. THE PROMPT (Optimized for Storytelling & Visuals)
    prompt = f"""
    Act as a Senior Editor for a viral Instagram News Page (like RVCJ Media or Tatva India).
    
    TASK: Read the news below and convert it into a valid JSON object.
    
    RULES FOR "image_info" (The Text Body):
    1. Do NOT use bullet points. 
    2. Write a short paragraph (2-3 sentences max).
    3. Explain the context: What happened? Why is it important?
    4. Use simple, conversational English (or Hinglish style).
    5. NO generic keywords. Write full, engaging sentences.
    
    RULES FOR "search_keyword" (The Image Subject):
    1. Extract the MAIN VISUAL SUBJECT. 
    2. If it's a person, output: "Portrait of [Name] face realistic"
    3. If it's a match, output: "[Team A] vs [Team B] cricket match"
    4. NEVER use metaphors (e.g., DO NOT say "Shining Star", say the person's real name).
    5. Keep it under 6 words.
    
    Input News: {text[:2000]}
    
    Output JSON format:
    {{
        "headline": "Short punchy headline (Max 7 words, Uppercase)",
        "image_info": "The 2-3 sentence summary here...",
        "short_caption": "Engaging caption for Instagram #Hashtags",
        "search_keyword": "Exact visual subject for AI image generator"
    }}
    """

    # ---------------------------------------------------------
    # LAYER 1: SPEED (The "Flash" Layer)
    # ---------------------------------------------------------
    
    # 1. Groq (Llama 3.3 70B)
    res = _call_openai_compat("Groq", "https://api.groq.com/openai/v1", os.getenv("GROQ_API_KEY"), "llama-3.3-70b-versatile", prompt)
    if res: return res

    # 2. Cerebras (Llama 3.1 70B)
    res = _call_openai_compat("Cerebras", "https://api.cerebras.ai/v1", os.getenv("CEREBRAS_API_KEY"), "llama3.1-70b", prompt)
    if res: return res

    # ---------------------------------------------------------
    # LAYER 2: INTELLIGENCE (The "Smart" Layer)
    # ---------------------------------------------------------

    # 3. NVIDIA NIM (Llama 3.1 405B)
    res = _call_openai_compat("Nvidia", "https://integrate.api.nvidia.com/v1", os.getenv("NVIDIA_API_KEY"), "meta/llama-3.1-405b-instruct", prompt)
    if res: return res

    # 4. Grok (xAI)
    res = _call_openai_compat("Grok", "https://api.x.ai/v1", os.getenv("XAI_API_KEY"), "grok-beta", prompt)
    if res: return res

    # 5. Together AI (Llama 3.3)
    res = _call_openai_compat("Together", "https://api.together.xyz/v1", os.getenv("TOGETHER_API_KEY"), "meta-llama/Llama-3.3-70B-Instruct-Turbo", prompt)
    if res: return res

    # ---------------------------------------------------------
    # LAYER 3: GOOGLE (Gemini)
    # ---------------------------------------------------------

    # 6. Gemini 2.0 Flash
    try:
        if os.getenv("GEMINI_API_KEY"):
            from google import genai
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            r = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            logger.info("🧠 AI WINNER: Gemini 2.0 Flash")
            return _parse_ai_json(r.text)
    except Exception as e:
        logger.warning(f"⚠️ Gemini Skipped: {e}")

    # ---------------------------------------------------------
    # LAYER 4: BACKUP (Direct APIs)
    # ---------------------------------------------------------

    # 7. Mistral API
    if _call_openai_compat("Mistral", "https://api.mistral.ai/v1", os.getenv("MISTRAL_API_KEY"), "mistral-small-latest", prompt) is not None:
         return _call_openai_compat("Mistral", "https://api.mistral.ai/v1", os.getenv("MISTRAL_API_KEY"), "mistral-small-latest", prompt)

    # 8. Cohere API
    try:
        if os.getenv("COHERE_API_KEY"):
            r = requests.post(
                "https://api.cohere.com/v1/chat",
                headers={"Authorization": f"Bearer {os.getenv('COHERE_API_KEY')}", "Content-Type": "application/json"},
                json={"message": prompt, "model": "command-r-plus"}
            )
            if r.status_code == 200:
                logger.info("🧠 AI WINNER: Cohere")
                return _parse_ai_json(r.json()["text"])
    except: pass

    # ---------------------------------------------------------
    # LAYER 5: OPENROUTER (The Final Net)
    # ---------------------------------------------------------

    # 9. OpenRouter
    res = _call_openai_compat("OpenRouter", "https://openrouter.ai/api/v1", os.getenv("OPENROUTER_API_KEY"), "openai/gpt-4o-mini", prompt)
    if res: return res

    # --- FALLBACK (If everything fails) ---
    logger.error("❌ CRITICAL: All AI providers failed. Using manual fallback.")
    return _fallback_data(text)