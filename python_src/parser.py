#!/usr/bin/env python3.9

import sys
import csv


# This parser is specific to a provided input format, and should be changed for different input formats.
# The important when making a parser is that the output is a csv with 3 columns, prefix, length, and next hop
# prefix-a string of the bit representation of the prefix
# length-the length of the prefix, this avoids having to call len repeatedly later on
# next hop-the ip address of the next hop, currently there aren't any restrictions on how it should represented

def main(argv):
    prefix_list = set()
    duplicate_list = set()
    if len(argv) != 2:
        print(argv)
        print("Incorrect Arg count")
        exit(1)
    with open(argv[0]) as input_file, open(argv[1], mode='w', newline='') as output_file:
        output_writer = csv.writer(output_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        line_count = 0
        output_writer.writerow(['Prefix', 'Length', 'NextHop'])
        for line in input_file:
            current_line = line.split()
            if current_line[4] not in prefix_list:
                prefix_list.add(current_line[4])
                output_writer.writerow([current_line[4], current_line[3], current_line[5]])
            else:
                duplicate_list.add(current_line[4])
            line_count += 1
        for prefix in duplicate_list:
            print(f"Duplicate found for {prefix}")
        print(f'Processed {line_count} lines, check output at {argv[1]}')


if __name__ == "__main__":
    main(sys.argv[1:])
