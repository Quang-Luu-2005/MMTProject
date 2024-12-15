import os

input_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input.txt")

def main():
    print("Please enter file(s) that you want to download:")
    print("Press Enter twice to stop")

    lines = []

    while True:
        line = input()
        if line == "":
            break
        
        lines.append(line)

    with open(input_file, "a") as f:  
        f.write('\n'.join(lines) + '\n')

    os.system('cls' if os.name == 'nt' else 'clear')
        

if __name__ == "__main__":
    main()