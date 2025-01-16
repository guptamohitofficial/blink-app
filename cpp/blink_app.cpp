
#include <iostream>
#include <opencv2/opencv.hpp>
#include <dlib/opencv.h>
#include <dlib/image_processing.h>
#include <dlib/image_processing/frontal_face_detector.h>
#include <nlohmann/json.hpp>
#include <fstream>
#include <chrono>
#include <vector>
#include <cmath>
#include <thread>
#include <future>
#include <cstdio>
#include <memory>
#include <stdexcept>
#include <string>

// Constants
const int FRAME_WIDTH = 1280;
const int FRAME_HEIGHT = 720;
const int FPS = 30;

// Alias for JSON
using json = nlohmann::json;

// Utility function to execute a system command and get the output
std::string exec(const char* cmd) {
    std::array<char, 128> buffer;
    std::string result;
#ifdef _WIN32
    std::unique_ptr<FILE, decltype(&_pclose)> pipe(_popen(cmd, "r"), _pclose);
#else
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd, "r"), pclose);
#endif
    if (!pipe) {
        throw std::runtime_error("popen() failed!");
    }
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
        result += buffer.data();
    }
    return result;
}

class FaceAnalyzer {
public:
    FaceAnalyzer()
        : detector(dlib::get_frontal_face_detector()),
          predictor(),
          EYE_AR_THRESH(0.25),
          BLINK_COOLDOWN(10),
          blink_counter(0),
          blink_cooldown_counter(0),
          is_eye_closed(false),
          start_time(std::chrono::steady_clock::now())
    {
        // Load the shape predictor
        try {
            dlib::deserialize("shape_predictor_68_face_landmarks.dat") >> predictor;
        }
        catch (const dlib::serialization_error& e) {
            std::cerr << "Error loading shape predictor: " << e.what() << std::endl;
            exit(EXIT_FAILURE);
        }
    }

    cv::Mat process_frame(const cv::Mat& frame) {
        if (frame.empty()) {
            return frame;
        }

        cv::Mat gray;
        cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);

        dlib::cv_image<uchar> cimg(gray);
        std::vector<dlib::rectangle> faces = detector(cimg);

        for (const auto& face : faces) {
            dlib::full_object_detection landmarks = predictor(cimg, face);
            std::vector<cv::Point> points;
            for (unsigned int i = 0; i < landmarks.num_parts(); ++i) {
                points.emplace_back(landmarks.part(i).x(), landmarks.part(i).y());
                cv::circle(frame, points.back(), 1, cv::Scalar(0, 255, 0), -1);
            }

            // Extract eye coordinates
            std::vector<cv::Point> left_eye(points.begin() + 42, points.begin() + 48);
            std::vector<cv::Point> right_eye(points.begin() + 36, points.begin() + 42);

            // Calculate EAR
            double left_ear = calculate_eye_aspect_ratio(left_eye);
            double right_ear = calculate_eye_aspect_ratio(right_eye);
            double ear = (left_ear + right_ear) / 2.0;

            // Blink detection with cooldown
            if (ear < EYE_AR_THRESH && !is_eye_closed && blink_cooldown_counter == 0) {
                is_eye_closed = true;
                blink_counter++;
                blink_cooldown_counter = BLINK_COOLDOWN;
            }
            else if (ear >= EYE_AR_THRESH) {
                is_eye_closed = false;
            }

            if (blink_cooldown_counter > 0) {
                blink_cooldown_counter--;
            }

            // Draw eye contours
            const cv::Scalar eye_color(0, 255, 0);
            std::vector<std::vector<cv::Point>> eyes = { left_eye, right_eye };
            for (const auto& eye : eyes) {
                std::vector<cv::Point> eye_copy = eye;
                cv::polylines(frame, eye_copy, true, eye_color, 1);
            }

            // Draw face rectangle
            cv::rectangle(frame, cv::Point(face.left(), face.top()), cv::Point(face.right(), face.bottom()), cv::Scalar(0, 255, 0), 2);
        }

        return frame;
    }

    double calculate_eye_aspect_ratio(const std::vector<cv::Point>& eye) {
        if (eye.size() != 6) return 0.0;
        double A = euclidean_distance(eye[1], eye[5]);
        double B = euclidean_distance(eye[2], eye[4]);
        double C = euclidean_distance(eye[0], eye[3]);
        double ear = (A + B) / (2.0 * C);
        return ear;
    }

    int get_and_reset_blink_count() {
        int blinks = blink_counter;
        blink_counter = 0;
        return blinks;
    }

public:
    dlib::frontal_face_detector detector;
    dlib::shape_predictor predictor;

    const double EYE_AR_THRESH;
    const int BLINK_COOLDOWN;

    int blink_counter;
    int blink_cooldown_counter;
    bool is_eye_closed;

    std::chrono::steady_clock::time_point start_time;

    double euclidean_distance(const cv::Point& p1, const cv::Point& p2) {
        return std::sqrt(std::pow((p1.x - p2.x), 2) + std::pow((p1.y - p2.y), 2));
    }
};

void get_thread_usage_via_cli(int pid) {
    try {
        // Example command for Unix-based systems
        std::string cmd = "ps -M " + std::to_string(pid);
        std::string result = exec(cmd.c_str());
        std::cout << result;
    }
    catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
    }
}

void capture_and_save_frame(const std::string& file_path, const cv::Mat& frame) {
    if (cv::imwrite(file_path, frame)) {
        std::cout << "Frame saved to " << file_path << std::endl;
    }
    else {
        std::cerr << "Failed to save frame to " << file_path << std::endl;
    }
}

cv::Mat process_saved_frame(const std::string& file_path) {
    cv::Mat img = cv::imread(file_path);
    if (img.empty()) {
        std::cerr << "Failed to read image from " << file_path << std::endl;
    }
    return img;
}

class FrameHandler {
public:
    FrameHandler(int frame_rate = 30, int camera_index = 0)
        : frame_rate(frame_rate),
          camera_index(camera_index),
          running(false),
          total_blinks(0),
          runtime(0.0)
    {
        capture.open(camera_index);
        if (!capture.isOpened()) {
            std::cerr << "Camera not accessible" << std::endl;
            // Handle as needed, possibly throw an exception
        }
        capture.set(cv::CAP_PROP_FRAME_WIDTH, FRAME_WIDTH);
        capture.set(cv::CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT);
        capture.set(cv::CAP_PROP_FPS, FPS);
    }

    ~FrameHandler() {
        if (capture.isOpened()) {
            capture.release();
        }
        cv::destroyAllWindows();
    }

    void append_list_to_json_file(const std::string& file_path, const std::vector<double>& new_list) {
        json j;
        if (std::ifstream(file_path)) {
            try {
                std::ifstream in(file_path);
                in >> j;
                if (!j.is_array()) {
                    j = json::array();
                }
            }
            catch (const json::parse_error& e) {
                j = json::array();
            }
        }
        for (const auto& item : new_list) {
            j.push_back(item);
        }
        std::ofstream out(file_path);
        out << j.dump(4);
    }

    void monitor_blinks() {
        running = true;
        FaceAnalyzer analyzer;
        // analyzer = FaceAnalyzer();
        auto start_time = std::chrono::steady_clock::now();
        auto last_epoch = std::chrono::steady_clock::now();
        auto last_epoch_per_fps = std::chrono::steady_clock::now();
        int frame_count = 0;
        int frame_count_per_sec = 0;

        try {
            while (running) {
                cv::Mat frame;
                bool ret = capture.read(frame);
                if (!ret || frame.empty()) {
                    std::cerr << "Failed to capture frame. Exiting..." << std::endl;
                    break;
                }

                frame_count++;
                cv::Mat processed_frame = analyzer.process_frame(frame);
                runtime = std::chrono::duration_cast<std::chrono::seconds>(
                              std::chrono::steady_clock::now() - analyzer.start_time)
                              .count();

                auto now = std::chrono::steady_clock::now();
                if (std::chrono::duration_cast<std::chrono::seconds>(now - last_epoch).count() >= 1) {
                    std::cout << "1 sec frame : " << frame_count_per_sec << std::endl;
                    frame_count_per_sec = 0;
                    last_epoch = now;
                }

                if (frame_count == FPS) {
                    int blinks = analyzer.get_and_reset_blink_count();
                    total_blinks += blinks;
                    auto time_took = std::chrono::duration_cast<std::chrono::seconds>(now - last_epoch_per_fps).count();
                    last_epoch_per_fps = now;
                    std::cout << "blinks : " << blinks << " - " << total_blinks << std::endl;
                    std::cout << "time / 30 frames : " << time_took << std::endl;
                    frame_count = 0;
                }

                frame_count_per_sec++;

                cv::imshow("Face Analysis", processed_frame);
                char key = static_cast<char>(cv::waitKey(1));
                if (key == 'q' || !running) {
                    break;
                }
            }
        }
        catch (const std::exception& err) {
            std::cerr << "Failed in monitoring blinks: " << err.what() << std::endl;
        }

        capture.release();
        cv::destroyAllWindows();
    }

private:
    int frame_rate;
    int camera_index;
    bool running;
    cv::VideoCapture capture;
    int total_blinks;
    double runtime;
};

int main() {
    try {
        FrameHandler frame_handler;
        frame_handler.monitor_blinks();
    }
    catch (const std::exception& err) {
        std::cerr << "Failed in main app: " << err.what() << std::endl;
    }

    return 0;
}