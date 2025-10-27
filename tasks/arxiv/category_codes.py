import random

CATEGORY_CODES = {
    "Computer Science": {
        "Artificial Intelligence": "cs.AI",
        "Computation and Language": "cs.CL",
        "Computer Vision and Pattern Recognition": "cs.CV",
        "Machine Learning": "cs.LG",
        "Cryptography and Security": "cs.CR",
        "Robotics": "cs.RO",
        "Software Engineering": "cs.SE",
        "Systems and Control": "cs.SY",
        "Networking and Internet Architecture": "cs.NI",
    },
    "Mathematics": {
        "Probability": "math.PR",
        "Statistics": "math.ST",
        "Optimization and Control": "math.OC",
        "Algebraic Geometry": "math.AG",
        "Number Theory": "math.NT",
        "Classical Analysis and ODEs": "math.CA",
    },
    "Physics": {
        "General Physics": "physics.gen-ph",
        "Applied Physics": "physics.app-ph",
        "Classical Physics": "physics.class-ph",
        "Atomic and Molecular Physics": "physics.atom-ph",
        "High Energy Physics - Theory": "hep-th",
        "High Energy Physics - Experiment": "hep-ex",
        "Astrophysics": "astro-ph",
    },
    "Quantitative Biology": {
        "Genomics": "q-bio.GN",
        "Neurons and Cognition": "q-bio.NC",
        "Populations and Evolution": "q-bio.PE",
        "Quantitative Methods": "q-bio.QM",
    },
    "Quantitative Finance": {
        "Portfolio Management": "q-fin.PM",
        "Statistical Finance": "q-fin.ST",
        "Trading and Market Microstructure": "q-fin.TR",
        "Risk Management": "q-fin.RM",
    },
    "Statistics": {
        "Machine Learning": "stat.ML",
        "Methodology": "stat.ME",
        "Applications": "stat.AP",
        "Computation": "stat.CO",
    },
    "Electrical Engineering and Systems Science": {
        "Signal Processing": "eess.SP",
        "Systems and Control": "eess.SY",
        "Audio and Speech Processing": "eess.AS",
    },
    "Economics": {
        "Theoretical Economics": "econ.TH",
        "General Economics": "econ.GN",
    },
}


def sample_category_code():
    subject = random.choice(list(CATEGORY_CODES.keys()))
    sub_categories: dict[str, str] = CATEGORY_CODES[subject]
    sub_category = random.choice(list(sub_categories.keys()))
    return subject, sub_category, sub_categories[sub_category]
