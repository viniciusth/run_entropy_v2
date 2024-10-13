from src.data.gen_buckets import PROCESSORS, TASKS_PER_BUCKET
from src.data.gen_results import scheduler_names


def run_analysis(file: str):
    data = None
    with open(file, "r") as f:
        data = eval(f.read())
    assert data is not None, "Data is None"

    print(data["missed"])
    for k, v in data["missed"].items():
        print(f"{k} missed {v} out of {TASKS_PER_BUCKET * 10 * len(PROCESSORS)} tests")
    total_cnt = 0
    scheds = scheduler_names()

    for p in PROCESSORS:
        print("-"*50)
        print(p, "processors")
        for i in range(10):
            print(f"{i*10}% -> {(i+1)*10}%")
            cnts = [0 for _ in range(len(scheds))]
            for s in range(len(scheds)):
                cnt = len(data["data"][scheds[s]][p][i])
                cnts[s] = cnt
            cnt = cnts[0]
            total_cnt += cnt
            for c in cnts:
                assert c == cnt, "Lengths don't match"

            if cnt == 0:
                print("No data")
                continue

            output = f"Count {cnt}"
            for s in scheds:
                entropy = 0
                entropymax = 0
                entropymin = int(1e9)
                for test in data["data"][s][p][i]:
                    entropy += test
                    entropymax = max(entropymax, test)
                    entropymin = min(entropymin, test)
                output += f" | {s} {entropy/cnt} ({entropymin}, {entropymax})"

            print(f"{i*10}% -> {(i+1)*10}%")
            print(output)
    print("-"*50)
    print(total_cnt, "total tests")
