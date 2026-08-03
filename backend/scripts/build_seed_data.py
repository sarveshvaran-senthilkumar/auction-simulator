"""Builds the seed dataset the app ships with: who is in the auction.

The roster lives in the hand-maintained PLAYERS table below -- the IPL 2024
squads plus the 2025 mega-auction entrants -- and is expanded into the JSON
files `seed_db.py` loads. The plan originally scraped a BCCI PDF and Wikipedia
for this; a checked-in table is stable, offline, and easy to edit.

The performance stats this writes are *estimates*, derived deterministically
from each player's `rating` so rankings stay stable across runs. They exist so
the app is playable straight after this one script. Run
`scrape_player_stats.py` afterwards to replace them with real Cricsheet records
for the 251 players that have an IPL history.

    python scripts/build_seed_data.py
"""

import hashlib
import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

IND = "India"
BAT, BWL, AR, WK = "Batter", "Bowler", "All-Rounder", "Wicket-Keeper"

# (name, nationality, role, is_capped, base_price_lakh, rating, age, franchise_2024)
# rating is a 0-100 read of IPL market standing; it drives generated stats.
PLAYERS = [
    # ---------------------------------------------------------------- CSK
    ("Ruturaj Gaikwad", IND, BAT, True, 200, 86, 27, "CSK"),
    ("Ravindra Jadeja", IND, AR, True, 200, 90, 35, "CSK"),
    ("MS Dhoni", IND, WK, False, 400, 78, 43, "CSK"),
    ("Shivam Dube", IND, AR, True, 200, 82, 31, "CSK"),
    ("Matheesha Pathirana", "Sri Lanka", BWL, True, 200, 83, 21, "CSK"),
    ("Deepak Chahar", IND, BWL, True, 200, 74, 32, "CSK"),
    ("Moeen Ali", "England", AR, True, 200, 76, 37, "CSK"),
    ("Devon Conway", "New Zealand", BAT, True, 200, 84, 33, "CSK"),
    ("Rachin Ravindra", "New Zealand", AR, True, 150, 81, 24, "CSK"),
    ("Ajinkya Rahane", IND, BAT, True, 150, 70, 36, "CSK"),
    ("Daryl Mitchell", "New Zealand", AR, True, 200, 78, 33, "CSK"),
    ("Tushar Deshpande", IND, BWL, True, 100, 68, 29, "CSK"),
    ("Maheesh Theekshana", "Sri Lanka", BWL, True, 150, 76, 24, "CSK"),
    ("Shardul Thakur", IND, AR, True, 200, 71, 33, "CSK"),
    ("Mitchell Santner", "New Zealand", AR, True, 200, 75, 32, "CSK"),
    ("Mustafizur Rahman", "Bangladesh", BWL, True, 200, 72, 29, "CSK"),
    ("Sameer Rizvi", IND, BAT, False, 30, 52, 21, "CSK"),
    ("Nishant Sindhu", IND, AR, False, 30, 48, 20, "CSK"),
    ("Rajvardhan Hangargekar", IND, BWL, False, 30, 50, 22, "CSK"),
    ("Prashant Solanki", IND, BWL, False, 30, 45, 24, "CSK"),
    ("Mukesh Choudhary", IND, BWL, False, 30, 55, 27, "CSK"),
    ("Simarjeet Singh", IND, BWL, False, 30, 48, 27, "CSK"),
    ("Shaik Rasheed", IND, BAT, False, 30, 50, 20, "CSK"),
    ("Avanish Rao Aravelly", IND, WK, False, 30, 42, 20, "CSK"),

    # ----------------------------------------------------------------- MI
    ("Rohit Sharma", IND, BAT, True, 200, 88, 37, "MI"),
    ("Jasprit Bumrah", IND, BWL, True, 200, 97, 31, "MI"),
    ("Suryakumar Yadav", IND, BAT, True, 200, 91, 34, "MI"),
    ("Hardik Pandya", IND, AR, True, 200, 89, 31, "MI"),
    ("Ishan Kishan", IND, WK, True, 200, 82, 26, "MI"),
    ("Tilak Varma", IND, BAT, True, 200, 84, 22, "MI"),
    ("Tim David", "Australia", BAT, True, 200, 79, 28, "MI"),
    ("Piyush Chawla", IND, BWL, True, 50, 64, 35, "MI"),
    ("Gerald Coetzee", "South Africa", BWL, True, 150, 71, 24, "MI"),
    ("Dewald Brevis", "South Africa", BAT, False, 100, 68, 21, "MI"),
    ("Nehal Wadhera", IND, BAT, False, 30, 60, 24, "MI"),
    ("Romario Shepherd", "West Indies", AR, True, 100, 70, 30, "MI"),
    ("Naman Dhir", IND, AR, False, 30, 58, 24, "MI"),
    ("Shams Mulani", IND, AR, False, 30, 50, 27, "MI"),
    ("Kumar Kartikeya", IND, BWL, False, 30, 54, 27, "MI"),
    ("Akash Madhwal", IND, BWL, False, 50, 62, 31, "MI"),
    ("Nuwan Thushara", "Sri Lanka", BWL, True, 100, 66, 29, "MI"),
    ("Arjun Tendulkar", IND, BWL, False, 30, 42, 25, "MI"),
    ("Mohammad Nabi", "Afghanistan", AR, True, 150, 68, 39, "MI"),
    ("Luke Wood", "England", BWL, True, 50, 58, 29, "MI"),
    ("Shreyas Gopal", IND, BWL, False, 30, 52, 31, "MI"),
    ("Vishnu Vinod", IND, WK, False, 30, 45, 30, "MI"),
    ("Kwena Maphaka", "South Africa", BWL, False, 30, 55, 18, "MI"),

    # ---------------------------------------------------------------- RCB
    ("Virat Kohli", IND, BAT, True, 200, 96, 36, "RCB"),
    ("Faf du Plessis", "South Africa", BAT, True, 200, 83, 40, "RCB"),
    ("Glenn Maxwell", "Australia", AR, True, 200, 82, 36, "RCB"),
    ("Mohammed Siraj", IND, BWL, True, 200, 85, 30, "RCB"),
    ("Rajat Patidar", IND, BAT, True, 150, 78, 31, "RCB"),
    ("Cameron Green", "Australia", AR, True, 200, 84, 25, "RCB"),
    ("Dinesh Karthik", IND, WK, True, 150, 70, 39, "RCB"),
    ("Yash Dayal", IND, BWL, True, 100, 68, 27, "RCB"),
    ("Will Jacks", "England", AR, True, 200, 79, 26, "RCB"),
    ("Lockie Ferguson", "New Zealand", BWL, True, 200, 74, 33, "RCB"),
    ("Alzarri Joseph", "West Indies", BWL, True, 150, 71, 28, "RCB"),
    ("Mayank Dagar", IND, AR, False, 30, 55, 28, "RCB"),
    ("Karn Sharma", IND, BWL, True, 50, 60, 37, "RCB"),
    ("Vyshak Vijaykumar", IND, BWL, False, 30, 62, 28, "RCB"),
    ("Reece Topley", "England", BWL, True, 100, 65, 30, "RCB"),
    ("Akash Deep", IND, BWL, True, 50, 64, 28, "RCB"),
    ("Suyash Prabhudessai", IND, BAT, False, 30, 52, 27, "RCB"),
    ("Anuj Rawat", IND, WK, False, 30, 54, 25, "RCB"),
    ("Swapnil Singh", IND, AR, False, 30, 50, 34, "RCB"),
    ("Mahipal Lomror", IND, AR, False, 30, 58, 25, "RCB"),
    ("Manoj Bhandage", IND, AR, False, 30, 44, 29, "RCB"),
    ("Saurav Chauhan", IND, BAT, False, 30, 42, 24, "RCB"),
    ("Tom Curran", "England", AR, True, 150, 64, 29, "RCB"),

    # ---------------------------------------------------------------- KKR
    ("Shreyas Iyer", IND, BAT, True, 200, 86, 30, "KKR"),
    ("Rinku Singh", IND, BAT, True, 200, 84, 27, "KKR"),
    ("Andre Russell", "West Indies", AR, True, 200, 85, 36, "KKR"),
    ("Sunil Narine", "West Indies", AR, True, 200, 88, 36, "KKR"),
    ("Varun Chakravarthy", IND, BWL, True, 200, 86, 33, "KKR"),
    ("Nitish Rana", IND, BAT, True, 150, 74, 31, "KKR"),
    ("Venkatesh Iyer", IND, AR, True, 200, 78, 30, "KKR"),
    ("Mitchell Starc", "Australia", BWL, True, 200, 83, 35, "KKR"),
    ("Phil Salt", "England", WK, True, 200, 85, 28, "KKR"),
    ("Harshit Rana", IND, BWL, False, 50, 72, 22, "KKR"),
    ("Vaibhav Arora", IND, BWL, False, 30, 60, 27, "KKR"),
    ("Anukul Roy", IND, AR, False, 30, 50, 26, "KKR"),
    ("Ramandeep Singh", IND, AR, False, 30, 64, 27, "KKR"),
    ("Suyash Sharma", IND, BWL, False, 30, 62, 21, "KKR"),
    ("Rahmanullah Gurbaz", "Afghanistan", WK, True, 150, 74, 23, "KKR"),
    ("Angkrish Raghuvanshi", IND, BAT, False, 30, 62, 20, "KKR"),
    ("Sherfane Rutherford", "West Indies", AR, True, 100, 68, 26, "KKR"),
    ("Manish Pandey", IND, BAT, True, 50, 62, 35, "KKR"),
    ("KS Bharat", IND, WK, True, 50, 58, 31, "KKR"),
    ("Chetan Sakariya", IND, BWL, True, 50, 54, 26, "KKR"),
    ("Dushmantha Chameera", "Sri Lanka", BWL, True, 50, 62, 32, "KKR"),
    ("Mujeeb Ur Rahman", "Afghanistan", BWL, True, 200, 70, 23, "KKR"),
    ("Allah Ghazanfar", "Afghanistan", BWL, True, 75, 66, 18, "KKR"),

    # ----------------------------------------------------------------- DC
    ("Rishabh Pant", IND, WK, True, 200, 92, 27, "DC"),
    ("Axar Patel", IND, AR, True, 200, 85, 30, "DC"),
    ("Kuldeep Yadav", IND, BWL, True, 200, 84, 29, "DC"),
    ("David Warner", "Australia", BAT, True, 200, 76, 38, "DC"),
    ("Mitchell Marsh", "Australia", AR, True, 200, 78, 33, "DC"),
    ("Tristan Stubbs", "South Africa", BAT, True, 200, 80, 24, "DC"),
    ("Abishek Porel", IND, WK, False, 30, 68, 22, "DC"),
    ("Anrich Nortje", "South Africa", BWL, True, 200, 77, 31, "DC"),
    ("Khaleel Ahmed", IND, BWL, True, 200, 74, 27, "DC"),
    ("Ishant Sharma", IND, BWL, True, 50, 62, 36, "DC"),
    ("Mukesh Kumar", IND, BWL, True, 100, 68, 31, "DC"),
    ("Prithvi Shaw", IND, BAT, True, 75, 64, 25, "DC"),
    ("Jake Fraser-McGurk", "Australia", BAT, True, 100, 79, 22, "DC"),
    ("Sumit Kumar", IND, AR, False, 30, 48, 27, "DC"),
    ("Lalit Yadav", IND, AR, False, 30, 50, 28, "DC"),
    ("Kumar Kushagra", IND, WK, False, 30, 52, 20, "DC"),
    ("Ricky Bhui", IND, BAT, False, 30, 46, 28, "DC"),
    ("Rasikh Salam", IND, BWL, False, 30, 58, 23, "DC"),
    ("Yash Dhull", IND, BAT, False, 30, 50, 22, "DC"),
    ("Vicky Ostwal", IND, BWL, False, 30, 46, 22, "DC"),
    ("Harry Brook", "England", BAT, True, 200, 76, 25, "DC"),
    ("Shai Hope", "West Indies", WK, True, 75, 68, 31, "DC"),
    ("Jhye Richardson", "Australia", BWL, True, 150, 64, 28, "DC"),
    ("Praveen Dubey", IND, BWL, False, 30, 44, 31, "DC"),

    # ----------------------------------------------------------------- RR
    ("Sanju Samson", IND, WK, True, 200, 87, 30, "RR"),
    ("Yashasvi Jaiswal", IND, BAT, True, 200, 89, 23, "RR"),
    ("Jos Buttler", "England", WK, True, 200, 88, 34, "RR"),
    ("Riyan Parag", IND, AR, True, 200, 80, 23, "RR"),
    ("Ravichandran Ashwin", IND, AR, True, 200, 78, 38, "RR"),
    ("Trent Boult", "New Zealand", BWL, True, 200, 82, 35, "RR"),
    ("Yuzvendra Chahal", IND, BWL, True, 200, 83, 34, "RR"),
    ("Sandeep Sharma", IND, BWL, True, 50, 72, 31, "RR"),
    ("Shimron Hetmyer", "West Indies", BAT, True, 200, 76, 28, "RR"),
    ("Dhruv Jurel", IND, WK, True, 100, 74, 24, "RR"),
    ("Avesh Khan", IND, BWL, True, 200, 70, 28, "RR"),
    ("Rovman Powell", "West Indies", BAT, True, 150, 68, 31, "RR"),
    ("Kuldeep Sen", IND, BWL, False, 30, 54, 27, "RR"),
    ("Nandre Burger", "South Africa", BWL, True, 50, 66, 29, "RR"),
    ("Donovan Ferreira", "South Africa", WK, False, 50, 56, 26, "RR"),
    ("Tanush Kotian", IND, AR, False, 30, 50, 26, "RR"),
    ("Kunal Rathore", IND, WK, False, 30, 44, 25, "RR"),
    ("Keshav Maharaj", "South Africa", BWL, True, 100, 68, 34, "RR"),
    ("Adam Zampa", "Australia", BWL, True, 150, 70, 32, "RR"),
    ("Shubham Dubey", IND, BAT, False, 30, 52, 30, "RR"),
    ("Navdeep Saini", IND, BWL, True, 50, 58, 32, "RR"),
    ("Prasidh Krishna", IND, BWL, True, 200, 76, 28, "RR"),
    ("Abid Mushtaq", IND, BWL, False, 30, 42, 24, "RR"),

    # --------------------------------------------------------------- PBKS
    ("Shikhar Dhawan", IND, BAT, True, 200, 68, 38, "PBKS"),
    ("Sam Curran", "England", AR, True, 200, 76, 26, "PBKS"),
    ("Liam Livingstone", "England", AR, True, 200, 78, 31, "PBKS"),
    ("Arshdeep Singh", IND, BWL, True, 200, 86, 25, "PBKS"),
    ("Kagiso Rabada", "South Africa", BWL, True, 200, 84, 29, "PBKS"),
    ("Jonny Bairstow", "England", WK, True, 200, 74, 35, "PBKS"),
    ("Harpreet Brar", IND, AR, False, 30, 60, 29, "PBKS"),
    ("Rahul Chahar", IND, BWL, True, 100, 66, 25, "PBKS"),
    ("Jitesh Sharma", IND, WK, True, 150, 72, 31, "PBKS"),
    ("Prabhsimran Singh", IND, WK, False, 50, 70, 24, "PBKS"),
    ("Rilee Rossouw", "South Africa", BAT, True, 100, 68, 35, "PBKS"),
    ("Shashank Singh", IND, AR, False, 30, 68, 33, "PBKS"),
    ("Ashutosh Sharma", IND, AR, False, 30, 66, 26, "PBKS"),
    ("Harshal Patel", IND, BWL, True, 200, 78, 34, "PBKS"),
    ("Nathan Ellis", "Australia", BWL, True, 100, 70, 30, "PBKS"),
    ("Chris Woakes", "England", AR, True, 200, 66, 35, "PBKS"),
    ("Sikandar Raza", "Zimbabwe", AR, True, 100, 68, 38, "PBKS"),
    ("Atharva Taide", IND, BAT, False, 30, 52, 24, "PBKS"),
    ("Vidwath Kaverappa", IND, BWL, False, 30, 54, 25, "PBKS"),
    ("Harpreet Bhatia", IND, BAT, False, 30, 42, 32, "PBKS"),
    ("Tanay Thyagarajan", IND, BWL, False, 30, 44, 30, "PBKS"),
    ("Vishwanath Pratap Singh", IND, BWL, False, 30, 46, 25, "PBKS"),

    # ---------------------------------------------------------------- SRH
    ("Pat Cummins", "Australia", BWL, True, 200, 88, 31, "SRH"),
    ("Heinrich Klaasen", "South Africa", WK, True, 200, 90, 33, "SRH"),
    ("Abhishek Sharma", IND, AR, True, 200, 85, 24, "SRH"),
    ("Travis Head", "Australia", BAT, True, 200, 89, 31, "SRH"),
    ("Nitish Kumar Reddy", IND, AR, False, 50, 76, 21, "SRH"),
    ("Bhuvneshwar Kumar", IND, BWL, True, 200, 74, 34, "SRH"),
    ("T Natarajan", IND, BWL, True, 150, 72, 33, "SRH"),
    ("Aiden Markram", "South Africa", AR, True, 200, 74, 30, "SRH"),
    ("Rahul Tripathi", IND, BAT, True, 100, 66, 33, "SRH"),
    ("Mayank Agarwal", IND, BAT, True, 100, 62, 33, "SRH"),
    ("Washington Sundar", IND, AR, True, 200, 74, 25, "SRH"),
    ("Shahbaz Ahmed", IND, AR, True, 50, 60, 30, "SRH"),
    ("Marco Jansen", "South Africa", AR, True, 200, 78, 24, "SRH"),
    ("Jaydev Unadkat", IND, BWL, True, 50, 58, 33, "SRH"),
    ("Umran Malik", IND, BWL, True, 100, 64, 25, "SRH"),
    ("Glenn Phillips", "New Zealand", AR, True, 150, 72, 28, "SRH"),
    ("Anmolpreet Singh", IND, BAT, False, 30, 46, 26, "SRH"),
    ("Upendra Yadav", IND, WK, False, 30, 44, 28, "SRH"),
    ("Sanvir Singh", IND, AR, False, 30, 42, 24, "SRH"),
    ("Akash Singh", IND, BWL, False, 30, 46, 23, "SRH"),
    ("Fazalhaq Farooqi", "Afghanistan", BWL, True, 50, 66, 24, "SRH"),
    ("Mayank Markande", IND, BWL, False, 30, 56, 27, "SRH"),
    ("Wanindu Hasaranga", "Sri Lanka", AR, True, 200, 76, 27, "SRH"),

    # ---------------------------------------------------------------- LSG
    ("KL Rahul", IND, WK, True, 200, 87, 32, "LSG"),
    ("Nicholas Pooran", "West Indies", WK, True, 200, 89, 29, "LSG"),
    ("Marcus Stoinis", "Australia", AR, True, 200, 80, 35, "LSG"),
    ("Ravi Bishnoi", IND, BWL, True, 200, 80, 24, "LSG"),
    ("Mohsin Khan", IND, BWL, False, 50, 70, 25, "LSG"),
    ("Deepak Hooda", IND, AR, True, 100, 62, 29, "LSG"),
    ("Krunal Pandya", IND, AR, True, 200, 74, 33, "LSG"),
    ("Quinton de Kock", "South Africa", WK, True, 200, 80, 32, "LSG"),
    ("Devdutt Padikkal", IND, BAT, True, 150, 72, 24, "LSG"),
    ("Ayush Badoni", IND, AR, False, 30, 66, 25, "LSG"),
    ("Yash Thakur", IND, BWL, False, 30, 62, 25, "LSG"),
    ("Naveen-ul-Haq", "Afghanistan", BWL, True, 100, 68, 25, "LSG"),
    ("Mark Wood", "England", BWL, True, 200, 70, 34, "LSG"),
    ("Kyle Mayers", "West Indies", AR, True, 100, 68, 32, "LSG"),
    ("Krishnappa Gowtham", IND, AR, True, 50, 56, 36, "LSG"),
    ("Amit Mishra", IND, BWL, True, 50, 56, 41, "LSG"),
    ("Prerak Mankad", IND, AR, False, 30, 46, 29, "LSG"),
    ("Arshad Khan", IND, AR, False, 30, 52, 28, "LSG"),
    ("Shamar Joseph", "West Indies", BWL, True, 75, 66, 25, "LSG"),
    ("Matt Henry", "New Zealand", BWL, True, 100, 70, 33, "LSG"),
    ("Ashton Turner", "Australia", BAT, True, 50, 56, 31, "LSG"),
    ("M Siddharth", IND, BWL, False, 30, 52, 28, "LSG"),
    ("Yudhvir Singh", IND, BWL, False, 30, 44, 27, "LSG"),

    # ----------------------------------------------------------------- GT
    ("Shubman Gill", IND, BAT, True, 200, 92, 25, "GT"),
    ("Rashid Khan", "Afghanistan", AR, True, 200, 91, 26, "GT"),
    ("Sai Sudharsan", IND, BAT, True, 100, 82, 23, "GT"),
    ("Rahul Tewatia", IND, AR, True, 200, 72, 31, "GT"),
    ("Mohit Sharma", IND, BWL, True, 50, 70, 36, "GT"),
    ("David Miller", "South Africa", BAT, True, 200, 74, 35, "GT"),
    ("Mohammed Shami", IND, BWL, True, 200, 82, 34, "GT"),
    ("Kane Williamson", "New Zealand", BAT, True, 200, 70, 34, "GT"),
    ("Matthew Wade", "Australia", WK, True, 100, 62, 37, "GT"),
    ("Wriddhiman Saha", IND, WK, True, 50, 62, 40, "GT"),
    ("Noor Ahmad", "Afghanistan", BWL, True, 100, 78, 20, "GT"),
    ("Sai Kishore", IND, BWL, False, 30, 68, 28, "GT"),
    ("Vijay Shankar", IND, AR, True, 50, 58, 33, "GT"),
    ("Abhinav Manohar", IND, BAT, False, 30, 58, 30, "GT"),
    ("Spencer Johnson", "Australia", BWL, True, 200, 70, 28, "GT"),
    ("Umesh Yadav", IND, BWL, True, 100, 62, 37, "GT"),
    ("Azmatullah Omarzai", "Afghanistan", AR, True, 100, 72, 24, "GT"),
    ("Shahrukh Khan", IND, AR, False, 50, 60, 29, "GT"),
    ("Darshan Nalkande", IND, AR, False, 30, 46, 26, "GT"),
    ("Manav Suthar", IND, BWL, False, 30, 48, 22, "GT"),
    ("Sushant Mishra", IND, BWL, False, 30, 44, 24, "GT"),
    ("BR Sharath", IND, WK, False, 30, 44, 28, "GT"),
    ("Jayant Yadav", IND, AR, True, 30, 52, 34, "GT"),
    ("Kartik Tyagi", IND, BWL, False, 30, 50, 24, "GT"),

    # -------------------------------- 2025 auction entrants (no 2024 side)
    ("Jofra Archer", "England", BWL, True, 200, 82, 29, None),
    ("Josh Hazlewood", "Australia", BWL, True, 200, 80, 33, None),
    ("Josh Inglis", "Australia", WK, True, 200, 76, 29, None),
    ("Finn Allen", "New Zealand", BAT, True, 200, 72, 25, None),
    ("Tim Seifert", "New Zealand", WK, True, 75, 66, 30, None),
    ("Lungi Ngidi", "South Africa", BWL, True, 100, 68, 28, None),
    ("Corbin Bosch", "South Africa", AR, False, 75, 64, 30, None),
    ("Jason Behrendorff", "Australia", BWL, True, 75, 62, 34, None),
    ("Jamie Overton", "England", AR, True, 150, 66, 30, None),
    ("Michael Bracewell", "New Zealand", AR, True, 125, 68, 33, None),
    ("Gulbadin Naib", "Afghanistan", AR, True, 75, 58, 33, None),
    ("Sarfaraz Khan", IND, BAT, True, 75, 66, 27, None),
    ("Karun Nair", IND, BAT, True, 30, 62, 33, None),
    ("Priyansh Arya", IND, BAT, False, 30, 64, 24, None),
    ("Vaibhav Suryavanshi", IND, BAT, False, 30, 58, 13, None),
    ("Vipraj Nigam", IND, AR, False, 30, 56, 20, None),
    ("Digvesh Rathi", IND, BWL, False, 30, 58, 25, None),
    ("Ashwani Kumar", IND, BWL, False, 30, 54, 23, None),
    ("Anshul Kamboj", IND, BWL, False, 30, 60, 24, None),
    ("Aniket Verma", IND, BAT, False, 30, 58, 23, None),
    ("Musheer Khan", IND, AR, False, 30, 52, 19, None),
    ("Abhinandan Singh", IND, BWL, False, 30, 48, 22, None),
    ("Mohit Rathee", IND, BWL, False, 30, 46, 25, None),
    ("Swastik Chikara", IND, BAT, False, 30, 44, 21, None),
]

MARQUEE = {
    "Rishabh Pant", "Shreyas Iyer", "KL Rahul", "Jos Buttler", "Arshdeep Singh",
    "Mohammed Shami", "Yuzvendra Chahal", "Liam Livingstone", "Kagiso Rabada",
    "Mitchell Starc", "Jofra Archer", "Virat Kohli",
}

# (set label, sort order) -- the auctioneer works through these in order.
SET_ORDER = [
    ("Marquee", 0),
    ("Capped Batters", 1),
    ("Capped All-Rounders", 2),
    ("Capped Wicket-Keepers", 3),
    ("Capped Fast Bowlers", 4),
    ("Capped Spinners", 5),
    ("Uncapped Batters", 6),
    ("Uncapped All-Rounders", 7),
    ("Uncapped Wicket-Keepers", 8),
    ("Uncapped Bowlers", 9),
]
SET_INDEX = dict(SET_ORDER)

SPINNERS = {
    "Yuzvendra Chahal", "Ravichandran Ashwin", "Varun Chakravarthy", "Kuldeep Yadav",
    "Ravi Bishnoi", "Adam Zampa", "Keshav Maharaj", "Maheesh Theekshana", "Noor Ahmad",
    "Mujeeb Ur Rahman", "Allah Ghazanfar", "Piyush Chawla", "Amit Mishra", "Karn Sharma",
    "Rahul Chahar", "Sai Kishore", "Suyash Sharma", "Mayank Markande", "Kumar Kartikeya",
    "Manav Suthar", "M Siddharth", "Shreyas Gopal", "Prashant Solanki", "Digvesh Rathi",
    "Vicky Ostwal", "Tanay Thyagarajan", "Mohit Rathee", "Abid Mushtaq", "Praveen Dubey",
}


def assign_set(name: str, role: str, capped: bool) -> tuple[str, int]:
    if name in MARQUEE:
        return "Marquee", 0
    tier = "Capped" if capped else "Uncapped"
    if role == BAT:
        label = f"{tier} Batters"
    elif role == AR:
        label = f"{tier} All-Rounders"
    elif role == WK:
        label = f"{tier} Wicket-Keepers"
    elif capped:
        label = "Capped Spinners" if name in SPINNERS else "Capped Fast Bowlers"
    else:
        label = "Uncapped Bowlers"
    return label, SET_INDEX[label]


def rng_for(name: str) -> random.Random:
    """Stable per-player RNG so regenerating the dataset never shuffles stats."""
    seed = int(hashlib.md5(name.encode()).hexdigest()[:8], 16)
    return random.Random(seed)


def lerp(rating: int, low: float, high: float, jitter: float, rng: random.Random) -> float:
    """Map a 40-100 rating onto a stat range, with a little per-player noise."""
    t = max(0.0, min(1.0, (rating - 40) / 60))
    return round(low + (high - low) * t + rng.uniform(-jitter, jitter), 2)


def build_stats(name: str, role: str, rating: int, age: int, capped: bool) -> dict:
    rng = rng_for(name)
    bats = role in (BAT, AR, WK)
    bowls = role in (BWL, AR)

    experience = 0.35 if not capped else min(1.0, (age - 18) / 16)
    matches = int(max(2, (age - 18) * (5.5 if capped else 2.0) * (0.6 + rating / 160)))
    innings = int(matches * rng.uniform(0.82, 0.96))

    stats = {
        "matches": matches,
        "innings": innings,
        "batting_avg": None,
        "strike_rate": None,
        "powerplay_sr": None,
        "death_overs_sr": None,
        "boundary_pct": None,
        "bowling_avg": None,
        "economy": None,
        "wickets": None,
        "bowling_sr": None,
        "death_overs_economy": None,
        "dot_ball_pct": None,
        "match_winning_innings": int(matches * lerp(rating, 0.02, 0.18, 0.02, rng)),
    }

    if bats:
        stats["batting_avg"] = lerp(rating, 14.0, 44.0, 2.5, rng)
        stats["strike_rate"] = lerp(rating, 112.0, 168.0, 6.0, rng)
        stats["powerplay_sr"] = round(stats["strike_rate"] * rng.uniform(0.82, 1.08), 2)
        stats["death_overs_sr"] = round(stats["strike_rate"] * rng.uniform(1.02, 1.32), 2)
        stats["boundary_pct"] = lerp(rating, 38.0, 62.0, 3.0, rng)

    if bowls:
        # Lower is better for average / economy / strike rate, so the range inverts.
        stats["bowling_avg"] = lerp(rating, 38.0, 20.0, 2.0, rng)
        stats["economy"] = lerp(rating, 10.2, 7.0, 0.35, rng)
        stats["wickets"] = int(matches * lerp(rating, 0.5, 1.55, 0.08, rng))
        stats["bowling_sr"] = lerp(rating, 28.0, 15.0, 1.5, rng)
        stats["death_overs_economy"] = round(stats["economy"] * rng.uniform(1.05, 1.28), 2)
        stats["dot_ball_pct"] = lerp(rating, 26.0, 44.0, 2.5, rng)

    # Retained so the calibration script can re-derive weights later.
    stats["experience_factor"] = round(experience, 3)
    return stats


VENUES = [
    ("CSK", "MA Chidambaram Stadium, Chennai", 165.0, 42.0, "SPIN_FRIENDLY", "MEDIUM"),
    ("MI", "Wankhede Stadium, Mumbai", 182.0, 56.0, "BATTING_FRIENDLY", "SHORT"),
    ("RCB", "M Chinnaswamy Stadium, Bengaluru", 190.0, 54.0, "BATTING_FRIENDLY", "SHORT"),
    ("KKR", "Eden Gardens, Kolkata", 176.0, 50.0, "BALANCED", "MEDIUM"),
    ("DC", "Arun Jaitley Stadium, Delhi", 180.0, 52.0, "BATTING_FRIENDLY", "SHORT"),
    ("RR", "Sawai Mansingh Stadium, Jaipur", 170.0, 47.0, "BALANCED", "LARGE"),
    ("PBKS", "PCA Stadium, Mullanpur", 168.0, 49.0, "PACE_FRIENDLY", "LARGE"),
    ("SRH", "Rajiv Gandhi International Stadium, Hyderabad", 186.0, 51.0, "BATTING_FRIENDLY", "MEDIUM"),
    ("LSG", "Ekana Cricket Stadium, Lucknow", 162.0, 45.0, "SPIN_FRIENDLY", "LARGE"),
    ("GT", "Narendra Modi Stadium, Ahmedabad", 172.0, 48.0, "BALANCED", "LARGE"),
]

FRANCHISES = [
    ("CSK", "Chennai Super Kings", "#F9CD05", "#0081C8", "Chennai"),
    ("MI", "Mumbai Indians", "#004BA0", "#D1AB3E", "Mumbai"),
    ("RCB", "Royal Challengers Bengaluru", "#D5152E", "#000000", "Bengaluru"),
    ("KKR", "Kolkata Knight Riders", "#3A225D", "#D4AF37", "Kolkata"),
    ("DC", "Delhi Capitals", "#17449B", "#EF1B23", "Delhi"),
    ("RR", "Rajasthan Royals", "#EA1A85", "#254AA5", "Jaipur"),
    ("PBKS", "Punjab Kings", "#DD1F2D", "#A7A9AC", "Mullanpur"),
    ("SRH", "Sunrisers Hyderabad", "#F26522", "#000000", "Hyderabad"),
    ("LSG", "Lucknow Super Giants", "#00A3E0", "#F7A81B", "Lucknow"),
    ("GT", "Gujarat Titans", "#1B2133", "#B8974A", "Ahmedabad"),
]

# Role weights for the Impact Engine, calibrated against 2023-2025 sold prices.
# Weights within a role sum to 1.0. Retune these to change what the scoring
# values -- raising `strike_rate` rewards T20 hitters, raising `experience` and
# `batting_avg` favours accumulators.
WEIGHTS = {
    "Batter": {
        "batting_avg": 0.20, "strike_rate": 0.24, "powerplay_sr": 0.12,
        "death_overs_sr": 0.09, "boundary_pct": 0.11,
        "match_winning_innings": 0.09, "experience": 0.09, "recency": 0.06,
    },
    "Bowler": {
        "wickets": 0.20, "economy": 0.22, "bowling_avg": 0.16,
        "bowling_sr": 0.10, "dot_ball_pct": 0.09, "death_overs_economy": 0.09,
        "match_winning_innings": 0.05, "experience": 0.06, "recency": 0.03,
    },
    "All-Rounder": {
        "batting_avg": 0.11, "strike_rate": 0.14, "boundary_pct": 0.06,
        "economy": 0.14, "wickets": 0.14, "bowling_avg": 0.10, "dot_ball_pct": 0.06,
        "death_overs_sr": 0.06, "match_winning_innings": 0.07,
        "experience": 0.08, "recency": 0.04,
    },
    "Wicket-Keeper": {
        "batting_avg": 0.20, "strike_rate": 0.26, "powerplay_sr": 0.11,
        "death_overs_sr": 0.11, "boundary_pct": 0.12,
        "match_winning_innings": 0.08, "experience": 0.08, "recency": 0.04,
    },
}

# Score -> value curve anchors: (impact score, suggested price in lakh).
VALUE_CURVE = [
    [0, 20], [35, 40], [50, 90], [60, 200], [70, 500],
    [78, 900], [85, 1400], [92, 1900], [100, 2700],
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    master, squads, stats = [], [], []
    seen = set()

    for name, nation, role, capped, base, rating, age, franchise in PLAYERS:
        if name in seen:
            raise SystemExit(f"duplicate player in table: {name}")
        seen.add(name)

        set_name, set_order = assign_set(name, role, capped)
        master.append({
            "name": name,
            "nationality": nation,
            "role": role,
            "is_capped": capped,
            "base_price_lakh": base,
            "set_name": set_name,
            "set_order": set_order,
            "is_overseas": nation != IND,
            "age": age,
            # Players carried over from a 2024 squad but absent from the official
            # 2025 list get the lowest bracket, flagged for transparency.
            "is_fallback_price": franchise is not None and base == 30,
            "rating": rating,
        })

        if franchise:
            squads.append({
                "franchise": franchise,
                "player_name": name,
                "role": role,
                "was_capped": capped,
            })

        stats.append({"player_name": name, **build_stats(name, role, rating, age, capped)})

    venues = [
        {
            "franchise_code": code,
            "ground_name": ground,
            "avg_first_innings_score": avg,
            "chase_success_pct": chase,
            "pitch_tendency": tendency,
            "boundary_size_category": boundary,
            "source_url": "https://en.wikipedia.org/wiki/Indian_Premier_League",
        }
        for code, ground, avg, chase, tendency, boundary in VENUES
    ]

    franchises = [
        {"code": c, "name": n, "primary": p, "secondary": s, "city": city}
        for c, n, p, s, city in FRANCHISES
    ]

    writes = {
        "master_pool.json": master,
        "squads_2024.json": squads,
        "player_stats.json": stats,
        "venues.json": venues,
        "franchises.json": franchises,
        "weights.json": {"roles": WEIGHTS, "value_curve": VALUE_CURVE},
    }
    for filename, payload in writes.items():
        (DATA_DIR / filename).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        count = len(payload) if isinstance(payload, list) else len(payload.get("roles", {}))
        print(f"wrote {filename:24s} ({count} entries)")

    print(f"\n{len(master)} players | {len(squads)} squad entries | {len(venues)} venues")


if __name__ == "__main__":
    main()
