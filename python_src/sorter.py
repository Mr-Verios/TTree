#!/usr/bin/env python3.9

import sys
import pandas


# Sorts the prefixes based on length and tiebreakers are settled by the value of the ip address from 0000 -> 1111
# This sorting makes expansion easy, since the earlier prefixes can be given priority over later prefixes
# NOTE: Sorting is a trivial task given the pandas module(thank you to whoever made that module)

def main(argv):
    if len(argv) != 2:
        print(argv)
        print("Incorrect Arg count, requires an input file and an output file")
        exit(1)
    with open(argv[0]) as input_file, open(argv[1], mode='w', newline='') as output_file:
        data = pandas.read_csv(input_file, index_col='Prefix')
        data.sort_values(['Length', 'Prefix'], axis=0, ascending=[False, True], inplace=True)
        data.to_csv(output_file)
        print(f"Sorted {input_file.name} by prefix length and prefix, output in {output_file.name}")


if __name__ == "__main__":
    main(sys.argv[1:])
