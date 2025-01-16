X86_64 = g++ -std=c++14 -O2 -o blink_app.out blink_app.cpp `pkg-config --cflags --libs opencv4` -ldlib -framework Accelerate

ARM64 = g++ -std=c++14 -O2 -o blink_app.out blink_app.cpp `pkg-config --cflags --libs opencv4` -I/opt/homebrew/Cellar/dlib/19.24.6/include -L/opt/homebrew/Cellar/dlib/19.24.6/lib -I/opt/homebrew/include -ldlib -framework Accelerate
