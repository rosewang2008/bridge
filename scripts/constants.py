RESULTS_DIR = "results"
DECISION_PATHS_DIR = "results/sankey"
LOGODDS_DIR = "results/logodds"
RESPONSES_DIR = "outputs/responses"

MISCONCEPTIONS = [
    {"name": "Student does not seem to understand or guessed the answer.", "value": "guess"},
    {"name": "Student misinterpreted the question.", "value": "misinterpret"},
    {"name": "Student made a careless mistake.", "value": "careless"},
    {"name": "Student has the right idea, but is not quite there.", "value": "right-idea"},
    {"name": "Student's answer is not precise enough or the tutor is being too picky about the form of the student's answer.", "value": "imprecise"},
    {"name": "You are not sure why the student made a mistake but you are going to try to diagnose the student.", "value": "diagnose"},
    {"name": "None of the above, but I have a different description. (please specify in the textbox)", "value": "other"},
]

REVISION_STRATEGIES = [
    {"name": "Explain a concept", "value": "explain_concept"},
    {"name": "Ask a question", "value": "ask_question"},
    {"name": "Provide a hint", "value": "provide_hint"},
    {"name": "Provide a strategy", "value": "provide_strategy"},
    {"name": "Provide a worked example", "value": "provide_example"},
    {"name": "Provide a minor correction", "value": "provide_correction"},
    {"name": "Provide a similar problem", "value": "provide_similar_problem"},
    {"name": "Simplify the question", "value": "simplify_question"},
    {"name": "Affirm the correct answer", "value": "affirm_correct_answer"},
    {"name": "Encourage the student", "value": "encourage_student"},
    {"name": "Other (please specify in textbox)", "value": "other"}
]

INTENTIONS = [
    {"name": "Motivate the student", "value": "motivate_student"},
    {"name": "Get the student to elaborate their answer", "value": "elaborate_answer"},
    {"name": "Correct the student's mistake", "value": "correct_mistake"},
    {"name": "Hint at the student's mistake", "value": "hint_mistake"},
    {"name": "Clarify the student's misunderstanding", "value": "clarify_misunderstanding"},
    {"name": "Help the student understand the lesson topic or solution strategy", "value": "understand_topic"},
    {"name": "Diagnose the student's mistake", "value": "diagnose_mistake"},
    {"name": "Support the student in their thinking or problem-solving", "value": "support_thinking"},
    {"name": "Explain the student's mistake (eg. what is wrong in their answer or why is it incorrect)", "value": "explain_mistake"},
    {"name": "Signal to the student that they have solved or not solved the problem", "value": "signal_goal"},
    {"name": "Other (please specify in textbox)", "value": "other"}
]

# create dictionary for prompt formatting

def format_dict(l):
    d = dict()
    for item in l:
        d[item['value']] = item['name']
    return d

MISCONCEPTIONS_N2V = format_dict(MISCONCEPTIONS)
STRATEGIES_N2V= format_dict(REVISION_STRATEGIES)
INTENTIONS_N2V = format_dict(INTENTIONS)