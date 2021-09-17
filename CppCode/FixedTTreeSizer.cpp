// FixedTTree.cpp : This file contains the 'main' function. Program execution begins and ends there.


#include <iostream>
#include <map>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <math.h>
using namespace std;

bool is_integer(string s) {
    int size = s.length();
    for (int i = 0; i < size; i++) {
        if (isdigit(s[i]) == false) {
            return false;
        }
    }
    return true;
}

bool is_prefix(string prefix, string value) {
    if (value.find(prefix) == 0) {
        return true;
    }
    else {
        return false;
    }
}

struct bit_node {
    bool covered;
    bit_node* zero_child;
    bit_node* one_child;
    bit_node(short count) {
        covered = false;
        zero_child = NULL;
        one_child = NULL;
        if (count != 0) {
            zero_child = new bit_node(count - 1);
            one_child = new bit_node(count - 1);
        }
    }
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

    void add_entry(string key) {
        my_contents[key] = NULL;
    }

    bool is_present(string key) {
        if (my_contents.find(key) != my_contents.end()) {
            return true;
        }
        else {
            return false;
        }
    }

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

    TCAM_Node* get_node(string key) {
        return my_contents[key];
    }
};

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

// Run program: Ctrl + F5 or Debug > Start Without Debugging menu
// Debug program: F5 or Debug > Start Debugging menu

// Tips for Getting Started: 
//   1. Use the Solution Explorer window to add/manage files
//   2. Use the Team Explorer window to connect to source control
//   3. Use the Output window to see build output and other messages
//   4. Use the Error List window to view errors
//   5. Go to Project > Add New Item to create new code files, or Project > Add Existing Item to add existing code files to the project
//   6. In the future, to open this project again, go to File > Open > Project and select the .sln file
