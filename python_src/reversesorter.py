#!/usr/bin/env python3.9

import sys
import pandas


# Just like sorter except that prefix's are ordered by length from shortest to longest, this allows TCAM tree building
# to be done in an easy and simple fashion (thanks again to the makers of the pandas module)

def main(argv):
    if len(argv) != 2:
        print(argv)
        print("Incorrect Arg count")
        exit(1)
    with open(argv[0]) as input_file, open(argv[1], mode='w', newline='') as output_file:
        data = pandas.read_csv(input_file, index_col='Prefix')
        data.sort_values(['Length', 'Prefix'], axis=0, ascending=[True, True], inplace=True)
        data.to_csv(output_file)
        print(f"Sorted {input_file.name} by prefix length and prefix, output in {output_file.name}")


if __name__ == "__main__":
    main(sys.argv[1:])
