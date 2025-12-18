
#include <iostream>
#include <string>
#include <cstdlib> 

int hardware_simulation(int finger_count) {
    
    if (finger_count >= 4) {
        return 1; 
    } 
    else if (finger_count <= 1) {
        return 0; 
    } 
    else {
        return -1; 
    }
}

int main(int argc, char* argv[]) {
   
    if (argc < 2) {
        
        std::cout << -1 << std::endl;
        return 0;
    }

    
    int input_val = std::atoi(argv[1]);

   
    int result = hardware_simulation(input_val);

    
    std::cout << result << std::endl;

    return 0;
}