#ifndef LINKED_LIST_HEADER
#define LINKED_LIST_HEADER

//typedef struct linked_list_node {
//    int foo;
//    float bar;
//} linked_list_node;

struct linked_list_node{
    int a;
    float b;
};

// so that we don't need to repeated type "struct linked_list_node",
// define a new type "linked_list_node" to be the same as "struct linked_list_node".
typedef struct linked_list_node linked_list_node;

#endif
