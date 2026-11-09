
filename = "environmental_data.csv"

with open(filename, "r", encoding="utf-8-sig") as f:
    lines = f.readlines()

for i in range(1448, 1459):
    print(f"\nLINE {i+1}:")
    print(repr(lines[i]))
