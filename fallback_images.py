import random
import urllib.parse

# ======================================================
# 1. THE "UNIVERSE" DATABASE (Infinite Keywords)
# ======================================================
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

MICROCOSM = [
    "Microscopic cell structure", "DNA double helix 4k", "Bacteria under electron microscope",
    "Virus strains high detail", "Red blood cells flowing", "Neuron firing brain",
    "Tardigrade water bear", "Amoeba proteus", "Fungal spores macro",
    "Crystal lattice structure", "Graphene sheet atomic view", "Nanobot technology",
    "Soil particles magnified", "Root systems underground", "Mycelium network"
]

NATURE = [
    "Amazon Rainforest aerial", "Mount Everest summit", "Sahara Desert dunes",
    "Great Barrier Reef coral", "Antarctica ice shelf", "Volcano erupting lava",
    "Bengal Tiger prowling", "African Elephant herd", "Blue Whale underwater",
    "Eagle flying high resolution", "Panda eating bamboo", "King Cobra hood open",
    "Deep sea bioluminescent creature", "Butterfly macro wing pattern",
    "Thunderstorm supercell", "Tornado touching down", "Northern Lights Aurora"
]

COSMOS = [
    "Earth from space ISS", "Moon surface craters", "Mars rover landscape",
    "Sun solar flare eruption", "Saturn rings high res", "Jupiter great red spot",
    "James Webb Telescope nebula", "Black hole event horizon", "Andromeda galaxy spiral",
    "Supernova explosion", "Asteroid belt rendering", "International Space Station",
    "Astronaut floating in space", "SpaceX Starship launch", "Milky Way galaxy core"
]

# Combine all lists for the Randomizer
ALL_MATTER = CRICKETERS + POLITICIANS + FOOTBALLERS + CITIES_LANDMARKS + TECH_TOPICS + MICROCOSM + NATURE + COSMOS

# ======================================================
# 2. THE SAFE STATIC POOL (No API needed, always works)
# ======================================================
STATIC_POOL = [
    "https://images.pexels.com/photos/1369476/pexels-photo-1369476.jpeg",
    "https://images.pexels.com/photos/1040499/pexels-photo-1040499.jpeg",
    "https://images.unsplash.com/photo-1557683316-973673baf926?w=1080",
    "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=1080",
    "https://images.pexels.com/photos/1618269/pexels-photo-1618269.jpeg", # Sports
    "https://images.pexels.com/photos/3183150/pexels-photo-3183150.jpeg", # Tech
    "https://images.pexels.com/photos/4629633/pexels-photo-4629633.jpeg"  # Politics
]

# ======================================================
# 3. THE "WHOLE INTERNET" SEARCH ENGINE (Flux Model)
# ======================================================

def get_image_url(search_keyword=None):
    """
    Intelligent Search Engine.
    1. If a keyword is provided -> Generates that EXACT image using high-quality prompt.
    2. If no keyword -> Picks from the UNIVERSE Database.
    """
    
    # Ignore "auto", "mixed", etc. that app.py might send by default
    if search_keyword in ["auto", "mixed", "picsum"]:
        search_keyword = None

    # --- STRATEGY A: SPECIFIC KEYWORD SEARCH ---
    if search_keyword and len(search_keyword) > 3:
        # "editorial news photography" and "no text" forces realism and stops weird AI text/cartoons.
        enhanced_prompt = f"editorial news photography of {search_keyword}, realistic, 4k, high detail, cinematic lighting, no text"
        safe_query = urllib.parse.quote(enhanced_prompt)
        seed = random.randint(1, 9999999)
        # Using FLUX Model (Best Quality)
        return f"https://image.pollinations.ai/prompt/{safe_query}?width=1080&height=620&model=flux&nologo=true&seed={seed}"

    # --- STRATEGY B: THE UNIVERSE DATABASE (Random Topic) ---
    choice = random.randint(1, 100)
    
    # 80% Chance to pick a random topic from our massive list (Modi, Black Hole, Cells, etc.)
    if choice <= 80:
        topic = random.choice(ALL_MATTER)
        enhanced_prompt = f"editorial news photography of {topic}, realistic, 4k, cinematic lighting, no text"
        safe_query = urllib.parse.quote(enhanced_prompt)
        seed = random.randint(1, 9999999)
        return f"https://image.pollinations.ai/prompt/{safe_query}?width=1080&height=620&model=flux&nologo=true&seed={seed}"

    # 15% Chance to use Picsum (Reliable random image)
    elif choice <= 95:
        return f"https://picsum.photos/1080/620?random={random.randint(1, 99999)}"

    # 5% Chance to use Static Pool (Safest)
    else:
        return random.choice(STATIC_POOL)

# ======================================================
# 4. EXPORTS FOR APP.PY
# ======================================================
# Create aliases so app.py doesn't crash
get_fallback_image_url = get_image_url
FALLBACK_IMAGES = STATIC_POOL