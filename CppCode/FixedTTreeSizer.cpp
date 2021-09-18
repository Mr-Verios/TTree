// FixedTTree.cpp : This file contains the 'main' function. Program execution begins and ends there.


#include <iostream>
#include <map>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <math.h>
using namespace std;

//This booloean function checks whether a string is a non-negative int
bool is_integer(string s) {
    int size = s.length();
    for (int i = 0; i < size; i++) {
        if (isdigit(s[i]) == false) {
            return false;
        }
    }
    return true;
}

//This boolean function checks whether prefix is a prefix of value
bool is_prefix(string prefix, string value) {
    if (value.find(prefix) == 0) {
        return true;
    }
    else {
        return false;
    }
}

//This struct is used to check the coverage of TCAM entries, to later see if a
//default entry is required. It is merely a node that holds a true or false value and
//pointers to 2 children, a zero child and a one child
struct bit_node {
    bool covered;
    bit_node* zero_child;
    bit_node* one_child;
    //Build the entire tree up front, based on the width of the TCAM node, passed in as count
    bit_node(short count) {
        covered = false;
        zero_child = NULL;
        one_child = NULL;
        if (count != 0) {
            zero_child = new bit_node(count - 1);
            one_child = new bit_node(count - 1);
        }
    }
    //This function updates the cover by going down the tree until the string terminates,
    //but it will stop earlier if it encounters a node already covered(i.e no need to
    //cover 001* if 0* has already been encountered)
    void update_cover(string bits) {
        if (covered)
            return;
        if (bits == "") {
            covered = true;
            return;
        }
        switch (bits[0]) {
        case '0':
            zero_child->update_cover(bits.substr(1, bits.size() - 1));
            break;
        case '1':
            one_child->update_cover(bits.substr(1, bits.size() - 1));
            break;
        default:
            cout << "Invalid prefix passed to bit_nodes" << endl;
        }
    }
    //Checks the cover to see if a default entry is required, it's a recursive function that
    //that returns false if it is possible to reach a leaf node that says false.
    bool check_cover() {
        bool child_status = zero_child && one_child;
        if (covered) {
            return true;
        }
        else if (child_status) {
            return zero_child->check_cover() && one_child->check_cover();
        }
        else {
            return false;
        }
    }
};

//A struct that represents a node in the TCAM tree. It contains info on the width, level, a bit node
//tree for coverage, and a map from prefixes to pointers. Values are not included because they are not
//needed to determine size
struct TCAM_Node {
    short my_width;
    short my_level;
    bit_node* cover_tree;
    map<string, TCAM_Node*> my_contents;

    TCAM_Node(short width, short level) {
        my_width = width;
        my_level = level;
        my_contents.empty();
        cover_tree = new bit_node(width);
    }

    /*
        This inserts prefixes into the simulated TCAM tree. The general insertion process is summarized as follows
        Check if the prefix ends in this node (i.e check whether there are not enough bits to go beyound this node)
        If yes, do the following:
          Insert new prefix into current node and check for duplicates(the provided input shouldn't have any)
        If no, do the following:
          Check to see if a prefix exists, if not make one
          Check to see if next node exists, if not make one
          Repeat the process at the next node, with the shortened prefix
    */
    void insert_prefix(string remaining_prefix, string original_prefix, short* strides) {
        if (remaining_prefix.size() <= my_width) {
            cover_tree->update_cover(remaining_prefix);
            string TCAM_key = remaining_prefix + string(my_width - remaining_prefix.size(), 'X');
            if (!is_present(TCAM_key)) {
                add_entry(TCAM_key);
            }
            else {
                cout << "Duplicates exist for " << original_prefix << " at lvl " << my_level << endl;
                exit(1);
            }
        }
        else {
            string stub = remaining_prefix.substr(0, my_width);
            cover_tree->update_cover(stub);
            if (!is_present(stub)) {
                add_entry(stub);
            }
            TCAM_Node* child = get_node(stub);
            if (child == NULL) {
                add_node(stub, strides[0]);
                child = get_node(stub);
            }
            string new_remaining_prefix = remaining_prefix.substr(my_width, remaining_prefix.size() - my_width);
            child->insert_prefix(new_remaining_prefix, original_prefix, strides + 1);
        }
    }

    //Currently unused, this function returns the lpm for a bit string
    string lpm_key(string key) {
        int range = my_width + 1;
        for (int i = 0; i < range; i++) {
            string search_key = key.substr(0, my_width - 1) + string(i, 'X');
            if (is_present(search_key)) {
                return search_key;
            }
        }
        return "";
    }

    //This function recursively goes thru the TCAM tree, checking whether the bit node tree covers all
    //addresses and if not, it adds the default entry. Also records how many bits have been used on default entries
    long long* default_solution() {
        long long* my_share = new long long[4];
        my_share[0] = 0;
        my_share[1] = 0;
        my_share[2] = 0;
        my_share[3] = 0;
        for (auto [key, value] : my_contents) {
            if (get_node(key) != NULL) {
                long long* child_share = get_node(key)->default_solution();
                my_share[0] += child_share[0];
                my_share[1] += child_share[1];
                my_share[2] += child_share[2];
                my_share[3] += child_share[3];
            }
        }
        if (!cover_tree->check_cover()) {
            add_entry(string(my_width, 'X'));
            my_share[0] += my_width;
            my_share[1] += 32;
            my_share[2] += 32;
            my_share[3] += 1;
        }
        return my_share;
    }

    //Recursively visits every node on the tree and sums up the number of bits used and entries present
    long long* get_size() {
        long long my_size = my_contents.size();
        long long* my_share = new long long[4];
        my_share[0] = my_size * my_width;
        my_share[1] = my_size * 32;
        my_share[2] = my_size * 32;
        my_share[3] = my_size;
        for (auto const& [key, value] : my_contents) {
            if (has_child(key)) {
                long long* child_share = get_node(key)->get_size();
                my_share[0] += child_share[0];
                my_share[1] += child_share[1];
                my_share[2] += child_share[2];
                my_share[3] += child_share[3];
            }
        }
        return my_share;
    }

    //Recursively visits every node on the tree and sums up how big a normal multi bit trie would have
    //been. This is simple because if a node exists in the TCAM tree then it would have existed in the
    //trie except the node would be completely expanded
    long long* get_trie_size() {
        long long my_size = pow(2, my_width);
        long long* my_share = new long long[4];
        my_share[0] = my_size * my_width;
        my_share[1] = my_size * 32;
        my_share[2] = my_size * 32;
        my_share[3] = my_size;
        for (auto const& [key, value] : my_contents) {
            if (has_child(key)) {
                long long* child_share = get_node(key)->get_trie_size();
                my_share[0] += child_share[0];
                my_share[1] += child_share[1];
                my_share[2] += child_share[2];
                my_share[3] += child_share[3];
            }
        }
        return my_share;
    }

    
    //Boolean function that checks whether a tcam entry exists for a given prefix
    bool is_present(string key) {
        if (my_contents.find(key) != my_contents.end()) {
            return true;
        }
        else {
            return false;
        }
    }

    
    //BELOW ARE SIMPLE WRAPPER FUNCTIONS

    bool has_child(string key) {
        if (my_contents[key] == NULL) {
            return false;
        }
        else {
            return true;
        }
    }

    void add_node(string key, short size) {
        my_contents[key] = new TCAM_Node(size, my_level + 1);
    }

    void add_entry(string key) {
        my_contents[key] = NULL;
    }

    TCAM_Node* get_node(string key) {
        return my_contents[key];
    }
};

//This struct pretty serves as a wrapper for the node structure, most likely did not need to exist
struct TCAM_Tree {
    short* my_strides = NULL;
    TCAM_Node* root = NULL;
    TCAM_Tree(short* strides) {
        my_strides = strides;
        root = new TCAM_Node(strides[0], 0);
    }

    void insert_prefix(string prefix) {
        root->insert_prefix(prefix, prefix, my_strides + 1);
    }

    long long* get_size() {
        return root->get_size();
    }

    long long* get_trie_size() {
        return root->get_trie_size();
    }

    short* get_strides() {
        return my_strides;
    }

    long long* default_solution() {
        return root->default_solution();
    }
};

int main(int argc, char** argv) {
    if (argc != 2) {
        cout << "Incorrect Arg format, provide only an input file" << endl;
        exit(1);
    }
    short strides[32];
    short sum = 0;
    cout << "Provide a list of positive ints (one at a time) that add up to 32 for the strides" << endl;
    for (int i = 0; i < 32; i++) {
        string x;
        cin >> x;
        if (is_integer(x) && stoi(x) > 0) {
            strides[i] = stoi(x);
            sum += stoi(x);
            if (sum > 32) {
                cout << "Stride sum cannot exceed 32, it was " << sum << endl;
                exit(1);
            }
            else if (sum == 32) {
                break;
            }
        }
        else {
            cout << "Strides must be positive integers" << endl;
            exit(1);
        }
    }
    TCAM_Tree tree = TCAM_Tree(strides);
    fstream input_file;
    input_file.open(argv[1], ios::in);
    if (input_file.fail()) {
        cout << "Failed to open file" << endl;
        exit(1);
    }
    int count = -1;
    vector<string> row;
    string line, word, temp;

    while (getline(input_file, line)) {
        count++;
        row.clear();
        stringstream buffer(line);
        while (getline(buffer, word, ',')) {
            row.push_back(word);
        }
        if (count == 0) {
            continue;
        }
        tree.insert_prefix(row[0]);
    }
    long long* wild_info = tree.default_solution();
    long long* size_info = tree.get_size();
    long long* trie_info = tree.get_trie_size();
    cout << "Size breakdown of Tree is as follows:" << endl;
    cout << "  -" << size_info[0] << " bits reserved for keys" << endl;
    cout << "  -" << size_info[1] << " bits reserved for bmps" << endl;
    cout << "  -" << size_info[2] << " bits reserved for pointers" << endl;
    cout << "  -" << size_info[3] << " entries in total" << endl;
    cout << "Of these bits, the following are used for default entries" << endl;
    cout << "  -" << wild_info[0] << " bits for keys" << endl;
    cout << "  -" << wild_info[1] << " bits for bmps" << endl;
    cout << "  -" << wild_info[2] << " bits for pointers" << endl;
    cout << "  -" << wild_info[3] << " default entries" << endl << endl;
    cout << "Size breakdown of a Trie would have been" << endl;
    cout << "  -" << trie_info[0] << " bits reserved for keys" << endl;
    cout << "  -" << trie_info[1] << " bits reserved for bmps" << endl;
    cout << "  -" << trie_info[2] << " bits reserved for pointers" << endl;
    cout << "  -" << trie_info[3] << " entries in total" << endl << endl;
    cout << "Size breakdown of a single TCAM would have been" << endl;
    cout << "  -" << 32*count << " bits reserved for keys" << endl;
    cout << "  -" << 32*count << " bits reserved for bmps" << endl;
    return 0;
}

