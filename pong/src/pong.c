//#include <stdio.h>
//
//int main(int argc, char** argv){
//	printf("sup\n");
//	int x = 3;
//	int y = 4;
//	int z = x + y;
//	printf("%d\n", z);
//	return 0;
//}

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// Function to swap two elements
void swap(int* a, int* b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

// Function to partition the array
int partition(int arr[], int low, int high) {
    int pivot = arr[high]; // Pivot element
    int i = (low - 1);     // Index of smaller element

    for (int j = low; j < high; j++) {
        // If current element is smaller than the pivot
        if (arr[j] < pivot) {
            i++;
            swap(&arr[i], &arr[j]);
        }
    }
    swap(&arr[i + 1], &arr[high]);
    return (i + 1);
}

// Function to perform quicksort
void quicksort(int arr[], int low, int high) {
    if (low < high) {
        // Partitioning index
        int pi = partition(arr, low, high);

        // Recursively sort elements before and after partition
        quicksort(arr, low, pi - 1);
        quicksort(arr, pi + 1, high);
    }
}

// Function to print the array
void printArray(int arr[], int size) {
    for (int i = 0; i < size; i++) {
        printf("%d ", arr[i]);
    }
    printf("\n");
}

int main() {
    int size = 10; // Size of the array
    int arr[10];

    // Seed the random number generator
    srand(time(NULL));

    // Populate the array with random numbers between 0 and 99
    for (int i = 0; i < size; i++) {
        arr[i] = rand() % 100;
    }

    printf("Unsorted array: ");
    printArray(arr, size);

    // Sort the array using quicksort
    quicksort(arr, 0, size - 1);

    printf("Sorted array: ");
    printArray(arr, size);

    return 0;
}
