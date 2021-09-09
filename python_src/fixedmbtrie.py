#!/usr/bin/env python3.9

import sys
import csv
import json


# NOTE: This implementation assumes the passed in csv has expanded prefixes so prefix insertion is simple

class TrieNode:
    # The width of the key for the Trie entry
    width = 0
    # The tree level the node is located at with the root being 0. Isn't used for much now, but could be useful later
    level = 0
    # A dictionary that simulates a Trie entry, is of the form (key -> [best matching prefix(bmp), next node])
    contents = {}

    # Initialize a node, must be given width of node and depth level
    def __init__(self, width, level):
        self.width = width
        self.level = level
        self.contents = {}
        self.node_builder('', width)

    # Node builder builds a node with empty entries, it does so recursively by adding a 0 and 1 until width is reached
    # at which point the entry is inserted.
    def node_builder(self, key, bits_remaining):
        if bits_remaining == 0:
            self.add_blank(key)
        else:
            self.node_builder(key + '0', bits_remaining - 1)
            self.node_builder(key + '1', bits_remaining - 1)

    # This function handles searching
    def search(self, prefix):
        # First search current node
        search_key = prefix[0:self.width]
        my_guess = self.get_bmp(search_key)
        child = self.get_node(search_key)
        # Then check branch if it exists, if it returns an answer than use that one since it is lpm
        if child is not None and len(prefix) > self.width:
            better_guess = child.search(prefix[self.width:])
            if better_guess is not None:
                my_guess = better_guess
        return my_guess

    # The insertion process is pretty straightforward
    # Check whether or not the prefix ends in this node
    #   If yes, make sure there are no duplicates as that is not allowed, then insert the prefix
    #   If no, check to see if there is an existing child and if not, make one. Then repeat the process there
    #   after removing the necessary bits
    def insert_prefix(self, prefix, bmp, strides):
        if len(prefix) == self.width:
            if self.get_bmp(prefix) is None:
                self.add_bmp(prefix, bmp)
            else:
                print(f"Duplicates exist for {bmp} at lvl {self.level}")
                exit(1)
        else:
            search_key = prefix[0:self.width]
            child = self.get_node(search_key)
            if child is None:
                self.add_node(search_key, strides[0])
                child = self.get_node(search_key)
            child.insert_prefix(prefix[self.width:], bmp, strides[1:])

    # Simple place holder for the initial status of an entry in the node
    def add_blank(self, key):
        self.contents[key] = [None, None]

    # Simple insertion, remember that an entries value is of the form [bmp, next_node]
    def add_bmp(self, key, bmp):
        self.contents[key][0] = bmp

    # Creates a new node when needed
    def add_node(self, key, size):
        self.contents[key][1] = TrieNode(size, self.level + 1)

    def get_width(self):
        return self.width

    # NOTE: Right now assume a fixed pointer and bmp size, but maybe that can change
    # Returns the number of bits used up, split between key, bmps, and pointers
    def get_size(self):
        my_share = [(2 ** self.width)*self.width, (2 ** self.width)*8, (2 ** self.width)*8]
        for entry in self.contents.values():
            if entry[1] is not None:
                my_share[0] += entry[1].get_size()[0]
                my_share[1] += entry[1].get_size()[1]
                my_share[2] += entry[1].get_size()[2]
        return my_share

    # Wrapper used to get an entries bmp and node
    def get_info(self, key):
        return self.contents[key]

    # Wrapper used to get an entries bmp
    def get_bmp(self, key):
        return self.contents[key][0]

    # Wrapper used to get an entries node
    def get_node(self, key):
        return self.contents[key][1]

    def print_contents(self):
        for i in self.contents:
            print(f"{i} points to bmp {self.contents[i][0]} and status of node is {self.contents[i][1] is not None}")

    # The current printing format I have for the trie, not the prettiest especially for large trees, but it works
    def ugly_print(self, indents):
        for i in self.contents:
            child = self.get_node(i)
            print(indents + f"{i} -> bmp: {self.contents[i][0]}")
            if child is not None:
                print(indents + '    ' + '|')
                print(indents + '    ' + 'V')
                self.get_node(i).ugly_print(indents + '    ')


class FixedTrie:
    strides = None
    root = None

    def __init__(self, strides):
        self.strides = strides
        self.root = TrieNode(strides[0], 0)

    def insert_p(self, prefix, bmp):
        self.root.insert_prefix(prefix, bmp, self.strides[1:])

    def search(self, prefix):
        return self.root.search(prefix)

    def get_size(self):
        return self.root.get_size()

    def get_stride(self):
        return self.strides

    def ugly_print(self):
        print("Tree appears as follows(pardon the ugly format)")
        self.root.ugly_print('')


def main(argv):
    strides = []
    stride_checks = []
    if len(argv) < 2:
        print(argv)
        print("Incorrect Arg format, please provide input file and output file and followed by a list of strides")
        exit(1)
    elif len(argv) > 2:
        stride_sum = 0
        stride_checks.append(stride_sum)
        for i in argv[2:]:
            if i.isdigit():
                strides.append(int(i))
                stride_sum += int(i)
                stride_checks.append(stride_sum)
            else:
                print("Optional parameter must be integers")
                exit(1)
        if stride_sum != 32:
            print("Strides must add up to 32")
            exit(1)
    else:
        strides = [8, 8, 8, 8]
        stride_checks = [0, 8, 16, 24, 32]

    with open(argv[0]) as input_file, open(argv[1], mode='w', newline='') as output_file:
        input_reader = csv.reader(input_file, delimiter=',')
        root = FixedTrie(strides)
        line_count = 0
        for line in input_reader:
            line_count += 1
            if line_count == 1:
                continue
            if int(line[2]) not in stride_checks:
                print(f"Invalid prefix size detected for {line[0]}")
                exit(1)
            root.insert_p(line[0], line[1])
        # root.ugly_print()
        size_info = root.get_size()
        print(f"Size breakdown of Trie is as follows:")
        print(f"  -{size_info[0]} bit reserved for keys")
        print(f"  -{size_info[1]} bit reserved for prefixes")
        print(f"  -{size_info[2]} bit reserved for pointers")
        """
        print("Searching for 11001001010101010100011100001111")
        print(f"Result is {root.search('11001001010101010100011100001111')}")
        print("Searching for 01001001010101010100011100001111")
        print(f"Result is {root.search('01001001010101010100011100001111')}")
        print("Searching for 00010001000010100101010100011010")
        print(f"Result is {root.search('00010001000010100101010100011010')}")
        """


if __name__ == "__main__":
    main(sys.argv[1:])