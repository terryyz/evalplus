import json
import os
from rich.progress import track

from eval_plus.utils import get_human_eval_plus, get_human_eval_plus_inputs

LLM_HOME_PATH = "/JawTitan/EvalPlus/humaneval"
COV_INFO_PATH = "min_cov_dir"
model_paths = os.listdir(LLM_HOME_PATH)

problems = get_human_eval_plus()
new_inputs = get_human_eval_plus_inputs()


# One dict is super huge, so split them into separate JSON files
def get_cover_info():
    if os.path.exists(COV_INFO_PATH): return
    os.makedirs(COV_INFO_PATH)
    cover_info = {f"HumanEval_{i}": {} for i in range(164)}
    for model_path in model_paths:
        if not model_path[-1].isdigit(): continue
        eval_json_path = os.path.join(LLM_HOME_PATH, model_path, "eval_results.json")
        if not os.path.exists(eval_json_path): continue
        with open(eval_json_path, "r") as f:
            res = json.load(f)["eval"]
            for task_id, v in res.items():
                for i_code, (status, res_list) in enumerate(v["base"]):
                    if status == "success": continue
                    code_id = hash(v["files"][i_code])
                    for i_test, res in enumerate(res_list):
                        test_id = f"base_{i_test}"
                        if res == False:
                            cover_info[task_id].setdefault(test_id, []).append(code_id)
                for i_code, (status, res_list) in enumerate(v["plus"]):
                    if status == "success": continue
                    code_id = hash(v["files"][i_code])
                    for i_test, res in enumerate(res_list):
                        test_id = f"plus_{i_test}"
                        if res == False:
                            cover_info[task_id].setdefault(test_id, []).append(code_id)
    for task_id, tests in cover_info.items():
        with open(os.path.join(COV_INFO_PATH, f"{task_id}.json"), "w") as f:
            json.dump(tests, f)

if __name__ == "__main__":
    get_cover_info()
    for i in track(range(164)):
        task_id = f"HumanEval_{i}"
        with open(os.path.join(COV_INFO_PATH, f"{task_id}.json"), "r") as f:
            tests = json.load(f)
        q, U = [], set()
        for test_name, test_cover in tests.items():
            cover_set = set(test_cover)
            q.append((test_name, cover_set))
            U = U.union(cover_set)
        # Greedy 
        min_cover = []
        while len(U) > 0:
            max_uncover_set, max_test_name = {}, ""
            for test_name, cover_set in q:
                if len(cover_set) > len(max_uncover_set):
                    max_uncover_set = cover_set
                    max_test_name = test_name
            min_cover.append(max_test_name)
            U = U - max_uncover_set
            qq = []
            for test_name, cover_set in q:
                new_cover_set = U.intersection(cover_set)
                if len(new_cover_set) != 0:
                    qq.append((test_name, new_cover_set))
            q = qq

        d = {"task_id": task_id, "inputs": []}
        for test in min_cover:
            tmp = test.split("_")
            t, n = tmp[0], int(tmp[1])
            if t == "base":
                d["inputs"].append(problems[i]["base_input"][n])
            else:
                d["inputs"].append(new_inputs[task_id][n])
        with open("HumanEvalPlusInputsMin.jsonl", "a") as f:
            f.write(json.dumps(d) + "\n")
