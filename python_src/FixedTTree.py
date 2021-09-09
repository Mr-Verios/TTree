#!/usr/bin/env python3.9

import sys
import csv

# This builder assumes that prefixes are inserted from shortest length to longest. This allows the program to assume
# that longer entries have priority over shorter ones as well as allowing longer entries to search for bmp's from
# shorter entries

# Assume that None is some default action, and if an explicit drop is desired the associated action must be stated
# (such as "Drop" and not be None)

# Note that this only builds the initial Tree, later updates are not covered properly and therefore the tree must
# be built from scratch if a change is made


class TcamNode:
    # The width of the key for the TCAM entry
    width = 0
    # The tree level the node is located at with the root being 0. Isn't used for much now, but could be useful later
    level = 0
    # A dictionary that simulates a TCAM entry, is of the form (key -> [best matching prefix(bmp), next node])
    contents = {}

    # Initialize a node, must be given width of node and depth level
    def __init__(self, width, level):
        self.width = width
        self.level = level
        self.contents = {}
        self.node_builder('', width)

    # Node builder builds a node with empty entries, it does so recursively by adding a 0 and 1 until width is reached
    # at which point the entry is inserted. Note that all the entries are initially blanks when first building a node,
    # the reasoning for this is to ensure that it is easy to determine whether a default entry of all * is needed. A
    # better explanation can be found at THE SLIDES
    def node_builder(self, key, bits_remaining):
        if bits_remaining == 0:
            self.add_blank(key)
        else:
            self.node_builder(key + '0', bits_remaining - 1)
            self.node_builder(key + '1', bits_remaining - 1)

    # Simple place holder for the initial status of an entry in the node
    def add_blank(self, key):
        self.contents[key] = [None, None]

    # This inserts prefixes into the simulated TCAM tree. The general insertion process is summarized as follows
    # Check if the prefix ends in this node (i.e check whether there are not enough bits to go beyound this node)
    # If yes, do the following:
    #   Remove usurped blank entries (i.e if width=4 and the prefix is 0*** then blanks 0000-0111 would be removed)
    #   Insert new prefix into current node
    # If no, do the following:
    #   Search for bmp in the current node to insert (it is okay if none are found)
    #   Continue on to next node (that may need to be built) and repeat the process
    def insert_prefix(self, remaining_prefix, original_prefix, strides):
        # First case is that the prefix stops at this node
        if len(remaining_prefix) <= self.width:
            # This function removes the unnecessary blanks
            self.usurp(remaining_prefix)
            # If the prefix is less than the width, fills remaining bits with wildcard *'s
            TCAM_entry = remaining_prefix + ('*' * (self.width - len(remaining_prefix)))
            # Need to check whether entry exists or not because it could have been removed by a previous prefix insert.
            # If an entry already exists, then you need to make sure that it is a blank otherwise that means that
            # there are duplicates for a given prefix which is not allowed in ip_routing
            if TCAM_entry not in self.contents:
                self.add_blank(TCAM_entry)
                self.add_bmp(TCAM_entry, original_prefix)
            elif self.get_bmp(TCAM_entry) is None:
                self.add_bmp(remaining_prefix, original_prefix)
            else:
                print(f"Duplicates exist for {original_prefix} at lvl {self.level}")
                exit(1)
        # Second case is that the prefix continues onto next node
        else:
            # First, extract the portion of the prefix that will be used as a key in this node for the next node
            stub = remaining_prefix[0:self.width]
            # Again, must create blank if the blank was previously removed
            if stub not in self.contents:
                self.add_blank(stub)
            # Check whether a next node already exists, if not create one
            child = self.get_node(stub)
            if child is None:
                self.add_node(stub, strides[0])
                child = self.get_node(stub)
            # Before moving on to the next node, attempt to find a bmp in the current node from a shorter prefix
            ancestor = self.lpm_key(stub)
            if ancestor is not None:
                self.add_bmp(stub, self.get_bmp(ancestor))
            child.insert_prefix(remaining_prefix[self.width:], original_prefix, strides[1:])

    # This function removes any blanks that are covered by a prefix(i.e 0*** covers 0000-0111)
    def usurp(self, prefix):
        usurped_list = []
        for key in self.contents:
            if key != prefix and key.startswith(prefix) and self.get_bmp(key) is None and self.get_node(key) is None:
                usurped_list.append(key)
        for key in usurped_list:
            self.contents.pop(key)

    # This function handles searching the tree
    def search(self, prefix):
        print(f"Entered lvl {self.level} with {prefix}")
        search_key = prefix[0:self.width]
        lmp = self.lpm_key(search_key)
        # Will report failures to find lpm, as these should never occur if tree is built properly
        if lmp is None:
            print("How did this happen, invalid search key")
            exit(1)
        # Store the bmp so far
        my_guess = self.get_bmp(lmp)
        # Check child to see if better bmp exists
        child = self.get_node(lmp)
        # Note that the second condition is most likely unnecessary
        if child is not None and len(prefix) > self.width:
            better_guess = child.search(prefix[self.width:])
            if better_guess is not None:
                my_guess = better_guess
        return my_guess

    # This function handles longest prefix match search, if given a key 0110 the search will proceed as follows
    # Search for 0110, if nothing
    # Search for 011*, if nothing
    # Search for 01**, if nothing
    # Search for 0***, if nothing
    # Search for ****, if nothing
    # return None
    def lpm_key(self, key):
        for i in range(self.width + 1):
            search_key = key[0:self.width - i] + '*' * i
            # print(f"Attempting search with {search_key}")
            if search_key in self.contents:
                return search_key
        else:
            return None

    # This function will remove any remaining blanks and compress them into a single **** entry, if no remaining
    # blanks are found then that means that **** is not required since all prefixes in the node are covered by other
    # keys. Note that this function is called after all prefixes have been inserted
    def default_solution(self):
        add_default = False
        removal_list = []
        for key in self.contents:
            # This first statement allows are nodes in the tree to be visited in a depth first fashion
            if self.get_node(key) is not None:
                self.get_node(key).default_solution()
            elif self.get_bmp(key) is None:
                add_default = True
                removal_list.append(key)
        # If a default was needed then the blanks are removed and the default is added
        if add_default:
            for key in removal_list:
                self.contents.pop(key)
            self.add_blank('*' * self.width)

    # This function puts the keys in order by length (longest at first) and then valued. This is done for visual
    # purposed and should not effect any properties of the node, or the behaviour of search. It is called after
    # insertion and default solution are called
    def order(self):
        # This list will hold the keys which will be ordered, note that entries that point to a next node will not
        # go in this list which is fine because entries are moved around by removing them and reinserting them. This
        # means that those entries will move to the top and since they are full width that is desired
        keys_to_order = []
        for key in self.contents:
            # Similar to default solution, this visits every node in a depth first pattern
            if self.get_node(key) is not None:
                self.get_node(key).order()
            else:
                keys_to_order.append(key)
        # This is where the sorting happens with the custom wild_len function seen below
        keys_to_order.sort(key=self.wild_len)
        # Now the entries are reorganized by simply popping and reinserting the keys with their repective values
        for key in keys_to_order:
            temp = self.get_info(key)
            self.contents.pop(key)
            self.contents[key] = temp

    # This is the custom function used to provide a key for the sorting, it simply returns a numeric value that
    # describes the weight of a prefix, longer prefixes have a smaller weight since *'s are treated as larger than
    # 0 and 1, so the prefix 0*** would weigh 6 while 0110 would weigh 2. Note that '0' has a weight of 0
    def wild_len(self, prefix):
        length = 0
        for char in prefix:
            if char == '1':
                length += 1
            elif char == '*':
                length += 2
        return length

    # Simple insertion, remember that an entries value is of the form [bmp, next_node]
    def add_bmp(self, key, bmp):
        self.contents[key][0] = bmp

    # Creates a new node when needed
    def add_node(self, key, size):
        self.contents[key][1] = TcamNode(size, self.level + 1)

    # NOTE: Right now assume a fixed pointer and bmp size, but maybe that can change
    # Returns the number of bits used up, split between key, bmps, and pointers
    def get_size(self):
        my_size = len(self.contents)
        my_share = [my_size * self.width, my_size * 8, my_size * 8]
        # Handles the depth first search of the tree
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

    # The current printing format I have for the trie, not the prettiest especially for large trees, but it works
    def ugly_print(self, indents):
        for i in self.contents:
            child = self.get_node(i)
            print(indents + f"{i} -> bmp: {self.contents[i][0]}")
            if child is not None:
                print(indents + '    ' + '|')
                print(indents + '    ' + 'V')
                self.get_node(i).ugly_print(indents + '    ')


# Honestly don't know if I need this since starting from a node does the same thing, maybe useful later
class TcamTree:
    # Records the fixed strides, if a variable stride is desired than that info will need to be passed during insertion
    strides = None
    # The root node of the tree
    root = None

    # The fixed stride is the only meta info needed for the tree
    def __init__(self, strides):
        self.strides = strides
        self.root = TcamNode(strides[0], 0)

    # The remaining functions are just wrapper functions that simply call the root with the given function
    def insert_prefix(self, prefix):
        self.root.insert_prefix(prefix, prefix, self.strides[1:])

    def search(self, prefix):
        return self.root.search(prefix)

    def get_size(self):
        return self.root.get_size()

    def get_stride(self):
        return self.strides

    def default_solution(self):
        self.root.default_solution()

    def order(self):
        self.root.order()

    def ugly_print(self):
        print("Tree appears as follows(pardon the ugly format)")
        self.root.ugly_print('')


def main(argv):
    # Local variable to hold strides given by command line argument
    strides = []

    # Need to have at least 2 args since there is an input and output file
    if len(argv) < 2:
        print(argv)
        print("Incorrect Arg format, provide input file and output file, followed by an optional list of strides")
        exit(1)
    # If the arg count is greater than 2, it is assumed a list of ints is passed for the fixed strides of the Tree
    elif len(argv) > 2:
        stride_sum = 0
        for i in argv[2:]:
            if i.isdigit():
                strides.append(int(i))
                stride_sum += int(i)
            else:
                print("Optional parameter must be integers")
                exit(1)
        if stride_sum != 32:
            print("Strides must add up to 32")
            exit(1)
    # If no ints are passed, than an 8 8 8 8 strides is assumed
    else:
        strides = [8, 8, 8, 8]

    # Now we go thru the process of inserting all prefixes
    with open(argv[0]) as input_file, open(argv[1], mode='w', newline='') as output_file:
        input_reader = csv.reader(input_file, delimiter=',')
        root = TcamTree(strides)
        line_count = -1
        # Note that this version builds a fixed multi bit trie and converts it to a TCAM Tree where the strides are
        # fixed
        single_width = 0
        for line in input_reader:
            # Skip line one since that holds column names for csv
            line_count += 1
            if line_count == -1:
                continue
            # Insert the prefix
            single_width = line[1]
            root.insert_prefix(line[0])
        # Now that the tree has been built, clean it up with default solution and ordering the entries
        root.default_solution()
        root.order()
        # This is my ugly printer
        # root.ugly_print()
        # Get Size
        size_info = root.get_size()
        print(f"Size breakdown of Trie is as follows:")
        print(f"  -{size_info[0]} bits reserved for keys")
        print(f"  -{size_info[1]} bits reserved for prefixes")
        print(f"  -{size_info[2]} bits reserved for pointers")
        print(f"A regular TCAM would have required the following")
        print(f"  -{single_width * line_count} bits reserved for keys")
        print(f"  -{8*line_count} bits reserved for bmps")


if __name__ == "__main__":
    main(sys.argv[1:])
