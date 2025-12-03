from foliage.phenology import get_color_for_tree

def verify_colors():
    symbols = ["ACPL", "ACRU", "PRCE2", "UNKNOWN"]
    dates = [250, 280, 300, 320, 350] # Summer, Start Fall, Peak, Late, Winter

    print(f"{'Symbol':<8} | {'DOY':<4} | {'Color (RGB)'}")
    print("-" * 30)

    for s in symbols:
        for d in dates:
            c = get_color_for_tree(s, d)
            print(f"{s:<8} | {d:<4} | {c}")

if __name__ == "__main__":
    verify_colors()
