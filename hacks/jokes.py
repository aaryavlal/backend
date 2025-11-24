import random, json, os, fcntl
from flask import current_app

scenarios_data = []
scenario_list = [
    "What computing method is best for weather forecasting with massive datasets?",
    "What computing method is best for processing a single video file with complex effects?",
    "What computing method is best for handling thousands of independent web requests?",
    "What computing method is best for training a deep learning neural network?",
    "What computing method is best for calculating the next frame in a video game?",
    "What computing method is best for analyzing DNA sequences across multiple genes?",
    "What computing method is best for rendering a Pixar movie with many independent frames?",
    "What computing method is best for real-time financial transaction processing?",
    "What computing method is best for simulating climate change over decades?",
    "What computing method is best for searching through a sorted array?"
]

def get_scenarios_file():
    # Always use Flask app.config['DATA_FOLDER'] for shared data
    data_folder = current_app.config['DATA_FOLDER']
    return os.path.join(data_folder, 'scenarios.json')

def _read_scenarios_file():
    SCENARIOS_FILE = get_scenarios_file()
    if not os.path.exists(SCENARIOS_FILE):
        return []
    with open(SCENARIOS_FILE, 'r') as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        try:
            data = json.load(f)
        except Exception:
            data = []
        fcntl.flock(f, fcntl.LOCK_UN)
    return data

def _write_scenarios_file(data):
    SCENARIOS_FILE = get_scenarios_file()
    with open(SCENARIOS_FILE, 'w') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        json.dump(data, f)
        fcntl.flock(f, fcntl.LOCK_UN)

def initScenarios():
    SCENARIOS_FILE = get_scenarios_file()
    # Only initialize if file does not exist
    if os.path.exists(SCENARIOS_FILE):
        return
    scenarios_data = []
    item_id = 0
    for item in scenario_list:
        scenarios_data.append({
            "id": item_id, 
            "scenario": item, 
            "distributed": 0, 
            "parallel": 0, 
            "sequential": 0
        })
        item_id += 1
    # prime some initial responses
    for i in range(10):
        id = random.choice(scenarios_data)['id']
        scenarios_data[id]['distributed'] += 1
    for i in range(8):
        id = random.choice(scenarios_data)['id']
        scenarios_data[id]['parallel'] += 1
    for i in range(5):
        id = random.choice(scenarios_data)['id']
        scenarios_data[id]['sequential'] += 1
    _write_scenarios_file(scenarios_data)

        
def getScenarios():
    return _read_scenarios_file()

def getScenario(id):
    scenarios = _read_scenarios_file()
    return scenarios[id]

def getRandomScenario():
    scenarios = _read_scenarios_file()
    return random.choice(scenarios)

def topDistributed():
    scenarios = _read_scenarios_file()
    best = 0
    bestID = -1
    for scenario in scenarios:
        if scenario['distributed'] > best:
            best = scenario['distributed']
            bestID = scenario['id']
    return scenarios[bestID] if bestID != -1 else None
    
def topParallel():
    scenarios = _read_scenarios_file()
    best = 0
    bestID = -1
    for scenario in scenarios:
        if scenario['parallel'] > best:
            best = scenario['parallel']
            bestID = scenario['id']
    return scenarios[bestID] if bestID != -1 else None

def topSequential():
    scenarios = _read_scenarios_file()
    best = 0
    bestID = -1
    for scenario in scenarios:
        if scenario['sequential'] > best:
            best = scenario['sequential']
            bestID = scenario['id']
    return scenarios[bestID] if bestID != -1 else None


# Atomic vote update with exclusive lock
def _vote_scenario(id, field):
    SCENARIOS_FILE = get_scenarios_file()
    with open(SCENARIOS_FILE, 'r+') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        scenarios = json.load(f)
        scenarios[id][field] += 1
        # Move file pointer to start before writing updated JSON
        f.seek(0)
        json.dump(scenarios, f)
        # Truncate file to remove any leftover data from previous content
        f.truncate()
        fcntl.flock(f, fcntl.LOCK_UN)
    return scenarios[id][field]

def addDistributed(id):
    return _vote_scenario(id, 'distributed')

def addParallel(id):
    return _vote_scenario(id, 'parallel')

def addSequential(id):
    return _vote_scenario(id, 'sequential')

def printScenario(scenario):
    print(scenario['id'], scenario['scenario'])
    print("  Distributed:", scenario['distributed'])
    print("  Parallel:", scenario['parallel'])
    print("  Sequential:", scenario['sequential'], "\n")

def countScenarios():
    scenarios = _read_scenarios_file()
    return len(scenarios)

if __name__ == "__main__": 
    initScenarios()  # initialize scenarios
    
    # Most voted for each type
    topD = topDistributed()
    if topD:
        print("Most voted Distributed Computing:")
        printScenario(topD)
    
    topP = topParallel()
    if topP:
        print("Most voted Parallel Computing:")
        printScenario(topP)
    
    topS = topSequential()
    if topS:
        print("Most voted Sequential Computing:")
        printScenario(topS)
    
    # Random scenario
    print("Random scenario:")
    printScenario(getRandomScenario())
    
    # Count of Scenarios
    print("Scenarios Count: " + str(countScenarios()))