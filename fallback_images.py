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

def get_fallback_image_url(source="auto") -> str:
    """
    Smart Image Generator.
    - Checks if the search keyword is valid.
    - Uses FLUX model (Better quality, fewer rate limits).
    """
    import random
    import urllib.parse
    
    # 1. Check if 'source' is actually a search keyword passed from app.py
    # If source is "auto" or "mixed", we treat it as generic.
    search_keyword = source if source not in ["auto", "mixed", "picsum"] else None

    # --- STRATEGY A: SPECIFIC AI SEARCH (If keyword exists) ---
    if search_keyword and len(search_keyword) > 3:
        # 🔥 FIX: Force "Realism" to avoid cartoons/rate limit placeholders
        enhanced_prompt = f"editorial news photography, {search_keyword}, highly detailed, 4k, realistic texture"
        
        safe_query = urllib.parse.quote(enhanced_prompt)
        seed = random.randint(1, 9999999) # Cache Buster
        
        # 🔥 USING FLUX MODEL (Better quality)
        return f"https://image.pollinations.ai/prompt/{safe_query}?width=1080&height=620&model=flux&nologo=true&seed={seed}"

    # --- STRATEGY B: RANDOM FALLBACK (If no keyword) ---
    choice = random.randint(1, 10)
    
    if choice <= 4:
        # Generic AI Image (Crowd/City)
        topics = ["crowded indian street market", "modern technology abstract", "breaking news studio background"]
        topic = random.choice(topics)
        safe_query = urllib.parse.quote(f"realistic photo of {topic}")
        seed = random.randint(1, 999999)
        return f"https://image.pollinations.ai/prompt/{safe_query}?width=1080&height=620&model=flux&nologo=true&seed={seed}"

    elif choice <= 7:
        # Picsum (Reliable)
        return f"https://picsum.photos/1080/620?random={random.randint(1, 99999)}"

    else:
        # Static Pool (Safest)
        return random.choice(STATIC_POOL)

# List compatibility
FALLBACK_IMAGES = [get_image_url() for _ in range(50)]