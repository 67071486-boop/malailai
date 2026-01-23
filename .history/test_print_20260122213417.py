import sys
import time

def main():
    print("[test_print] stdout hello", flush=True)
    print("[test_print] stderr hello", file=sys.stderr, flush=True)
    for i in range(3):
        print(f"[test_print] tick {i}", flush=True)
        time.sleep(1)

if __name__ == "__main__":
    main()
