import sqlite3
import json
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
from config import ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_USERNAME, DB_PATH, DATA_DIR

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.execute('PRAGMA busy_timeout=30000')
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = connect()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS activity(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        details TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS experiments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        difficulty TEXT DEFAULT 'Beginner',
        safety_level TEXT DEFAULT 'Low',
        principles TEXT,
        description TEXT,
        aim TEXT,
        materials TEXT,
        apparatus TEXT,
        chemicals TEXT,
        safety_precautions TEXT,
        procedure TEXT,
        interactive_steps TEXT,
        green_points TEXT,
        waste_generated TEXT,
        waste_management TEXT,
        alternatives TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS quiz_questions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        correct_answer TEXT NOT NULL,
        explanation TEXT,
        topic TEXT NOT NULL,
        difficulty TEXT DEFAULT 'Medium',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS quiz_attempts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        topic TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        score INTEGER NOT NULL,
        total_questions INTEGER NOT NULL,
        percentage REAL NOT NULL,
        correct_answers INTEGER NOT NULL,
        review_json TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS practical_attempts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        experiment_id INTEGER NOT NULL,
        experiment_name TEXT NOT NULL,
        observations TEXT,
        result TEXT,
        conclusion TEXT,
        waste_info TEXT,
        status TEXT DEFAULT 'Completed',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(experiment_id) REFERENCES experiments(id)
    );
    CREATE TABLE IF NOT EXISTS reports(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        practical_id INTEGER,
        experiment_id INTEGER,
        title TEXT NOT NULL,
        content_json TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS chat_messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    c.commit()

    # Ensure users has is_admin column
    try:
        c.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
        c.commit()
    except Exception:
        pass

    # Ensure activity has details column
    try:
        c.execute("ALTER TABLE activity ADD COLUMN details TEXT")
        c.commit()
    except Exception:
        pass

    # Ensure reports has practical_id and experiment_id columns
    try:
        c.execute("ALTER TABLE reports ADD COLUMN practical_id INTEGER")
        c.commit()
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE reports ADD COLUMN experiment_id INTEGER")
        c.commit()
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE reports ADD COLUMN description TEXT")
        c.commit()
    except Exception:
        pass
    # Ensure reports has content_json column (older DBs used 'description' instead)
    try:
        c.execute("ALTER TABLE reports ADD COLUMN content_json TEXT NOT NULL DEFAULT '{}'")
        c.commit()
    except Exception:
        pass

    # Seed an admin only when credentials are explicitly configured.
    admin = c.execute("SELECT id FROM users WHERE username=?", (ADMIN_USERNAME,)).fetchone()
    if not admin and ADMIN_PASSWORD:
        c.execute(
            "INSERT INTO users(name, username, email, password_hash, is_admin) VALUES (?,?,?,?,?)",
            ("Administrator", ADMIN_USERNAME, ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), 1)
        )
        c.commit()

    # Seed experiments if empty
    exp_count = c.execute("SELECT COUNT(*) n FROM experiments").fetchone()['n']
    if exp_count == 0:
        seed_experiments(c)

    # Seed quiz questions if empty
    q_count = c.execute("SELECT COUNT(*) n FROM quiz_questions").fetchone()['n']
    if q_count == 0:
        seed_quiz_questions(c)

    c.close()

def seed_experiments(c):
    experiments = [
        {
            "id": 1,
            "name": "Esterification with Safer Conditions",
            "category": "Organic Chemistry",
            "difficulty": "Intermediate",
            "safety_level": "Low-Medium",
            "principles": json.dumps(["Atom Economy", "Safer Solvents & Auxiliaries", "Energy Efficiency", "Catalysis"]),
            "description": "Preparation of ethyl acetate from bio-ethanol and acetic acid using a solid acid or mild catalyst in a gentle water bath.",
            "aim": "To synthesize an ester (ethyl acetate) with high atom economy while minimizing solvent waste and thermal energy expenditure.",
            "materials": json.dumps(["Glacial acetic acid (or dilute bio-based acetic acid)", "Ethanol (renewable feedstock)", "Mild acid catalyst / Amberlyst-15 resin", "Deionized water", "Saturated sodium bicarbonate solution"]),
            "apparatus": json.dumps(["50 mL Round-bottom flask / boiling tube", "Gentle water bath (heating mantle at 65°C)", "Reflux condenser", "Separatory funnel", "Thermometer", "Safety goggles & nitrile gloves"]),
            "chemicals": json.dumps(["Acetic Acid: 0.1 mol (6.0 g)", "Ethanol: 0.15 mol (6.9 g)", "Catalyst: 0.2 g Amberlyst-15 resin (reusable)", "Sodium bicarbonate: 5% solution"]),
            "safety_precautions": json.dumps([
                "Wear safety splash goggles, lab coat, and chemical-resistant nitrile gloves.",
                "Handle glacial acetic acid in a fume hood or well-ventilated area.",
                "Use a water bath; never heat flammable ethanol directly with an open flame.",
                "Ensure pressure relief when venting the separatory funnel."
            ]),
            "procedure": json.dumps([
                "Accurately measure 6.0 g of acetic acid and 6.9 g of ethanol into a reaction flask.",
                "Add 0.2 g of solid acid catalyst resin beads.",
                "Fit with a reflux condenser and immerse in a 65°C water bath for 30 minutes.",
                "Allow the reaction mixture to cool to ambient temperature.",
                "Decant the liquid from the reusable solid catalyst.",
                "Wash organic layer with 5% sodium bicarbonate to neutralize remaining acid.",
                "Dry the ester over anhydrous sodium sulfate and determine volume and mass."
            ]),
            "interactive_steps": json.dumps([
                {
                    "step": 1,
                    "title": "Reagent Measurement & Catalyst Addition",
                    "instruction": "Measure stoichiometric amounts of acetic acid and ethanol. Add reusable Amberlyst-15 solid catalyst instead of concentrated sulfuric acid.",
                    "action_name": "Mix Reactants & Catalyst",
                    "feedback": "Reactants mixed. Notice the solid resin catalyst eliminates corrosive liquid acid waste."
                },
                {
                    "step": 2,
                    "title": "Gentle Water Bath Heating",
                    "instruction": "Set the temperature controller to 65°C using a closed water bath. Reflux gently for 30 minutes.",
                    "action_name": "Start Water Bath Reflux",
                    "feedback": "Heating initiated. Ambient water bath heating saves energy compared to high-temperature oil baths."
                },
                {
                    "step": 3,
                    "title": "Catalyst Separation & Product Isolation",
                    "instruction": "Cool reaction mixture. Filter and decant the ester-containing liquid to recover solid catalyst beads for reuse.",
                    "action_name": "Decant & Recover Catalyst",
                    "feedback": "Catalyst separated intact. It can be washed and reused for subsequent runs (Principle #9: Catalysis)."
                },
                {
                    "step": 4,
                    "title": "Neutralization & Washing",
                    "instruction": "Wash the crude ester with 5% sodium bicarbonate solution to neutralize unreacted acetic acid.",
                    "action_name": "Wash with Bicarbonate",
                    "feedback": "Gentle effervescence observed ($CO_2$ evolved). Aqueous layer contains biodegradable sodium acetate."
                }
            ]),
            "green_points": json.dumps([
                "Atom Economy: Theoretical atom economy of 83% with water as the only stoichiometric by-product.",
                "Reusable solid catalyst replaces hazardous concentrated sulfuric acid.",
                "Uses renewable bio-ethanol as a feedstock.",
                "Low-temperature water bath reduces energy consumption (Principle #6)."
            ]),
            "waste_generated": "Aqueous wash containing dilute sodium acetate and residual ethanol; recoverable solid catalyst.",
            "waste_management": "Neutralize aqueous wash to pH 7 before drain disposal in accordance with regulations; recover and air-dry Amberlyst-15 resin for reuse.",
            "alternatives": json.dumps([
                "Replaced corrosive concentrated $H_2SO_4$ with reusable heterogeneous acid resin (Amberlyst-15).",
                "Replaced toxic volatile organic reaction solvents with neat reactants."
            ])
        },
        {
            "id": 2,
            "name": "Solvent-Free Aldol Reaction",
            "category": "Organic Chemistry",
            "difficulty": "Intermediate",
            "safety_level": "Low",
            "principles": json.dumps(["Prevention", "Atom Economy", "Safer Solvents & Auxiliaries"]),
            "description": "Solid-state or neat aldol condensation between an aldehyde and a ketone catalyzed by mild base with zero reaction solvent.",
            "aim": "To perform a carbon-carbon bond forming aldol condensation under completely solvent-free conditions, maximizing atom economy and eliminating solvent waste.",
            "materials": json.dumps(["Benzaldehyde or 4-chlorobenzaldehyde (neat)", "Acetone or cyclohexanone (neat)", "Solid sodium hydroxide pellets / grindable mild base", "Mortar and pestle", "Ice-water bath"]),
            "apparatus": json.dumps(["Porcelain mortar and pestle", "Watch glass / spatula", "Small Hirsch funnel with vacuum flask", "Melting point apparatus", "Analytical balance"]),
            "chemicals": json.dumps(["Benzaldehyde: 10 mmol (1.06 g)", "Cyclohexanone: 5 mmol (0.49 g)", "Solid NaOH: 0.1 g (finely ground)"]),
            "safety_precautions": json.dumps([
                "Wear safety glasses, lab coat, and nitrile gloves.",
                "Grind solid NaOH gently to avoid airborne caustic particulate; wear mask or work inside fume hood.",
                "Avoid skin contact with aldehydes and aromatic ketones."
            ]),
            "procedure": json.dumps([
                "Weigh aldehyde and ketone in a 2:1 stoichiometric ratio.",
                "Transfer reactants into a dry porcelain mortar without adding any organic solvent.",
                "Add powdered NaOH catalyst.",
                "Grind the mixture steadily with a pestle for 10-15 minutes.",
                "Observe the liquid reaction slurry solidify into a paste and then into a firm crystalline mass.",
                "Add 10 mL of ice-cold water to precipitate the product and dissolve residual base.",
                "Collect crystals via vacuum filtration and wash with cold water."
            ]),
            "interactive_steps": json.dumps([
                {
                    "step": 1,
                    "title": "Neat Reagent Charging",
                    "instruction": "Transfer the liquid aldehyde and ketone directly into the mortar. Notice that no solvent (e.g., ethanol or ether) is added.",
                    "action_name": "Charge Neat Reagents",
                    "feedback": "Reagents charged. 100% solvent elimination achieved in the reaction phase."
                },
                {
                    "step": 2,
                    "title": "Solid Base Addition & Grinding",
                    "instruction": "Add ground sodium hydroxide and begin grinding thoroughly with the pestle.",
                    "action_name": "Grind Mixture",
                    "feedback": "Mechanochemical energy initiates the aldol reaction. The yellow liquid turns thick and opaque."
                },
                {
                    "step": 3,
                    "title": "Crystallization & Solidification",
                    "instruction": "Continue grinding as enone product forms and crystallizes out.",
                    "action_name": "Observe Crystallization",
                    "feedback": "The mixture transitions into a bright yellow solid cake. Rapid, high-conversion synthesis complete."
                },
                {
                    "step": 4,
                    "title": "Aqueous Wash & Filtration",
                    "instruction": "Triturate with cold water to remove salt and filter the crude crystalline solid.",
                    "action_name": "Filter & Wash Crystals",
                    "feedback": "Pure crystalline dibenzylidene product isolated on Hirsch funnel."
                }
            ]),
            "green_points": json.dumps([
                "Zero organic solvent used in reaction phase (Principle #5).",
                "High atom economy (~93%) with elimination of only two water molecules.",
                "Ambient temperature and atmospheric pressure mechanochemical reaction (Principle #6)."
            ]),
            "waste_generated": "Dilute aqueous alkaline filtrate (~15 mL) containing traces of unreacted aldehyde.",
            "waste_management": "Neutralize alkaline filtrate with dilute HCl to pH 6-8 before discharge. Zero hazardous organic solvent waste generated.",
            "alternatives": json.dumps([
                "Replaced 50 mL of flammable ethanol/methanol reaction solvent with solid-state grinding.",
                "Replaced toxic halogenated extraction solvents with simple cold-water washing."
            ])
        },
        {
            "id": 3,
            "name": "Natural Acid-Base Indicator",
            "category": "Analytical Chemistry",
            "difficulty": "Beginner",
            "safety_level": "Low",
            "principles": json.dumps(["Use of Renewable Feedstocks", "Designing Safer Chemicals", "Prevention"]),
            "description": "Extraction of anthocyanin pigments from red cabbage using water, and application as a multi-range natural indicator.",
            "aim": "To extract anthocyanin bio-pigments using water as a green solvent and characterize acid-base transition ranges without hazardous synthetic indicators.",
            "materials": json.dumps(["Fresh red cabbage leaves (chopped)", "Boiling deionized water", "Household/lab test solutions (vinegar, lemon juice, baking soda, soap solution, dilute HCl, dilute NaOH)"]),
            "apparatus": json.dumps(["250 mL Beaker", "Hot plate / kettle", "Glass funnel & filter paper", "Well plate / test tube rack", "Droppers"]),
            "chemicals": json.dumps(["Anthocyanin extract in water (non-toxic)", "Dilute hydrochloric acid (0.1 M)", "Dilute sodium hydroxide (0.1 M)", "Standard pH buffers 1-12"]),
            "safety_precautions": json.dumps([
                "Wear safety glasses and gloves when testing acid and base solutions.",
                "Handle boiling water with thermal insulated gloves.",
                "Wash hands thoroughly after completing tests."
            ]),
            "procedure": json.dumps([
                "Chop 20 g of red cabbage into small shreds.",
                "Place into a 250 mL beaker and add 100 mL of boiling water.",
                "Allow to steep for 10 minutes until deep purple anthocyanin extracts into solution.",
                "Filter extract through fluted filter paper into an Erlenmeyer flask.",
                "Pipette 2 mL of extract into series of test wells.",
                "Add test solutions across pH 1 to 13 and observe vivid color transitions (Red -> Purple -> Blue -> Green -> Yellow)."
            ]),
            "interactive_steps": json.dumps([
                {
                    "step": 1,
                    "title": "Aqueous Bio-Extraction",
                    "instruction": "Steep chopped cabbage in boiling water to extract water-soluble anthocyanins.",
                    "action_name": "Extract Anthocyanins",
                    "feedback": "Deep violet solution formed. 100% renewable bio-resource extracted using pure water."
                },
                {
                    "step": 2,
                    "title": "Filtration of Plant Pulp",
                    "instruction": "Filter the plant pulp to obtain a clear, concentrated indicator solution.",
                    "action_name": "Filter Solution",
                    "feedback": "Solid cabbage waste is 100% biodegradable and compostable."
                },
                {
                    "step": 3,
                    "title": "Acidic Spectrum Testing",
                    "instruction": "Add dilute acid (pH 2-4) to test well containing indicator.",
                    "action_name": "Test Acid Sample",
                    "feedback": "Solution turns bright pink/red due to flavylium cation formation."
                },
                {
                    "step": 4,
                    "title": "Basic Spectrum Testing",
                    "instruction": "Add dilute base (pH 9-12) to test well containing indicator.",
                    "action_name": "Test Base Sample",
                    "feedback": "Solution turns emerald green then yellow as quinonoidal species form."
                }
            ]),
            "green_points": json.dumps([
                "100% renewable bio-based indicator replacing petroleum-derived synthetic dyes (Principle #7).",
                "Pure water used as solvent; zero VOC exposure (Principle #5).",
                "Waste is non-hazardous and completely compostable (Principle #10)."
            ]),
            "waste_generated": "Biodegradable cabbage leaves; neutralized aqueous test solutions.",
            "waste_management": "Plant pulp can be composted. Neutralize test solutions and dispose via standard drain.",
            "alternatives": json.dumps([
                "Replaces toxic phenolphthalein, methyl orange, and bromothymol blue dyes.",
                "Replaces hazardous solvent extraction (e.g. methanol) with hot water extraction."
            ])
        },
        {
            "id": 4,
            "name": "Microscale Reaction Study",
            "category": "Green Lab Practice",
            "difficulty": "Beginner",
            "safety_level": "Very Low",
            "principles": json.dumps(["Prevention", "Inherently Safer Chemistry", "Real-Time Analysis"]),
            "description": "Miniaturization of chemical reactions using micro-well plates and capillary droppers to cut chemical consumption and waste by 95%.",
            "aim": "To demonstrate chemical precipitation and complexation at microscale (microliter scale), measuring quantitative reduction in chemical waste and exposure.",
            "materials": json.dumps(["24-well microplate", "Fine-tip polyethylene pipettes", "Micro-spatulas", "Color chart comparison card"]),
            "apparatus": json.dumps(["Microplate", "Micro-pipettes (10-100 uL)", "Digital micro-balance", "Magnifying glass"]),
            "chemicals": json.dumps(["0.05 M Iron(III) chloride (2 drops / 0.1 mL)", "0.05 M Potassium thiocyanate (2 drops / 0.1 mL)", "0.1 M Silver nitrate (1 drop)", "0.1 M Sodium chloride (1 drop)"]),
            "safety_precautions": json.dumps([
                "Standard PPE: safety spectacles and gloves.",
                "Avoid contact with silver nitrate (causes skin discoloration).",
                "Work on a white bench mat for clear visibility of micro-scale reactions."
            ]),
            "procedure": json.dumps([
                "Place a clean 24-well plate over a white background sheet.",
                "Dispense exactly 2 drops (~0.1 mL) of 0.05 M FeCl3 into Well A1.",
                "Add 2 drops (~0.1 mL) of 0.05 M KSCN into Well A1; record instantaneous deep blood-red complexation.",
                "In Well B1, dispense 1 drop of 0.1 M AgNO3 and 1 drop of 0.1 M NaCl; record immediate white AgCl precipitation.",
                "Calculate total volume of chemical consumed: ~0.3 mL total compared to 50 mL for macroscale test.",
                "Calculate waste reduction percentage: >98% waste volume reduction."
            ]),
            "interactive_steps": json.dumps([
                {
                    "step": 1,
                    "title": "Well Plate Setup & Calibration",
                    "instruction": "Set up a 24-well microplate and calibrate dropper volumes (1 drop approx. 0.05 mL).",
                    "action_name": "Calibrate Microplate",
                    "feedback": "Microplate configured. Total experiment capacity reduced by a factor of 100x."
                },
                {
                    "step": 2,
                    "title": "Micro-Complexation Reaction",
                    "instruction": "Dispense 2 drops of iron(III) chloride and 2 drops of potassium thiocyanate.",
                    "action_name": "Dispense Iron & Thiocyanate",
                    "feedback": "Instantaneous deep red $[Fe(SCN)]^{2+}$ complex formed with only 0.1 mL total volume."
                },
                {
                    "step": 3,
                    "title": "Micro-Precipitation Reaction",
                    "instruction": "Dispense 1 drop of silver nitrate and 1 drop of sodium chloride in Well B1.",
                    "action_name": "Dispense Silver & Chloride",
                    "feedback": "Curdy white AgCl precipitate observed. Microscale provides identical observational clarity."
                },
                {
                    "step": 4,
                    "title": "Waste Metric Computation",
                    "instruction": "Tabulate mass and volume of waste generated versus traditional beaker tests.",
                    "action_name": "Calculate Green Metrics",
                    "feedback": "Over 98% reduction in hazardous chemical waste and 99% cost reduction achieved."
                }
            ]),
            "green_points": json.dumps([
                "Source Reduction: Waste prevented at origin (Principle #1: Prevention).",
                "Inherently Safer: Tiny volumes minimize risk of fire, thermal runaway, and toxic exposure (Principle #12).",
                "E-factor drastically lowered; high educational throughput with minimal environmental footprint."
            ]),
            "waste_generated": "Total liquid waste is less than 0.5 mL.",
            "waste_management": "Collect microplate liquid using an absorbent wipe or syringe into dedicated heavy-metal micro-waste container. No gallons of waste generated.",
            "alternatives": json.dumps([
                "Replaces traditional macroscale 50-100 mL test-tube reactions with 0.1 mL micro-wells.",
                "Reduces reagent consumption and associated environmental footprint by 99%."
            ])
        }
    ]

    for exp in experiments:
        c.execute("""
        INSERT OR REPLACE INTO experiments (
            id, name, category, difficulty, safety_level, principles, description,
            aim, materials, apparatus, chemicals, safety_precautions, procedure,
            interactive_steps, green_points, waste_generated, waste_management, alternatives
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            exp["id"], exp["name"], exp["category"], exp["difficulty"], exp["safety_level"],
            exp["principles"], exp["description"], exp["aim"], exp["materials"],
            exp["apparatus"], exp["chemicals"], exp["safety_precautions"], exp["procedure"],
            exp["interactive_steps"], exp["green_points"], exp["waste_generated"],
            exp["waste_management"], exp["alternatives"]
        ))
    c.commit()

def seed_quiz_questions(c):
    questions = [
        # --- TOPIC: 12 Principles ---
        {
            "question": "Which principle of green chemistry states that it is better to prevent waste than to treat or clean up waste after it is formed?",
            "option_a": "Principle 1: Waste Prevention",
            "option_b": "Principle 5: Safer Solvents",
            "option_c": "Principle 9: Catalysis",
            "option_d": "Principle 11: Real-Time Analysis",
            "correct_answer": "Principle 1: Waste Prevention",
            "explanation": "Principle 1 (Prevention) is the foundational rule of Green Chemistry: design chemical processes to prevent waste rather than managing it afterwards.",
            "topic": "12 Principles",
            "difficulty": "Easy"
        },
        {
            "question": "Principle #6 advocates for 'Design for Energy Efficiency'. What experimental condition is preferred under this principle?",
            "option_a": "Operating at ambient temperature and ambient pressure",
            "option_b": "Heating above 200°C for at least 24 hours",
            "option_c": "High-pressure autoclave synthesis exclusively",
            "option_d": "Cryogenic cooling with liquid helium",
            "correct_answer": "Operating at ambient temperature and ambient pressure",
            "explanation": "Designing for energy efficiency means minimizing energy inputs by conducting reactions at ambient temperature and pressure whenever practical.",
            "topic": "12 Principles",
            "difficulty": "Easy"
        },
        {
            "question": "Which principle focuses on avoiding unnecessary protecting groups and temporary modifications in multi-step organic syntheses?",
            "option_a": "Reduce Derivatives (Principle 8)",
            "option_b": "Design for Degradation (Principle 10)",
            "option_c": "Renewable Feedstocks (Principle 7)",
            "option_d": "Atom Economy (Principle 2)",
            "correct_answer": "Reduce Derivatives (Principle 8)",
            "explanation": "Principle 8 states that unnecessary derivatization (blocking groups, protection/deprotection) should be minimized or avoided because such steps require additional reagents and generate waste.",
            "topic": "12 Principles",
            "difficulty": "Medium"
        },
        {
            "question": "What is the core concept behind Principle 10: 'Design for Degradation'?",
            "option_a": "Chemical products should break down into innocuous degradation products after their functional life",
            "option_b": "Chemicals should be permanently bio-accumulative in marine food webs",
            "option_c": "Chemical containers should dissolve immediately upon contact with water",
            "option_d": "Reagents should undergo spontaneous detonation during reaction",
            "correct_answer": "Chemical products should break down into innocuous degradation products after their functional life",
            "explanation": "Principle 10 ensures that chemical products are designed so that at the end of their function they break down into harmless substances and do not persist in the environment.",
            "topic": "12 Principles",
            "difficulty": "Medium"
        },
        {
            "question": "Principle 11 promotes 'Real-Time Analysis for Pollution Prevention'. What is its primary objective in industrial and laboratory chemistry?",
            "option_a": "Continuous in-process monitoring to detect and prevent hazardous by-product formation before it occurs",
            "option_b": "Analyzing polluted rivers only after factory discharge",
            "option_c": "Recording lab notebook entries once per year",
            "option_d": "Replacing all sensors with manual color inspections",
            "correct_answer": "Continuous in-process monitoring to detect and prevent hazardous by-product formation before it occurs",
            "explanation": "Real-time in-line monitoring enables early detection and adjustment to prevent runaway reactions or hazardous waste creation before it happens.",
            "topic": "12 Principles",
            "difficulty": "Hard"
        },

        # --- TOPIC: Atom Economy ---
        {
            "question": "How is percentage Atom Economy defined in green chemistry metrics?",
            "option_a": "(Molecular Weight of Desired Product / Total Molecular Weight of All Reactants) x 100",
            "option_b": "(Actual Yield in grams / Theoretical Yield in grams) x 100",
            "option_c": "(Total Volume of Waste / Total Volume of Solvent) x 100",
            "option_d": "(Mass of Catalyst / Mass of Limiting Reagent) x 100",
            "correct_answer": "(Molecular Weight of Desired Product / Total Molecular Weight of All Reactants) x 100",
            "explanation": "Atom Economy measures how many atoms from the reactants end up in the desired final product rather than by-products.",
            "topic": "Atom Economy",
            "difficulty": "Easy"
        },
        {
            "question": "Which reaction type inherently has a theoretical 100% Atom Economy?",
            "option_a": "Addition reaction (e.g. Diels-Alder or catalytic hydrogenation)",
            "option_b": "Bimolecular nucleophilic substitution (SN2) with stoichiometric salt by-product",
            "option_c": "Hofmann elimination producing triethylamine and water",
            "option_d": "Wittig reaction producing triphenylphosphine oxide waste",
            "correct_answer": "Addition reaction (e.g. Diels-Alder or catalytic hydrogenation)",
            "explanation": "Addition reactions combine all reactant atoms into a single product with zero stoichiometric by-products, giving 100% atom economy.",
            "topic": "Atom Economy",
            "difficulty": "Medium"
        },
        {
            "question": "A reaction has a 98% chemical yield but an Atom Economy of only 25%. What does this indicate about the synthesis?",
            "option_a": "The reaction completed cleanly, but 75% of the reactant atoms were lost as stoichiometric waste by-products",
            "option_b": "The reaction failed and almost no product was formed",
            "option_c": "The reaction consumed zero solvents",
            "option_d": "The reaction violates the conservation of mass",
            "correct_answer": "The reaction completed cleanly, but 75% of the reactant atoms were lost as stoichiometric waste by-products",
            "explanation": "Yield only measures product recovery against theoretical expectations; low atom economy means the reaction pathway itself generates large amounts of by-product waste (like bulky leaving groups).",
            "topic": "Atom Economy",
            "difficulty": "Hard"
        },
        {
            "question": "What is the environmental factor (E-factor) metric proposed by Roger Sheldon?",
            "option_a": "Total mass of waste (kg) / Mass of desired product (kg)",
            "option_b": "Mass of product / Mass of reactant",
            "option_c": "Number of principles satisfied / 12",
            "option_d": "Energy consumed (Joules) / Reaction time (hours)",
            "correct_answer": "Total mass of waste (kg) / Mass of desired product (kg)",
            "explanation": "The Sheldon E-factor is defined as the total mass of waste generated divided by the mass of desired final product. Ideal green reactions approach an E-factor of zero.",
            "topic": "Atom Economy",
            "difficulty": "Hard"
        },

        # --- TOPIC: Safety & Emergencies ---
        {
            "question": "What is the very first action a student should take if a chemical spill occurs in the laboratory?",
            "option_a": "Alert the laboratory supervisor/instructor immediately and alert nearby peers",
            "option_b": "Pour water onto an unknown chemical powder immediately",
            "option_c": "Leave the building silently without telling anyone",
            "option_d": "Soak the spill with paper towels and place them into regular trash",
            "correct_answer": "Alert the laboratory supervisor/instructor immediately and alert nearby peers",
            "explanation": "Safety protocol requires notifying the supervisor immediately so that appropriate spill neutralizers and PPE can be deployed safely.",
            "topic": "Safety & Emergencies",
            "difficulty": "Easy"
        },
        {
            "question": "What is the minimum recommended duration for flushing eyes at an emergency eye-wash station following chemical exposure?",
            "option_a": "15 minutes with eyelids held wide open",
            "option_b": "30 seconds with eyes closed",
            "option_c": "2 minutes with intermittent blinking",
            "option_d": "1 hour with cold milk",
            "correct_answer": "15 minutes with eyelids held wide open",
            "explanation": "Standard OSHA and laboratory safety protocol requires continuous flushing for at least 15 minutes to completely wash away corrosive or irritant chemicals.",
            "topic": "Safety & Emergencies",
            "difficulty": "Medium"
        },
        {
            "question": "Why are volatile organic solvents heated in a closed water bath or heating mantle rather than over a direct Bunsen burner flame?",
            "option_a": "Flammable solvent vapors can ignite readily upon contact with an open flame",
            "option_b": "Water baths make the reaction 100 times slower",
            "option_c": "Bunsen burners can only heat water, not organic compounds",
            "option_d": "Glassware will instantly turn into liquid under a flame",
            "correct_answer": "Flammable solvent vapors can ignite readily upon contact with an open flame",
            "explanation": "Organic solvents such as ethanol, acetone, and ethyl acetate are highly flammable; an open flame presents an extreme fire and explosion hazard.",
            "topic": "Safety & Emergencies",
            "difficulty": "Easy"
        },
        {
            "question": "Principle 12 ('Inherently Safer Chemistry for Accident Prevention') advises selecting chemical forms that minimize which specific risks?",
            "option_a": "Explosions, fires, toxic releases, and exothermic runaway reactions",
            "option_b": "Student curiosity and exam grades",
            "option_c": "The price of glassware only",
            "option_d": "The color intensity of dyes",
            "correct_answer": "Explosions, fires, toxic releases, and exothermic runaway reactions",
            "explanation": "Principle 12 seeks to inherently minimize accident hazards like fires, toxic vapor releases, and violent explosions through choice of safer reagents.",
            "topic": "Safety & Emergencies",
            "difficulty": "Medium"
        },

        # --- TOPIC: Waste Management ---
        {
            "question": "Why must halogenated organic waste (e.g. dichloromethane, chloroform) be strictly segregated from non-halogenated solvent waste (e.g. ethanol, acetone)?",
            "option_a": "Halogenated solvents require specialized high-temperature incineration to avoid dioxin formation and cannot be safely incinerated together",
            "option_b": "Mixing them produces instant solid gold",
            "option_c": "Halogenated solvents are completely harmless drinkable liquids",
            "option_d": "Non-halogenated solvents can never evaporate",
            "correct_answer": "Halogenated solvents require specialized high-temperature incineration to avoid dioxin formation and cannot be safely incinerated together",
            "explanation": "Halogenated solvents are hazardous, toxic, and expensive to treat; mixing them with non-halogenated waste unnecessarily contaminates the entire volume.",
            "topic": "Waste Management",
            "difficulty": "Medium"
        },
        {
            "question": "According to the Waste Management Hierarchy, which level is the most preferred environmental action?",
            "option_a": "Source Reduction and Waste Prevention",
            "option_b": "Landfill Disposal",
            "option_c": "Ocean Dumping",
            "option_d": "Chemical Neutralization after large-scale release",
            "correct_answer": "Source Reduction and Waste Prevention",
            "explanation": "Source reduction (preventing waste before it is generated) is always at the top of the waste hierarchy.",
            "topic": "Waste Management",
            "difficulty": "Easy"
        },
        {
            "question": "How can dilute aqueous acidic or basic waste be handled responsibly in a teaching lab before disposal, where authorized?",
            "option_a": "Neutralization to pH 6-8 using mild neutralizing agents followed by proper verification",
            "option_b": "Pouring concentrated fuming acid directly down the domestic drain",
            "option_c": "Boiling off all liquids into the classroom air",
            "option_d": "Mixing with concentrated cyanide to neutralize it",
            "correct_answer": "Neutralization to pH 6-8 using mild neutralizing agents followed by proper verification",
            "explanation": "In-lab neutralization of dilute inorganic acids and bases to neutral pH (6-8) is a standard green practice that avoids hazardous liquid transport.",
            "topic": "Waste Management",
            "difficulty": "Medium"
        },
        {
            "question": "What is the primary green advantage of recovering solvents via rotary evaporation or fractional distillation?",
            "option_a": "Recovers purified solvent for reuse, reducing raw material purchase and hazardous waste generation",
            "option_b": "Destroys all carbon atoms permanently",
            "option_c": "Changes the chemical identity into water",
            "option_d": "Increases total hazardous waste volume",
            "correct_answer": "Recovers purified solvent for reuse, reducing raw material purchase and hazardous waste generation",
            "explanation": "Closed-loop solvent recovery saves resources, lowers carbon footprint, and eliminates hazardous waste shipments.",
            "topic": "Waste Management",
            "difficulty": "Hard"
        },

        # --- TOPIC: Solvents & Catalysis ---
        {
            "question": "Which of the following solvents is classified as a 'preferred green solvent' due to low toxicity and biodegradability?",
            "option_a": "Water and bio-based ethanol",
            "option_b": "Benzene and carbon tetrachloride",
            "option_c": "Hexamethylphosphoramide (HMPA)",
            "option_d": "Dichloromethane (DCM)",
            "correct_answer": "Water and bio-based ethanol",
            "explanation": "Water, ethanol, ethyl lactate, and 2-MeTHF are classic green solvents that replace toxic, carcinogenic volatile organics.",
            "topic": "Solvents & Catalysis",
            "difficulty": "Easy"
        },
        {
            "question": "Why are catalytic reagents superior to stoichiometric reagents under Green Chemistry Principle 9?",
            "option_a": "Catalysts are used in small sub-stoichiometric amounts, lower activation energy, and can be regenerated and reused",
            "option_b": "Catalysts always increase the total mass of solid waste",
            "option_c": "Catalysts get consumed in 1:1 molar proportions",
            "option_d": "Catalysts cannot operate at ambient temperatures",
            "correct_answer": "Catalysts are used in small sub-stoichiometric amounts, lower activation energy, and can be regenerated and reused",
            "explanation": "Catalysts dramatically reduce waste because they are not consumed in the reaction and can carry out thousands of reaction cycles.",
            "topic": "Solvents & Catalysis",
            "difficulty": "Medium"
        },
        {
            "question": "In the Esterification experiment, why is Amberlyst-15 resin used instead of concentrated sulfuric acid?",
            "option_a": "It is a solid heterogeneous catalyst that can be easily filtered and reused without generating corrosive acidic waste",
            "option_b": "It is a hazardous volatile gas that evaporates away",
            "option_c": "It turns the product into plastic",
            "option_d": "It requires high amounts of toxic benzene",
            "correct_answer": "It is a solid heterogeneous catalyst that can be easily filtered and reused without generating corrosive acidic waste",
            "explanation": "Amberlyst-15 is a solid acid resin; simple decantation or filtration recovers it for reuse, completely avoiding caustic acid effluents.",
            "topic": "Solvents & Catalysis",
            "difficulty": "Medium"
        },
        {
            "question": "What is a major green benefit of conducting a 'Solvent-Free' Aldol reaction?",
            "option_a": "Eliminates flammable, volatile organic solvents, simplifies product isolation, and reduces environmental footprint",
            "option_b": "Requires 100 gallons of solvent during grinding",
            "option_c": "Ensures that the reaction takes at least 5 days to complete",
            "option_d": "Guarantees zero chemical conversion",
            "correct_answer": "Eliminates flammable, volatile organic solvents, simplifies product isolation, and reduces environmental footprint",
            "explanation": "Neat or mechanochemical reactions eliminate solvent purchase, handling, exposure, and disposal entirely.",
            "topic": "Solvents & Catalysis",
            "difficulty": "Hard"
        },
        {
            "question": "Which of the following represents a renewable, bio-based feedstock (Principle 7)?",
            "option_a": "Lactic acid derived from corn starch fermentation",
            "option_b": "Petroleum crude oil distillates",
            "option_c": "Coal tar extracts",
            "option_d": "Natural gas hydrocarbons",
            "correct_answer": "Lactic acid derived from corn starch fermentation",
            "explanation": "Biomass derivatives like lactic acid from agricultural starch are renewable on human timescales, unlike fossil fuels.",
            "topic": "Solvents & Catalysis",
            "difficulty": "Easy"
        },
        {
            "question": "What is an enantioselective biocatalyst (enzyme) particularly celebrated for in sustainable organic synthesis?",
            "option_a": "High selectivity producing only the desired mirror-image stereoisomer, minimizing side-product waste and protecting groups",
            "option_b": "Generating radioactive waste",
            "option_c": "Requiring boiling temperatures above 300°C",
            "option_d": "Inability to work in water",
            "correct_answer": "High selectivity producing only the desired mirror-image stereoisomer, minimizing side-product waste and protecting groups",
            "explanation": "Enzymes operate under ambient conditions in aqueous media and exhibit extraordinary chemo-, regio-, and enantioselectivity, preventing unwanted isomer waste.",
            "topic": "Solvents & Catalysis",
            "difficulty": "Hard"
        }
    ]

    for q in questions:
        c.execute("""
        INSERT INTO quiz_questions (
            question, option_a, option_b, option_c, option_d,
            correct_answer, explanation, topic, difficulty
        ) VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            q["question"], q["option_a"], q["option_b"], q["option_c"], q["option_d"],
            q["correct_answer"], q["explanation"], q["topic"], q["difficulty"]
        ))
    c.commit()

# --- User operations ---
def create_user(name, username, email, password, is_admin=0):
    c = connect()
    c.execute(
        'INSERT INTO users(name,username,email,password_hash,is_admin) VALUES(?,?,?,?,?)',
        (name, username, email, generate_password_hash(password), is_admin)
    )
    c.commit()
    c.close()

def get_user(username):
    c = connect()
    r = c.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
    c.close()
    return r

def get_user_by_id(uid):
    c = connect()
    r = c.execute('SELECT id, name, username, email, is_admin, created_at FROM users WHERE id=?', (uid,)).fetchone()
    c.close()
    return r

def valid_password(row, password):
    return row and check_password_hash(row['password_hash'], password)

# --- Activity Logging ---
def log_activity(user_id, act_type, details=None):
    c = None
    try:
        c = connect()
        c.execute('INSERT INTO activity(user_id, type, details) VALUES(?,?,?)', (user_id, act_type, details))
        c.commit()
    except Exception:
        pass
    finally:
        if c:
            c.close()

# --- Chat persistence ---
def save_chat_message(user_id, role, content):
    c = connect()
    c.execute('INSERT INTO chat_messages(user_id, role, content) VALUES(?,?,?)', (user_id, role, content))
    c.commit()
    c.close()

def get_chat_history(user_id, limit=60):
    c = connect()
    rows = c.execute('SELECT role, content, created_at FROM chat_messages WHERE user_id=? ORDER BY id ASC LIMIT ?', (user_id, limit)).fetchall()
    c.close()
    return [dict(r) for r in rows]

def clear_chat_history(user_id):
    c = connect()
    c.execute('DELETE FROM chat_messages WHERE user_id=?', (user_id,))
    c.commit()
    c.close()

# --- Quiz Attempts ---
def save_quiz_attempt(user_id, topic, difficulty, score, total_questions, percentage, correct_answers, review_json):
    c = connect()
    cur = c.execute("""
    INSERT INTO quiz_attempts(user_id, topic, difficulty, score, total_questions, percentage, correct_answers, review_json)
    VALUES (?,?,?,?,?,?,?,?)
    """, (user_id, topic, difficulty, score, total_questions, percentage, correct_answers, review_json))
    att_id = cur.lastrowid
    c.commit()
    c.close()
    log_activity(user_id, 'Quiz', f"Scored {score}/{total_questions} ({percentage:.1f}%) on {topic} ({difficulty})")
    return att_id

def get_user_quiz_attempts(user_id, limit=50):
    c = connect()
    rows = c.execute("""
    SELECT id, topic, difficulty, score, total_questions, percentage, correct_answers, created_at
    FROM quiz_attempts WHERE user_id=? ORDER BY id DESC LIMIT ?
    """, (user_id, limit)).fetchall()
    c.close()
    return [dict(r) for r in rows]

# --- Practicals ---
def save_practical_attempt(user_id, experiment_id, experiment_name, observations, result, conclusion, waste_info):
    c = connect()
    try:
        cur = c.execute("""
        INSERT INTO practical_attempts(user_id, experiment_id, experiment_name, observations, result, conclusion, waste_info)
        VALUES (?,?,?,?,?,?,?)
        """, (user_id, experiment_id, experiment_name, observations, result, conclusion, waste_info))
        prac_id = cur.lastrowid
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()
    log_activity(user_id, 'Practical Lab', f"Completed virtual practical for '{experiment_name}'")
    return prac_id

def get_user_practical_attempts(user_id, limit=50):
    c = connect()
    rows = c.execute("""
    SELECT id, experiment_id, experiment_name, observations, result, conclusion, waste_info, status, created_at
    FROM practical_attempts WHERE user_id=? ORDER BY id DESC LIMIT ?
    """, (user_id, limit)).fetchall()
    c.close()
    return [dict(r) for r in rows]

# --- Reports ---
def save_report(user_id, practical_id, experiment_id, title, content_dict):
    c = connect()
    content_str = json.dumps(content_dict)
    try:
        cur = c.execute("""
        INSERT INTO reports(user_id, practical_id, experiment_id, title, content_json)
        VALUES (?,?,?,?,?)
        """, (user_id, practical_id, experiment_id, title, content_str))
        rep_id = cur.lastrowid
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()
    log_activity(user_id, 'Report Generated', f"Generated laboratory record: '{title}'")
    return rep_id

def get_user_reports(user_id, limit=50):
    c = connect()
    rows = c.execute("""
    SELECT id, practical_id, experiment_id, title, created_at
    FROM reports WHERE user_id=? ORDER BY id DESC LIMIT ?
    """, (user_id, limit)).fetchall()
    c.close()
    return [dict(r) for r in rows]

def get_report_by_id(rep_id, user_id=None):
    c = connect()
    if user_id:
        row = c.execute("SELECT * FROM reports WHERE id=? AND user_id=?", (rep_id, user_id)).fetchone()
    else:
        row = c.execute("SELECT * FROM reports WHERE id=?", (rep_id,)).fetchone()
    c.close()
    if not row:
        return None
    d = dict(row)
    d['content'] = json.loads(d['content_json'])
    return d
