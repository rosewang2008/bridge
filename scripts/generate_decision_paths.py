"""
NOTE: RUN THIS SCRIPT FROM THE ROOT DIRECTORY OF THE REPOSITORY.

This script replicates Figure 2 from our paper https://arxiv.org/pdf/2310.10648v2.pdf:
- It generates the decision paths for the human expert, gpt-4, chatgpt, and llama-2-70b models.
- It also reports the path entropies.

The Sankey diagrams will be saved in results/decision_paths/ as .pdf files.
"""

import json
import sys
import os
from collections import defaultdict
import plotly.graph_objects as go
sys.path.append(os.getcwd())
from scripts.constants import *


# Go through json and build Sankey diagram for (e -> z_what) and (z_what -> z_why)
ERROR_OFFSET = 0
ERROR_INDICES = {
    _['value']: ERROR_OFFSET + i for i, _ in enumerate(MISCONCEPTIONS)
}
num_errors = len(ERROR_INDICES) # 7 
NA_ERROR_IDX = ERROR_INDICES['other']

Z_WHAT_OFFSET = max(ERROR_INDICES.values()) + 1
Z_WHAT_INDICES = {
    _['value']: Z_WHAT_OFFSET + i for i, _ in enumerate(REVISION_STRATEGIES)
}
num_z_what = len(Z_WHAT_INDICES) # 11
NA_STRATEGY_IDX = Z_WHAT_INDICES['other']

Z_WHY_OFFSET = max(Z_WHAT_INDICES.values()) + 1
Z_WHY_INDICES = {
    _['value']: Z_WHY_OFFSET + i for i, _ in enumerate(INTENTIONS)
}
num_z_why = len(Z_WHY_INDICES) # 11
NA_INTENTION_IDX = Z_WHY_INDICES['other']

def get_error_idx(error):
    # Range: 0, 6
    return NA_ERROR_IDX if error not in ERROR_INDICES else ERROR_INDICES[error]

def get_strategy_idx(strategy):
    # Range: 7, 17
    return NA_STRATEGY_IDX if strategy not in Z_WHAT_INDICES else Z_WHAT_INDICES[strategy]

def get_intention_idx(intention):
    # Range: 18, 28
    return NA_INTENTION_IDX if intention not in Z_WHY_INDICES else Z_WHY_INDICES[intention]

def build_sankey(data, title):
    result = defaultdict(lambda: defaultdict(lambda: 0))

    # Creating edges for decision paths
    for _ in data:
        e = _['e']
        z_what = _['z_what']
        z_why = _['z_why']

        e_idx = get_error_idx(e) 
        z_what_idx = get_strategy_idx(z_what)
        z_why_idx = get_intention_idx(z_why)

        result[e_idx][z_what_idx] += 1
        result[z_what_idx][z_why_idx] += 1

    source = []
    target = []
    value = []
    for source_key in result.keys():
        for target_key in result[source_key].keys():
            source.append(source_key)
            target.append(target_key)
            value.append(result[source_key][target_key])

    label = [_['value'] for _ in MISCONCEPTIONS + REVISION_STRATEGIES + INTENTIONS]
    # Make aeshetic 'rgba(255,0,255, 0.8)'
    node_colors = ['rgba(255,204,204, 1.0)'] * num_errors + ['rgba(204,221,170, 1.0)'] * num_z_what + ['rgba(187,204,238, 1.0)'] * num_z_why
    # Replace opacity with 0.4
    link_circle_color = ['rgba(221,221,221, 1.0)'] * len(source) + ['rgba(0,255,0, 0.4)'] * len(source) + ['rgba(0,0,255, 0.4)'] * len(source)

    x_positions = [0.5]* len(label)
    for idx in Z_WHAT_INDICES.values():
        x_positions[idx] = 10

    fig = go.Figure(data=[go.Sankey(
      node = dict(
        pad = 15,
        thickness = 20,
        line = dict(color = "black", width = 0.5),
        label = label,
        color = node_colors,
        x = x_positions,
      ),
      link = dict(
        source = source,
        target = target,
        value = value,
        color = link_circle_color
    ))])
  
    # Increase width of figure and put middle text on the left side
    fig.update_layout(title_text=title, font_size=15, width=1000)
    output_path = os.path.join(DECISION_PATHS_DIR, f"{title}.pdf")

    # TODO: Uncomment to show the figure (optional)
    # fig.show()

    # Create into a pdf
    fig.write_image(output_path)
    print(f"Saved to {output_path}")

def calculate_entropy(data): 
    # Entropy over error, strategy, intention
    from collections import defaultdict
    total = len(data)
    # Initialize 0 for all 
    counts = {i: 0 for i in range(num_errors + num_z_what + num_z_why)}
    
    for _ in data:
        e = _['e']
        z_what = _['z_what']
        z_why = _['z_why']

        e_idx = get_error_idx(e)
        z_what_idx = get_strategy_idx(z_what)
        z_why_idx = get_intention_idx(z_why)

        counts[e_idx] += 1
        counts[z_what_idx] += 1
        counts[z_why_idx] += 1
    
    # Calculate entropy
    import math
    entropy = 0
    for count in counts.values():
        if count == 0:
            continue
        prob = count / total
        entropy += prob * math.log(prob)
    return -entropy

if __name__ == "__main__":
    expert_data = json.load(open(os.path.join(RESPONSES_DIR, 'expert_expert.json')))
    gpt4_data = json.load(open(os.path.join(RESPONSES_DIR, 'gpt4_gpt4.json')))
    chatgpt_data = json.load(open(os.path.join(RESPONSES_DIR, 'chatgpt_chatgpt.json')))
    llama_data = json.load(open(os.path.join(RESPONSES_DIR, 'llama-2-70b-chat_llama-2-70b-chat.json')))

    for data, title in [
            (expert_data, "Human Expert"), 
            (gpt4_data, "GPT-4"), 
            (chatgpt_data, "ChatGPT"), 
            (llama_data, "llama-2-70b-chat")
            ]:
        print(f"Entropy for {title}: {calculate_entropy(data)}")
        build_sankey(data, title)