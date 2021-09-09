#!/usr/bin/env python3.9

import sys
import csv

# This is necessary to build a fixed stride multi-bit trie. The prefixes are expanded to the appropriate stride
# and the original prefix is recorded alongside the expanded prefix.

# The set built in of python makes checking for duplicates easy during expansion
prefix_list = set()
# Used as checkpoints to stop expansion
stride_checks = []
# Needed this to be a global to be used across functions
output_writer = csv.writer


# Wrapper function to add prefix to set
def add_to_set(prefix):
    global prefix_list
    prefix_list.add(prefix)


# Returns true if prefix already exists (given order of prefixes, this implies a longer prefix already claimed it)
def is_subsumed(prefix):
    global prefix_list
    if prefix in prefix_list:
        return True
    return False


# First step of expansion is figuring when expansion should stop
def find_checkpoint(length):
    global stride_checks
    for i in stride_checks:
        if i >= length:
            return i
    print("Length should not exceed 32")
    exit(1)


# Does the actual expansion by recursively adding 0 and 1 until checkpoint is reached, at which point the new expanded
# prefix is recorded. Next hop info is simply copied over and serves no functional purpose
def expand(expanded_prefix, original_prefix, length, checkpoint, next_hop):
    global output_writer
    if length == checkpoint:
        if not is_subsumed(expanded_prefix):
            add_to_set(expanded_prefix)
            output_writer.writerow([expanded_prefix, original_prefix, length, next_hop])
    else:
        expand(expanded_prefix + '0', original_prefix, length + 1, checkpoint, next_hop)
        expand(expanded_prefix + '1', original_prefix, length + 1, checkpoint, next_hop)


def main(argv):
    global stride_checks
    global prefix_list
    global output_writer
    # Checks to make sure that at least 2 args are passed, since you need 2 files
    if len(argv) < 2:
        print(argv)
        print("Incorrect Arg format, please provide input file and output file and optional followed by a list of "
              "strides")
        exit(1)
    # The following ensures that any optional parameters passed were a list of ints summing to 32, for the strides
    elif len(argv) > 2:
        stride_sum = 0
        stride_checks.append(stride_sum)
        for i in argv[2:]:
            if i.isdigit():
                stride_sum += int(i)
                stride_checks.append(stride_sum)
            else:
                print("Optional parameter must be integers")
                exit(1)
        if stride_sum != 32:
            print("Strides must add up to 32")
            exit(1)
    # Otherwise, a stride of 8 8 8 8 is assumed
    else:
        stride_checks = [0, 8, 16, 24, 32]

    # All that's left is to go thru the process line by line
    with open(argv[0]) as input_file, open(argv[1], mode='w', newline='') as output_file:
        input_reader = csv.reader(input_file, delimiter=',')
        output_writer = csv.writer(output_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        line_count = -1
        output_writer.writerow(['Prefix', 'Original', 'Length', 'NextHop'])
        for line in input_reader:
            line_count += 1
            if line_count == 0:
                continue
            expand(line[0], line[0], int(line[1]), find_checkpoint(int(line[1])), line[2])
        print(f'{line_count} lines were expanded to {len(prefix_list)}, check output at {argv[1]}')


if __name__ == "__main__":
    main(sys.argv[1:])
