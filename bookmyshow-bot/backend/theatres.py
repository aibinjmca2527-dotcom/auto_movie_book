# ─── Accurate Theatre Data for Kerala Cities ───────────────────────────────────
# Manually verified theatre data for Kochi, Alappuzha, Changanassery

THEATRES = {
    "KOCHI": [
        {"name": "PVR Cinemas - LuLu Mall Kochi",         "area": "Edapally, Kochi",          "code": "PVRL", "maps_url": "https://www.google.com/maps/search/?api=1&query=PVR+Cinemas+LuLu+Mall+Kochi"},
        {"name": "Cinepolis - LuLu Mall Kochi",           "area": "Edapally, Kochi",          "code": "CNPL", "maps_url": "https://www.google.com/maps/search/?api=1&query=Cinepolis+LuLu+Mall+Kochi"},
        {"name": "PVR INOX - Oberon Mall",                "area": "Edapally, Kochi",          "code": "PVRO", "maps_url": "https://www.google.com/maps/search/?api=1&query=PVR+INOX+Oberon+Mall+Kochi"},
        {"name": "Shenoys Cinemas",                       "area": "MG Road, Kochi",           "code": "SHEN", "maps_url": "https://www.google.com/maps/search/?api=1&query=Shenoys+Cinemas+Kochi"},
        {"name": "Kavitha Theatre",                       "area": "Thrippunithura, Kochi",    "code": "KAVT", "maps_url": "https://www.google.com/maps/search/?api=1&query=Kavitha+Theatre+Thrippunithura"},
        {"name": "Padma Theatre",                         "area": "Aluva, Kochi",             "code": "PADM", "maps_url": "https://www.google.com/maps/search/?api=1&query=Padma+Theatre+Aluva+Kochi"},
        {"name": "Saritha Theatre",                       "area": "MG Road, Ernakulam",       "code": "SART", "maps_url": "https://www.google.com/maps/search/?api=1&query=Saritha+Theatre+Ernakulam"},
        {"name": "Rajhans Cinemas",                       "area": "Kakkanad, Kochi",          "code": "RAJH", "maps_url": "https://www.google.com/maps/search/?api=1&query=Rajhans+Cinemas+Kakkanad+Kochi"},
        {"name": "INOX - Bhavans",                        "area": "Thrissur Road, Kochi",     "code": "INXB", "maps_url": "https://www.google.com/maps/search/?api=1&query=INOX+Bhavans+Kochi"},
        {"name": "Gold Cinema",                           "area": "North Paravur, Kochi",     "code": "GOLC", "maps_url": "https://www.google.com/maps/search/?api=1&query=Gold+Cinema+North+Paravur"},
        {"name": "Fun Republic Mall Cinemas",             "area": "Kadavanthra, Kochi",       "code": "FUNR", "maps_url": "https://www.google.com/maps/search/?api=1&query=Fun+Republic+Mall+Kochi"},
        {"name": "Carnival Cinemas - Muthoot Plaza",      "area": "Pathadipalam, Kochi",      "code": "CARM", "maps_url": "https://www.google.com/maps/search/?api=1&query=Carnival+Cinemas+Muthoot+Plaza+Kochi"},
        {"name": "Kanaka Theatre",                        "area": "Perumbavoor, Kochi",       "code": "KANA", "maps_url": "https://www.google.com/maps/search/?api=1&query=Kanaka+Theatre+Perumbavoor"},
        {"name": "Diana Theatre",                         "area": "Angamaly, Kochi",          "code": "DIAN", "maps_url": "https://www.google.com/maps/search/?api=1&query=Diana+Theatre+Angamaly"},
        {"name": "Merryland Cinemas",                     "area": "Fort Kochi",               "code": "MERR", "maps_url": "https://www.google.com/maps/search/?api=1&query=Merryland+Cinemas+Fort+Kochi"},
    ],

    "ALPY": [
        {"name": "Pan Asia Cinemas",                      "area": "Alappuzha Town",           "code": "PANA", "maps_url": "https://www.google.com/maps/search/?api=1&query=Pan+Asia+Cinemas+Alappuzha"},
        {"name": "AEC Cinemas",                           "area": "Alappuzha Town",           "code": "AECC", "maps_url": "https://www.google.com/maps/search/?api=1&query=AEC+Cinemas+Alappuzha"},
        {"name": "Sowparnika Theatre",                    "area": "Alappuzha",                "code": "SOWP", "maps_url": "https://www.google.com/maps/search/?api=1&query=Sowparnika+Theatre+Alappuzha"},
        {"name": "Vijaya Theatre",                        "area": "Cherthala, Alappuzha",     "code": "VIJA", "maps_url": "https://www.google.com/maps/search/?api=1&query=Vijaya+Theatre+Cherthala"},
        {"name": "Kavitha Theatre",                       "area": "Kayamkulam, Alappuzha",    "code": "KAVK", "maps_url": "https://www.google.com/maps/search/?api=1&query=Kavitha+Theatre+Kayamkulam"},
        {"name": "Sree Theatre",                          "area": "Haripad, Alappuzha",       "code": "SREH", "maps_url": "https://www.google.com/maps/search/?api=1&query=Sree+Theatre+Haripad"},
        {"name": "Mafia Cinemas",                         "area": "Mavelikkara, Alappuzha",   "code": "MAFI", "maps_url": "https://www.google.com/maps/search/?api=1&query=Mafia+Cinemas+Mavelikkara"},
        {"name": "Ambal Theatre",                         "area": "Ambalapuzha, Alappuzha",   "code": "AMBL", "maps_url": "https://www.google.com/maps/search/?api=1&query=Ambal+Theatre+Ambalapuzha"},
        {"name": "Geetha Theatre",                        "area": "Alappuzha Town",           "code": "GEET", "maps_url": "https://www.google.com/maps/search/?api=1&query=Geetha+Theatre+Alappuzha"},
        {"name": "Santhi Theatre",                        "area": "Alappuzha",                "code": "SANT", "maps_url": "https://www.google.com/maps/search/?api=1&query=Santhi+Theatre+Alappuzha"},
    ],

    "KTYM": [
        {"name": "Carnival Cinemas - Kottayam",           "area": "Kottayam Town",            "code": "CARK", "maps_url": "https://www.google.com/maps/search/?api=1&query=Carnival+Cinemas+Kottayam"},
        {"name": "Martin's Cinema",                       "area": "Kottayam Town",            "code": "MART", "maps_url": "https://www.google.com/maps/search/?api=1&query=Martins+Cinema+Kottayam"},
        {"name": "Sree Theatre Changanassery",            "area": "Changanassery, Kottayam",  "code": "SREC", "maps_url": "https://www.google.com/maps/search/?api=1&query=Sree+Theatre+Changanassery"},
        {"name": "Mini Theatre Changanassery",            "area": "Changanassery, Kottayam",  "code": "MINC", "maps_url": "https://www.google.com/maps/search/?api=1&query=Mini+Theatre+Changanassery"},
        {"name": "Kavitha Cinemas",                       "area": "Kottayam Town",            "code": "KAVC", "maps_url": "https://www.google.com/maps/search/?api=1&query=Kavitha+Cinemas+Kottayam"},
        {"name": "Vasantha Theatre",                      "area": "Pala, Kottayam",           "code": "VAST", "maps_url": "https://www.google.com/maps/search/?api=1&query=Vasantha+Theatre+Pala+Kottayam"},
        {"name": "Suja Cinemas",                          "area": "Ettumanoor, Kottayam",     "code": "SUJA", "maps_url": "https://www.google.com/maps/search/?api=1&query=Suja+Cinemas+Ettumanoor"},
        {"name": "Sreekumar Theatre",                     "area": "Changanassery, Kottayam",  "code": "SKUM", "maps_url": "https://www.google.com/maps/search/?api=1&query=Sreekumar+Theatre+Changanassery"},
        {"name": "Uday Cinema",                           "area": "Kottayam Town",            "code": "UDAY", "maps_url": "https://www.google.com/maps/search/?api=1&query=Uday+Cinema+Kottayam"},
        {"name": "Vaiga Theatre",                         "area": "Vaikom, Kottayam",         "code": "VAIG", "maps_url": "https://www.google.com/maps/search/?api=1&query=Vaiga+Theatre+Vaikom"},
    ],

    "TVM": [
        {"name": "PVR Cinemas - Trivandrum",              "area": "Palayam, Thiruvananthapuram", "code": "PVRT", "maps_url": "https://www.google.com/maps/search/?api=1&query=PVR+Cinemas+Trivandrum"},
        {"name": "Carnival Cinemas - Trivandrum",         "area": "Kazhakkoottam, TVM",       "code": "CART", "maps_url": "https://www.google.com/maps/search/?api=1&query=Carnival+Cinemas+Trivandrum"},
        {"name": "Sreekumar Theatre",                     "area": "Thiruvananthapuram",        "code": "SKUT", "maps_url": "https://www.google.com/maps/search/?api=1&query=Sreekumar+Theatre+Trivandrum"},
        {"name": "Kalabhavan Theatre",                    "area": "Thiruvananthapuram",        "code": "KALB", "maps_url": "https://www.google.com/maps/search/?api=1&query=Kalabhavan+Theatre+Trivandrum"},
        {"name": "Rajasree Theatre",                      "area": "Thiruvananthapuram",        "code": "RAJS", "maps_url": "https://www.google.com/maps/search/?api=1&query=Rajasree+Theatre+Trivandrum"},
        {"name": "Casino Theatre",                        "area": "Thiruvananthapuram",        "code": "CASI", "maps_url": "https://www.google.com/maps/search/?api=1&query=Casino+Theatre+Trivandrum"},
        {"name": "Attukal Bhagavathy Theatre",            "area": "Thiruvananthapuram",        "code": "ATTK", "maps_url": "https://www.google.com/maps/search/?api=1&query=Attukal+Theatre+Trivandrum"},
        {"name": "Kairali Theatre",                       "area": "Thiruvananthapuram",        "code": "KAIR", "maps_url": "https://www.google.com/maps/search/?api=1&query=Kairali+Theatre+Trivandrum"},
    ],

    "CALICUT": [
        {"name": "PVR Cinemas - Calicut",                 "area": "Focus Mall, Kozhikode",    "code": "PVRC", "maps_url": "https://www.google.com/maps/search/?api=1&query=PVR+Cinemas+Calicut"},
        {"name": "Cinepolis - Calicut",                   "area": "Kozhikode",                "code": "CNPC", "maps_url": "https://www.google.com/maps/search/?api=1&query=Cinepolis+Calicut"},
        {"name": "Regina Theatre",                        "area": "Kozhikode Town",           "code": "REGI", "maps_url": "https://www.google.com/maps/search/?api=1&query=Regina+Theatre+Kozhikode"},
        {"name": "Kairali Theatre",                       "area": "Kozhikode",                "code": "KAIK", "maps_url": "https://www.google.com/maps/search/?api=1&query=Kairali+Theatre+Kozhikode"},
        {"name": "Sangeetha Theatre",                     "area": "Kozhikode",                "code": "SANG", "maps_url": "https://www.google.com/maps/search/?api=1&query=Sangeetha+Theatre+Kozhikode"},
    ],

    "TCR": [
        {"name": "Sangeetha Theatre",                     "area": "Thrissur Town",            "code": "SNGT", "maps_url": "https://www.google.com/maps/search/?api=1&query=Sangeetha+Theatre+Thrissur"},
        {"name": "Priya Theatre",                         "area": "Thrissur Town",            "code": "PRIY", "maps_url": "https://www.google.com/maps/search/?api=1&query=Priya+Theatre+Thrissur"},
        {"name": "Akashvani Theatre",                     "area": "Thrissur",                 "code": "AKAS", "maps_url": "https://www.google.com/maps/search/?api=1&query=Akashvani+Theatre+Thrissur"},
        {"name": "Navarathna Theatre",                    "area": "Thrissur",                 "code": "NAVA", "maps_url": "https://www.google.com/maps/search/?api=1&query=Navarathna+Theatre+Thrissur"},
        {"name": "Guruvayur Cineplex",                    "area": "Guruvayur, Thrissur",      "code": "GURV", "maps_url": "https://www.google.com/maps/search/?api=1&query=Guruvayur+Cineplex+Thrissur"},
    ],

    "KANN": [
        {"name": "Cinepolis - Kannur",                    "area": "Kannur Town",              "code": "CNPK", "maps_url": "https://www.google.com/maps/search/?api=1&query=Cinepolis+Kannur"},
        {"name": "Sapna Theatre",                         "area": "Kannur Town",              "code": "SAPN", "maps_url": "https://www.google.com/maps/search/?api=1&query=Sapna+Theatre+Kannur"},
        {"name": "Abhilash Theatre",                      "area": "Thalassery, Kannur",       "code": "ABHI", "maps_url": "https://www.google.com/maps/search/?api=1&query=Abhilash+Theatre+Thalassery"},
    ],

    "PKD": [
        {"name": "Carnival Cinemas - Palakkad",           "area": "Palakkad Town",            "code": "CARP", "maps_url": "https://www.google.com/maps/search/?api=1&query=Carnival+Cinemas+Palakkad"},
        {"name": "Sree Theatre",                          "area": "Palakkad Town",            "code": "SREP", "maps_url": "https://www.google.com/maps/search/?api=1&query=Sree+Theatre+Palakkad"},
        {"name": "Chithra Theatre",                       "area": "Palakkad",                 "code": "CHIT", "maps_url": "https://www.google.com/maps/search/?api=1&query=Chithra+Theatre+Palakkad"},
    ],

    "MLM": [
        {"name": "Amutha Cinemas",                        "area": "Manjeri, Malappuram",      "code": "AMUT", "maps_url": "https://www.google.com/maps/search/?api=1&query=Amutha+Cinemas+Manjeri"},
        {"name": "Skyline Cinemas",                       "area": "Malappuram Town",          "code": "SKYL", "maps_url": "https://www.google.com/maps/search/?api=1&query=Skyline+Cinemas+Malappuram"},
        {"name": "Sree Theatre",                          "area": "Tirur, Malappuram",        "code": "SRET", "maps_url": "https://www.google.com/maps/search/?api=1&query=Sree+Theatre+Tirur"},
    ],
}

# City code aliases — map all variants to main code
CITY_THEATRE_MAP = {
    "KOCHI": "KOCHI", "ERNAKULAM": "KOCHI",
    "ALPY": "ALPY",
    "KTYM": "KTYM",
    "TVM": "TVM",
    "CALICUT": "CALICUT",
    "TCR": "TCR",
    "KANN": "KANN",
    "PKD": "PKD",
    "MLM": "MLM",
}

def get_theatres_for_city(city_code: str) -> list:
    mapped = CITY_THEATRE_MAP.get(city_code.upper(), city_code.upper())
    return THEATRES.get(mapped, [])
