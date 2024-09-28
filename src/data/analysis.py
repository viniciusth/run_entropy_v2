

from src.data.gen_buckets import PROCESSORS, TASKS_PER_BUCKET


def run_analysis(file: str):
    data = None
    with open(file, "r") as f:
        data = eval(f.read())
    assert data is not None, "Data is None"

    print("Missed", data["missed"], "out of", TASKS_PER_BUCKET * 10 * len(PROCESSORS))

    for p in PROCESSORS:
        print("-"*50)
        print(p, "processors")
        for i in range(10):
            cnt = len(data["data"]["fg_run"][p][i])
            assert cnt == len(data["data"]["p_reorder"][p][i]), "Lengths don't match"
            p_reorder = 0
            fg_run = 0
            for test in data["data"]["fg_run"][p][i]:
                fg_run += test
            for test in data["data"]["p_reorder"][p][i]:
                p_reorder += test
            print(f"{i*10}% -> {(i+1)*10}%")
            print(f"Count {cnt} | FG-Run {fg_run/cnt} | P-Reorder {p_reorder/cnt}")
